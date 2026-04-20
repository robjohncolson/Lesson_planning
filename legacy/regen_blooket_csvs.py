"""Regenerate Blooket CSVs for Lesson 3-5 from the question bank.

Pulls from `questionbank/registry.jsonl` using the tag scheme:
  blooket-pool   = DOK 1 only, safe for flashcard format
  do-now-bridge  = recall of previous-day rules (target ~25%)
  today-preview  = single-concept primer for today (~75%)
  day{N}-...     = day binding for lesson selection

Reports the bridge/preview ratio per day so it stays close to the 25/75
design rule.
"""
import qb


def build_day(day_tag: str, csv_path: str, label: str) -> None:
    pool = [q for q in qb.select(lesson="3-5", tags=["blooket-pool"])
            if day_tag in q.get("tags", [])]
    bridge  = [q for q in pool if "do-now-bridge"  in q.get("tags", [])]
    preview = [q for q in pool if "today-preview" in q.get("tags", [])]
    other   = [q for q in pool if q not in bridge and q not in preview]

    n = len(pool)
    if n == 0:
        print(f"[{label}] empty pool \u2014 skipping {csv_path}")
        return

    pct_bridge = 100 * len(bridge) / n
    pct_preview = 100 * len(preview) / n
    flag = " " if 20 <= pct_bridge <= 30 else "*"

    print(f"[{label}] {n:3d} items  |  bridge {len(bridge):3d} ({pct_bridge:4.1f}%)"
          f"  preview {len(preview):3d} ({pct_preview:4.1f}%)"
          f"  other {len(other):3d}  {flag}target ratio 25/75")

    qb.to_blooket_csv([q["id"] for q in pool], csv_path)
    print(f"  \u2192 wrote {csv_path}")


if __name__ == "__main__":
    build_day("day2-graphing",     "Blooket_Day2_GraphingFactoredForm.csv", "Day 2")
    build_day("day3-multiplicity", "Blooket_Day3_Multiplicity.csv",         "Day 3")
