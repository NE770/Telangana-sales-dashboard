"""Telangana building-materials sales dashboard: Flask API on a SQLite database.
Run:  pip install flask   then   python app.py   then open http://127.0.0.1:5000
The first run creates sales.db and fills it with generated sample data."""
import math
import os
import random
import sqlite3
from datetime import date, timedelta

from flask import Flask, g, jsonify, request, send_from_directory

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sales.db")
app = Flask(__name__)

DISTRICTS = ["Hyderabad", "Rangareddy", "Medchal-Malkajgiri", "Warangal",
             "Karimnagar", "Khammam", "Nizamabad", "Sangareddy"]
BASE = [2100000, 1300000, 1150000, 600000, 500000, 450000, 400000, 350000]  # rupees per day
# name, category, unit, unit price, typical quantity per order, sales weight, growth trend
PRODUCTS = [
    ("Tata Tiscon TMT", "Steel", "t", 62000, 1.5, .20, .25),
    ("Vizag Steel TMT", "Steel", "t", 59000, 1.5, .14, -.10),
    ("JSW Neosteel TMT", "Steel", "t", 60500, 1.5, .12, .35),
    ("UltraTech Cement", "Cement", "bags", 400, 40, .15, .10),
    ("Sagar Cements", "Cement", "bags", 380, 40, .10, .40),
    ("Dalmia Cement", "Cement", "bags", 395, 40, .09, -.20),
    ("Birla Aerocon AAC Blocks", "Blocks", "m3", 4800, 10, .08, -.30),
]


def seed():
    con = sqlite3.connect(DB)
    con.executescript("""
        CREATE TABLE districts(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
        CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
                              unit TEXT NOT NULL, unit_price REAL NOT NULL, typical_qty REAL NOT NULL);
        CREATE TABLE sales(id INTEGER PRIMARY KEY, sale_date TEXT NOT NULL,
                           district_id INTEGER NOT NULL REFERENCES districts(id),
                           product_id INTEGER NOT NULL REFERENCES products(id),
                           quantity REAL NOT NULL, revenue REAL NOT NULL, orders INTEGER NOT NULL);
        CREATE TABLE traffic(sale_date TEXT NOT NULL, district_id INTEGER NOT NULL REFERENCES districts(id),
                             visits INTEGER NOT NULL, PRIMARY KEY(sale_date, district_id));
        CREATE INDEX idx_sales_date ON sales(sale_date, district_id);
    """)
    con.executemany("INSERT INTO districts(name) VALUES (?)", [(d,) for d in DISTRICTS])
    con.executemany("INSERT INTO products(name,category,unit,unit_price,typical_qty) VALUES (?,?,?,?,?)",
                    [p[:5] for p in PRODUCTS])
    rnd, end, days = random.Random(11), date(2026, 11, 12), 730
    sales, traffic = [], []
    for i in range(days):
        d = (end - timedelta(days=days - 1 - i)).isoformat()
        wk = .78 if date.fromisoformat(d).weekday() >= 5 else 1
        season = 1 + .15 * math.sin(i / 58) + i / days * .25
        for k in range(len(DISTRICTS)):
            day_rev = BASE[k] * season * wk * (.85 + rnd.random() * .3)
            w = [p[5] * (1 + p[6] * (i / days - .5)) * (1 + .25 * math.sin(j * 2 + k * 1.7))
                 for j, p in enumerate(PRODUCTS)]
            total, orders_day = sum(w), 0
            for j, p in enumerate(PRODUCTS):
                rev = day_rev * w[j] / total
                qty = rev / p[3]
                orders = max(1, round(qty / p[4]))
                orders_day += orders
                sales.append((d, k + 1, j + 1, round(qty, 2), round(rev, 2), orders))
            traffic.append((d, k + 1, round(orders_day / (.03 * (.9 + rnd.random() * .2)))))
    con.executemany("INSERT INTO sales(sale_date,district_id,product_id,quantity,revenue,orders) VALUES (?,?,?,?,?,?)", sales)
    con.executemany("INSERT INTO traffic VALUES (?,?,?)", traffic)
    con.commit()
    con.close()


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    c = g.pop("db", None)
    if c:
        c.close()


def windows(days):
    end = date.fromisoformat(db().execute("SELECT MAX(sale_date) FROM sales").fetchone()[0])
    start = end - timedelta(days=days - 1)
    return ((start.isoformat(), end.isoformat()),
            ((start - timedelta(days=days)).isoformat(), (start - timedelta(days=1)).isoformat()))


def where(w, dist, table=""):
    sql = f" WHERE {table}sale_date BETWEEN ? AND ?"
    args = [w[0], w[1]]
    if dist:
        sql += f" AND {table}district_id = ?"
        args.append(dist)
    return sql, args


def totals(w, dist):
    sql, args = where(w, dist)
    r = db().execute("SELECT COALESCE(SUM(revenue),0) revenue, COALESCE(SUM(orders),0) orders FROM sales" + sql, args).fetchone()
    v = db().execute("SELECT COALESCE(SUM(visits),0) FROM traffic" + sql, args).fetchone()[0]
    return {"revenue": r["revenue"], "orders": r["orders"], "visits": v}


def daily(w, dist):
    sql, args = where(w, dist)
    rows = db().execute("SELECT sale_date d, SUM(revenue) v FROM sales" + sql + " GROUP BY sale_date ORDER BY sale_date", args)
    return [dict(r) for r in rows]


def by_product(w, dist):
    sql, args = where(w, dist, "s.")
    rows = db().execute("""SELECT p.id, p.name, p.category, p.unit, SUM(s.quantity) qty, SUM(s.revenue) rev
                           FROM sales s JOIN products p ON p.id = s.product_id""" + sql + " GROUP BY p.id", args)
    return {r["id"]: dict(r) for r in rows}


@app.get("/api/districts")
def districts():
    return jsonify([dict(r) for r in db().execute("SELECT id, name FROM districts ORDER BY id")])


@app.get("/api/dashboard")
def dashboard():
    days = request.args.get("days", 30, type=int)
    dist = request.args.get("district", 0, type=int)
    days = days if days in (30, 90, 365) else 30
    cur, prev = windows(days)
    sql, args = where(cur, 0, "s.")
    regions = db().execute("""SELECT d.id, d.name, SUM(s.revenue) rev FROM sales s
                              JOIN districts d ON d.id = s.district_id""" + sql + " GROUP BY d.id ORDER BY d.id", args)
    now, before = by_product(cur, dist), by_product(prev, dist)
    products = [{**p, "prev_rev": before.get(i, {}).get("rev", 0)} for i, p in now.items()]
    return jsonify({
        "range": {"start": cur[0], "end": cur[1]},
        "current": totals(cur, dist), "previous": totals(prev, dist),
        "series": {"current": daily(cur, dist), "previous": daily(prev, dist)},
        "regions": [dict(r) for r in regions],
        "products": sorted(products, key=lambda p: -p["rev"]),
    })


@app.get("/")
def index():
    return send_from_directory(app.root_path, "index.html")


if __name__ == "__main__":
    if not os.path.exists(DB):
        seed()
    app.run(debug=True)
