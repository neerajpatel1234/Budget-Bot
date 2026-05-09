"""
Spending Line Chart — 12-month multi-category trend
Reads all CSV files from a folder, categorises transactions, and plots a
line chart styled after the OECD/EU reference graph (dotted grid, right-side
labels, clean axes, no chart border).

Usage:
    python spending_line_chart.py
    # or override the folder:
    python spending_line_chart.py /path/to/your/csv/folder

Requires:  pip install matplotlib
"""

import csv
import sys
import re
from collections import defaultdict
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    import numpy as np
except ImportError:
    sys.exit("matplotlib is required.  Run:  pip install matplotlib")

# ── Folder containing the CSV files ────────────────────────────────────────
DEFAULT_FOLDER = Path("/Users/neerajpatel/Finance/Credit Card Statements/2026")

# ── Category rules (same as the main app) ──────────────────────────────────
RULES = [
    ("Payment / Refund", [
        "payment - thank you", "payment thank you", "direct credit",
        "refund", "reversal", "credit transfer",
    ]),
    ("Transport", [
        "didi", "uber", "ola cab", "metlink", "nz bus", "taxicab", "taxi",
        "parking", "bp ", "z energy", "mobil", "gull", "caltex",
        "fuel", "petrol", "transit", "snapper",
    ]),
    ("Travel", [
        "air new zealand", "air nz", "jetstar", "qantas", "virgin australia",
        "expedia", "booking.com", "airbnb", "hotel", "motel", "hostel",
        "hilton", "marriott", "novotel",
    ]),
    ("Groceries", [
        "new world", "countdown", "pak'nsave", "paknsave", "fresh choice",
        "four square", "moore wilsons", "farro", "plenty foods", "windcave*plenty",
    ]),
    ("Eating Out", [
        "mcdonald", "mcdonalds", "kfc", "subway", "burger king", "wendys",
        "pizza", "domino", "noodle", "sushi", "kebab", "little india",
        "istana", "old quarter", "windcave*the old", "restaurant", "bistro",
        "cafe", "coffee", "bakery", "thai", "dumpling",
        "fish & chip", "fish and chip", "takeaway",
    ]),
    ("Entertainment", [
        "embassy theatre", "hoyts", "event cinema", "reading cinema",
        "sky stadium", "ticketek", "ticketmaster", "steam ", "playstation",
        "xbox", "nintendo", "spotify", "netflix", "disney+",
        "amazon prime", "youtube premium",
    ]),
    ("Bills", [
        "apple.com", "apple.com/bill", "rocket mobile", "2degrees",
        "vodafone", "spark", "orcon", "skinny", "trustpower",
        "genesis energy", "contact energy", "mercury energy", "meridian",
        "wellington electricity", "insurance", "aia", "southern cross",
        "aa insurance", "rent", "body corp", "rates", "gym",
        "les mills", "anytime fitness",
    ]),
    ("Shopping", [
        "the warehouse", "thewarehouse", "bunnings", "mitre 10",
        "placemakers", "briscoes", "harvey norman", "jb hi-fi",
        "noel leeming", "spotlight", "kmart", "farmers", "glassons",
        "cotton on", "h&m", "zara", "amazon", "trademe", "ebay",
        "chemist warehouse", "life pharmacy", "unichem", "whitcoulls",
        "paper plus", "mighty ape",
    ]),
]

# Colours that match the existing app palette
CAT_COLOURS = {
    "Bills":         "#534AB7",   # purple
    "Groceries":     "#1D9E75",   # green
    "Transport":     "#185FA5",   # navy
    "Shopping":      "#BA7517",   # amber
    "Eating Out":    "#D85A30",   # orange-red
    "Entertainment": "#D4537E",   # pink
    "Travel":        "#0F6E56",   # dark teal
    "Other":         "#888780",   # grey
}

MONTH_ORDER = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

# ── Helpers ─────────────────────────────────────────────────────────────────

def categorise(description: str) -> str:
    desc_lower = description.lower()
    for category, keywords in RULES:
        for kw in keywords:
            if kw in desc_lower:
                return category
    return "Other"


def month_label_from_path(p: Path) -> str:
    """
    Try to extract a month from the filename.
    Accepts patterns like:  January, Jan, 01, 1, 2026-01, jan-2026, etc.
    Falls back to the stem if nothing matches.
    """
    stem = p.stem.lower()
    month_names = {
        "january": "Jan", "february": "Feb", "march": "Mar",
        "april": "Apr", "may": "May", "june": "Jun",
        "july": "Jul", "august": "Aug", "september": "Sep",
        "october": "Oct", "november": "Nov", "december": "Dec",
        "jan": "Jan", "feb": "Feb", "mar": "Mar",
        "apr": "Apr",               "jun": "Jun",
        "jul": "Jul", "aug": "Aug", "sep": "Sep",
        "oct": "Oct", "nov": "Nov", "dec": "Dec",
    }
    for word, label in month_names.items():
        if word in stem:
            return label
    # Try numeric month
    m = re.search(r'(?<!\d)(0?[1-9]|1[0-2])(?!\d)', stem)
    if m:
        idx = int(m.group(1)) - 1
        return MONTH_ORDER[idx]
    return p.stem  # fallback


def load_csv(path: Path) -> list:
    with open(path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(2048)
    delimiter = "\t" if "\t" in sample else ","
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            clean = {k.strip(): v.strip() for k, v in row.items() if k}
            rows.append(clean)
    return rows


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FOLDER

    if not folder.exists():
        sys.exit(f"Folder not found: {folder}")

    csv_files = sorted(folder.glob("*.csv")) + sorted(folder.glob("*.tsv"))
    if not csv_files:
        sys.exit(f"No CSV/TSV files found in: {folder}")

    # month_label → { category → total }
    month_data: dict[str, dict[str, float]] = {}
    month_sort_key: dict[str, int] = {}

    for csv_path in csv_files:
        label = month_label_from_path(csv_path)
        sort_key = MONTH_ORDER.index(label) if label in MONTH_ORDER else 99
        month_sort_key[label] = sort_key

        totals: dict[str, float] = defaultdict(float)
        try:
            rows = load_csv(csv_path)
        except Exception as e:
            print(f"  Warning: could not read {csv_path.name}: {e}")
            continue

        for row in rows:
            desc = row.get("Description", "")
            cat = categorise(desc)
            if cat == "Payment / Refund":
                continue
            try:
                amt = float(row.get("Amount", 0) or 0)
            except ValueError:
                amt = 0.0
            if amt > 0:
                totals[cat] += amt

        if label not in month_data:
            month_data[label] = {}
        for cat, val in totals.items():
            month_data[label][cat] = month_data[label].get(cat, 0) + val

    if not month_data:
        sys.exit("No data could be loaded from the CSV files.")

    # Sort months chronologically
    months = sorted(month_data.keys(), key=lambda m: month_sort_key.get(m, 99))

    # Collect all categories that appear in any month
    all_cats = set()
    for m in months:
        all_cats.update(month_data[m].keys())
    all_cats.discard("Payment / Refund")

    # Only plot categories that have at least some spend
    active_cats = [c for c in all_cats if any(month_data[m].get(c, 0) > 0 for m in months)]
    # Sort by total spend (descending) for label placement priority
    active_cats.sort(key=lambda c: -sum(month_data[m].get(c, 0) for m in months))

    # ── Build series arrays ──────────────────────────────────────────────
    x = np.arange(len(months))
    series: dict[str, np.ndarray] = {}
    for cat in active_cats:
        series[cat] = np.array([month_data[m].get(cat, 0) for m in months])

    # ── Plot ─────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(11, 5.5), facecolor="white")
    ax.set_facecolor("white")

    for cat in active_cats:
        colour = CAT_COLOURS.get(cat, "#888780")
        y = series[cat]
        ax.plot(x, y, color=colour, linewidth=2.0, marker="o",
                markersize=3.5, markerfacecolor=colour, zorder=3)

        # Right-side label at the last data point
        last_x = x[-1]
        last_y = y[-1]
        ax.annotate(
            cat,
            xy=(last_x, last_y),
            xytext=(last_x + 0.18, last_y),
            fontsize=8.5,
            color=colour,
            va="center",
            fontfamily="DejaVu Sans",
        )

    # ── Axes styling (OECD-style) ─────────────────────────────────────────
    ax.set_xticks(x)
    ax.set_xticklabels(months, fontsize=9, color="#444444")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.tick_params(axis="y", labelsize=8.5, colors="#444444", length=0)
    ax.tick_params(axis="x", length=0, colors="#444444")

    # Dotted horizontal grid only
    ax.yaxis.grid(True, linestyle=":", linewidth=0.7, color="#BBBBBB", zorder=0)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)

    # Remove all spines except bottom
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#BBBBBB")
    ax.spines["bottom"].set_linewidth(0.8)

    # Extend x-axis right to make room for labels
    ax.set_xlim(-0.3, len(months) - 0.5 + 2.2)

    ax.set_title(
        "Monthly Spending by Category  (NZD)",
        fontsize=12, fontweight="bold", color="#1A1A1A",
        loc="left", pad=12,
    )
    fig.text(0.01, 0.01, f"Source: {folder}", fontsize=7, color="#AAAAAA")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()