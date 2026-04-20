"""Generate offline SVG QR codes for the teacher pacers.

Each SVG points to the GitHub Pages URL of its pacer. The resulting SVGs
are embedded by the pacer HTMLs via a fixed-position overlay so the
teacher can point a phone camera at the laptop screen and open the pacer
on their phone (handy when circulating during DOK-3 work).

Run:  python build_pacer_qr.py
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import segno

BASE_URL = "https://robjohncolson.github.io/Lesson_planning"

PACERS = [
    ("index.html",             "qr_index.svg"),
    ("Day_2_Pacer.html",       "qr_day2_pacer.svg"),
    ("Day_3_Pacer.html",       "qr_day3_pacer.svg"),
    ("Day_3_Pacer_short.html", "qr_day3_pacer_short.svg"),
    ("Day_23_Pacer.html",      "qr_day23_pacer.svg"),
    ("Day_45_Pacer.html",      "qr_day45_pacer.svg"),
    ("Day_6_Pacer.html",        "qr_day6_pacer.svg"),
    ("Day_7_Pacer.html",        "qr_day7_pacer.svg"),
    ("Day_8_Pacer.html",        "qr_day8_pacer.svg"),
    ("Day_23_Pacer_short.html", "qr_day23_pacer_short.svg"),
    ("Day_45_Pacer_short.html", "qr_day45_pacer_short.svg"),
]


def build():
    for pacer, out in PACERS:
        url = f"{BASE_URL}/{pacer}"
        qr = segno.make(url, error="m")
        # dark=navy to match the pacer header bar; light=None so it sits
        # transparently on whatever background the pacer places it on.
        qr.save(out, kind="svg", scale=4, border=0,
                dark="#0B3C6C", light=None, xmldecl=False, svgns=True)
        print(f"  {url}  \u2192  {out}")


if __name__ == "__main__":
    build()
