#!/usr/bin/env python3
"""Check generated theme tokens, YAML structure and non-live metric state handling."""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import yaml

ROOT = Path(__file__).resolve().parents[1]


def main():
    theme_files = list((ROOT / "themes").glob("*.yaml"))
    assert len(theme_files) == 1, "HACS expects a single theme configuration file"
    themes = yaml.safe_load(theme_files[0].read_text())
    assert set(themes) == {"Harmony Blue", "Harmony Green"}
    for name, theme in themes.items():
        assert theme["card-mod-theme"] == name
        assert "dark" in theme["modes"]
        refs = set(re.findall(r"var\(--(harmony-[\w-]+)", json.dumps(theme)))
        assert refs - set(theme) <= {"harmony-tone"}, refs - set(theme)
    templates = yaml.safe_load((ROOT / "templates/button_card_templates.yaml").read_text())["button_card_templates"]
    metric = templates["harmony_metric"]
    variables = metric["variables"]
    tone = metric["styles"]["card"][0]["--harmony-tone"]
    cases = [
        {"kind": "co2", "raw": "444", "label": "Gut", "tone": "mint"},
        {"kind": "co2", "raw": "800", "label": "Erhöht", "tone": "gold"},
        {"kind": "co2", "raw": "1200", "label": "Schlecht", "tone": "peach"},
        {"kind": "co2", "raw": "1600", "label": "Lüften!", "tone": "error"},
        {"kind": "co2", "raw": "0", "label": "Wert unplausibel", "tone": "secondary"},
        {"kind": "humidity", "raw": "0", "label": "Trocken", "tone": "gold"},
        {"kind": "humidity", "raw": "101", "label": "Wert unplausibel", "tone": "secondary"},
        {"kind": "pm25", "raw": "0", "label": "Sehr gut", "tone": "mint"},
        {"kind": "pm25", "raw": "-1", "label": "Wert unplausibel", "tone": "secondary"},
        {"kind": "temperature", "raw": "-274", "label": "Wert unplausibel", "tone": "secondary"},
        {"kind": "temperature", "raw": "0", "label": "Raumtemperatur", "tone": "peach"},
    ]
    for raw, label in [("unknown", "Keine Daten"), ("unavailable", "Offline"), ("", "Messwert ungültig"), ("NaN", "Messwert ungültig"), ("Infinity", "Messwert ungültig")]:
        cases.append({"kind": "co2", "raw": raw, "label": label, "tone": "secondary"})
    cases.append({"kind": "co2", "raw": "444", "restored": True, "label": "Status wird geladen", "tone": "secondary"})
    payload = {"state": metric["state_display"], "label": metric["label"], "tone": tone, "variables": variables, "cases": cases}
    node = os.environ.get("CODEX_PRIMARY_RUNTIME_NODE") or shutil.which("node")
    if not node:
        raise RuntimeError("Node.js required for executable metric-state checks")
    program = r"""
const fs = require('fs');
const p = JSON.parse(fs.readFileSync(0,'utf8'));
const run = (code, entity, variables) => new Function('entity','variables',code.slice(3,-3))(entity,variables);
for (const test of p.cases) {
  const entity = {state:test.raw, attributes:{restored:!!test.restored}};
  const vars = {...p.variables, harmony_kind:test.kind};
  const label = run(p.label,entity,vars);
  const tone = run(p.tone,entity,vars);
  const state = run(p.state,entity,vars);
  if (label !== test.label || !tone.includes(test.tone)) throw Error(JSON.stringify({test,label,tone,state}));
  if (test.tone === 'secondary' && state === '0') throw Error('Missing value became zero');
}
const vars={...p.variables,harmony_kind:'co2'};
if (run(p.label,undefined,vars)!=='Keine Daten') throw Error('Missing entity');
console.log(p.cases.length+' metric-state cases passed.');
"""
    subprocess.run([node, "-e", program], input=json.dumps(payload), text=True, check=True)
    print("Theme structure, custom token references and generated templates passed.")


if __name__ == "__main__":
    main()
