#!/usr/bin/env python3
"""Build reusable button-card templates; no instance-specific entities."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]

READING = r"""
const raw = entity?.state;
const n = typeof raw === 'string' && raw.trim() !== '' ? Number(raw) : NaN;
const kind = variables.harmony_kind || 'generic';
const restored = entity?.attributes?.restored === true;
const numeric = Number.isFinite(n);
const plausible = numeric && (kind === 'temperature' ? n >= -273.15
  : kind === 'humidity' ? n >= 0 && n <= 100
  : kind === 'co2' ? n >= 1 && n <= 1000000
  : kind === 'pm25' ? n >= 0 : true);
let reason = restored ? 'Status wird geladen' : !entity || raw === 'unknown' ? 'Keine Daten'
  : raw === 'unavailable' ? 'Offline' : !numeric ? 'Messwert ungültig'
  : !plausible ? 'Wert unplausibel' : '';
let tone = 'var(--secondary-text-color)';
let status = reason;
if (!reason) {
  if (kind === 'temperature') {
    tone = n > 28 ? 'var(--harmony-error)' : n > 25 ? 'var(--harmony-gold)' : 'var(--harmony-peach)';
    status = variables.harmony_note || 'Raumtemperatur';
  } else if (kind === 'humidity') {
    tone = n > 70 ? 'var(--harmony-error)' : n < 30 || n > 60 ? 'var(--harmony-gold)' : 'var(--harmony-cyan)';
    status = n < 30 ? 'Trocken' : n <= 60 ? 'Gut' : n <= 70 ? 'Erhöht' : 'Hoch';
  } else if (kind === 'pm25') {
    tone = n > 35 ? 'var(--harmony-error)' : n > 20 ? 'var(--harmony-peach)' : n > 10 ? 'var(--harmony-gold)' : 'var(--harmony-mint)';
    status = n <= 5 ? 'Sehr gut' : n <= 10 ? 'Gut' : n <= 20 ? 'Erhöht' : n <= 35 ? 'Schlecht' : 'Sehr schlecht';
  } else if (kind === 'co2') {
    const warning = variables.harmony_co2_warning ?? 800;
    const high = variables.harmony_co2_high ?? 1200;
    const alarm = variables.harmony_co2_alarm ?? 1600;
    tone = n >= alarm ? 'var(--harmony-error)' : n >= high ? 'var(--harmony-peach)' : n >= warning ? 'var(--harmony-gold)' : 'var(--harmony-mint)';
    status = n >= alarm ? 'Lüften!' : n >= high ? 'Schlecht' : n >= warning ? 'Erhöht' : 'Gut';
  } else {
    tone = 'var(--harmony-blue)';
    status = variables.harmony_note || '';
  }
}
"""


def js(expression):
    return "[[[\n" + READING.strip() + "\n" + expression + "\n]]]"


def templates():
    return {
        "harmony_base": {
            "show_name": True, "show_icon": True, "show_label": True,
            "tap_action": {"action": "more-info"}, "hold_action": {"action": "more-info"},
            "styles": {
                "card": [
                    {"border-radius": "var(--harmony-card-radius, 22px)"},
                    {"padding": "var(--harmony-card-padding, 16px)"},
                    {"box-shadow": "var(--harmony-card-shadow, none)"},
                    {"background": "var(--harmony-card-surface, var(--card-background-color))"},
                    {"border": "var(--harmony-card-border, 1px solid var(--divider-color))"},
                    {"box-sizing": "border-box"}, {"height": "100%"}, {"min-height": "84px"},
                ],
                "grid": [{"grid-template-areas": '"i n" "i l"'}, {"grid-template-columns": "40px minmax(0,1fr)"}, {"column-gap": "12px"}],
                "img_cell": [{"width": "40px"}, {"height": "40px"}, {"justify-self": "start"}, {"border-radius": "var(--harmony-icon-radius,13px)"}, {"background": "var(--harmony-icon-surface)"}],
                "icon": [{"width": "24px"}, {"color": "var(--harmony-tone, var(--primary-color))"}],
                "name": [{"justify-self": "start"}, {"text-align": "left"}, {"font-size": "var(--harmony-title-size,14px)"}, {"font-weight": 500}, {"white-space": "normal"}],
                "label": [{"justify-self": "start"}, {"text-align": "left"}, {"font-size": "var(--harmony-secondary-size,12px)"}, {"color": "var(--secondary-text-color)"}, {"white-space": "pre-line"}, {"line-height": "1.45"}, {"overflow-wrap": "anywhere"}],
            },
        },
        "harmony_metric": {
            "template": "harmony_base", "show_state": True,
            "variables": {"harmony_kind": "generic", "harmony_unit": "", "harmony_decimals": 1, "harmony_note": ""},
            "state_display": js("if (reason) return reason;\nreturn n.toLocaleString(variables.harmony_locale || 'de-CH', {minimumFractionDigits: variables.harmony_decimals ?? 1, maximumFractionDigits: variables.harmony_decimals ?? 1}) + (variables.harmony_unit ? ' ' + variables.harmony_unit : '');"),
            "label": js("return status;"),
            "styles": {
                "card": [
                    {"--harmony-tone": js("return tone;")},
                    {"padding": "var(--harmony-card-padding,16px) var(--harmony-card-padding,16px) 0"}, {"min-height": "150px"},
                    {"overflow": "hidden"}, {"background": "var(--harmony-metric-surface, var(--card-background-color))"},
                ],
                "grid": [{"grid-template-areas": '"i n" "s s" "l l"'}, {"grid-template-columns": "30px minmax(0,1fr)"}, {"grid-template-rows": "30px minmax(34px,auto) auto"}, {"column-gap": "8px"}, {"row-gap": "10px"}],
                "img_cell": [{"width": "30px"}, {"height": "30px"}, {"border-radius": "10px"}],
                "icon": [{"width": "19px"}],
                "name": [{"font-size": "13px"}, {"color": "var(--secondary-text-color)"}],
                "state": [{"justify-self": "start"}, {"text-align": "left"}, {"font-size": js("return reason ? '16px' : 'var(--harmony-value-size,26px)';")}, {"font-weight": 500}, {"line-height": "1.25"}, {"letter-spacing": "-0.03em"}, {"color": "var(--harmony-tone)"}, {"white-space": "normal"}],
                "label": [{"align-self": "end"}, {"background": "var(--harmony-footer-surface)"}, {"color": "var(--harmony-tone)"}, {"margin": "0 calc(-1 * var(--harmony-card-padding,16px))"}, {"width": "calc(100% + 2 * var(--harmony-card-padding,16px))"}, {"padding": "8px var(--harmony-card-padding,16px)"}, {"font-size": "var(--harmony-secondary-size,12px)"}, {"min-height": "33px"}, {"box-sizing": "border-box"}],
            },
        },
    }


if __name__ == "__main__":
    (ROOT / "templates/button_card_templates.yaml").write_text(
        "# Einmalig in die Rohkonfiguration eines Dashboards übernehmen.\n"
        + yaml.safe_dump({"button_card_templates": templates()}, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8"
    )
