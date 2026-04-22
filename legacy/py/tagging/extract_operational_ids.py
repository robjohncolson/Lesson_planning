"""Scan every build_L*_packets.py and extract the ID lists it imports from the bank.
Writes tagging/operational_ids.json mapping builder filename -> {list_name: [ids]}.
"""
import json, re
from pathlib import Path

NAMES = ("DO_NOW_IDS","LAUNCH_IDS","EXPLORE_IDS","TRY_IT_IDS","PRACTICE_IDS",
         "EXIT_IDS","REINFORCE_IDS","DOK3_ID","DOK3_PAIR_ID")

out = {}
for p in sorted(Path('.').glob('build_L*_packets.py')):
    src = p.read_text(encoding='utf-8')
    d = {}
    annotations: dict[str, str] = {}
    for name in NAMES:
        # list form
        m = re.search(rf'^{name}\s*=\s*\[([^\]]+)\]', src, re.MULTILINE | re.DOTALL)
        if m:
            body = m.group(1)
            ids = re.findall(r'"([^"]+)"', body)
            if ids:
                d[name] = ids
            # pull inline comment (if any) from the same line as the ID literal
            for line in body.splitlines():
                line_m = re.search(r'"([^"]+)"\s*,?\s*#\s*(.+?)\s*$', line)
                if line_m:
                    annotations[line_m.group(1)] = line_m.group(2).strip()
            continue
        # scalar form
        m = re.search(rf'^{name}\s*=\s*"([^"]+)"\s*(?:#\s*(.+?))?\s*$', src, re.MULTILINE)
        if m:
            d[name] = [m.group(1)]
            if m.group(2):
                annotations[m.group(1)] = m.group(2).strip()
    # also pull docstring lines 1-24 for role/cadence context
    docstring_match = re.match(r'"""(.*?)"""', src, re.DOTALL)
    doc = docstring_match.group(1)[:1500] if docstring_match else ""
    out[p.name] = {"ids": d, "doc_head": doc, "annotations": annotations}

Path('tagging/operational_ids.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
print(f"Extracted {sum(len(v['ids']) for v in out.values())} ID-list assignments across {len(out)} builders.")
