"""
Spending Line Chart — last 8 months, multi-category trend
Searches all year subfolders inside the given root for *_categorised.csv files,
picks the 8 most recent months, and plots a styled dashboard.

Usage:
    python spending_line_chart.py
    python spending_line_chart.py "/path/to/Credit Card Statements"

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

# ── Default root folder ──────────────────────────────────────────────────────
DEFAULT_ROOT = Path("/Users/neerajpatel/Finance/Credit Card Statements")

# ── Design tokens ────────────────────────────────────────────────────────────
BG       = "#0F1117"
PANEL    = "#171B26"
BORDER   = "#252A3A"
SURFACE  = "#1E2235"
TEXT_PRI = "#E8EAF0"
TEXT_SEC = "#8892A4"
TEXT_DIM = "#3A4155"
GRID_COL = "#1C2133"

CAT_COLOURS = {
    "Total Spending":       "#4F8EF7",
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

MONTH_NAME_MAP = {
    "january":"Jan","february":"Feb","march":"Mar","april":"Apr",
    "may":"May","june":"Jun","july":"Jul","august":"Aug",
    "september":"Sep","october":"Oct","november":"Nov","december":"Dec",
    "jan":"Jan","feb":"Feb","mar":"Mar","apr":"Apr",
    "jun":"Jun","jul":"Jul","aug":"Aug","sep":"Sep",
    "oct":"Oct","nov":"Nov","dec":"Dec",
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def parse_month_year(p: Path):
    stem = p.stem.lower().replace("_categorised", "")
    parent_name = p.parent.name
    year_match = re.search(r'\b(20\d{2})\b', parent_name)
    year = int(year_match.group(1)) if year_match else None
    if not year:
        fy = re.search(r'\b(20\d{2})\b', stem)
        year = int(fy.group(1)) if fy else 2025

    month_idx = None
    short = None
    for word, label in MONTH_NAME_MAP.items():
        if word in stem:
            month_idx = MONTH_ORDER.index(label)
            short = label
            break
    if month_idx is None:
        m = re.search(r'(?<!\d)(0?[1-9]|1[0-2])(?!\d)', stem)
        if m:
            month_idx = int(m.group(1)) - 1
            short = MONTH_ORDER[month_idx]
    if month_idx is None:
        return None

    display = f"{short} {str(year)[2:]}"
    return (year, month_idx, short, display)


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
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
    return (r, g, b, alpha)


def draw_panel(fig, left, bottom, width, height,
               cat, colour, months, x, y_vals, total_label):
    """Draw one category panel — shared by Total Spending and every category."""
    ax = fig.add_axes([left, bottom, width, height])
    ax.set_facecolor(PANEL)

    rgba_fill = hex_to_rgba(colour, 0.10)

    ax.yaxis.grid(True, color=GRID_COL, linewidth=0.8, linestyle="-", zorder=0)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)

    verts_x = np.concatenate([[x[0]], x, [x[-1]]])
    verts_y = np.concatenate([[0], y_vals, [0]])
    poly = plt.Polygon(list(zip(verts_x, verts_y)),
                       closed=True, facecolor=rgba_fill, edgecolor="none", zorder=1)
    ax.add_patch(poly)

    ax.plot(x, y_vals, color=colour, linewidth=2.0,
            solid_capstyle="round", zorder=3)
    ax.scatter(x, y_vals, s=38, zorder=4,
               facecolors=PANEL, edgecolors=colour, linewidths=1.8)

    y_max = y_vals.max() if y_vals.max() > 0 else 1
    for xi, yi in zip(x, y_vals):
        if yi <= 0:
            continue
        ax.text(xi, yi + y_max * 0.09, f"${yi:,.0f}",
                ha="center", va="bottom", fontsize=7,
                color=colour, fontweight="bold", zorder=5)

    ax.text(0.012, 0.96, cat, transform=ax.transAxes,
            fontsize=9, fontweight="bold", color=colour,
            va="top", ha="left", zorder=6)
    ax.text(0.988, 0.96, total_label, transform=ax.transAxes,
            fontsize=7, color=TEXT_SEC, va="top", ha="right", zorder=6)

    ax.set_xticks(x)
    ax.set_xticklabels(months, fontsize=8, color=TEXT_SEC, fontfamily="monospace")
    ax.tick_params(axis="x", length=0, pad=4)

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.tick_params(axis="y", labelsize=7, colors=TEXT_DIM, length=0, pad=3)
    ax.yaxis.set_label_position("right")
    ax.yaxis.tick_right()

    ax.set_ylim(0, y_max * 1.38)
    ax.set_xlim(-0.5, len(months) - 0.5)

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(BORDER)
        spine.set_linewidth(0.8)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ROOT
    if not root.exists():
        sys.exit(f"Folder not found: {root}")

    search_paths = [root] + [p for p in sorted(root.iterdir()) if p.is_dir()]
    all_csv: list[Path] = []
    for sp in search_paths:
        all_csv.extend(sp.glob("*_categorised.csv"))

    if not all_csv:
        sys.exit(f"No *_categorised.csv files found under: {root}")

    parsed = []
    for p in all_csv:
        info = parse_month_year(p)
        if info:
            parsed.append((info, p))
        else:
            print(f"  Warning: could not parse date from {p.name}, skipping.")

    if not parsed:
        sys.exit("Could not determine dates for any CSV files.")

    parsed.sort(key=lambda t: (t[0][0], t[0][1]))
    parsed = parsed[-8:]

    print(f"\nUsing {len(parsed)} month(s):")
    for info, p in parsed:
        print(f"  {info[3]:>8}  ←  {p.relative_to(root)}")

    month_data: dict[str, dict[str, float]] = {}
    month_labels: list[str] = []

    for (year, month_idx, short, display), csv_path in parsed:
        try:
            totals = load_categorised_csv(csv_path)
        except Exception as e:
            print(f"  Warning: {csv_path.name}: {e}")
            continue
        if display not in month_data:
            month_data[display] = {}
            month_labels.append(display)
        for cat, val in totals.items():
            month_data[display][cat] = month_data[display].get(cat, 0) + val

    if not month_data:
        sys.exit("No data could be loaded.")

    months = month_labels

    all_cats: set = set()
    for m in months:
        all_cats.update(month_data[m].keys())
    all_cats.discard("Payment / Refund")

    active_cats = [c for c in all_cats if any(month_data[m].get(c, 0) > 0 for m in months)]
    active_cats.sort(key=lambda c: -sum(month_data[m].get(c, 0) for m in months))

    # Prepend Total Spending as a virtual category
    TOTAL_KEY = "Total Spending"
    all_panels = [TOTAL_KEY] + active_cats

    # Pre-compute total spending per month (stored in month_data under TOTAL_KEY)
    for m in months:
        month_data[m][TOTAL_KEY] = sum(
            v for cat, v in month_data[m].items() if cat != "Income"
        )

    x = np.arange(len(months))

    # ── Layout ──────────────────────────────────────────────────────────────
    ncols = 3
    nrows = (len(all_panels) + ncols - 1) // ncols

    row_height_in    = 3.0
    header_height_in = 0.75
    footer_height_in = 0.40

    fig_height = header_height_in + nrows * row_height_in + footer_height_in + 0.3

    fig = plt.figure(figsize=(15, fig_height), facecolor=BG)

    # ── Header ───────────────────────────────────────────────────────────────
    header_frac = header_height_in / fig_height
    hax = fig.add_axes([0, 1 - header_frac, 1, header_frac])
    hax.set_facecolor(PANEL)
    hax.set_xlim(0, 1); hax.set_ylim(0, 1)
    hax.axis("off")
    hax.axhline(y=0, color="#4F8EF7", linewidth=2.5, xmin=0, xmax=1)
    hax.text(0.022, 0.62, "◈  Spending Dashboard",
             color=TEXT_PRI, fontsize=14, fontweight="bold",
             va="center", transform=hax.transAxes)
    hax.text(0.022, 0.20, "MONTHLY CATEGORY TRENDS · NZD",
             color=TEXT_SEC, fontsize=8, va="center",
             transform=hax.transAxes, fontfamily="monospace")
    if months:
        hax.text(0.978, 0.50, f"  {months[0]} – {months[-1]}  ",
                 color="#4F8EF7", fontsize=8, ha="right", va="center",
                 transform=hax.transAxes,
                 bbox=dict(facecolor=SURFACE, edgecolor="#4F8EF7",
                           linewidth=0.8, boxstyle="round,pad=0.4"))

    # ── Grid coordinates ─────────────────────────────────────────────────────
    footer_frac  = footer_height_in / fig_height
    plot_top     = 1 - header_frac - 0.01
    plot_bottom  = footer_frac + 0.01
    plot_height  = plot_top - plot_bottom

    left_margin  = 0.04
    right_margin = 0.02
    h_gap        = 0.035
    v_gap        = 0.018

    col_w   = (1 - left_margin - right_margin - h_gap * (ncols - 1)) / ncols
    row_h   = plot_height / nrows

    # ── Draw all panels ───────────────────────────────────────────────────────
    for i, cat in enumerate(all_panels):
        row = i // ncols
        col = i % ncols

        left   = left_margin + col * (col_w + h_gap)
        bottom = plot_top - (row + 1) * row_h + v_gap * 0.5

        colour  = CAT_COLOURS.get(cat, "#78909C")
        y_vals  = np.array([month_data[m].get(cat, 0) for m in months])
        total   = sum(month_data[m].get(cat, 0) for m in months)

        avg = np.mean(y_vals[y_vals > 0]) if np.any(y_vals > 0) else 0
        if cat == TOTAL_KEY:
            total_label = f"Avg ${np.mean(y_vals):,.0f}/mo  ·  Total ${total:,.0f}"
        else:
            total_label = f"Avg  ${avg:,.0f}/mo"

        draw_panel(fig, left, bottom, col_w, row_h - v_gap,
                   cat, colour, months, x, y_vals, total_label)

    # ── Footer ───────────────────────────────────────────────────────────────
    fig.text(0.022, 0.012, f"Source: {root}",
             fontsize=7.5, color=TEXT_DIM, fontfamily="monospace")
    fig.text(0.978, 0.012,
             f"Last 8 months  ·  {len(active_cats)} categories",
             fontsize=7.5, color=TEXT_DIM, ha="right", fontfamily="monospace")

    plt.show()


if __name__ == "__main__":
    main()