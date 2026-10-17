#!/usr/bin/env python3
"""Generate the single HACS theme file. Requires PyYAML."""
from pathlib import Path
import copy
import yaml

ROOT = Path(__file__).resolve().parents[1]

PALETTES = {
    "Harmony Blue": {
        "bg": "#263e4b", "surface": "#355361", "header": "#35596e",
        "line": "#597988", "text": "#f0f7fa", "muted": "#c6d9e4",
        "site": "#b2ddfa", "site_rgb": "178, 221, 250", "secondary": "#3d6070",
    },
    "Harmony Green": {
        "bg": "#293f37", "surface": "#365247", "header": "#355747",
        "line": "#567366", "text": "#f0f7f2", "muted": "#c2d7ca",
        "site": "#a9d8bd", "site_rgb": "169, 216, 189", "secondary": "#3d5b4e",
    },
}

TOKENS = {
    "harmony-version": "1.0.0",
    "harmony-card-radius": "22px",
    "harmony-card-padding": "16px",
    "harmony-gap": "12px",
    "harmony-icon-size": "40px",
    "harmony-icon-radius": "13px",
    "harmony-title-size": "14px",
    "harmony-secondary-size": "12px",
    "harmony-value-size": "clamp(23px, 5.6vw, 29px)",
    "harmony-heading-size": "20px",
    "harmony-blue": "#91d3ff",
    "harmony-blue-rgb": "145, 211, 255",
    "harmony-cyan": "#8fdee4",
    "harmony-cyan-rgb": "143, 222, 228",
    "harmony-peach": "#ffc490",
    "harmony-peach-rgb": "255, 196, 144",
    "harmony-mint": "#a7e6ba",
    "harmony-mint-rgb": "167, 230, 186",
    "harmony-gold": "#ffda8b",
    "harmony-gold-rgb": "255, 218, 139",
    "harmony-violet": "#d0b8f0",
    "harmony-violet-rgb": "208, 184, 240",
    "harmony-error": "#ff9c9c",
    "harmony-error-rgb": "255, 156, 156",
    "harmony-warning": "#ffda8b",
    "harmony-warning-rgb": "255, 218, 139",
    "harmony-success": "#a7e6ba",
    "harmony-success-rgb": "167, 230, 186",
    "harmony-card-shadow": "0 3px 9px rgba(10, 24, 20, 0.10), inset 0 1px rgba(255,255,255,0.035)",
    "harmony-card-surface": "var(--card-background-color)",
    "harmony-card-border": "1px solid var(--divider-color)",
    "harmony-weather-surface": "linear-gradient(125deg, color-mix(in srgb, var(--harmony-blue) 22%, var(--card-background-color)), var(--card-background-color))",
    "harmony-metric-surface": "linear-gradient(145deg, color-mix(in srgb, var(--harmony-tone, var(--primary-color)) 13%, var(--card-background-color)), var(--card-background-color))",
    "harmony-status-surface": "color-mix(in srgb, var(--harmony-tone, var(--primary-color)) 8%, var(--card-background-color))",
    "harmony-footer-surface": "color-mix(in srgb, var(--harmony-tone, var(--primary-color)) 12%, var(--card-background-color))",
    "harmony-icon-surface": "color-mix(in srgb, var(--harmony-tone, var(--primary-color)) 23%, var(--card-background-color))",
    "ha-card-background": "var(--card-background-color)",
    "ha-card-border-radius": "var(--harmony-card-radius)",
    "ha-card-border-width": "1px",
    "ha-card-border-color": "var(--divider-color)",
    "ha-card-box-shadow": "var(--harmony-card-shadow)",
    "app-header-text-color": "var(--primary-text-color)",
    "app-theme-color": "var(--app-header-background-color)",
    "sidebar-background-color": "var(--card-background-color)",
    "sidebar-text-color": "var(--primary-text-color)",
    "sidebar-icon-color": "var(--secondary-text-color)",
    "sidebar-selected-text-color": "var(--primary-color)",
    "sidebar-selected-icon-color": "var(--primary-color)",
    "error-color": "var(--harmony-error)",
    "warning-color": "var(--harmony-warning)",
    "success-color": "var(--harmony-success)",
    "info-color": "var(--harmony-blue)",
    "state-light-active-color": "var(--harmony-gold)",
    "state-fan-active-color": "var(--harmony-cyan)",
    "state-climate-heat-color": "var(--harmony-peach)",
    "state-climate-cool-color": "var(--harmony-blue)",
    "state-climate-dry-color": "var(--harmony-cyan)",
    "state-climate-fan_only-color": "var(--harmony-cyan)",
    "state-climate-auto-color": "var(--harmony-violet)",
    "state-climate-heat_cool-color": "var(--harmony-violet)",
    "state-switch-active-color": "var(--harmony-mint)",
    "state-input_boolean-active-color": "var(--harmony-mint)",
    "state-binary_sensor-door-on-color": "var(--harmony-error)",
    "state-binary_sensor-door-off-color": "var(--harmony-mint)",
    "state-alarm_control_panel-triggered-color": "var(--harmony-error)",
    "state-alarm_control_panel-pending-color": "var(--harmony-warning)",
    "state-alarm_control_panel-armed_away-color": "var(--harmony-mint)",
    "state-alarm_control_panel-armed_home-color": "var(--harmony-mint)",
    "state-alarm_control_panel-armed_night-color": "var(--harmony-mint)",
    "mush-card-primary-font-size": "14px",
    "mush-card-secondary-font-size": "12px",
    "mush-card-primary-font-weight": "500",
    "mush-icon-size": "40px",
    "mush-icon-border-radius": "13px",
    "mush-title-font-size": "20px",
    "mush-subtitle-font-size": "13px",
    "mush-title-padding": "16px 4px 8px",
    "mush-title-spacing": "4px",
    "mush-rgb-blue": "var(--harmony-blue-rgb)",
    "mush-rgb-light-blue": "var(--harmony-blue-rgb)",
    "mush-rgb-cyan": "var(--harmony-cyan-rgb)",
    "mush-rgb-green": "var(--harmony-mint-rgb)",
    "mush-rgb-orange": "var(--harmony-peach-rgb)",
    "mush-rgb-amber": "var(--harmony-gold-rgb)",
    "mush-rgb-yellow": "var(--harmony-gold-rgb)",
    "mush-rgb-red": "var(--harmony-error-rgb)",
    "mush-rgb-purple": "var(--harmony-violet-rgb)",
    "weather-card-accent": "var(--harmony-blue)",
    "weather-card-cloud": "var(--harmony-blue)",
    "weather-card-rain": "var(--harmony-blue)",
    "weather-card-sun": "var(--harmony-gold)",
    "weather-card-tab-background": "color-mix(in srgb, var(--harmony-blue) 12%, var(--card-background-color))",
    "umweltkarte-good-color": "var(--harmony-mint)",
    "umweltkarte-acceptable-color": "#c3dda2",
    "umweltkarte-moderate-color": "var(--harmony-gold)",
    "umweltkarte-high-color": "var(--harmony-peach)",
    "umweltkarte-very-high-color": "var(--harmony-error)",
    "umweltkarte-extreme-color": "var(--harmony-violet)",
    "umweltkarte-chart-color": "var(--harmony-cyan)",
    "feiertage-family-color": "var(--harmony-gold)",
    "feiertage-next-color": "var(--harmony-blue)",
}

BASE_CSS = """ha-card {
  --card-primary-font-size: var(--harmony-title-size);
  --card-primary-font-weight: 500;
  --card-secondary-font-size: var(--harmony-secondary-size);
  --icon-size: var(--harmony-icon-size);
  --icon-border-radius: var(--harmony-icon-radius);
  border-radius: var(--harmony-card-radius);
  box-shadow: var(--harmony-card-shadow);
}
:host(.harmony-weather) ha-card, ha-card.harmony-weather {
  background: var(--harmony-weather-surface);
}
:host(.harmony-control) ha-card, ha-card.harmony-control {
  overflow: hidden;
}
"""


def build():
    themes = {}
    for name, p in PALETTES.items():
        theme = copy.deepcopy(TOKENS)
        theme.update({
            "card-mod-theme": name, "card-mod-card": BASE_CSS,
            "harmony-site-name": "Blue" if name.endswith("Blue") else "Green",
            "harmony-muted": p["muted"],
            "primary-color": p["site"], "rgb-primary-color": p["site_rgb"],
            "accent-color": p["site"], "light-primary-color": p["secondary"],
            "primary-background-color": p["bg"], "secondary-background-color": p["secondary"],
            "clear-background-color": p["bg"], "lovelace-background": p["bg"],
            "card-background-color": p["surface"], "app-header-background-color": p["header"],
            "primary-text-color": p["text"], "secondary-text-color": p["muted"],
            "text-primary-color": p["bg"], "divider-color": p["line"],
            "outline-color": p["line"], "input-fill-color": p["secondary"],
            "state-inactive-color": p["muted"],
            "modes": {"dark": {"primary-color": p["site"]}},
        })
        themes[name] = theme
    (ROOT / "themes/harmony.yaml").write_text(
        "# Harmony 1.0.0 – beide Farbvarianten in einer HACS-Theme-Datei.\n"
        "# Erzeugt mit tools/build_theme.py.\n" + yaml.safe_dump(themes, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8"
    )


if __name__ == "__main__":
    build()
