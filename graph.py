"""
Spending Line Chart — 12-month multi-category trend
Reads all *_categorised.csv files from a folder and plots a line chart
styled after the OECD/EU reference graph (dotted grid, right-side labels).

Each _categorised.csv must have two columns: Category, Amount
(exactly as saved by the Spending Categoriser app).

Usage:
    python spending_line_chart.py
    # or override the folder:
    python spending_line_chart.py /path/to/your/csv/folder

Requires:  pip install matplotlib
"""

import csv
import sys
import re
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    import numpy as np
except ImportError:
    sys.exit("matplotlib is required.  Run:  pip install matplotlib")

# ── Folder containing the categorised CSV files ─────────────────────────────
DEFAULT_FOLDER = Path("/Users/neerajpatel/Finance/Credit Card Statements/2026")

# ── Colours matching the main app ───────────────────────────────────────────
CAT_COLOURS = {
    "Groceries":            "#1D9E75",
    "Dining / Eating Out":  "#D85A30",
    "Transport":            "#185FA5",
    "Fuel":                 "#2874A6",
    "Bills & Utilities":    "#534AB7",
    "Shopping":             "#BA7517",
    "Entertainment":        "#D4537E",
    "Health & Medical":     "#C0392B",
    "Travel":               "#0F6E56",
    "Income":               "#27AE60",
    "Other":                "#5F5E5A",
}

MONTH_ORDER = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

# ── Helpers ──────────────────────────────────────────────────────────────────

def month_label_from_path(p: Path) -> str:
    """Extract a short month label from the filename, ignoring '_categorised'."""
    stem = p.stem.lower().replace("_categorised", "")
    month_names = {
        "january": "Jan",   "february": "Feb",  "march": "Mar",
        "april": "Apr",     "may": "May",        "june": "Jun",
        "july": "Jul",      "august": "Aug",     "september": "Sep",
        "october": "Oct",   "november": "Nov",   "december": "Dec",
        "jan": "Jan", "feb": "Feb", "mar": "Mar", "apr": "Apr",
        "jun": "Jun", "jul": "Jul", "aug": "Aug", "sep": "Sep",
        "oct": "Oct", "nov": "Nov", "dec": "Dec",
    }
    for word, label in month_names.items():
        if word in stem:
            return label
    # Numeric month fallback
    m = re.search(r'(?<!\d)(0?[1-9]|1[0-2])(?!\d)', stem)
    if m:
        return MONTH_ORDER[int(m.group(1)) - 1]
    return p.stem  # last resort


def load_categorised_csv(path: Path) -> dict:
    """Read a _categorised.csv → {Category: Amount}."""
    totals: dict[str, float] = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cat = row.get("Category", "").strip()
            if not cat or cat == "Payment / Refund":
                continue
            try:
                amt = float(row.get("Amount", 0) or 0)
            except ValueError:
                amt = 0.0
            totals[cat] = totals.get(cat, 0) + amt
    return totals


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FOLDER

    if not folder.exists():
        sys.exit(f"Folder not found: {folder}")

    csv_files = sorted(folder.glob("*_categorised.csv"))
    if not csv_files:
        sys.exit(f"No *_categorised.csv files found in: {folder}")

    print(f"Found {len(csv_files)} categorised file(s):")
    for f in csv_files:
        print(f"  {f.name}")

    month_data: dict[str, dict[str, float]] = {}
    month_sort_key: dict[str, int] = {}

    for csv_path in csv_files:
        label = month_label_from_path(csv_path)
        month_sort_key[label] = MONTH_ORDER.index(label) if label in MONTH_ORDER else 99
        try:
            totals = load_categorised_csv(csv_path)
        except Exception as e:
            print(f"  Warning: could not read {csv_path.name}: {e}")
            continue
        if label not in month_data:
            month_data[label] = {}
        for cat, val in totals.items():
            month_data[label][cat] = month_data[label].get(cat, 0) + val

    if not month_data:
        sys.exit("No data could be loaded.")

    months = sorted(month_data.keys(), key=lambda m: month_sort_key.get(m, 99))

    all_cats: set = set()
    for m in months:
        all_cats.update(month_data[m].keys())
    all_cats.discard("Payment / Refund")

    active_cats = [c for c in all_cats if any(month_data[m].get(c, 0) > 0 for m in months)]
    active_cats.sort(key=lambda c: -sum(month_data[m].get(c, 0) for m in months))

    x = np.arange(len(months))
    n_cats = len(active_cats)

    # ── Small-multiple layout: one panel per category ─────────────────────
    ncols = 3
    nrows = (n_cats + ncols - 1) // ncols
    fig, axes = plt.subplots(
        nrows, ncols,
        figsize=(13, nrows * 2.6 + 1.2),
        facecolor="white",
    )
    fig.suptitle(
        "Monthly Spending by Category  (NZD)",
        fontsize=13, fontweight="bold", color="#1A1A1A",
        x=0.01, ha="left", y=0.99,
    )

    axes_flat = axes.flatten() if n_cats > 1 else [axes]

    for i, cat in enumerate(active_cats):
        ax = axes_flat[i]
        colour = CAT_COLOURS.get(cat, "#888780")
        y = np.array([month_data[m].get(cat, 0) for m in months])

        ax.set_facecolor("#FAFAFA")
        ax.fill_between(x, y, alpha=0.10, color=colour, zorder=1)
        ax.plot(x, y, color=colour, linewidth=2.2, marker="o",
                markersize=5, markerfacecolor="white",
                markeredgecolor=colour, markeredgewidth=1.8, zorder=3)

        # Dollar value above each point
        for xi, yi in zip(x, y):
            if yi > 0:
                ax.text(xi, yi, f"${yi:,.0f}",
                        ha="center", va="bottom",
                        fontsize=7.5, color=colour, fontweight="bold")

        # Panel title (category name in its colour)
        ax.set_title(cat, fontsize=10, fontweight="bold",
                     color=colour, pad=6, loc="left")

        # X axis — month labels
        ax.set_xticks(x)
        ax.set_xticklabels(months, fontsize=8, color="#555555")
        ax.tick_params(axis="x", length=0)

        # Y axis — minimal
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
        ax.tick_params(axis="y", labelsize=7.5, colors="#888888", length=0)

        # Give breathing room above the highest point for the label
        y_max = y.max() if y.max() > 0 else 1
        ax.set_ylim(0, y_max * 1.30)
        ax.set_xlim(-0.4, len(months) - 0.6)

        # Dotted horizontal grid
        ax.yaxis.grid(True, linestyle=":", linewidth=0.6, color="#CCCCCC", zorder=0)
        ax.xaxis.grid(False)
        ax.set_axisbelow(True)

        # Remove all spines except bottom
        for spine in ["top", "right", "left"]:
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color("#CCCCCC")

    # Hide any unused panels
    for j in range(n_cats, len(axes_flat)):
        axes_flat[j].set_visible(False)

    fig.text(0.01, 0.005, f"Source: {folder}", fontsize=7, color="#AAAAAA")
    plt.tight_layout(rect=[0, 0.01, 1, 0.97])
    plt.show()


if __name__ == "__main__":
    main()