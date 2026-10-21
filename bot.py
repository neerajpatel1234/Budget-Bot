"""
Spending Categoriser — Apple-style light GUI
Run with:  python spending_categoriser_gui.py

Requires only Python 3 standard library (tkinter is built-in).
Learned rules are saved to rules.json in the same folder as this script.
"""

import csv
import json
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
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

# Apple system colours
CAT_COLOURS = {
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

LEARNED_RULES_PATH = Path(__file__).parent / "rules.json"

# ── Design tokens (apple.com light) ─────────────────────────────────────────
WHITE        = "#FFFFFF"
BG           = "#F5F5F7"   # Apple section grey
BORDER       = "#D2D2D7"
HAIRLINE     = "#E8E8ED"
TEXT_PRI     = "#1D1D1F"
TEXT_SEC     = "#6E6E73"
TEXT_DIM     = "#86868B"
ACCENT       = "#0071E3"   # Apple link blue
ACCENT_HOVER = "#0077ED"
ACCENT_TINT  = "#E8F1FD"
SUCCESS      = "#34C759"
DANGER       = "#FF3B30"
MANUAL_ROW   = "#FFF8E1"
ROW_ALT      = "#FBFBFD"

if sys.platform == "darwin":
    FAMILY, MONO = ".AppleSystemUIFont", "Menlo"
elif sys.platform.startswith("win"):
    FAMILY, MONO = "Segoe UI", "Consolas"
else:
    FAMILY, MONO = "Helvetica", "Courier"

FONT_HERO    = (FAMILY, 30, "bold")
FONT_HEADING = (FAMILY, 15, "bold")
FONT_BODY    = (FAMILY, 12)
FONT_BOLD    = (FAMILY, 12, "bold")
FONT_SMALL   = (FAMILY, 11)
FONT_NAV     = (FAMILY, 12)
FONT_MONO    = (MONO, 10)
FONT_MED     = (FAMILY, 22, "bold")


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


# ── Drawing helpers ─────────────────────────────────────────────────────────

def rrect(c, x1, y1, x2, y2, r, **kw):
    """Rounded rectangle on a canvas."""
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
           x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
           x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    kw.setdefault("outline", "")
    return c.create_polygon(pts, smooth=True, **kw)


class PillButton(tk.Canvas):
    """Apple-style pill button."""
    STYLES = {
        #            fill       hover      text       disabled-fill  disabled-text
        "primary":   (ACCENT,   ACCENT_HOVER, WHITE,   HAIRLINE, "#AEAEB2"),
        "secondary": (HAIRLINE, "#DCDCE0",  TEXT_PRI,  HAIRLINE, "#AEAEB2"),
        "danger":    (DANGER,   "#E0352B",  WHITE,     HAIRLINE, "#AEAEB2"),
        "tint":      (ACCENT_TINT, "#D6E6FB", ACCENT,  HAIRLINE, "#AEAEB2"),
    }

    def __init__(self, parent, text, command, style="primary",
                 state="normal", padx=18, height=32):
        self._font = tkfont.Font(font=FONT_BOLD)
        self._text, self._command = text, command
        self._style, self._state = style, state
        self._padx, self._h = padx, height
        self._hover = False
        super().__init__(parent, width=self._width(), height=height,
                         bg=parent.cget("bg"), highlightthickness=0, bd=0)
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<Button-1>", self._click)
        self._draw()

    def _width(self):
        return self._font.measure(self._text) + 2 * self._padx

    def _set_hover(self, v):
        self._hover = v
        self._draw()

    def _click(self, _):
        if self._state == "normal" and self._command:
            self._command()

    def _draw(self):
        fill, hover, fg, dfill, dfg = self.STYLES[self._style]
        enabled = self._state == "normal"
        self.configure(cursor="hand2" if enabled else "arrow")
        self.delete("all")
        w = int(self.cget("width"))
        rrect(self, 0, 0, w, self._h, self._h / 2,
              fill=(hover if self._hover else fill) if enabled else dfill)
        self.create_text(w / 2, self._h / 2, text=self._text, font=FONT_BOLD,
                         fill=fg if enabled else dfg)

    def configure(self, cnf=None, **kw):
        if cnf:
            kw.update(cnf)
        changed = False
        if "text" in kw:
            self._text = kw.pop("text")
            kw["width"] = self._width()
            changed = True
        if "state" in kw:
            self._state = kw.pop("state")
            changed = True
        super().configure(**kw)
        if changed:
            self._draw()

    config = configure


# ── Re-categorise Dialog ────────────────────────────────────────────────────

class RecategoriseDialog(tk.Toplevel):
    def __init__(self, parent, transactions, item_ids, tree, on_done):
        super().__init__(parent)
        self.title("Re-categorise")
        self.resizable(False, False)
        self.configure(bg=WHITE)

        self._transactions = transactions
        self._item_ids = item_ids
        self._tree = tree
        self._on_done = on_done
        self._result_var = tk.StringVar()

        self._build()
        self.update_idletasks()
        self.geometry(f"+{parent.winfo_rootx() + 200}+{parent.winfo_rooty() + 120}")
        self.grab_set()

    def _build(self):
        body = tk.Frame(self, bg=WHITE)
        body.pack(fill="both", padx=32, pady=28)

        tk.Label(body, text="Assign a category", bg=WHITE, fg=TEXT_PRI,
                 font=(FAMILY, 20, "bold")).pack(anchor="w")

        if len(self._item_ids) == 1:
            vals = self._tree.item(self._item_ids[0], "values")
            desc = vals[1] if len(vals) > 1 else ""
            current = vals[2] if len(vals) > 2 else ""
            info, sub = f'“{desc}”', f"Currently {current}"
        else:
            info = f"{len(self._item_ids)} transactions selected"
            sub = "A rule will be saved for each description"

        tk.Label(body, text=info, bg=WHITE, fg=TEXT_PRI, font=FONT_BOLD,
                 wraplength=380, justify="left").pack(anchor="w", pady=(10, 0))
        tk.Label(body, text=sub, bg=WHITE, fg=TEXT_SEC,
                 font=FONT_SMALL).pack(anchor="w", pady=(2, 14))

        note = tk.Frame(body, bg=BG, padx=14, pady=10)
        note.pack(fill="x", pady=(0, 16))
        tk.Label(note, text="Your choice is saved to rules.json and applied to future imports.",
                 bg=BG, fg=TEXT_SEC, font=FONT_SMALL, wraplength=380,
                 justify="left").pack(anchor="w")

        grid = tk.Frame(body, bg=WHITE)
        grid.pack(fill="x")
        for i, cat in enumerate(ALL_CATEGORIES):
            row_f = tk.Frame(grid, bg=WHITE)
            row_f.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 24), pady=4)
            tk.Label(row_f, text="●", bg=WHITE, fg=CAT_COLOURS.get(cat, TEXT_SEC),
                     font=FONT_SMALL).pack(side="left", padx=(0, 2))
            tk.Radiobutton(
                row_f, text=cat, variable=self._result_var, value=cat,
                bg=WHITE, fg=TEXT_PRI, activebackground=WHITE,
                activeforeground=TEXT_PRI, selectcolor=WHITE,
                font=FONT_BODY, cursor="hand2", highlightthickness=0, bd=0,
            ).pack(side="left")

        tk.Frame(body, bg=HAIRLINE, height=1).pack(fill="x", pady=(20, 16))

        btn_row = tk.Frame(body, bg=WHITE)
        btn_row.pack(fill="x")
        PillButton(btn_row, "Apply", self._apply).pack(side="right")
        PillButton(btn_row, "Cancel", self.destroy,
                   style="secondary").pack(side="right", padx=(0, 8))

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
        self.geometry("1000x720")
        self.minsize(820, 580)
        self.configure(bg=BG)

        self._transactions = []
        self._csv_path = ""
        self._learned: dict = load_learned_rules()
        self._active_tab = tk.StringVar(value="summary")
        self._chart_data = []
        self._chart_total = 0.0

        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Light.Treeview",
                        background=WHITE, fieldbackground=WHITE,
                        foreground=TEXT_PRI, rowheight=36,
                        font=FONT_BODY, borderwidth=0, relief="flat")
        style.configure("Light.Treeview.Heading",
                        background=WHITE, foreground=TEXT_DIM,
                        font=FONT_SMALL, relief="flat", borderwidth=0,
                        padding=(10, 10))
        style.map("Light.Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", WHITE)])
        style.map("Light.Treeview.Heading",
                  background=[("active", WHITE)])
        style.layout("Light.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        style.configure("Light.Vertical.TScrollbar",
                        background=BORDER, troughcolor=WHITE,
                        bordercolor=WHITE, lightcolor=BORDER, darkcolor=BORDER,
                        arrowcolor=WHITE, width=8, relief="flat")
        style.map("Light.Vertical.TScrollbar", background=[("active", TEXT_DIM)])
        style.configure("Light.TCombobox",
                        fieldbackground=WHITE, background=WHITE,
                        foreground=TEXT_PRI, selectbackground=ACCENT_TINT,
                        selectforeground=TEXT_PRI, arrowcolor=TEXT_SEC,
                        bordercolor=BORDER, lightcolor=WHITE, darkcolor=WHITE,
                        padding=4)
        self.option_add("*TCombobox*Listbox.background", WHITE)
        self.option_add("*TCombobox*Listbox.foreground", TEXT_PRI)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.option_add("*TCombobox*Listbox.font", FONT_BODY)

    # ── Layout ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._learned_var = tk.StringVar()
        self._path_var = tk.StringVar(value="")

        # Global nav bar (apple.com style)
        nav = tk.Frame(self, bg=WHITE, height=56)
        nav.pack(fill="x")
        nav.pack_propagate(False)
        tk.Label(nav, text="◈", bg=WHITE, fg=TEXT_PRI,
                 font=(FAMILY, 18)).pack(side="left", padx=(24, 6))
        tk.Label(nav, text="Spending", bg=WHITE, fg=TEXT_PRI,
                 font=FONT_BOLD).pack(side="left")

        right = tk.Frame(nav, bg=WHITE)
        right.pack(side="right", padx=20)
        self._btn_run = PillButton(right, "Categorise", self._run, state="disabled")
        self._btn_run.pack(side="right")
        PillButton(right, "Choose CSV…", self._browse,
                   style="secondary").pack(side="right", padx=(0, 8))

        tabs = tk.Frame(nav, bg=WHITE)
        tabs.place(relx=0.5, rely=0.5, anchor="center")
        self._tabs = {}
        for key, label in (("summary", "Overview"),
                           ("transactions", "Transactions"),
                           ("rules", "Learned Rules")):
            self._tabs[key] = self._make_tab(tabs, key, label)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # Page header
        self._main = tk.Frame(self, bg=BG)
        self._main.pack(fill="both", expand=True)

        hdr = tk.Frame(self._main, bg=BG)
        hdr.pack(fill="x", padx=40, pady=(28, 8))
        titles = tk.Frame(hdr, bg=BG)
        titles.pack(side="left")
        self._page_title = tk.Label(titles, text="Overview", bg=BG,
                                    fg=TEXT_PRI, font=FONT_HERO)
        self._page_title.pack(anchor="w")
        self._status_var = tk.StringVar(value="Choose a CSV file to begin.")
        tk.Label(titles, textvariable=self._status_var, bg=BG, fg=TEXT_SEC,
                 font=(FAMILY, 13)).pack(anchor="w", pady=(2, 0))
        self._btn_save = PillButton(hdr, "Export summary", self._save,
                                    style="tint", state="disabled")
        self._btn_save.pack(side="right", anchor="s")

        self._frames = {k: tk.Frame(self._main, bg=BG)
                        for k in ("summary", "transactions", "rules")}
        self._build_summary_frame()
        self._build_tx_frame()
        self._build_rules_frame()
        self._update_learned_label()
        self._switch_tab("summary")

    def _make_tab(self, parent, key, label):
        f = tk.Frame(parent, bg=WHITE, cursor="hand2")
        f.pack(side="left", padx=14)
        lbl = tk.Label(f, text=label, bg=WHITE, fg=TEXT_SEC, font=FONT_NAV)
        lbl.pack(pady=(4, 2))
        under = tk.Frame(f, bg=WHITE, height=2)
        under.pack(fill="x")

        def enter(_):
            if self._active_tab.get() != key:
                lbl.config(fg=TEXT_PRI)

        def leave(_):
            if self._active_tab.get() != key:
                lbl.config(fg=TEXT_SEC)

        for w in (f, lbl, under):
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)
            w.bind("<Button-1>", lambda _e, k=key: self._switch_tab(k))
        return lbl, under

    def _switch_tab(self, key):
        self._active_tab.set(key)
        for k, (lbl, under) in self._tabs.items():
            on = k == key
            lbl.config(fg=TEXT_PRI if on else TEXT_SEC)
            under.config(bg=ACCENT if on else WHITE)
        self._page_title.config(text={"summary": "Overview",
                                      "transactions": "Transactions",
                                      "rules": "Learned Rules"}[key])
        for k, frm in self._frames.items():
            if k == key:
                frm.pack(fill="both", expand=True)
            else:
                frm.pack_forget()

    # ── Summary frame ───────────────────────────────────────────────────────

    def _build_summary_frame(self):
        frm = self._frames["summary"]
        self._cards_row = tk.Frame(frm, bg=BG)
        self._cards_row.pack(fill="x", padx=40, pady=(12, 16))
        for i in range(4):
            self._cards_row.columnconfigure(i, weight=1, uniform="cards")

        self._canvas = tk.Canvas(frm, bg=BG, highlightthickness=0, bd=0)
        self._canvas.pack(fill="both", expand=True, padx=40, pady=(0, 32))
        self._canvas.bind("<Configure>", lambda _e: self._draw_chart())

    def _make_metric_card(self, col, label, value, dot):
        card = tk.Frame(self._cards_row, bg=WHITE, padx=20, pady=16)
        card.grid(row=0, column=col, sticky="nsew",
                  padx=(0, 12 if col < 3 else 0))
        top = tk.Frame(card, bg=WHITE)
        top.pack(anchor="w")
        tk.Label(top, text="●", bg=WHITE, fg=dot, font=FONT_SMALL).pack(side="left")
        tk.Label(top, text=" " + label, bg=WHITE, fg=TEXT_SEC,
                 font=FONT_SMALL).pack(side="left")
        tk.Label(card, text=value, bg=WHITE, fg=TEXT_PRI,
                 font=FONT_MED).pack(anchor="w", pady=(6, 0))

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

        self._make_metric_card(0, "Total spending", f"${spend_total:,.2f}", ACCENT)
        self._make_metric_card(1, "Transactions", str(spend_count), "#AF52DE")
        self._make_metric_card(2, "Average", f"${avg:,.2f}", SUCCESS)
        self._make_metric_card(3, "Top category", top_cat,
                               CAT_COLOURS.get(top_cat, ACCENT))

        self._chart_data = top
        self._chart_total = spend_total
        self._draw_chart()

    def _draw_chart(self):
        c = self._canvas
        c.delete("all")
        if not self._chart_data:
            return
        W = max(c.winfo_width(), 600)
        H = max(c.winfo_height(), 260)
        rrect(c, 0, 0, W, H, 18, fill=WHITE)

        c.create_text(28, 30, anchor="w", text="Spending breakdown",
                      fill=TEXT_PRI, font=FONT_HEADING)

        data = self._chart_data
        max_val = data[0][1]
        bar_x0, bar_x1 = 200, W - 170
        bar_area = max(bar_x1 - bar_x0, 50)
        row_h = max(34, min(46, (H - 70) // len(data)))

        y = 58
        for cat, val in data:
            mid = y + row_h // 2
            colour = CAT_COLOURS.get(cat, TEXT_SEC)
            bar_w = max(8, int(val / max_val * bar_area))
            pct = val / self._chart_total * 100 if self._chart_total else 0
            c.create_text(28, mid, anchor="w", text=cat,
                          fill=TEXT_PRI, font=FONT_BODY)
            rrect(c, bar_x0, mid - 5, bar_x1, mid + 5, 5, fill=BG)
            rrect(c, bar_x0, mid - 5, bar_x0 + bar_w, mid + 5, 5, fill=colour)
            c.create_text(W - 28, mid, anchor="e",
                          text=f"${val:,.2f}   {pct:.0f}%",
                          fill=TEXT_SEC, font=FONT_SMALL)
            y += row_h

    # ── Transactions frame ──────────────────────────────────────────────────

    def _build_tx_frame(self):
        frm = self._frames["transactions"]

        toolbar = tk.Frame(frm, bg=BG)
        toolbar.pack(fill="x", padx=40, pady=(8, 10))

        tk.Label(toolbar, text="Category", bg=BG, fg=TEXT_SEC,
                 font=FONT_SMALL).pack(side="left")
        self._filter_var = tk.StringVar(value="All")
        self._filter_menu = ttk.Combobox(
            toolbar, textvariable=self._filter_var, state="readonly",
            width=20, style="Light.TCombobox", font=FONT_BODY)
        self._filter_menu["values"] = ["All"]
        self._filter_menu.pack(side="left", padx=(8, 14))
        self._filter_menu.bind("<<ComboboxSelected>>", lambda _: self._render_table())

        self._count_label = tk.Label(toolbar, text="", bg=BG,
                                      fg=TEXT_DIM, font=FONT_SMALL)
        self._count_label.pack(side="left")

        self._btn_recategorise = PillButton(
            toolbar, "Re-categorise", self._recategorise_selected,
            state="disabled")
        self._btn_recategorise.pack(side="right")

        tk.Label(frm, text="Double-click or right-click a row to reassign its category.",
                 bg=BG, fg=TEXT_DIM, font=FONT_SMALL, anchor="w",
                 ).pack(fill="x", padx=40, pady=(0, 8))

        cols = ("Date", "Description", "Category", "Amount")
        card = tk.Frame(frm, bg=WHITE, padx=12, pady=10)
        card.pack(fill="both", expand=True, padx=40, pady=(0, 32))

        self._tree = ttk.Treeview(card, columns=cols, show="headings",
                                   selectmode="extended", style="Light.Treeview")
        widths = {"Date": 100, "Description": 360, "Category": 160, "Amount": 100}
        for col in cols:
            self._tree.heading(col, text=col, anchor="e" if col == "Amount" else "w")
            self._tree.column(col, width=widths[col],
                               anchor="e" if col == "Amount" else "w",
                               stretch=(col == "Description"))

        vsb = ttk.Scrollbar(card, orient="vertical", command=self._tree.yview,
                             style="Light.Vertical.TScrollbar")
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._tree.tag_configure("odd",         background=ROW_ALT)
        self._tree.tag_configure("even",        background=WHITE)
        self._tree.tag_configure("manual_odd",  background=MANUAL_ROW)
        self._tree.tag_configure("manual_even", background=MANUAL_ROW)

        self._tree.bind("<Double-1>",         self._on_double_click)
        self._tree.bind("<Button-2>",         self._on_right_click)
        self._tree.bind("<Button-3>",         self._on_right_click)
        self._tree.bind("<<TreeviewSelect>>", self._on_selection_change)

        self._context_menu = tk.Menu(self, tearoff=0, bg=WHITE, fg=TEXT_PRI,
                                      activebackground=ACCENT,
                                      activeforeground=WHITE,
                                      font=FONT_BODY, bd=0, relief="flat")
        self._context_menu.add_command(label="  Re-categorise…",
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
        toolbar.pack(fill="x", padx=40, pady=(8, 4))
        tk.Label(toolbar, textvariable=self._learned_var, bg=BG, fg=TEXT_SEC,
                 font=FONT_SMALL).pack(side="left")
        self._btn_delete_rule = PillButton(
            toolbar, "Delete rule", self._delete_selected_rule,
            style="danger", state="disabled")
        self._btn_delete_rule.pack(side="right")

        tk.Label(frm, text=str(LEARNED_RULES_PATH), bg=BG, fg=TEXT_DIM,
                 font=FONT_MONO, anchor="w").pack(fill="x", padx=40, pady=(0, 10))

        card = tk.Frame(frm, bg=WHITE, padx=12, pady=10)
        card.pack(fill="both", expand=True, padx=40, pady=(0, 32))

        cols = ("Keyword / Description", "Category")
        self._rules_tree = ttk.Treeview(card, columns=cols, show="headings",
                                         selectmode="browse", style="Light.Treeview")
        self._rules_tree.heading("Keyword / Description", text="Keyword / Description", anchor="w")
        self._rules_tree.heading("Category", text="Category", anchor="w")
        self._rules_tree.column("Keyword / Description", width=520, stretch=True)
        self._rules_tree.column("Category", width=180, anchor="w")

        vsb2 = ttk.Scrollbar(card, orient="vertical", command=self._rules_tree.yview,
                              style="Light.Vertical.TScrollbar")
        self._rules_tree.configure(yscrollcommand=vsb2.set)
        self._rules_tree.pack(side="left", fill="both", expand=True)
        vsb2.pack(side="right", fill="y")

        self._rules_tree.tag_configure("odd",  background=ROW_ALT)
        self._rules_tree.tag_configure("even", background=WHITE)
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
        self._learned_var.set(
            f"{n} learned rule{'s' if n != 1 else ''} · applied on every import"
            if n else "No learned rules yet — re-categorise a transaction to create one.")

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
            self._transactions = []
            self._chart_data = []
            self._canvas.delete("all")
            for w in self._cards_row.winfo_children():
                w.destroy()
            self._tree.delete(*self._tree.get_children())
            self._btn_save.config(state="disabled")
            self._btn_recategorise.config(state="disabled")

            self._status_var.set(f"Loading {name}…")
            self._run()

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
        self._status_var.set(f"{Path(self._csv_path).name} · {n} transactions categorised")
        self._btn_run.config(state="normal", text="Categorise")
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
        self._btn_run.config(state="normal", text="Categorise")
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