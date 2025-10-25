# backroom
Concept: AI-driven inventory intelligence tool that bridges the backroom and sales floor.  Core Idea: Use vision + data analytics to detect low stock, automate reorder insights, and visualize “shelf vs. backroom” discrepancies in real time. 

backroom/
 ├─ app.py
 ├─ data/
 │   ├─ raw/            # original files (e.g., inventory.csv moves here)
 │   ├─ processed/      # cleaned CSVs written here
 │   └─ shelves/
 ├─ models/
 ├─ scripts/
 │   └─ clean_data.py   # CLI entrypoint that calls src.cleaning
 ├─ src/
 │   ├─ detect.py
 │   ├─ forecast.py
 │   ├─ cleaning.py     # ← your data cleaning functions live here
 │   └─ utils.py
 └─ README.md
