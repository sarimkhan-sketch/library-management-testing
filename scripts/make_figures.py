"""Draws the two figures used in the report and slides into reports/figures/."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from report_data import FIGURES, load

SURFACE = "#fcfcfb"
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
PASS, FAIL, BLUE = "#0ca30c", "#d03b3b", "#2a78d6"


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK_2, length=0, labelsize=10)


def cycles_chart(cycles):
    fig, ax = plt.subplots(figsize=(7, 3.4), facecolor=SURFACE)
    style(ax)
    names = [c["cycle"] for c in cycles]
    passed = [c["passed"] for c in cycles]
    failed = [c["failed"] for c in cycles]
    ax.bar(names, passed, width=0.5, color=PASS, edgecolor=SURFACE, linewidth=2, label="Passed")
    ax.bar(names, failed, width=0.5, bottom=passed, color=FAIL, edgecolor=SURFACE, linewidth=2,
           label="Failed")
    for i, (p, f) in enumerate(zip(passed, failed)):
        ax.text(i, p / 2, f"{p} passed", ha="center", va="center", color="white", fontsize=10,
                fontweight="bold")
        if f:
            ax.text(i, p + f / 2, f"{f} failed", ha="center", va="center", color="white",
                    fontsize=10, fontweight="bold")
    ax.set_ylim(0, 50)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_ylabel("Test cases (45 per cycle)", color=INK_2, fontsize=10)
    ax.set_title("Test results per execution cycle", loc="left", color=INK, fontsize=12,
                 fontweight="bold")
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(1, 1), labelcolor=INK_2)
    fig.tight_layout()
    fig.savefig(FIGURES / "fig1_cycles.png", dpi=200)
    plt.close(fig)


def coverage_chart(coverage):
    files = sorted(coverage, key=lambda f: coverage[f]["percent_covered"])
    pct = [coverage[f]["percent_covered"] for f in files]
    fig, ax = plt.subplots(figsize=(7, 3.0), facecolor=SURFACE)
    style(ax)
    ax.barh(files, pct, height=0.55, color=BLUE)
    for y, (f, p) in enumerate(zip(files, pct)):
        s = coverage[f]
        ax.text(p + 1, y, f"{p:.0f}%  ({s['covered_lines']}/{s['num_statements']} lines)",
                va="center", color=INK_2, fontsize=9)
    ax.set_xlim(0, 125)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title("Statement coverage by module (cycle 3, pytest-cov)", loc="left", color=INK,
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(FIGURES / "fig2_coverage.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    FIGURES.mkdir(parents=True, exist_ok=True)
    data = load()
    cycles_chart(data["cycles"])
    coverage_chart(data["coverage"])
    print("figures saved to", FIGURES)
