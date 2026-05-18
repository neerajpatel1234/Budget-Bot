"""
Spending Line Chart — 12-month multi-category trend
Reads all *_categorised.csv files from a folder and plots a styled dashboard.

Each _categorised.csv must have two columns: Category, Amount
(as saved by the Spending Categoriser app).

Usage:
    python spending_line_chart.py
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
    import matplotlib.patches as mpatches
    import matplotlib.font_manager as fm
    import numpy as np
except ImportError:
    sys.exit("matplotlib is required.  Run:  pip install matplotlib")

# ── Folder containing the categorised CSV files ─────────────────────────────
DEFAULT_FOLDER = Path("/Users/neerajpatel/Finance/Credit Card Statements/2026")

# ── Design tokens (matches the GUI) ─────────────────────────────────────────
BG          = "#0F1117"
PANEL       = "#171B26"
BORDER      = "#252A3A"
SURFACE     = "#1E2235"
TEXT_PRI    = "#E8EAF0"
TEXT_SEC    = "#8892A4"
TEXT_DIM    = "#3A4155"
GRID_COL    = "#1C2133"

CAT_COLOURS = {
    "Groceries":            "#2ECC71",
    "Dining / Eating Out":  "#E74C3C",
    "Transport":            "#3498DB",
    "Fuel":                 "#1ABC9C",
    "Bills & Utilities":    "#9B59B6",
    "Shopping":             "#F39C12",
    "Entertainment":        "#E91E8C",
    "Health & Medical":     "#FF5252",
    "Travel":               "#00BCD4",
    "Income":               "#27AE60",
    "Other":                "#78909C",
}

MONTH_ORDER = ["Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"]

# ── Helpers ──────────────────────────────────────────────────────────────────

def month_label_from_path(p: Path) -> str:
    stem = p.stem.lower().replace("_categorised", "")
    month_names = {
        "january":"Jan","february":"Feb","march":"Mar","april":"Apr",
        "may":"May","june":"Jun","july":"Jul","august":"Aug",
        "september":"Sep","october":"Oct","november":"Nov","december":"Dec",
        "jan":"Jan","feb":"Feb","mar":"Mar","apr":"Apr",
        "jun":"Jun","jul":"Jul","aug":"Aug","sep":"Sep",
        "oct":"Oct","nov":"Nov","dec":"Dec",
    }
    for word, label in month_names.items():
        if word in stem:
            return label
    m = re.search(r'(?<!\d)(0?[1-9]|1[0-2])(?!\d)', stem)
    if m:
        return MONTH_ORDER[int(m.group(1)) - 1]
    return p.stem


def load_categorised_csv(path: Path) -> dict:
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


def hex_to_rgba(hex_color: str, alpha: float):
    """Convert #RRGGBB to (r,g,b,a) for matplotlib."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
    return (r, g, b, alpha)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FOLDER
    if not folder.exists():
        sys.exit(f"Folder not found: {folder}")

    csv_files = sorted(folder.glob("*_categorised.csv"))
    if not csv_files:
        sys.exit(f"No *_categorised.csv files found in: {folder}")

    print(f"Found {len(csv_files)} file(s):")
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
            print(f"  Warning: {csv_path.name}: {e}")
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

    # ── Layout ──────────────────────────────────────────────────────────────
    ncols = 3
    nrows = (n_cats + ncols - 1) // ncols

    fig = plt.figure(
        figsize=(15, nrows * 3.1 + 2.2),
        facecolor=BG,
    )

    # Header band
    header_height = 0.072
    header_ax = fig.add_axes([0, 1 - header_height, 1, header_height])
    header_ax.set_facecolor(PANEL)
    header_ax.set_xlim(0, 1)
    header_ax.set_ylim(0, 1)
    header_ax.axis("off")

    # Accent rule
    header_ax.axhline(y=0, color="#4F8EF7", linewidth=2.5, xmin=0, xmax=1)

    # Title
    header_ax.text(0.022, 0.62, "◈  Spending Dashboard",
                   color=TEXT_PRI, fontsize=14, fontweight="bold",
                   va="center", transform=header_ax.transAxes)
    header_ax.text(0.022, 0.20, "MONTHLY CATEGORY TRENDS · NZD",
                   color=TEXT_SEC, fontsize=8, va="center",
                   transform=header_ax.transAxes,
                   fontfamily="monospace")

    # Month range badge
    if months:
        badge_text = f"  {months[0]}–{months[-1]}  "
        header_ax.text(0.978, 0.50, badge_text,
                       color="#4F8EF7", fontsize=8,
                       ha="right", va="center",
                       transform=header_ax.transAxes,
                       bbox=dict(facecolor=SURFACE, edgecolor="#4F8EF7",
                                 linewidth=0.8, boxstyle="round,pad=0.4"))

    # ── Subplots ─────────────────────────────────────────────────────────────
    plot_top    = 1 - header_height - 0.02
    plot_bottom = 0.06
    plot_height = plot_top - plot_bottom

    left_margin  = 0.04
    right_margin = 0.02
    h_gap        = 0.035

    col_w = (1 - left_margin - right_margin - h_gap * (ncols - 1)) / ncols
    row_h = plot_height / nrows
    v_gap = 0.03

    for i, cat in enumerate(active_cats):
        row = i // ncols
        col = i % ncols

        left   = left_margin + col * (col_w + h_gap)
        bottom = plot_top - (row + 1) * row_h + v_gap * 0.5
        width  = col_w
        height = row_h - v_gap

        ax = fig.add_axes([left, bottom, width, height])
        ax.set_facecolor(PANEL)

        colour   = CAT_COLOURS.get(cat, "#78909C")
        rgba_fill = hex_to_rgba(colour, 0.10)
        rgba_line = hex_to_rgba(colour, 1.00)

        y_vals = np.array([month_data[m].get(cat, 0) for m in months])

        # Grid
        ax.yaxis.grid(True, color=GRID_COL, linewidth=0.8,
                      linestyle="-", zorder=0)
        ax.xaxis.grid(False)
        ax.set_axisbelow(True)

        # Area fill
        ax.fill_between(x, y_vals, alpha=0, zorder=1)   # dummy for scaling
        verts_x = np.concatenate([[x[0]], x, [x[-1]]])
        verts_y = np.concatenate([[0], y_vals, [0]])
        poly = plt.Polygon(
            list(zip(verts_x, verts_y)),
            closed=True, facecolor=rgba_fill, edgecolor="none", zorder=1,
        )
        ax.add_patch(poly)

        # Line
        ax.plot(x, y_vals, color=colour, linewidth=2.0,
                solid_capstyle="round", zorder=3)

        # Dots — open circle with coloured ring
        ax.scatter(x, y_vals, s=38, zorder=4,
                   facecolors=PANEL, edgecolors=colour, linewidths=1.8)

        # Value labels — only on non-zero points, with smart placement
        y_max = y_vals.max() if y_vals.max() > 0 else 1
        for xi, yi in zip(x, y_vals):
            if yi <= 0:
                continue
            offset = y_max * 0.09
            va = "bottom"
            ax.text(xi, yi + offset, f"${yi:,.0f}",
                    ha="center", va=va,
                    fontsize=7, color=colour, fontweight="bold",
                    zorder=5)

        # Category badge (top-left inside panel)
        ax.text(0.012, 0.96, cat,
                transform=ax.transAxes,
                fontsize=9, fontweight="bold", color=colour,
                va="top", ha="left", zorder=6)

        # Monthly total below category name
        total = sum(month_data[m].get(cat, 0) for m in months)
        ax.text(0.012, 0.76, f"Total  ${total:,.0f}",
                transform=ax.transAxes,
                fontsize=7, color=TEXT_SEC, va="top", ha="left")

        # X axis
        ax.set_xticks(x)
        ax.set_xticklabels(months, fontsize=8, color=TEXT_SEC,
                            fontfamily="monospace")
        ax.tick_params(axis="x", length=0, pad=4)

        # Y axis
        ax.yaxis.set_major_formatter(
            ticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
        ax.tick_params(axis="y", labelsize=7, colors=TEXT_DIM,
                        length=0, pad=3)
        ax.yaxis.set_label_position("right")
        ax.yaxis.tick_right()

        # Limits
        ax.set_ylim(0, y_max * 1.38)
        ax.set_xlim(-0.5, len(months) - 0.5)

        # Panel border
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color(BORDER)
            spine.set_linewidth(0.8)

    # Footer
    fig.text(0.022, 0.018,
             f"Source: {folder}",
             fontsize=7.5, color=TEXT_DIM,
             fontfamily="monospace")
    fig.text(0.978, 0.018,
             f"{len(csv_files)} month{'s' if len(csv_files) != 1 else ''}  ·  "
             f"{len(active_cats)} categories",
             fontsize=7.5, color=TEXT_DIM, ha="right",
             fontfamily="monospace")

    plt.show()


if __name__ == "__main__":
    main()