"""
Spending Categoriser — GUI version
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
from tkinter import filedialog, font, messagebox, ttk


# ── Category rules ─────────────────────────────────────────────────────────
RULES = [
    ("Income", [
        "salary", "payroll", "wages", "direct credit",
        "interest", "dividend", "tax refund",
    ]),

    ("Groceries", [
        "new world", "countdown", "woolworths",
        "pak'nsave", "paknsave", "fresh choice",
        "four square", "farro", "costco",
        "moore wilsons",
    ]),

    ("Dining / Eating Out", [
        "mcdonald", "mcdonalds", "kfc", "subway",
        "burger king", "wendys", "pizza",
        "restaurant", "bistro", "cafe",
        "coffee", "bakery", "sushi",
        "thai", "dumpling", "takeaway",
        "uber eats",
    ]),

    ("Transport", [
        "uber", "didi", "ola", "taxi",
        "snapper", "at hop", "bus",
        "train", "parking",
    ]),

    ("Fuel", [
        "bp ", "z energy", "mobil",
        "gull", "caltex", "fuel",
        "petrol",
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
        "jb hi-fi", "noel leeming",
        "mighty ape",
    ]),

    ("Entertainment", [
        "spotify", "netflix", "disney+",
        "youtube premium", "amazon prime",
        "steam", "playstation", "xbox",
        "nintendo", "cinema", "hoyts",
        "event cinema", "ticketmaster",
        "ticketek",
    ]),

    ("Health & Medical", [
        "doctor", "medical", "dentist",
        "chemist", "pharmacy", "hospital",
        "physio", "healthcare",
        "unichem", "life pharmacy",
        "chemist warehouse",
    ]),

    ("Travel", [
        "air new zealand", "air nz",
        "jetstar", "qantas",
        "booking.com", "expedia",
        "airbnb", "hotel",
        "motel", "hostel",
    ]),
]

CATEGORY_ORDER = [
    "Groceries",
    "Dining / Eating Out",
    "Transport",
    "Fuel",
    "Bills & Utilities",
    "Shopping",
    "Entertainment",
    "Health & Medical",
    "Travel",
    "Income",
    "Other",
]

ALL_CATEGORIES = CATEGORY_ORDER.copy()

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

# Path to learned rules file (same folder as this script)
LEARNED_RULES_PATH = Path(__file__).parent / "rules.json"


# ── Learned rules persistence ──────────────────────────────────────────────

def load_learned_rules() -> dict:
    """Returns {description_lower: category} from rules.json."""
    if LEARNED_RULES_PATH.exists():
        try:
            with open(LEARNED_RULES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {entry["keyword"].lower(): entry["category"]
                    for entry in data.get("rules", [])}
        except Exception:
            return {}
    return {}


def save_learned_rule(description: str, category: str) -> None:
    """Appends or updates a rule for the exact description in rules.json."""
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


# ── Categorisation ─────────────────────────────────────────────────────────

def categorise(description: str, learned: dict) -> str:
    """Learned rules (exact match) take priority over built-in substring rules."""
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
        writer = csv.DictWriter(f, fieldnames=["Category", "Amount"], delimiter=",")
        writer.writeheader()
        for cat in ordered:
            writer.writerow({"Category": cat, "Amount": f"{totals[cat]:.2f}"})


# ── Re-categorise Dialog ───────────────────────────────────────────────────

class RecategoriseDialog(tk.Toplevel):
    def __init__(self, parent, transactions, item_ids, tree, on_done):
        super().__init__(parent)
        self.title("Re-categorise")
        self.resizable(False, False)
        self.grab_set()
        self.configure(bg="#F7F6F2")

        self._transactions = transactions
        self._item_ids = item_ids
        self._tree = tree
        self._on_done = on_done
        self._result_var = tk.StringVar()

        self._build()
        self.update_idletasks()
        pw = parent.winfo_rootx()
        py = parent.winfo_rooty()
        self.geometry(f"+{pw + 160}+{py + 180}")

    def _build(self):
        pad = dict(padx=20, pady=8)

        header = tk.Frame(self, bg="#1A1A1A", height=44)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Assign Category",
                 bg="#1A1A1A", fg="#F7F6F2",
                 font=("Georgia", 12, "bold")).pack(side="left", padx=16, pady=10)

        if len(self._item_ids) == 1:
            vals = self._tree.item(self._item_ids[0], "values")
            desc = vals[1] if len(vals) > 1 else ""
            current_cat = vals[2] if len(vals) > 2 else ""
            info_text = f'"{desc}"'
            sub_text = f"Currently: {current_cat}"
        else:
            info_text = f"{len(self._item_ids)} transactions selected"
            sub_text = "All will be assigned the chosen category — rules saved for each"

        tk.Label(self, text=info_text, bg="#F7F6F2", fg="#1A1A1A",
                 font=("Georgia", 10, "bold"), wraplength=340,
                 justify="left").pack(anchor="w", **pad)
        tk.Label(self, text=sub_text, bg="#F7F6F2", fg="#888",
                 font=("Georgia", 9)).pack(anchor="w", padx=20, pady=(0, 6))

        tk.Label(
            self, text="💾  A rule will be saved to rules.json for future CSVs",
            bg="#FFFDE7", fg="#7A6000",
            font=("Georgia", 9), padx=10, pady=4,
        ).pack(fill="x", padx=20, pady=(0, 8))

        rb_frame = tk.Frame(self, bg="#F7F6F2")
        rb_frame.pack(fill="x", padx=20, pady=(0, 12))

        for i, cat in enumerate(ALL_CATEGORIES):
            colour = CAT_COLOURS.get(cat, "#888")
            tk.Radiobutton(
                rb_frame, text=cat,
                variable=self._result_var, value=cat,
                bg="#F7F6F2", fg="#222",
                activebackground="#F7F6F2",
                selectcolor=colour,
                font=("Georgia", 10),
                cursor="hand2",
            ).grid(row=i // 2, column=i % 2, sticky="w", padx=8, pady=3)

        btn_row = tk.Frame(self, bg="#F7F6F2")
        btn_row.pack(fill="x", padx=20, pady=(4, 16))

        tk.Button(
            btn_row, text="Cancel", command=self.destroy,
            bg="#EDECE6", fg="#444", relief="flat",
            font=("Georgia", 10), padx=14, pady=5,
            activebackground="#D8D7D0", cursor="hand2",
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            btn_row, text="Apply & Save Rule", command=self._apply,
            bg="#D85A30", fg="white", relief="flat",
            font=("Georgia", 10, "bold"), padx=14, pady=5,
            activebackground="#BF4A22", activeforeground="white",
            cursor="hand2",
        ).pack(side="right")

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
                                               f"Could not update rules.json:\n{e}",
                                               parent=self)
                    break

        self.destroy()
        self._on_done(saved_rules)


# ── GUI ────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Spending Categoriser")
        self.geometry("860x680")
        self.minsize(700, 520)
        self.configure(bg="#F7F6F2")

        self._transactions = []
        self._csv_path = ""
        self._learned: dict = load_learned_rules()

        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg="#1A1A1A", height=52)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Spending Categoriser",
                 bg="#1A1A1A", fg="#F7F6F2",
                 font=("Georgia", 15, "bold")).pack(side="left", padx=20, pady=14)
        self._learned_count_var = tk.StringVar()
        self._update_learned_label()
        tk.Label(header, textvariable=self._learned_count_var,
                 bg="#1A1A1A", fg="#888",
                 font=("Georgia", 9)).pack(side="right", padx=20)

        # File picker
        picker = tk.Frame(self, bg="#EDECE6", pady=10)
        picker.pack(fill="x")
        tk.Label(picker, text="CSV file:", bg="#EDECE6", fg="#444",
                 font=("Georgia", 10)).pack(side="left", padx=(16, 6))
        self._path_var = tk.StringVar(value="No file selected")
        tk.Label(picker, textvariable=self._path_var, bg="#EDECE6",
                 fg="#222", font=("Courier", 10), anchor="w",
                 width=55).pack(side="left")
        tk.Button(picker, text="Browse…", command=self._browse,
                  bg="#1A1A1A", fg="white", relief="flat",
                  font=("Georgia", 10), padx=14, pady=4,
                  activebackground="#333", activeforeground="white",
                  cursor="hand2").pack(side="left", padx=10)
        self._btn_run = tk.Button(picker, text="▶  Categorise", command=self._run,
                                   bg="#D85A30", fg="white", relief="flat",
                                   font=("Georgia", 10, "bold"), padx=16, pady=4,
                                   activebackground="#BF4A22", activeforeground="white",
                                   cursor="hand2", state="disabled")
        self._btn_run.pack(side="left", padx=4)

        # Status
        self._status_var = tk.StringVar(value="Select a CSV file to begin.")
        tk.Label(self, textvariable=self._status_var,
                 bg="#F7F6F2", fg="#888", font=("Georgia", 9),
                 anchor="w").pack(fill="x", padx=16, pady=(6, 2))

        # Notebook
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background="#F7F6F2", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Georgia", 10),
                        padding=[14, 6], background="#EDECE6", foreground="#555")
        style.map("TNotebook.Tab",
                  background=[("selected", "#F7F6F2")],
                  foreground=[("selected", "#1A1A1A")])

        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        self._tab_summary = tk.Frame(self._nb, bg="#F7F6F2")
        self._nb.add(self._tab_summary, text="  Summary  ")
        self._tab_tx = tk.Frame(self._nb, bg="#F7F6F2")
        self._nb.add(self._tab_tx, text="  Transactions  ")
        self._tab_rules = tk.Frame(self._nb, bg="#F7F6F2")
        self._nb.add(self._tab_rules, text="  Learned Rules  ")

        self._build_summary_tab()
        self._build_tx_tab()
        self._build_rules_tab()

    # ── Summary tab ─────────────────────────────────────────────────────

    def _build_summary_tab(self):
        self._cards_frame = tk.Frame(self._tab_summary, bg="#F7F6F2")
        self._cards_frame.pack(fill="x", padx=12, pady=(12, 8))
        self._canvas = tk.Canvas(self._tab_summary, bg="#F7F6F2",
                                  highlightthickness=0, height=320)
        self._canvas.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self._btn_save = tk.Button(self._tab_summary, text="💾  Save categorised CSV…",
                                    command=self._save,
                                    bg="#1A1A1A", fg="white", relief="flat",
                                    font=("Georgia", 10), padx=16, pady=5,
                                    activebackground="#333", activeforeground="white",
                                    cursor="hand2", state="disabled")
        self._btn_save.pack(pady=(0, 10))

    def _render_summary(self):
        for w in self._cards_frame.winfo_children():
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

        metrics = [
            ("Total spending", f"${spend_total:.2f}"),
            ("Transactions", str(spend_count)),
            ("Avg per txn", f"${spend_total/spend_count:.2f}" if spend_count else "$0.00"),
        ]
        top = sorted(((c, v) for c, v in totals.items() if v > 0), key=lambda x: -x[1])
        if top:
            metrics.append(("Top category", top[0][0]))

        for label, value in metrics:
            card = tk.Frame(self._cards_frame, bg="#EDECE6", padx=16, pady=10)
            card.pack(side="left", padx=(0, 10))
            tk.Label(card, text=label, bg="#EDECE6", fg="#888",
                     font=("Georgia", 9)).pack(anchor="w")
            tk.Label(card, text=value, bg="#EDECE6", fg="#1A1A1A",
                     font=("Georgia", 14, "bold")).pack(anchor="w")

        self._canvas.delete("all")
        self._canvas.update_idletasks()
        W = self._canvas.winfo_width() or 800
        H = self._canvas.winfo_height() or 300

        spending_cats = sorted([(c, v) for c, v in totals.items() if v > 0],
                                key=lambda x: -x[1])
        if not spending_cats:
            return

        max_val = spending_cats[0][1]
        bar_area_w = W - 180
        row_h = min(38, (H - 20) // max(len(spending_cats), 1))
        y = 16

        for cat, val in spending_cats:
            colour = CAT_COLOURS.get(cat, "#888")
            bar_w = max(4, int(val / max_val * bar_area_w))
            pct = val / spend_total * 100 if spend_total else 0
            self._canvas.create_text(6, y + row_h // 2, anchor="nw",
                                      text=cat, fill="#444", font=("Georgia", 9))
            self._canvas.create_rectangle(130, y + 4, 130 + bar_w, y + row_h - 4,
                                           fill=colour, outline="")
            self._canvas.create_text(136 + bar_w, y + row_h // 2, anchor="w",
                                      text=f"  ${val:.2f}  ({pct:.0f}%)",
                                      fill="#555", font=("Georgia", 9))
            y += row_h

    # ── Transactions tab ────────────────────────────────────────────────

    def _build_tx_tab(self):
        bar = tk.Frame(self._tab_tx, bg="#F7F6F2")
        bar.pack(fill="x", padx=12, pady=(10, 4))

        tk.Label(bar, text="Filter by category:", bg="#F7F6F2",
                 fg="#555", font=("Georgia", 10)).pack(side="left")
        self._filter_var = tk.StringVar(value="All")
        self._filter_menu = ttk.Combobox(bar, textvariable=self._filter_var,
                                          state="readonly", width=20, font=("Georgia", 10))
        self._filter_menu["values"] = ["All"]
        self._filter_menu.pack(side="left", padx=8)
        self._filter_menu.bind("<<ComboboxSelected>>", lambda _: self._render_table())

        self._count_label = tk.Label(bar, text="", bg="#F7F6F2",
                                      fg="#888", font=("Georgia", 9))
        self._count_label.pack(side="left", padx=6)

        self._btn_recategorise = tk.Button(
            bar, text="✎  Re-categorise Selected",
            command=self._recategorise_selected,
            bg="#534AB7", fg="white", relief="flat",
            font=("Georgia", 9, "bold"), padx=12, pady=3,
            activebackground="#3F38A0", activeforeground="white",
            cursor="hand2", state="disabled",
        )
        self._btn_recategorise.pack(side="right", padx=(0, 4))

        tk.Label(
            self._tab_tx,
            text="💡 Double-click or right-click a row to reassign — rules are saved to rules.json automatically",
            bg="#F7F6F2", fg="#AAAAAA", font=("Georgia", 8), anchor="w",
        ).pack(fill="x", padx=14, pady=(0, 4))

        cols = ("Date", "Description", "Category", "Amount")
        style = ttk.Style()
        style.configure("Treeview", font=("Georgia", 10), rowheight=24,
                        background="#FFFFFF", fieldbackground="#FFFFFF", foreground="#222")
        style.configure("Treeview.Heading", font=("Georgia", 10, "bold"),
                        background="#EDECE6", foreground="#1A1A1A")
        style.map("Treeview", background=[("selected", "#D85A30")],
                  foreground=[("selected", "white")])

        frame = tk.Frame(self._tab_tx, bg="#F7F6F2")
        frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="extended")
        widths = {"Date": 100, "Description": 340, "Category": 140, "Amount": 90}
        for col in cols:
            self._tree.heading(col, text=col)
            anchor = "e" if col == "Amount" else "w"
            self._tree.column(col, width=widths[col], anchor=anchor,
                               stretch=(col == "Description"))

        vsb = ttk.Scrollbar(frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._tree.tag_configure("odd",         background="#FAFAF7")
        self._tree.tag_configure("even",        background="#FFFFFF")
        self._tree.tag_configure("manual_odd",  background="#FFF8E1")
        self._tree.tag_configure("manual_even", background="#FFFDE7")

        self._tree.bind("<Double-1>",         self._on_double_click)
        self._tree.bind("<Button-2>",         self._on_right_click)
        self._tree.bind("<Button-3>",         self._on_right_click)
        self._tree.bind("<<TreeviewSelect>>", self._on_selection_change)

        self._context_menu = tk.Menu(self, tearoff=0, bg="#F7F6F2", fg="#1A1A1A",
                                      activebackground="#D85A30", activeforeground="white",
                                      font=("Georgia", 10))
        self._context_menu.add_command(label="✎  Re-categorise…",
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
        self._count_label.config(text=f"{len(txs)} transactions")

    # ── Learned Rules tab ───────────────────────────────────────────────

    def _build_rules_tab(self):
        bar = tk.Frame(self._tab_rules, bg="#F7F6F2")
        bar.pack(fill="x", padx=12, pady=(10, 4))

        tk.Label(bar, text="Rules learned from manual corrections",
                 bg="#F7F6F2", fg="#555", font=("Georgia", 10)).pack(side="left")

        self._btn_delete_rule = tk.Button(
            bar, text="🗑  Delete Selected Rule",
            command=self._delete_selected_rule,
            bg="#AA3333", fg="white", relief="flat",
            font=("Georgia", 9, "bold"), padx=12, pady=3,
            activebackground="#882222", activeforeground="white",
            cursor="hand2", state="disabled",
        )
        self._btn_delete_rule.pack(side="right")

        tk.Label(self._tab_rules, text=f"Saved to: {LEARNED_RULES_PATH}",
                 bg="#F7F6F2", fg="#AAAAAA", font=("Courier", 8),
                 anchor="w").pack(fill="x", padx=14, pady=(0, 4))

        frame = tk.Frame(self._tab_rules, bg="#F7F6F2")
        frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        cols = ("Keyword / Description", "Category")
        self._rules_tree = ttk.Treeview(frame, columns=cols,
                                         show="headings", selectmode="browse")
        self._rules_tree.heading("Keyword / Description", text="Keyword / Description")
        self._rules_tree.heading("Category", text="Category")
        self._rules_tree.column("Keyword / Description", width=520, stretch=True)
        self._rules_tree.column("Category", width=160, anchor="w")

        vsb2 = ttk.Scrollbar(frame, orient="vertical", command=self._rules_tree.yview)
        self._rules_tree.configure(yscrollcommand=vsb2.set)
        self._rules_tree.pack(side="left", fill="both", expand=True)
        vsb2.pack(side="right", fill="y")

        self._rules_tree.tag_configure("odd",  background="#FAFAF7")
        self._rules_tree.tag_configure("even", background="#FFFFFF")
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
        if not messagebox.askyesno("Delete rule",
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
        self._status_var.set(f"Rule deleted — {len(self._learned)} learned rules remain.")

    # ── Manual re-categorisation ─────────────────────────────────────────

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
            f"{len(self._transactions)} transactions — "
            f"{manual_count} manually re-categorised — "
            f"{len(self._learned)} learned rules saved"
        )

    def _update_learned_label(self):
        n = len(self._learned)
        self._learned_count_var.set(
            f"{n} learned rule{'s' if n != 1 else ''}" if n else ""
        )

    # ── Actions ─────────────────────────────────────────────────────────

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select bank CSV",
            filetypes=[("CSV files", "*.csv *.tsv *.txt"), ("All files", "*.*")],
        )
        if path:
            self._csv_path = path
            self._path_var.set(Path(path).name)
            self._btn_run.config(state="normal")
            self._status_var.set(f"Ready — {Path(path).name}")
            self._transactions = []
            self._render_clear()

    def _render_clear(self):
        self._canvas.delete("all")
        self._tree.delete(*self._tree.get_children())
        for w in self._cards_frame.winfo_children():
            w.destroy()
        self._btn_save.config(state="disabled")
        self._btn_recategorise.config(state="disabled")

    def _run(self):
        if not self._csv_path:
            return
        self._btn_run.config(state="disabled")
        self._status_var.set("Categorising…")
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
        self._status_var.set(f"Done — {n} transactions categorised.")
        self._btn_run.config(state="normal")
        self._btn_save.config(state="normal")

        cats = sorted({tx["Category"] for tx in self._transactions},
                      key=lambda c: CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else 99)
        self._filter_menu["values"] = ["All"] + cats
        self._filter_var.set("All")

        self._render_summary()
        self._render_table()
        self._nb.select(0)

    def _on_error(self, msg):
        self._status_var.set("Error — see dialog")
        self._btn_run.config(state="normal")
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
                messagebox.showinfo("Saved", f"File saved to:\n{out_path}")
            except Exception as e:
                messagebox.showerror("Save failed", str(e))


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()