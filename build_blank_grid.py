"""Generate a clean blank Cartesian coordinate grid PNG for student sketches.

Output: assets/blank_grid.png  (reused across packets)
"""
import os
import matplotlib.pyplot as plt


def build(path, *, xlim=(-6, 6), ylim=(-8, 8), minor_step=1,
          major_step=2, size=(4.0, 3.0)):
    fig, ax = plt.subplots(figsize=size, dpi=180)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axhline(0, color="black", linewidth=1.2)
    ax.axvline(0, color="black", linewidth=1.2)
    # Minor gridlines
    ax.set_xticks(range(xlim[0], xlim[1] + 1, minor_step), minor=True)
    ax.set_yticks(range(ylim[0], ylim[1] + 1, minor_step), minor=True)
    # Major ticks + labels
    xmajor = list(range(xlim[0], xlim[1] + 1, major_step))
    ymajor = list(range(ylim[0], ylim[1] + 1, major_step))
    ax.set_xticks(xmajor)
    ax.set_yticks(ymajor)
    ax.grid(which="minor", color="#CCCCCC", linewidth=0.3)
    ax.grid(which="major", color="#999999", linewidth=0.5)
    ax.tick_params(axis="both", labelsize=7, length=2, pad=1, color="#666666")
    # Axis-label placement (tiny x and y at the ends)
    ax.text(xlim[1] - 0.2, 0.3, "x", fontsize=9, fontstyle="italic")
    ax.text(0.2, ylim[1] - 0.6, "y", fontsize=9, fontstyle="italic")
    # Remove spines, rely on axis lines
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_aspect("auto")
    fig.tight_layout(pad=0.2)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  wrote {path}")


if __name__ == "__main__":
    build("assets/blank_grid.png")
