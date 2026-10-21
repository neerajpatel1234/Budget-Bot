"""
Spending Line Chart — last 8 months, multi-category trend
Apple-style light theme (matches spending_categoriser_gui.py)

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
    from matplotlib.patches import FancyBboxPatch
    import numpy as np
except ImportError:
    sys.exit("matplotlib is required.  Run:  pip install matplotlib")

# ── Default root folder ──────────────────────────────────────────────────────
DEFAULT_ROOT = Path("/Users/neerajpatel/Finance/Credit Card Statements")

# ── Design tokens (apple.com light) ──────────────────────────────────────────
WHITE        = "#FFFFFF"
BG           = "#F5F5F7"
BORDER       = "#D2D2D7"
HAIRLINE     = "#E8E8ED"
TEXT_PRI     = "#1D1D1F"
TEXT_SEC     = "#6E6E73"
TEXT_DIM     = "#86868B"
ACCENT       = "#0071E3"
ACCENT_TINT  = "#E8F1FD"
GRID_COL     = "#EDEDF0"

# Prefer the system font on each platform, fall back gracefully
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["SF Pro Text", "Helvetica Neue", "Segoe UI",
                                   "Helvetica", "Arial", "DejaVu Sans"]

CAT_COLOURS = {
    "Total Spending":       "#0071E3",
    "Groceries":            "#34C759",
    "Dining / Eating Out":  "#FF3B30",
    "Transport":            "#007AFF",
    "Fuel":                 "#32ADE6",
    "Bills & Utilities":    "#AF52DE",
    "Shopping":             "#FF9500",
    "Entertainment":        "#FF2D55",
    "Health & Medical":     "#A2845E",
    "Travel":               "#5856D6",
    "Income":               "#248A3D",
    "Other":                "#8E8E93",
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


def draw_card(fig, left, bottom, width, height, radius_in=0.18):
    """Rounded white card behind a panel (figure coordinates)."""
    fw, fh = fig.get_size_inches()
    card = FancyBboxPatch(
        (left, bottom), width, height,
        boxstyle=f"round,pad=0,rounding_size={radius_in / fw}",
        mutation_aspect=fw / fh,
        transform=fig.transFigure,
        facecolor=WHITE, edgecolor="none", zorder=0)
    fig.add_artist(card)


def draw_panel(fig, left, bottom, width, height,
               cat, colour, months, x, y_vals, total_label):
    """Draw one category panel — shared by Total Spending and every category."""
    draw_card(fig, left, bottom, width, height)

    pad_x, pad_y = 0.012, 0.012
    ax = fig.add_axes([left + pad_x, bottom + pad_y * 1.4,
                       width - 2 * pad_x - 0.004, height - pad_y * 2.2])
    ax.set_facecolor("none")

    ax.yaxis.grid(True, color=GRID_COL, linewidth=0.8, linestyle="-", zorder=0)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)

    verts_x = np.concatenate([[x[0]], x, [x[-1]]])
    verts_y = np.concatenate([[0], y_vals, [0]])
    poly = plt.Polygon(list(zip(verts_x, verts_y)),
                       closed=True, facecolor=hex_to_rgba(colour, 0.12),
                       edgecolor="none", zorder=1)
    ax.add_patch(poly)

    ax.plot(x, y_vals, color=colour, linewidth=2.2,
            solid_capstyle="round", zorder=3)
    ax.scatter(x, y_vals, s=40, zorder=4,
               facecolors=WHITE, edgecolors=colour, linewidths=2.0)

    y_max = y_vals.max() if y_vals.max() > 0 else 1
    for xi, yi in zip(x, y_vals):
        if yi <= 0:
            continue
        ax.text(xi, yi + y_max * 0.09, f"${yi:,.0f}",
                ha="center", va="bottom", fontsize=7.5,
                color=TEXT_PRI, fontweight="semibold", zorder=5)

    # Title: coloured dot + dark label, summary on the right
    ax.text(0.0, 0.97, "●", transform=ax.transAxes, fontsize=8,
            color=colour, va="top", ha="left", zorder=6)
    ax.text(0.035, 0.97, cat, transform=ax.transAxes,
            fontsize=10.5, fontweight="bold", color=TEXT_PRI,
            va="top", ha="left", zorder=6)
    ax.text(1.0, 0.965, total_label, transform=ax.transAxes,
            fontsize=7.5, color=TEXT_SEC, va="top", ha="right", zorder=6)

    ax.set_xticks(x)
    ax.set_xticklabels(months, fontsize=8, color=TEXT_SEC)
    ax.tick_params(axis="x", length=0, pad=5)

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.tick_params(axis="y", labelsize=7, colors=TEXT_DIM, length=0, pad=3)
    ax.yaxis.set_label_position("right")
    ax.yaxis.tick_right()

    ax.set_ylim(0, y_max * 1.38)
    ax.set_xlim(-0.5, len(months) - 0.5)

    for side, spine in ax.spines.items():
        if side == "bottom":
            spine.set_visible(True)
            spine.set_color(BORDER)
            spine.set_linewidth(0.8)
        else:
            spine.set_visible(False)


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

    row_height_in    = 3.1
    header_height_in = 0.95
    footer_height_in = 0.45

    fig_height = header_height_in + nrows * row_height_in + footer_height_in + 0.3

    fig = plt.figure(figsize=(15, fig_height), facecolor=BG)
    try:
        fig.canvas.manager.set_window_title("Spending Dashboard")
    except Exception:
        pass

    # ── Header (apple.com style: white bar, big title, hairline) ─────────────
    header_frac = header_height_in / fig_height
    hax = fig.add_axes([0, 1 - header_frac, 1, header_frac])
    hax.set_facecolor(WHITE)
    hax.set_xlim(0, 1); hax.set_ylim(0, 1)
    hax.set_xticks([]); hax.set_yticks([])
    for s in hax.spines.values():
        s.set_visible(False)
    hax.axhline(y=0, color=BORDER, linewidth=1.0)
    hax.text(0.022, 0.64, "Spending Dashboard",
             color=TEXT_PRI, fontsize=20, fontweight="bold",
             va="center", transform=hax.transAxes)
    hax.text(0.022, 0.25, "Monthly category trends · NZD",
             color=TEXT_SEC, fontsize=10, va="center",
             transform=hax.transAxes)
    if months:
        hax.text(0.978, 0.50, f"  {months[0]} – {months[-1]}  ",
                 color=ACCENT, fontsize=9.5, fontweight="semibold",
                 ha="right", va="center", transform=hax.transAxes,
                 bbox=dict(facecolor=ACCENT_TINT, edgecolor="none",
                           boxstyle="round,pad=0.5,rounding_size=1.0"))

    # ── Grid coordinates ─────────────────────────────────────────────────────
    footer_frac  = footer_height_in / fig_height
    plot_top     = 1 - header_frac - 0.012
    plot_bottom  = footer_frac + 0.01
    plot_height  = plot_top - plot_bottom

    left_margin  = 0.022
    right_margin = 0.022
    h_gap        = 0.014
    v_gap        = 0.014

    col_w   = (1 - left_margin - right_margin - h_gap * (ncols - 1)) / ncols
    row_h   = plot_height / nrows

    # ── Draw all panels ───────────────────────────────────────────────────────
    for i, cat in enumerate(all_panels):
        row = i // ncols
        col = i % ncols

        left   = left_margin + col * (col_w + h_gap)
        bottom = plot_top - (row + 1) * row_h + v_gap * 0.5

        colour  = CAT_COLOURS.get(cat, "#8E8E93")
        y_vals  = np.array([month_data[m].get(cat, 0) for m in months])
        total   = sum(month_data[m].get(cat, 0) for m in months)

        avg = np.mean(y_vals[y_vals > 0]) if np.any(y_vals > 0) else 0
        if cat == TOTAL_KEY:
            total_label = f"Avg ${np.mean(y_vals):,.0f}/mo  ·  Total ${total:,.0f}"
        else:
            total_label = f"Avg ${avg:,.0f}/mo"

        draw_panel(fig, left, bottom, col_w, row_h - v_gap,
                   cat, colour, months, x, y_vals, total_label)

    # ── Footer ───────────────────────────────────────────────────────────────
    fig.text(0.022, 0.014, f"Source: {root}",
             fontsize=8, color=TEXT_DIM)
    fig.text(0.978, 0.014,
             f"Last 8 months  ·  {len(active_cats)} categories",
             fontsize=8, color=TEXT_DIM, ha="right")

    plt.show()


if __name__ == "__main__":
    main()