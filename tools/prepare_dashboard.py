#!/usr/bin/env python3
"""Prepare a local dashboard copy for Harmony. Never writes to Home Assistant.

Input: a dashboard YAML/JSON, or a HA Pruefexport ZIP containing one dashboard.
Runtime actions, entity IDs, features and routes are retained. Output is private.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import re
import zipfile
import yaml

from build_templates import templates

ROOT = Path(__file__).resolve().parents[1]

BASE = """ha-card {
  border-radius: var(--harmony-card-radius, 22px);
  box-shadow: var(--harmony-card-shadow, none);
  --card-primary-font-size: var(--harmony-title-size, 14px);
  --card-primary-font-weight: 500;
  --card-secondary-font-size: var(--harmony-secondary-size, 12px);
  --icon-size: var(--harmony-icon-size, 40px);
}
"""
INFO = """.primary {
  font-size: var(--harmony-title-size, 14px) !important;
  font-weight: 500 !important;
  white-space: normal !important;
  overflow-wrap: anywhere;
}
.secondary {
  font-size: var(--harmony-secondary-size, 12px) !important;
  line-height: 1.45 !important;
  white-space: pre-line !important;
  overflow-wrap: anywhere;
}
"""
COLORS = {
    "70,140,255": "blue", "60,150,255": "blue", "40,200,255": "cyan",
    "60,200,220": "cyan", "38,166,154": "cyan", "70,220,110": "mint",
    "40,190,110": "mint", "40,190,100": "mint", "255,155,40": "peach",
    "255,160,50": "peach", "255,170,40": "gold", "255,193,7": "gold",
    "255,210,50": "gold", "255,70,70": "error", "255,80,70": "error",
    "255,60,60": "error", "255,140,30": "peach", "255,130,30": "peach",
    "160,110,230": "violet",
}


def css_restyle(text: str) -> str:
    # Only visual declarations; never rewrite state guards, routes or actions.
    def background(match):
        value = match.group(0)
        channels = re.findall(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", value)
        if any(all(int(c) <= 48 for c in rgb) for rgb in channels):
            return "background: var(--harmony-card-surface, var(--card-background-color));"
        return value
    text = re.sub(r"background\s*:\s*linear-gradient\([\s\S]*?\)\s*;", background, text)
    def flat_background(match):
        if all(int(match.group(i)) <= 48 for i in [1, 2, 3]):
            return "background: var(--harmony-card-surface, var(--card-background-color));"
        return match.group(0)
    text = re.sub(r"background\s*:\s*rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)[^;]*;", flat_background, text)
    text = re.sub(r"box-shadow\s*:\s*[^;{}]+;", "box-shadow: var(--harmony-card-shadow, none);", text)
    text = re.sub(r"border-radius:\s*(?:18|20|22|24)px\s*;", "border-radius: var(--harmony-card-radius,22px);", text)
    text = text.replace("24px 24px 0 0", "var(--harmony-card-radius) var(--harmony-card-radius) 0 0")
    text = text.replace("0 0 24px 24px", "0 0 var(--harmony-card-radius) var(--harmony-card-radius)")
    for rgb, role in COLORS.items():
        pattern = r"rgba\(\s*" + r"\s*,\s*".join(rgb.split(",")) + r"\s*,"
        text = re.sub(pattern, f"rgba(var(--harmony-{role}-rgb),", text)
        # Some Jinja styles store RGB triplets in a local colour mapping.
        text = text.replace("'" + rgb + "'", "'var(--harmony-" + role + "-rgb)'")
    return text


def transform_strings(value):
    if isinstance(value, str):
        return css_restyle(value)
    if isinstance(value, dict):
        return {k: transform_strings(v) for k, v in value.items()}
    if isinstance(value, list):
        return [transform_strings(v) for v in value]
    return value


def add_style(card: dict, css: str, klass: str | None = None, mushroom=False):
    mod = card.setdefault("card_mod", {})
    if klass:
        classes = mod.get("class", "")
        if isinstance(classes, list):
            classes = " ".join(classes)
        mod["class"] = " ".join(dict.fromkeys((classes + " harmony " + klass).split()))
    old = mod.get("style", "")
    if mushroom:
        if isinstance(old, str):
            old = {".": old}
        old["."] = old.get(".", "") + "\n" + css
        old["mushroom-state-info$"] = old.get("mushroom-state-info$", "") + "\n" + INFO
        old["mushroom-shape-icon$"] = old.get("mushroom-shape-icon$", "") + "\n.shape { border-radius: var(--harmony-icon-radius,13px) !important; }"
        mod["style"] = old
    elif isinstance(old, dict):
        old["."] = old.get(".", "") + "\n" + css
    else:
        mod["style"] = old + "\n" + css


def kind_for(entity: str) -> str | None:
    if not entity.startswith("sensor."):
        return None
    for suffix, kind in [("_temperatur", "temperature"), ("_luftfeuchtigkeit", "humidity"), ("_kohlendioxid", "co2"), ("_pm25", "pm25")]:
        if entity.endswith(suffix):
            return kind
    return None


def metric_card(card, kind):
    units = {"temperature": "°C", "humidity": "%", "co2": "ppm", "pm25": "µg/m³"}
    new = {k: copy.deepcopy(v) for k, v in card.items() if k in [
        "entity", "icon", "tap_action", "hold_action", "double_tap_action", "grid_options", "visibility"
    ]}
    new.update({"type": "custom:button-card", "template": "harmony_metric", "name": card.get("primary", kind),
                "variables": {"harmony_kind": kind, "harmony_unit": units[kind], "harmony_decimals": 0 if kind == "co2" else 1,
                              "harmony_note": "Raumtemperatur" if kind == "temperature" else "", "harmony_locale": "de-DE"}})
    dependencies = card.get("entity_id")
    if isinstance(dependencies, list):
        new["triggers_update"] = copy.deepcopy(dependencies)
    return new


def prepare(dashboard, theme):
    result = copy.deepcopy(dashboard)
    counts = {"cards": 0, "metric_cards": 0, "styles": 0, "masked_alignment_repaired": 0}
    base_templates = result.setdefault("button_card_templates", {})
    # Retain existing named templates and logic, replacing only their presentation.
    base_templates.update(templates())
    if "ob_base" in base_templates:
        base_templates["ob_base"] = {"template": "harmony_base"}
    if "ob_metric" in base_templates:
        base_templates["ob_metric"] = {"template": "harmony_metric"}

    def walk(node):
        if isinstance(node, list):
            return [walk(v) for v in node]
        if not isinstance(node, dict):
            return node
        out = {k: walk(v) for k, v in node.items()}
        typ = out.get("type", "")
        entity = out.get("entity", "")
        if not isinstance(entity, str):
            entity = ""
        if "card_mod" in out:
            out["card_mod"] = transform_strings(out["card_mod"])
        # Export sanitization can replace a common CSS alignment word.
        if out.get("justify-self") == "[MASKIERT]":
            out["justify-self"] = "start"
            counts["masked_alignment_repaired"] += 1
        if not typ:
            return out
        counts["cards"] += 1
        if typ in ["custom:mushroom-legacy-template-card", "custom:mushroom-template-card"]:
            kind = kind_for(entity)
            if kind and "alpstuga" in entity:
                counts["metric_cards"] += 1
                return metric_card(out, kind)
            if out.get("layout") == "vertical" and (entity.startswith("binary_sensor.") or entity.startswith("climate.")):
                out["layout"] = "horizontal"
            add_style(out, BASE + "ha-card { background: var(--harmony-card-surface, var(--card-background-color)); }", "harmony-status", mushroom=True)
            counts["styles"] += 1
        elif typ == "tile":
            if out.get("features"):
                out["features_position"] = "bottom"
                out.setdefault("grid_options", {})["rows"] = "auto"
            if entity.startswith("light."):
                tone = "{{ 'var(--harmony-gold)' if is_state(config.entity, 'on') else 'var(--secondary-text-color)' }}"
            elif entity.startswith("fan."):
                tone = "{{ 'var(--harmony-cyan)' if is_state(config.entity, 'on') else 'var(--secondary-text-color)' }}"
            else:
                tone = "{{ {'heat':'var(--harmony-peach)', 'cool':'var(--harmony-blue)', 'dry':'var(--harmony-cyan)', 'fan_only':'var(--harmony-cyan)', 'auto':'var(--harmony-violet)', 'heat_cool':'var(--harmony-violet)'}.get(states(config.entity), 'var(--secondary-text-color)') }}"
            add_style(out, BASE + "ha-card { --harmony-tone: " + tone + "; --tile-color: var(--harmony-tone) !important; background: var(--harmony-card-surface); overflow: hidden; --ha-tile-icon-border-radius: var(--harmony-icon-radius); }\nhui-card-features { background: var(--harmony-footer-surface); border-radius: 14px; box-sizing: border-box; padding: 10px !important; }", "harmony-control")
            counts["styles"] += 1
        elif typ == "custom:mushroom-title-card":
            add_style(out, ":host { --title-font-size: var(--harmony-heading-size,20px); --subtitle-font-size: 13px; --title-padding: 16px 4px 8px; --title-spacing: 4px; }", "harmony-heading")
        elif typ == "custom:button-card":
            if out.get("template") == "ob_metric":
                v = out.setdefault("variables", {})
                v.update({"harmony_kind": v.get("kind") or kind_for(entity) or "generic", "harmony_unit": v.get("unit", ""), "harmony_decimals": v.get("decimals", 1), "harmony_note": v.get("note", "")})
                if v["harmony_kind"] == "co2":
                    v.update({"harmony_co2_warning": 1200, "harmony_co2_high": 2000, "harmony_co2_alarm": 2000})
            styles = out.get("styles", {})
            for group in ["card", "name", "label"]:
                for rule in styles.get(group, []):
                    if group == "card":
                        if "border-radius" in rule and rule["border-radius"] in ["18px", "20px", "22px", "24px"]:
                            rule["border-radius"] = "var(--harmony-card-radius,22px)"
                        if "box-shadow" in rule:
                            rule["box-shadow"] = "var(--harmony-card-shadow,none)"
                        if "background" in rule and isinstance(rule["background"], str) and not rule["background"].lstrip().startswith("[[["):
                            rewritten = css_restyle("background: " + rule["background"] + ";")
                            rule["background"] = rewritten.removeprefix("background: ").removesuffix(";")
                    if rule.get("font-weight") in ["600", 600, "700", 700]:
                        rule["font-weight"] = 500
        elif typ in ["picture-entity", "custom:mini-graph-card"]:
            add_style(out, BASE, "harmony-media" if typ == "picture-entity" else "harmony-graph")
        elif typ == "custom:arandjelovac-weather-card":
            add_style(out, "ha-card { background: var(--harmony-weather-surface) !important; }", "harmony-weather")
        elif typ in ["custom:ha-umweltkarte", "custom:wetterwarnungen-card", "custom:feiertage-serbien-card", "custom:arandjelovac-live-card"]:
            add_style(out, BASE + "ha-card { background: var(--harmony-card-surface); }\n.symbol { background: color-mix(in srgb, var(--tone, var(--harmony-cyan)) 20%, var(--card-background-color)); }", "harmony-information")
        elif typ == "custom:stack-in-card":
            # Forecast stack contains a deliberately transparent inner forecast.
            if any(c.get("type") == "weather-forecast" for c in out.get("cards", [])):
                add_style(out, "ha-card { background: var(--harmony-weather-surface); border-radius: var(--harmony-card-radius); box-shadow: var(--harmony-card-shadow); overflow: hidden; }", "harmony-weather")
        elif typ == "grid":
            children = out.get("cards", [])
            # Give door histories and detailed infrastructure room for readable lines.
            if children and all(c.get("entity", "").startswith("binary_sensor.myggbett_") for c in children):
                out["columns"] = 1
            if children and all(c.get("entity", "").endswith("_zustand") for c in children):
                out["columns"] = 1
        elif typ == "custom:auto-entities":
            f = out.get("filter", {})
            if isinstance(f.get("template"), str):
                f["template"] = css_restyle(f["template"])
        return out

    # Do not traverse template definitions as cards or change existing action logic.
    result["views"] = walk(result.get("views", []))
    for view in result["views"]:
        view["theme"] = theme
    # Only layout properties in original button templates are standardized.
    for key in ["ob_door", "ob_quick"]:
        if key not in base_templates:
            continue
        t = base_templates[key]
        for rule in t.get("styles", {}).get("card", []):
            if "border-radius" in rule:
                rule["border-radius"] = "var(--harmony-card-radius,22px)"
        if key == "ob_door":
            t.setdefault("styles", {}).setdefault("card", []).append({"box-shadow": "var(--harmony-card-shadow)"})
    return result, counts


class ReadableDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def represent_str(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|" if "\n" in data else None)


ReadableDumper.add_representer(str, represent_str)


def dump_dashboard(data):
    return yaml.dump(data, Dumper=ReadableDumper, sort_keys=False, allow_unicode=True, width=120)


def load_input(path):
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            names = [n for n in archive.namelist() if n.startswith("dashboards/dashboard-") and n.endswith(".json")]
            if len(names) != 1:
                raise ValueError("Expected one named dashboard in the ZIP; pass an individual YAML/JSON instead")
            return json.loads(archive.read(names[0]))
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--theme", choices=["Harmony Blue", "Harmony Green"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    dashboard = load_input(args.input)
    if not isinstance(dashboard, dict) or not isinstance(dashboard.get("views"), list):
        raise ValueError("Input must be a dashboard with views")
    if "harmony_metric" in dashboard.get("button_card_templates", {}):
        raise ValueError("Dashboard is already prepared for Harmony; use the original dashboard")
    migrated, counts = prepare(dashboard, args.theme)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(dump_dashboard(migrated), encoding="utf-8")
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
