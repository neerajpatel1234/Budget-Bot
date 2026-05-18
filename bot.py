"""
Spending Categoriser — Redesigned GUI
Run with:  python spending_categoriser_gui.py

Requires only Python 3 standard library (tkinter is built-in).
Learned rules are saved to rules.json in the same folder as this script.
"""

import csv
import json
import sys
import threading
import tkinter as tk
from collections import defaultdict
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


# ── Category rules ─────────────────────────────────────────────────────────
RULES = [
    ("Income", [
        "salary", "payroll", "wages", "direct credit",
        "interest", "dividend", "tax refund",
    ]),
    ("Groceries", [
        "new world", "countdown", "woolworths",
        "pak'nsave", "paknsave", "fresh choice",
        "four square", "farro", "costco", "moore wilsons",
    ]),
    ("Dining / Eating Out", [
        "mcdonald", "mcdonalds", "kfc", "subway",
        "burger king", "wendys", "pizza",
        "restaurant", "bistro", "cafe",
        "coffee", "bakery", "sushi",
        "thai", "dumpling", "takeaway", "uber eats",
    ]),
    ("Transport", [
        "uber", "didi", "ola", "taxi",
        "snapper", "at hop", "bus", "train", "parking",
    ]),
    ("Fuel", [
        "bp ", "z energy", "mobil",
        "gull", "caltex", "fuel", "petrol",
    ]),
    ("Bills & Utilities", [
        "spark", "vodafone", "one nz",
        "2degrees", "orcon", "skinny",
        "contact energy", "meridian",
        "mercury energy", "genesis",
        "watercare", "power", "electricity",
        "gas bill", "internet",
        "apple.com/bill", "apple.com",
    ]),
    ("Shopping", [
        "amazon", "trademe", "ebay",
        "the warehouse", "kmart",
        "farmers", "glassons",
        "cotton on", "zara", "h&m",
        "briscoes", "mitre 10",
        "bunnings", "harvey norman",
        "jb hi-fi", "noel leeming", "mighty ape",
    ]),
    ("Entertainment", [
        "spotify", "netflix", "disney+",
        "youtube premium", "amazon prime",
        "steam", "playstation", "xbox",
        "nintendo", "cinema", "hoyts",
        "event cinema", "ticketmaster", "ticketek",
    ]),
    ("Health & Medical", [
        "doctor", "medical", "dentist",
        "chemist", "pharmacy", "hospital",
        "physio", "healthcare",
        "unichem", "life pharmacy", "chemist warehouse",
    ]),
    ("Travel", [
        "air new zealand", "air nz",
        "jetstar", "qantas",
        "booking.com", "expedia",
        "airbnb", "hotel", "motel", "hostel",
    ]),
]

CATEGORY_ORDER = [
    "Groceries", "Dining / Eating Out", "Transport", "Fuel",
    "Bills & Utilities", "Shopping", "Entertainment",
    "Health & Medical", "Travel", "Income", "Other",
]
ALL_CATEGORIES = CATEGORY_ORDER.copy()

# Refined palette — each category gets a distinct accent
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

LEARNED_RULES_PATH = Path(__file__).parent / "rules.json"

# ── Design tokens ───────────────────────────────────────────────────────────
BG           = "#0F1117"   # deep navy-black
PANEL        = "#171B26"   # card/panel
SIDEBAR      = "#13161F"   # sidebar
BORDER       = "#252A3A"   # subtle border
SURFACE      = "#1E2235"   # elevated surface
ACCENT       = "#4F8EF7"   # primary blue accent
ACCENT2      = "#7C6AF4"   # secondary purple
TEXT_PRI     = "#E8EAF0"   # primary text
TEXT_SEC     = "#8892A4"   # secondary/muted text
TEXT_DIM     = "#505A70"   # very dim
SUCCESS      = "#2ECC71"
WARNING      = "#F39C12"
DANGER       = "#E74C3C"

# Solid tint approximations (tkinter doesn't support 8-digit hex / alpha)
ACCENT_TINT  = "#1A2A45"   # ACCENT at ~12% on BG
CANVAS_TRACK = "#1C2133"   # very dark bar track

FONT_TITLE   = ("Helvetica Neue", 13, "bold")
FONT_HEADING = ("Helvetica Neue", 11, "bold")
FONT_BODY    = ("Helvetica Neue", 10)
FONT_SMALL   = ("Helvetica Neue", 9)
FONT_MONO    = ("Menlo", 9)
FONT_BIG     = ("Helvetica Neue", 22, "bold")
FONT_MED     = ("Helvetica Neue", 16, "bold")


# ── Learned rules persistence ───────────────────────────────────────────────
def load_learned_rules() -> dict:
    if LEARNED_RULES_PATH.exists():
        try:
            with open(LEARNED_RULES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {e["keyword"].lower(): e["category"] for e in data.get("rules", [])}
        except Exception:
            return {}
    return {}


def save_learned_rule(description: str, category: str) -> None:
    keyword = description.strip().lower()
    rules = []
    if LEARNED_RULES_PATH.exists():
        try:
            with open(LEARNED_RULES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            rules = data.get("rules", [])
        except Exception:
            rules = []
    found = False
    for entry in rules:
        if entry["keyword"].lower() == keyword:
            entry["category"] = category
            found = True
            break
    if not found:
        rules.append({"keyword": keyword, "category": category})
    rules.sort(key=lambda e: e["keyword"])
    with open(LEARNED_RULES_PATH, "w", encoding="utf-8") as f:
        json.dump({"rules": rules}, f, indent=2, ensure_ascii=False)


def categorise(description: str, learned: dict) -> str:
    desc_lower = description.lower()
    if desc_lower in learned:
        return learned[desc_lower]
    for category, keywords in RULES:
        for kw in keywords:
            if kw in desc_lower:
                return category
    return "Other"


def load_csv(path: str) -> list:
    with open(path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(2048)
    delimiter = "\t" if "\t" in sample else ","
    transactions = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for i, row in enumerate(reader):
            clean = {k.strip(): v.strip() for k, v in row.items() if k}
            clean["_id"] = i
            transactions.append(clean)
    return transactions


def save_csv(transactions: list, output_path: str) -> None:
    if not transactions:
        return
    totals = defaultdict(float)
    for tx in transactions:
        cat = tx.get("Category", "Other")
        if cat == "Payment / Refund":
            continue
        try:
            totals[cat] += float(tx.get("Amount", 0) or 0)
        except ValueError:
            pass
    ordered = sorted(totals.keys(),
                     key=lambda c: CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else 99)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Category", "Amount"])
        writer.writeheader()
        for cat in ordered:
            writer.writerow({"Category": cat, "Amount": f"{totals[cat]:.2f}"})


# ── Helper widgets ──────────────────────────────────────────────────────────

def styled_button(parent, text, command, style="primary", **kw):
    styles = {
        "primary": dict(bg=ACCENT,   fg=TEXT_PRI,  ab="#3A7AE0", af=TEXT_PRI),
        "danger":  dict(bg=DANGER,   fg=TEXT_PRI,  ab="#C0392B", af=TEXT_PRI),
        "ghost":   dict(bg=SURFACE,  fg=TEXT_SEC,  ab=BORDER,    af=TEXT_PRI),
        "purple":  dict(bg=ACCENT2,  fg=TEXT_PRI,  ab="#6254D0",  af=TEXT_PRI),
        "dark":    dict(bg=PANEL,    fg=TEXT_SEC,  ab=SURFACE,   af=TEXT_PRI),
    }
    s = styles.get(style, styles["primary"])
    btn = tk.Button(
        parent, text=text, command=command,
        bg=s["bg"], fg=s["fg"],
        activebackground=s["ab"], activeforeground=s["af"],
        relief="flat", bd=0,
        font=FONT_BODY, cursor="hand2",
        padx=kw.pop("padx", 14), pady=kw.pop("pady", 6),
        **kw,
    )
    return btn


def pill_label(parent, text, color):
    """Coloured pill badge."""
    f = tk.Frame(parent, bg=color + "28", padx=7, pady=2)
    tk.Label(f, text=text, bg=color + "28", fg=color,
             font=FONT_SMALL).pack()
    return f


# ── Re-categorise Dialog ────────────────────────────────────────────────────

class RecategoriseDialog(tk.Toplevel):
    def __init__(self, parent, transactions, item_ids, tree, on_done):
        super().__init__(parent)
        self.title("Re-categorise")
        self.resizable(False, False)
        self.grab_set()
        self.configure(bg=BG)
        self.overrideredirect(False)

        self._transactions = transactions
        self._item_ids = item_ids
        self._tree = tree
        self._on_done = on_done
        self._result_var = tk.StringVar()

        self._build()
        self.update_idletasks()
        pw, py = parent.winfo_rootx(), parent.winfo_rooty()
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{pw + 200}+{py + 150}")

    def _build(self):
        # Top bar
        bar = tk.Frame(self, bg=PANEL, height=52)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        tk.Label(bar, text="Assign Category", bg=PANEL, fg=TEXT_PRI,
                 font=FONT_HEADING).pack(side="left", padx=20, pady=14)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", padx=20, pady=16)

        # Info
        if len(self._item_ids) == 1:
            vals = self._tree.item(self._item_ids[0], "values")
            desc = vals[1] if len(vals) > 1 else ""
            current = vals[2] if len(vals) > 2 else ""
            info = f'"{desc}"'
            sub  = f"Current: {current}"
        else:
            info = f"{len(self._item_ids)} transactions selected"
            sub  = "A rule will be saved for each description"

        tk.Label(body, text=info, bg=BG, fg=TEXT_PRI,
                 font=FONT_HEADING, wraplength=360, justify="left").pack(anchor="w")
        tk.Label(body, text=sub, bg=BG, fg=TEXT_SEC,
                 font=FONT_SMALL).pack(anchor="w", pady=(2, 10))

        # Note banner
        note = tk.Frame(body, bg=ACCENT_TINT, padx=12, pady=7)
        note.pack(fill="x", pady=(0, 14))
        tk.Label(note, text="💾  Rule saved to rules.json for future imports",
                 bg=ACCENT_TINT, fg=ACCENT, font=FONT_SMALL).pack(anchor="w")

        # Radio grid
        grid = tk.Frame(body, bg=BG)
        grid.pack(fill="x")

        for i, cat in enumerate(ALL_CATEGORIES):
            colour = CAT_COLOURS.get(cat, TEXT_SEC)
            row_f = tk.Frame(grid, bg=BG)
            row_f.grid(row=i // 2, column=i % 2, sticky="ew",
                       padx=(0, 20), pady=3)
            rb = tk.Radiobutton(
                row_f, text=cat,
                variable=self._result_var, value=cat,
                bg=BG, fg=TEXT_PRI,
                activebackground=BG, activeforeground=TEXT_PRI,
                selectcolor=colour,
                font=FONT_BODY, cursor="hand2",
                highlightthickness=0,
            )
            rb.pack(side="left")

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(14, 12))

        btn_row = tk.Frame(body, bg=BG)
        btn_row.pack(fill="x")
        styled_button(btn_row, "Cancel", self.destroy, style="ghost").pack(side="right", padx=(8, 0))
        styled_button(btn_row, "Apply & Save", self._apply, style="primary").pack(side="right")

    def _apply(self):
        new_cat = self._result_var.get()
        if not new_cat:
            messagebox.showwarning("No selection", "Please choose a category.", parent=self)
            return
        saved_rules = 0
        for iid in self._item_ids:
            vals = self._tree.item(iid, "values")
            date, desc = vals[0], vals[1]
            for tx in self._transactions:
                if tx.get("Date", "") == date and tx.get("Description", "") == desc:
                    tx["Category"] = new_cat
                    tx["_manual"] = True
                    try:
                        save_learned_rule(desc, new_cat)
                        saved_rules += 1
                    except Exception as e:
                        messagebox.showwarning("Rule not saved",
                                               f"Could not update rules.json:\n{e}", parent=self)
                    break
        self.destroy()
        self._on_done(saved_rules)


# ── Main App ────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Spending Categoriser")
        self.geometry("980x700")
        self.minsize(800, 560)
        self.configure(bg=BG)

        self._transactions = []
        self._csv_path = ""
        self._learned: dict = load_learned_rules()
        self._active_tab = tk.StringVar(value="summary")

        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        # Treeview
        style.configure("Dark.Treeview",
                        background=PANEL, fieldbackground=PANEL,
                        foreground=TEXT_PRI, rowheight=28,
                        font=FONT_BODY, borderwidth=0)
        style.configure("Dark.Treeview.Heading",
                        background=SURFACE, foreground=TEXT_SEC,
                        font=FONT_SMALL, relief="flat", padding=(8, 6))
        style.map("Dark.Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "#FFFFFF")])
        style.map("Dark.Treeview.Heading",
                  background=[("active", BORDER)])
        # Scrollbar
        style.configure("Dark.Vertical.TScrollbar",
                        background=SURFACE, troughcolor=PANEL,
                        bordercolor=PANEL, arrowcolor=TEXT_DIM, width=8)
        style.map("Dark.Vertical.TScrollbar",
                  background=[("active", BORDER)])
        # Combobox
        style.configure("Dark.TCombobox",
                        fieldbackground=SURFACE, background=SURFACE,
                        foreground=TEXT_PRI, selectbackground=ACCENT,
                        bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)

    def _build_ui(self):
        # ── Sidebar ──────────────────────────────────────────────────────
        self._sidebar = tk.Frame(self, bg=SIDEBAR, width=200)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        # Logo / brand
        brand = tk.Frame(self._sidebar, bg=SIDEBAR, pady=20)
        brand.pack(fill="x")
        tk.Label(brand, text="◈", bg=SIDEBAR, fg=ACCENT,
                 font=("Helvetica Neue", 20)).pack()
        tk.Label(brand, text="Spending", bg=SIDEBAR, fg=TEXT_PRI,
                 font=("Helvetica Neue", 11, "bold")).pack()
        tk.Label(brand, text="Categoriser", bg=SIDEBAR, fg=TEXT_SEC,
                 font=FONT_SMALL).pack()

        tk.Frame(self._sidebar, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(0, 8))

        # Nav buttons
        self._nav_btns = {}
        nav_items = [
            ("summary",      "▣  Overview",       "Summary & charts"),
            ("transactions", "≡  Transactions",   "Browse & edit"),
            ("rules",        "⚙  Learned Rules",  "Auto-categorise"),
        ]
        for key, label, sub in nav_items:
            btn = self._make_nav_btn(key, label, sub)
            self._nav_btns[key] = btn

        # Spacer
        tk.Frame(self._sidebar, bg=SIDEBAR).pack(fill="both", expand=True)

        # File section at bottom of sidebar
        file_section = tk.Frame(self._sidebar, bg=SIDEBAR, padx=12, pady=12)
        file_section.pack(fill="x")
        tk.Frame(file_section, bg=BORDER, height=1).pack(fill="x", pady=(0, 10))
        tk.Label(file_section, text="DATA SOURCE", bg=SIDEBAR, fg=TEXT_DIM,
                 font=("Helvetica Neue", 8, "bold")).pack(anchor="w")
        self._path_var = tk.StringVar(value="No file loaded")
        self._path_label = tk.Label(file_section, textvariable=self._path_var,
                                    bg=SIDEBAR, fg=TEXT_SEC, font=FONT_MONO,
                                    wraplength=160, justify="left", anchor="w")
        self._path_label.pack(anchor="w", pady=(4, 8))
        styled_button(file_section, "Browse CSV…", self._browse,
                      style="ghost").pack(fill="x", pady=(0, 4))
        self._btn_run = styled_button(file_section, "▶  Categorise",
                                      self._run, style="primary", state="disabled")
        self._btn_run.pack(fill="x")

        # Learned count
        self._learned_var = tk.StringVar()
        self._update_learned_label()
        tk.Label(file_section, textvariable=self._learned_var,
                 bg=SIDEBAR, fg=ACCENT, font=FONT_SMALL).pack(anchor="w", pady=(8, 0))

        # ── Main content ──────────────────────────────────────────────────
        self._main = tk.Frame(self, bg=BG)
        self._main.pack(side="left", fill="both", expand=True)

        # Top bar
        topbar = tk.Frame(self._main, bg=PANEL, height=52)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        self._page_title = tk.Label(topbar, text="Overview", bg=PANEL, fg=TEXT_PRI,
                                    font=FONT_HEADING)
        self._page_title.pack(side="left", padx=24, pady=14)
        self._status_var = tk.StringVar(value="Select a CSV file to begin")
        tk.Label(topbar, textvariable=self._status_var, bg=PANEL, fg=TEXT_SEC,
                 font=FONT_SMALL).pack(side="right", padx=24)
        tk.Frame(self._main, bg=BORDER, height=1).pack(fill="x")

        # Content frames
        self._frames = {}
        for key in ("summary", "transactions", "rules"):
            f = tk.Frame(self._main, bg=BG)
            self._frames[key] = f

        self._build_summary_frame()
        self._build_tx_frame()
        self._build_rules_frame()

        self._switch_tab("summary")

    def _make_nav_btn(self, key, label, sub):
        f = tk.Frame(self._sidebar, bg=SIDEBAR, cursor="hand2")
        f.pack(fill="x", padx=8, pady=2)

        inner = tk.Frame(f, bg=SIDEBAR, padx=12, pady=9)
        inner.pack(fill="x")
        lbl = tk.Label(inner, text=label, bg=SIDEBAR, fg=TEXT_SEC,
                       font=FONT_BODY, anchor="w")
        lbl.pack(fill="x")
        sub_lbl = tk.Label(inner, text=sub, bg=SIDEBAR, fg=TEXT_DIM,
                           font=FONT_SMALL, anchor="w")
        sub_lbl.pack(fill="x")

        def _enter(e): 
            if self._active_tab.get() != key:
                f.config(bg=SURFACE)
                inner.config(bg=SURFACE)
                lbl.config(bg=SURFACE)
                sub_lbl.config(bg=SURFACE)
        def _leave(e):
            if self._active_tab.get() != key:
                f.config(bg=SIDEBAR)
                inner.config(bg=SIDEBAR)
                lbl.config(bg=SIDEBAR)
                sub_lbl.config(bg=SIDEBAR)
        def _click(e): self._switch_tab(key)

        for w in (f, inner, lbl, sub_lbl):
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)
            w.bind("<Button-1>", _click)

        return (f, inner, lbl, sub_lbl)

    def _switch_tab(self, key):
        prev = self._active_tab.get()
        # Reset previous
        if prev in self._nav_btns:
            f, inner, lbl, sub_lbl = self._nav_btns[prev]
            for w in (f, inner, lbl, sub_lbl):
                w.config(bg=SIDEBAR)
            lbl.config(fg=TEXT_SEC)

        self._active_tab.set(key)

        # Highlight active
        f, inner, lbl, sub_lbl = self._nav_btns[key]
        for w in (f, inner, lbl, sub_lbl):
            w.config(bg=ACCENT_TINT)
        lbl.config(fg=ACCENT)

        # Titles
        titles = {"summary": "Overview", "transactions": "Transactions", "rules": "Learned Rules"}
        self._page_title.config(text=titles[key])

        # Show/hide frames
        for k, frm in self._frames.items():
            if k == key:
                frm.pack(fill="both", expand=True)
            else:
                frm.pack_forget()

    # ── Summary frame ───────────────────────────────────────────────────────

    def _build_summary_frame(self):
        frm = self._frames["summary"]

        # Metric cards row
        self._cards_row = tk.Frame(frm, bg=BG)
        self._cards_row.pack(fill="x", padx=20, pady=(20, 12))

        # Chart area
        chart_wrap = tk.Frame(frm, bg=BG)
        chart_wrap.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        chart_hdr = tk.Frame(chart_wrap, bg=BG)
        chart_hdr.pack(fill="x", pady=(0, 8))
        tk.Label(chart_hdr, text="Spending Breakdown", bg=BG,
                 fg=TEXT_PRI, font=FONT_HEADING).pack(side="left")

        self._canvas = tk.Canvas(chart_wrap, bg=PANEL, highlightthickness=0,
                                  highlightbackground=BORDER, bd=0)
        self._canvas.pack(fill="both", expand=True)

        # Save button
        btn_row = tk.Frame(frm, bg=BG)
        btn_row.pack(fill="x", padx=20, pady=(0, 16))
        self._btn_save = styled_button(btn_row, "↓  Export CSV Summary",
                                       self._save, style="ghost", state="disabled")
        self._btn_save.pack(side="right")

    def _make_metric_card(self, parent, label, value, accent=None):
        card = tk.Frame(parent, bg=PANEL, padx=18, pady=14)
        card.pack(side="left", padx=(0, 10), ipadx=4)

        if accent:
            bar = tk.Frame(card, bg=accent, width=3, height=40)
            bar.pack(side="left", padx=(0, 12), fill="y")

        info = tk.Frame(card, bg=PANEL)
        info.pack(side="left")
        tk.Label(info, text=label, bg=PANEL, fg=TEXT_SEC,
                 font=FONT_SMALL).pack(anchor="w")
        tk.Label(info, text=value, bg=PANEL, fg=TEXT_PRI,
                 font=FONT_MED).pack(anchor="w")
        return card

    def _render_summary(self):
        for w in self._cards_row.winfo_children():
            w.destroy()

        totals = defaultdict(float)
        counts = defaultdict(int)
        for tx in self._transactions:
            try:
                amount = float(tx.get("Amount", 0) or 0)
            except ValueError:
                amount = 0.0
            totals[tx["Category"]] += amount
            counts[tx["Category"]] += 1

        spend_total = sum(v for v in totals.values() if v > 0)
        spend_count = sum(counts[c] for c in totals if totals[c] > 0)
        avg = spend_total / spend_count if spend_count else 0
        top = sorted(((c, v) for c, v in totals.items() if v > 0), key=lambda x: -x[1])
        top_cat = top[0][0] if top else "—"
        top_col = CAT_COLOURS.get(top_cat, ACCENT)

        self._make_metric_card(self._cards_row, "Total Spending",
                               f"${spend_total:,.2f}", ACCENT)
        self._make_metric_card(self._cards_row, "Transactions",
                               str(spend_count), ACCENT2)
        self._make_metric_card(self._cards_row, "Avg per Transaction",
                               f"${avg:,.2f}", SUCCESS)
        self._make_metric_card(self._cards_row, "Top Category",
                               top_cat, top_col)

        self._canvas.delete("all")
        self._canvas.update_idletasks()
        W = max(self._canvas.winfo_width(), 600)
        H = max(self._canvas.winfo_height(), 260)

        spending_cats = sorted([(c, v) for c, v in totals.items() if v > 0],
                                key=lambda x: -x[1])
        if not spending_cats:
            return

        max_val = spending_cats[0][1]
        label_w = 170
        pct_w = 80
        bar_x0 = label_w + 12
        bar_x1 = W - pct_w - 16
        bar_area = bar_x1 - bar_x0
        n = len(spending_cats)
        row_h = max(28, min(44, (H - 24) // n))

        y = 16
        for i, (cat, val) in enumerate(spending_cats):
            colour = CAT_COLOURS.get(cat, TEXT_SEC)
            bar_w = max(4, int(val / max_val * bar_area))
            pct = val / spend_total * 100 if spend_total else 0

            # Row bg on hover (alternate subtle shading)
            bg_col = PANEL if i % 2 == 0 else BG
            self._canvas.create_rectangle(0, y, W, y + row_h,
                                           fill=bg_col, outline="")

            # Category label
            self._canvas.create_text(14, y + row_h // 2, anchor="w",
                                      text=cat, fill=TEXT_SEC, font=FONT_BODY)

            # Track
            self._canvas.create_rectangle(bar_x0, y + row_h // 2 - 6,
                                           bar_x1, y + row_h // 2 + 6,
                                           fill=CANVAS_TRACK, outline="")
            # Bar
            self._canvas.create_rectangle(bar_x0, y + row_h // 2 - 6,
                                           bar_x0 + bar_w, y + row_h // 2 + 6,
                                           fill=colour, outline="")
            # Amount
            self._canvas.create_text(W - 14, y + row_h // 2, anchor="e",
                                      text=f"${val:,.2f}  ({pct:.0f}%)",
                                      fill=TEXT_SEC, font=FONT_SMALL)
            y += row_h

    # ── Transactions frame ──────────────────────────────────────────────────

    def _build_tx_frame(self):
        frm = self._frames["transactions"]

        toolbar = tk.Frame(frm, bg=BG)
        toolbar.pack(fill="x", padx=20, pady=(16, 8))

        # Filter
        tk.Label(toolbar, text="Category", bg=BG, fg=TEXT_SEC,
                 font=FONT_SMALL).pack(side="left")
        self._filter_var = tk.StringVar(value="All")
        self._filter_menu = ttk.Combobox(
            toolbar, textvariable=self._filter_var,
            state="readonly", width=18,
            style="Dark.TCombobox", font=FONT_BODY,
        )
        self._filter_menu["values"] = ["All"]
        self._filter_menu.pack(side="left", padx=(6, 16))
        self._filter_menu.bind("<<ComboboxSelected>>", lambda _: self._render_table())

        self._count_label = tk.Label(toolbar, text="", bg=BG,
                                      fg=TEXT_DIM, font=FONT_SMALL)
        self._count_label.pack(side="left")

        self._btn_recategorise = styled_button(
            toolbar, "✎  Re-categorise",
            self._recategorise_selected,
            style="purple", state="disabled",
        )
        self._btn_recategorise.pack(side="right")

        tk.Label(frm,
                 text="Double-click or right-click a row to reassign its category",
                 bg=BG, fg=TEXT_DIM, font=FONT_SMALL, anchor="w",
                 ).pack(fill="x", padx=20, pady=(0, 6))

        cols = ("Date", "Description", "Category", "Amount")

        tree_wrap = tk.Frame(frm, bg=BG)
        tree_wrap.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        self._tree = ttk.Treeview(tree_wrap, columns=cols, show="headings",
                                   selectmode="extended", style="Dark.Treeview")

        widths = {"Date": 100, "Description": 360, "Category": 150, "Amount": 100}
        for col in cols:
            self._tree.heading(col, text=col)
            self._tree.column(col, width=widths[col], anchor="e" if col == "Amount" else "w",
                               stretch=(col == "Description"))

        vsb = ttk.Scrollbar(tree_wrap, orient="vertical",
                             command=self._tree.yview,
                             style="Dark.Vertical.TScrollbar")
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Row tags
        self._tree.tag_configure("odd",         background=PANEL)
        self._tree.tag_configure("even",        background=BG)
        self._tree.tag_configure("manual_odd",  background="#2A2010")
        self._tree.tag_configure("manual_even", background="#241E0E")

        self._tree.bind("<Double-1>",         self._on_double_click)
        self._tree.bind("<Button-2>",         self._on_right_click)
        self._tree.bind("<Button-3>",         self._on_right_click)
        self._tree.bind("<<TreeviewSelect>>", self._on_selection_change)

        self._context_menu = tk.Menu(self, tearoff=0, bg=PANEL, fg=TEXT_PRI,
                                      activebackground=ACCENT,
                                      activeforeground="#FFFFFF",
                                      font=FONT_BODY, bd=0,
                                      relief="flat")
        self._context_menu.add_command(label="  ✎  Re-categorise…",
                                        command=self._recategorise_selected)

    def _render_table(self):
        self._tree.delete(*self._tree.get_children())
        sel = self._filter_var.get()
        txs = (self._transactions if sel == "All"
               else [t for t in self._transactions if t["Category"] == sel])
        for i, tx in enumerate(txs):
            is_manual = tx.get("_manual", False)
            tag = ("manual_odd" if i % 2 else "manual_even") if is_manual else \
                  ("odd"        if i % 2 else "even")
            try:
                amt = float(tx.get("Amount", 0) or 0)
                amt_str = f"${amt:,.2f}"
            except ValueError:
                amt_str = tx.get("Amount", "")
            self._tree.insert("", "end", values=(
                tx.get("Date", ""),
                tx.get("Description", ""),
                tx.get("Category", ""),
                amt_str,
            ), tags=(tag,))
        self._count_label.config(text=f"{len(txs)} rows")

    # ── Rules frame ─────────────────────────────────────────────────────────

    def _build_rules_frame(self):
        frm = self._frames["rules"]

        toolbar = tk.Frame(frm, bg=BG)
        toolbar.pack(fill="x", padx=20, pady=(16, 8))
        tk.Label(toolbar, text="Rules are applied on every import — most-specific match wins.",
                 bg=BG, fg=TEXT_SEC, font=FONT_SMALL).pack(side="left")
        self._btn_delete_rule = styled_button(
            toolbar, "🗑  Delete Rule",
            self._delete_selected_rule,
            style="danger", state="disabled",
        )
        self._btn_delete_rule.pack(side="right")

        tk.Label(frm, text=f"  {LEARNED_RULES_PATH}",
                 bg=BG, fg=TEXT_DIM, font=FONT_MONO, anchor="w").pack(fill="x", padx=16, pady=(0, 6))

        tree_wrap = tk.Frame(frm, bg=BG)
        tree_wrap.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        cols = ("Keyword / Description", "Category")
        self._rules_tree = ttk.Treeview(tree_wrap, columns=cols, show="headings",
                                         selectmode="browse", style="Dark.Treeview")
        self._rules_tree.heading("Keyword / Description", text="Keyword / Description")
        self._rules_tree.heading("Category", text="Category")
        self._rules_tree.column("Keyword / Description", width=520, stretch=True)
        self._rules_tree.column("Category", width=180, anchor="w")

        vsb2 = ttk.Scrollbar(tree_wrap, orient="vertical",
                              command=self._rules_tree.yview,
                              style="Dark.Vertical.TScrollbar")
        self._rules_tree.configure(yscrollcommand=vsb2.set)
        self._rules_tree.pack(side="left", fill="both", expand=True)
        vsb2.pack(side="right", fill="y")

        self._rules_tree.tag_configure("odd",  background=PANEL)
        self._rules_tree.tag_configure("even", background=BG)
        self._rules_tree.bind("<<TreeviewSelect>>",
                               lambda _: self._btn_delete_rule.config(
                                   state="normal" if self._rules_tree.selection() else "disabled"))
        self._refresh_rules_tab()

    def _refresh_rules_tab(self):
        self._rules_tree.delete(*self._rules_tree.get_children())
        for i, (kw, cat) in enumerate(sorted(self._learned.items())):
            tag = "odd" if i % 2 else "even"
            self._rules_tree.insert("", "end", values=(kw, cat), tags=(tag,))

    def _delete_selected_rule(self):
        sel = self._rules_tree.selection()
        if not sel:
            return
        vals = self._rules_tree.item(sel[0], "values")
        kw = vals[0]
        if not messagebox.askyesno("Delete Rule",
                                    f'Remove the learned rule for:\n\n"{kw}"?'):
            return
        self._learned.pop(kw.lower(), None)
        rules = []
        if LEARNED_RULES_PATH.exists():
            try:
                with open(LEARNED_RULES_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                rules = [e for e in data.get("rules", [])
                         if e["keyword"].lower() != kw.lower()]
            except Exception:
                rules = []
        with open(LEARNED_RULES_PATH, "w", encoding="utf-8") as f:
            json.dump({"rules": rules}, f, indent=2, ensure_ascii=False)
        self._refresh_rules_tab()
        self._update_learned_label()
        self._status_var.set(f"Rule deleted — {len(self._learned)} remaining")

    # ── Interactions ────────────────────────────────────────────────────────

    def _on_double_click(self, event):
        row = self._tree.identify_row(event.y)
        if not row:
            return
        if row not in self._tree.selection():
            self._tree.selection_set(row)
        self._recategorise_selected()

    def _on_right_click(self, event):
        row = self._tree.identify_row(event.y)
        if not row:
            return
        if row not in self._tree.selection():
            self._tree.selection_set(row)
        try:
            self._context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._context_menu.grab_release()

    def _on_selection_change(self, event):
        state = "normal" if self._tree.selection() and self._transactions else "disabled"
        self._btn_recategorise.config(state=state)

    def _recategorise_selected(self):
        selected = self._tree.selection()
        if not selected:
            messagebox.showinfo("No selection", "Select one or more transactions first.")
            return
        RecategoriseDialog(
            parent=self,
            transactions=self._transactions,
            item_ids=list(selected),
            tree=self._tree,
            on_done=self._after_recategorise,
        )

    def _after_recategorise(self, saved_rules: int):
        self._learned = load_learned_rules()
        self._update_learned_label()
        self._refresh_rules_tab()

        cats = sorted({tx["Category"] for tx in self._transactions},
                      key=lambda c: CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else 99)
        self._filter_menu["values"] = ["All"] + cats

        self._render_table()
        self._render_summary()

        manual_count = sum(1 for tx in self._transactions if tx.get("_manual"))
        self._status_var.set(
            f"{len(self._transactions)} transactions · "
            f"{manual_count} manual · "
            f"{len(self._learned)} rules saved"
        )

    def _update_learned_label(self):
        n = len(self._learned)
        self._learned_var.set(f"  {n} learned rule{'s' if n != 1 else ''}" if n else "")

    # ── Actions ─────────────────────────────────────────────────────────────

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select bank CSV",
            filetypes=[("CSV files", "*.csv *.tsv *.txt"), ("All files", "*.*")],
        )
        if path:
            self._csv_path = path
            name = Path(path).name
            self._path_var.set(name)
            self._btn_run.config(state="normal")
            self._status_var.set(f"Ready — {name}")
            self._transactions = []
            self._canvas.delete("all")
            for w in self._cards_row.winfo_children():
                w.destroy()
            self._tree.delete(*self._tree.get_children())
            self._btn_save.config(state="disabled")
            self._btn_recategorise.config(state="disabled")

    def _run(self):
        if not self._csv_path:
            return
        self._btn_run.config(state="disabled", text="Processing…")
        self._status_var.set("Categorising transactions…")
        threading.Thread(target=self._do_categorise, daemon=True).start()

    def _do_categorise(self):
        try:
            txs = load_csv(self._csv_path)
            learned = self._learned
            for tx in txs:
                tx["Category"] = categorise(tx.get("Description", ""), learned)
            self._transactions = txs
            self.after(0, self._on_done)
        except Exception as e:
            self.after(0, lambda: self._on_error(str(e)))

    def _on_done(self):
        n = len(self._transactions)
        self._status_var.set(f"{n} transactions categorised")
        self._btn_run.config(state="normal", text="▶  Categorise")
        self._btn_save.config(state="normal")

        cats = sorted({tx["Category"] for tx in self._transactions},
                      key=lambda c: CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else 99)
        self._filter_menu["values"] = ["All"] + cats
        self._filter_var.set("All")

        self._render_summary()
        self._render_table()
        self._switch_tab("summary")

    def _on_error(self, msg):
        self._status_var.set("Error processing file")
        self._btn_run.config(state="normal", text="▶  Categorise")
        messagebox.showerror("Error", f"Could not process file:\n\n{msg}")

    def _save(self):
        if not self._transactions:
            return
        default = Path(self._csv_path).stem + "_categorised.csv"
        out_path = filedialog.asksaveasfilename(
            title="Save categorised CSV",
            initialfile=default,
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if out_path:
            try:
                save_csv(self._transactions, out_path)
                self._status_var.set(f"Saved → {Path(out_path).name}")
                messagebox.showinfo("Saved", f"File saved:\n{out_path}")
            except Exception as e:
                messagebox.showerror("Save failed", str(e))


# ── Entry point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()