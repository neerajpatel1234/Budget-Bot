"""
Spending Categoriser — GUI version
Run with:  python spending_categoriser_gui.py

Requires only Python 3 standard library (tkinter is built-in).
"""

import csv
import sys
import threading
import tkinter as tk
from collections import defaultdict
from pathlib import Path
from tkinter import filedialog, font, messagebox, ttk


# ── Category rules ─────────────────────────────────────────────────────────
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

CATEGORY_ORDER = [
    "Groceries", "Eating Out", "Shopping", "Bills",
    "Transport", "Travel", "Entertainment", "Payment / Refund", "Other",
]

CAT_COLOURS = {
    "Bills":            "#534AB7",
    "Groceries":        "#1D9E75",
    "Transport":        "#185FA5",
    "Shopping":         "#BA7517",
    "Eating Out":       "#D85A30",
    "Entertainment":    "#D4537E",
    "Travel":           "#0F6E56",
    "Payment / Refund": "#888780",
    "Other":            "#5F5E5A",
}


def categorise(description: str) -> str:
    desc_lower = description.lower()
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
    base_fields = [f for f in transactions[0].keys() if f not in ("_id", "Category")]
    fieldnames = base_fields[:2] + ["Category"] + base_fields[2:]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(transactions)


# ── GUI ────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Spending Categoriser")
        self.geometry("860x640")
        self.minsize(700, 500)
        self.configure(bg="#F7F6F2")

        self._transactions = []
        self._csv_path = ""

        self._build_ui()

    # ── Layout ──────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header bar ──────────────────────────────────────────────────
        header = tk.Frame(self, bg="#1A1A1A", height=52)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="Spending Categoriser",
            bg="#1A1A1A", fg="#F7F6F2",
            font=("Georgia", 15, "bold"),
        ).pack(side="left", padx=20, pady=14)

        # ── File picker bar ─────────────────────────────────────────────
        picker = tk.Frame(self, bg="#EDECE6", pady=10)
        picker.pack(fill="x")

        tk.Label(picker, text="CSV file:", bg="#EDECE6", fg="#444",
                 font=("Georgia", 10)).pack(side="left", padx=(16, 6))

        self._path_var = tk.StringVar(value="No file selected")
        tk.Label(picker, textvariable=self._path_var, bg="#EDECE6",
                 fg="#222", font=("Courier", 10), anchor="w",
                 width=55).pack(side="left")

        btn_browse = tk.Button(
            picker, text="Browse…", command=self._browse,
            bg="#1A1A1A", fg="white", relief="flat",
            font=("Georgia", 10), padx=14, pady=4,
            activebackground="#333", activeforeground="white",
            cursor="hand2",
        )
        btn_browse.pack(side="left", padx=10)

        self._btn_run = tk.Button(
            picker, text="▶  Categorise", command=self._run,
            bg="#D85A30", fg="white", relief="flat",
            font=("Georgia", 10, "bold"), padx=16, pady=4,
            activebackground="#BF4A22", activeforeground="white",
            cursor="hand2", state="disabled",
        )
        self._btn_run.pack(side="left", padx=4)

        # ── Status label ────────────────────────────────────────────────
        self._status_var = tk.StringVar(value="Select a CSV file to begin.")
        tk.Label(self, textvariable=self._status_var,
                 bg="#F7F6F2", fg="#888", font=("Georgia", 9),
                 anchor="w").pack(fill="x", padx=16, pady=(6, 2))

        # ── Notebook (tabs) ─────────────────────────────────────────────
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

        # Tab 1 — Summary
        self._tab_summary = tk.Frame(self._nb, bg="#F7F6F2")
        self._nb.add(self._tab_summary, text="  Summary  ")

        # Tab 2 — Transactions
        self._tab_tx = tk.Frame(self._nb, bg="#F7F6F2")
        self._nb.add(self._tab_tx, text="  Transactions  ")

        self._build_summary_tab()
        self._build_tx_tab()

    # ── Summary tab ─────────────────────────────────────────────────────

    def _build_summary_tab(self):
        # Metric cards row
        self._cards_frame = tk.Frame(self._tab_summary, bg="#F7F6F2")
        self._cards_frame.pack(fill="x", padx=12, pady=(12, 8))

        # Bar chart canvas
        self._canvas = tk.Canvas(self._tab_summary, bg="#F7F6F2",
                                  highlightthickness=0, height=320)
        self._canvas.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        # Save button
        self._btn_save = tk.Button(
            self._tab_summary, text="💾  Save categorised CSV…",
            command=self._save,
            bg="#1A1A1A", fg="white", relief="flat",
            font=("Georgia", 10), padx=16, pady=5,
            activebackground="#333", activeforeground="white",
            cursor="hand2", state="disabled",
        )
        self._btn_save.pack(pady=(0, 10))

    def _render_summary(self):
        # Clear cards
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

        # Metric cards
        metrics = [
            ("Total spending", f"${spend_total:.2f}"),
            ("Transactions", str(spend_count)),
            ("Avg per txn",
             f"${spend_total/spend_count:.2f}" if spend_count else "$0.00"),
        ]
        top = sorted(((c, v) for c, v in totals.items() if v > 0),
                     key=lambda x: -x[1])
        if top:
            metrics.append(("Top category", top[0][0]))

        for label, value in metrics:
            card = tk.Frame(self._cards_frame, bg="#EDECE6",
                            padx=16, pady=10)
            card.pack(side="left", padx=(0, 10))
            tk.Label(card, text=label, bg="#EDECE6", fg="#888",
                     font=("Georgia", 9)).pack(anchor="w")
            tk.Label(card, text=value, bg="#EDECE6", fg="#1A1A1A",
                     font=("Georgia", 14, "bold")).pack(anchor="w")

        # Bar chart
        self._canvas.delete("all")
        self._canvas.update_idletasks()
        W = self._canvas.winfo_width() or 800
        H = self._canvas.winfo_height() or 300

        spending_cats = sorted(
            [(c, v) for c, v in totals.items() if v > 0],
            key=lambda x: -x[1],
        )
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

            # Category label
            self._canvas.create_text(
                6, y + row_h // 2, anchor="nw",
                text=cat, fill="#444",
                font=("Georgia", 9),
            )
            # Bar
            self._canvas.create_rectangle(
                130, y + 4,
                130 + bar_w, y + row_h - 4,
                fill=colour, outline="",
            )
            # Value + pct
            self._canvas.create_text(
                136 + bar_w, y + row_h // 2,
                anchor="w",
                text=f"  ${val:.2f}  ({pct:.0f}%)",
                fill="#555", font=("Georgia", 9),
            )
            y += row_h

    # ── Transactions tab ────────────────────────────────────────────────

    def _build_tx_tab(self):
        # Filter bar
        bar = tk.Frame(self._tab_tx, bg="#F7F6F2")
        bar.pack(fill="x", padx=12, pady=(10, 4))

        tk.Label(bar, text="Filter by category:", bg="#F7F6F2",
                 fg="#555", font=("Georgia", 10)).pack(side="left")

        self._filter_var = tk.StringVar(value="All")
        self._filter_menu = ttk.Combobox(
            bar, textvariable=self._filter_var,
            state="readonly", width=20,
            font=("Georgia", 10),
        )
        self._filter_menu["values"] = ["All"]
        self._filter_menu.pack(side="left", padx=8)
        self._filter_menu.bind("<<ComboboxSelected>>", lambda _: self._render_table())

        self._count_label = tk.Label(bar, text="", bg="#F7F6F2",
                                      fg="#888", font=("Georgia", 9))
        self._count_label.pack(side="left", padx=6)

        # Treeview
        cols = ("Date", "Description", "Category", "Amount")
        style = ttk.Style()
        style.configure("Treeview", font=("Georgia", 10),
                        rowheight=24, background="#FFFFFF",
                        fieldbackground="#FFFFFF", foreground="#222")
        style.configure("Treeview.Heading", font=("Georgia", 10, "bold"),
                        background="#EDECE6", foreground="#1A1A1A")
        style.map("Treeview", background=[("selected", "#D85A30")],
                  foreground=[("selected", "white")])

        frame = tk.Frame(self._tab_tx, bg="#F7F6F2")
        frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._tree = ttk.Treeview(frame, columns=cols,
                                   show="headings", selectmode="browse")
        widths = {"Date": 100, "Description": 340, "Category": 140, "Amount": 90}
        for col in cols:
            self._tree.heading(col, text=col)
            anchor = "e" if col == "Amount" else "w"
            self._tree.column(col, width=widths[col],
                               anchor=anchor, stretch=(col == "Description"))

        vsb = ttk.Scrollbar(frame, orient="vertical",
                             command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Alternating row colours
        self._tree.tag_configure("odd",  background="#FAFAF7")
        self._tree.tag_configure("even", background="#FFFFFF")

    def _render_table(self):
        self._tree.delete(*self._tree.get_children())
        sel = self._filter_var.get()
        txs = (self._transactions if sel == "All"
               else [t for t in self._transactions if t["Category"] == sel])
        for i, tx in enumerate(txs):
            tag = "odd" if i % 2 else "even"
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

    def _run(self):
        if not self._csv_path:
            return
        self._btn_run.config(state="disabled")
        self._status_var.set("Categorising…")
        threading.Thread(target=self._do_categorise, daemon=True).start()

    def _do_categorise(self):
        try:
            txs = load_csv(self._csv_path)
            for tx in txs:
                tx["Category"] = categorise(tx.get("Description", ""))
            self._transactions = txs
            self.after(0, self._on_done)
        except Exception as e:
            self.after(0, lambda: self._on_error(str(e)))

    def _on_done(self):
        n = len(self._transactions)
        self._status_var.set(f"Done — {n} transactions categorised.")
        self._btn_run.config(state="normal")
        self._btn_save.config(state="normal")

        # Update filter dropdown
        cats = sorted({tx["Category"] for tx in self._transactions},
                      key=lambda c: CATEGORY_ORDER.index(c)
                      if c in CATEGORY_ORDER else 99)
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