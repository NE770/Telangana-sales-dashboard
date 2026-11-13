# Telangana Building Materials Sales Dashboard

An interactive sales analytics dashboard for steel, cement and block brands across eight Telangana districts. The page reads its data from a SQLite database through a Flask REST API.


http://127.0.0.1:5000/
<img width="1577" height="962" alt="Telangana sales dashboard" src="https://github.com/user-attachments/assets/0dfc5b40-6dc2-4297-b69b-846496f15cc1" />


## Features
- KPI strip: revenue, orders, average order value and conversion rate, each compared with the previous period
- Revenue trend chart (current vs previous period) drawn in SVG, with hover tooltips
- Filters for time range (30 days, 90 days, 12 months) and district
- Revenue by district, and a top-products table with quantity and growth
- Responsive layout with automatic light and dark mode

## Tech stack
- **Backend:** Python, Flask, SQLite (`sqlite3`)
- **Frontend:** HTML, CSS, vanilla JavaScript
- **Database:** four tables (`districts`, `products`, `sales`, `traffic`) with foreign keys and an index; aggregation is done in SQL (`SUM`, `GROUP BY`, `JOIN`) with parameterised queries

## How it works
1. `python app.py` creates `sales.db` on first run and fills it with generated sample data.
2. The browser calls `/api/dashboard?days=30&district=0`.
3. Flask runs SQL for the current and previous period and returns JSON.
4. `index.html` renders the KPIs, chart, district bars and product table from that JSON.

## Run it locally
```
pip install -r requirements.txt
python app.py
```
Then open http://127.0.0.1:5000

## Data
Brand names (Tata Tiscon, Vizag Steel, JSW Neosteel, UltraTech, Sagar Cements, Dalmia, Birla Aerocon) are real. All sales figures are generated sample data, not real company data.

## About this project
Built with AI assistance (Claude), then customised by me.

**What I changed or added:**
- ("i have changed the values and some brand names which are in my own added ")

## Author
Neerudi Rahul
