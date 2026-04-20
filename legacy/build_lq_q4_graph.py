"""Generate a clean student-facing graph of y = x\u00b3 + 3x\u00b2 + x + 3
for the Combined Day 2-3 Do Now (Savvas Lesson Quiz Q4).

The Savvas answer-key image highlights the correct choice; this version
shows only the graph with no answer indication.

Output: assets/lq_q4_student_graph.png
"""
import os
import numpy as np
import matplotlib.pyplot as plt


def build(path, *, xlim=(-4.5, 2.5), ylim=(-3, 7)):
    x = np.linspace(xlim[0], xlim[1], 600)
    y = x**3 + 3*x**2 + x + 3

    fig, ax = plt.subplots(figsize=(3.6, 3.0), dpi=180)
    ax.axhline(0, color="black", linewidth=1.0)
    ax.axvline(0, color="black", linewidth=1.0)

    # Savvas-style minor grid every 1, major grid every 2
    ax.set_xticks(range(int(xlim[0]), int(xlim[1]) + 1, 1), minor=True)
    ax.set_yticks(range(int(ylim[0]), int(ylim[1]) + 1, 1), minor=True)
    ax.set_xticks([-4, -2, 0, 2])
    ax.set_yticks([2, 4, 6])
    ax.grid(which="minor", color="#CCCCCC", linewidth=0.3)
    ax.grid(which="major", color="#999999", linewidth=0.5)

    ax.plot(x, y, color="#0B3C6C", linewidth=1.8)

    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.tick_params(axis="both", labelsize=8, length=2, pad=1)
    ax.text(xlim[1] - 0.3, 0.35, "x", fontsize=10, fontstyle="italic")
    ax.text(0.25, ylim[1] - 0.6, "y", fontsize=10, fontstyle="italic")

    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout(pad=0.2)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  wrote {path}")


if __name__ == "__main__":
    build("assets/lq_q4_student_graph.png")
