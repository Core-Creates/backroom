# 🏭 Backroom — Inventory Intelligence

**Concept:**  
AI-driven inventory intelligence tool that bridges the *backroom* and *sales floor*.

**Core Idea:**  
Use computer vision and data analytics to detect low stock, automate reorder insights, and visualize “shelf vs. backroom” discrepancies in real time. Backroom helps store operators and inventory managers save time, reduce waste, and maintain optimal stock levels.

---

## 📁 Project Structure
```
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
```
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

## 🧠 Open Source Libraries / Tools Used

| Library / Tool | Purpose |
|----------------|----------|
| **`duckdb`** | Lightweight in-process analytical database for fast SQL queries on CSVs and Parquet files. |
| **`pandas`** | Data manipulation and cleaning. |
| **`numpy`** | Efficient numerical computation. |
| **`scikit-learn`** | Machine learning for forecasting, anomaly detection, and metrics. |
| **`ultralytics` (YOLOv8)** | Object detection for shelf gap and inventory visibility. |
| **`opencv-python`** | Image processing and visualization for shelf photo analysis. |
| **`streamlit`** or **`gradio`** | Rapid UI prototyping for model demos. |
| **`matplotlib` / `plotly`** | Visualization and dashboards for metrics and analytics. |
| **`python-dotenv`** | Manage environment variables for local and deployment setups. |

---

## ⚙️ Next Steps

1. Implement `cleaning.py` pipeline for robust data validation and deduplication.  
2. Integrate `detect.py` with YOLOv8 lightweight weights for on-device inference.  
3. Connect `forecast.py` to a simple reorder simulation using SKU-level historical data.  
4. Wrap models into `app.py` Streamlit interface for demo submission.  
5. Add `notebooks/` directory for experimentation and model testing (optional).  

---

## 💡 Suggested Enhancements

- **NLP Q&A module** — “What do I need to restock today?” powered by `duckdb` + LLM query parser.  
- **Predictive alerts** — Real-time notifications for projected stockouts in the next 48 hours.  
- **Inventory heatmaps** — Visual overview of low-stock areas across multiple stores.  
- **API integration** — Connect with ERP or POS systems for live data updates.

---

> _Backroom — See. Sense. Restock._