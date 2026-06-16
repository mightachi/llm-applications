"""Generate synthetic but realistic demo data with seeded reconciliation issues.

Produces:
  - data/samples/purchase_register.csv  (buyer's books, Tally-style export)
  - data/samples/gstr2b.json            (official GSTR-2B JSON shape)
  - data/samples/invoices/*.txt         (a couple of OCR-style unstructured invoices)

The two files are deliberately INCONSISTENT so the engine surfaces every case:
matched, amount mismatch, missing-in-2B (supplier didn't file), duplicate, missing-in-books.
"""

from __future__ import annotations

import csv
import json
import os
from datetime import date

HERE = os.path.dirname(__file__)
SAMPLES = os.path.join(HERE, "samples")
BUYER_GSTIN = "27ABCDE1234F1Z5"  # Maharashtra

# (gstin, name, inv_no, date, taxable, cgst, sgst, igst)
BOOKS = [
    ("27AAACS1111A1Z1", "Sai Traders",        "INV-1001", "05-04-2026", 100000, 9000, 9000, 0),
    ("27AAACS2222B1Z2", "Bharat Steel",        "INV-1002", "07-04-2026", 250000, 22500, 22500, 0),
    ("24AAACG3333C1Z3", "Gujarat Polymers",    "GJ/778",   "09-04-2026", 180000, 0, 0, 32400),  # interstate IGST
    ("27AAACS4444D1Z4", "Pune Hardware",       "PH-50",    "11-04-2026", 60000, 5400, 5400, 0),
    ("29AAACS5555E1Z5", "Bengaluru Components", "BLR-9001", "12-04-2026", 320000, 0, 0, 57600),  # interstate
    ("27AAACS6666F1Z6", "Konkan Logistics",    "KL-204",   "14-04-2026", 45000, 4050, 4050, 0),
    ("27AAACS6666F1Z6", "Konkan Logistics",    "KL-204",   "14-04-2026", 45000, 4050, 4050, 0),  # DUPLICATE
    ("27AAACS7777G1Z7", "Mumbai Packaging",    "MP-1188",  "16-04-2026", 90000, 8100, 8100, 0),
]

# GSTR-2B reflects what suppliers ACTUALLY filed.
TWOB = [
    # Sai Traders: matched
    ("27AAACS1111A1Z1", "Sai Traders",        "INV-1001", "05-04-2026", 100000, 9000, 9000, 0),
    # Bharat Steel: AMOUNT MISMATCH (filed lower tax than booked)
    ("27AAACS2222B1Z2", "Bharat Steel",        "INV-1002", "07-04-2026", 240000, 21600, 21600, 0),
    # Gujarat Polymers: matched (typo in invoice no to test fuzzy match: GJ778 vs GJ/778)
    ("24AAACG3333C1Z3", "Gujarat Polymers",    "GJ778",    "09-04-2026", 180000, 0, 0, 32400),
    # Pune Hardware: MISSING (supplier didn't file) -> not present
    # Bengaluru Components: matched
    ("29AAACS5555E1Z5", "Bengaluru Components", "BLR-9001", "12-04-2026", 320000, 0, 0, 57600),
    # Konkan Logistics: matched (single)
    ("27AAACS6666F1Z6", "Konkan Logistics",    "KL-204",   "14-04-2026", 45000, 4050, 4050, 0),
    # Mumbai Packaging: MISSING in 2B (supplier didn't file)
    # Extra: supplier filed an invoice the buyer never booked -> MISSING IN BOOKS
    ("27AAACS8888H1Z8", "Nashik Chemicals",    "NC-77",    "15-04-2026", 70000, 6300, 6300, 0),
]


def write_purchase_register() -> None:
    path = os.path.join(SAMPLES, "purchase_register.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Supplier GSTIN", "Supplier Name", "Invoice No", "Invoice Date",
                    "Taxable Value", "CGST", "SGST", "IGST"])
        for row in BOOKS:
            w.writerow(row)
    print("wrote", path)


def write_gstr2b() -> None:
    """Build the official GSTR-2B-ish JSON grouped by supplier (ctin)."""
    by_supplier: dict[str, dict] = {}
    for gstin, name, inum, dt, txval, cgst, sgst, igst in TWOB:
        s = by_supplier.setdefault(gstin, {"ctin": gstin, "trdnm": name, "inv": []})
        s["inv"].append({
            "inum": inum, "dt": dt, "txval": txval,
            "items": [{"txval": txval, "camt": cgst, "samt": sgst, "iamt": igst}],
        })
    doc = {
        "data": {
            "rtnprd": "042026",
            "gstin": BUYER_GSTIN,
            "docdata": {"b2b": list(by_supplier.values())},
        }
    }
    path = os.path.join(SAMPLES, "gstr2b.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
    print("wrote", path)


def write_unstructured_invoices() -> None:
    inv_dir = os.path.join(SAMPLES, "invoices")
    os.makedirs(inv_dir, exist_ok=True)
    samples = {
        "pune_hardware.txt": (
            "PUNE HARDWARE\nGSTIN: 27AAACS4444D1Z4\nTax Invoice No: PH-50  Date: 11-04-2026\n"
            "Taxable Value: 60,000.00\nCGST 9%: 5,400.00\nSGST 9%: 5,400.00\nTotal: 70,800.00\n"
        ),
        "mumbai_packaging.txt": (
            "Mumbai Packaging Pvt Ltd\nGSTIN 27AAACS7777G1Z7\nInvoice # MP-1188 dated 16-04-2026\n"
            "Taxable 90,000.00  CGST 8,100.00  SGST 8,100.00  Invoice Total 1,06,200.00\n"
        ),
    }
    for name, text in samples.items():
        with open(os.path.join(inv_dir, name), "w", encoding="utf-8") as f:
            f.write(text)
    print("wrote", inv_dir, "/*.txt")


if __name__ == "__main__":
    os.makedirs(SAMPLES, exist_ok=True)
    write_purchase_register()
    write_gstr2b()
    write_unstructured_invoices()
