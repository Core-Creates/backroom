# backroom
Concept: AI-driven inventory intelligence tool that bridges the backroom and sales floor.  Core Idea: Use vision + data analytics to detect low stock, automate reorder insights, and visualize “shelf vs. backroom” discrepancies in real time. 
'''
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
'''
## 🧾 Directory Overview

### `app.py`
Main Streamlit or Gradio application that runs the Backroom UI.

### `data/`
- **`raw/`** — Stores unprocessed or incoming data (e.g., `inventory.csv`).
- **`processed/`** — Holds cleaned and prepared datasets used for modeling.
- **`shelves/`** — Sample shelf images or vision datasets.

### `models/`
Contains trained or downloaded model weights (e.g., YOLO or ML models).

### `scripts/`
- **`clean_data.py`** — Command-line script that calls `src.cleaning` to clean raw CSVs.

### `src/`
- **`detect.py`** — Vision-based shelf gap detection logic.  
- **`forecast.py`** — Reorder prediction and demand forecasting logic.  
- **`cleaning.py`** — Data cleaning and preprocessing functions.  
- **`utils.py`** — Generic helper utilities and shared functions.

### `README.md`
Top-level documentation for installation, setup, and usage instructions.
