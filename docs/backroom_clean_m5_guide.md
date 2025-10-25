# Backroom Data Cleaning Script — M5 (`backroom_clean_m5.py`)

A friendly, copy-pasteable guide for cleaning the **M5 Forecasting – Accuracy** dataset and exporting tidy outputs (CSV, Parquet, DuckDB, sample CSV).

---

## 🧭 What this does

- Converts the wide daily sales matrices (`d_1..d_N`) into a **long, tidy** table  
- Joins **calendar** and **sell prices**  
- Parses dates, runs simple data-quality checks, and computes **`revenue = sold_qty × sell_price`**  
- Writes:
  - `m5_clean_long.csv`
  - `dq_report.md`
  - *(optional)* Parquet (single file or partitioned)
  - *(optional)* DuckDB database
  - *(optional)* sample CSV (first N rows)

---

## ✅ Requirements

- **Python 3.9+**
- Install packages (inside your virtualenv):
  ```powershell
  pip install -r requirements.txt
  ```
## 🚀 Quick start (Windows, PowerShell)

### From your repo root (where scripts\backroom_clean_m5.py lives):

``` python .\scripts\backroom_clean_m5.py ` ```
```  --m5-zip "~\Downloads\m5-forecasting-accuracy.zip" ` ```
``` --out-dir ".\m5_out" `
```  --to-parquet ` ```
```  --partition-by state_id,store_id ` ```
```  --sample-csv 100000 ` ```
```  --to-duckdb ` ```
```  --duckdb-path ".\m5_out\m5.duckdb" ```


#### Note: In PowerShell, multiline continuation uses the backtick (`), not a backslash.

### Using cmd.exe instead?
``` python scripts\backroom_clean_m5.py ^ ```
```  --m5-zip "~\m5-forecasting-accuracy.zip" ^ ```
```  --out-dir .\m5_out ^ ```
```  --to-parquet ^ ```
```  --partition-by state_id,store_id ^ ```
```  --sample-csv 100000 ^ ```
```  --to-duckdb ^ ```
```  --duckdb-path .\m5_out\m5.duckdb ```

## 🧩 Alternate inputs

### Instead of --m5-zip, you may point to the 3 raw CSVs directly:

``` python .\scripts\backroom_clean_m5.py ` ```
```  --sales-csv "C:\path\sales_train_validation.csv" ` ```
```  --calendar-csv "C:\path\calendar.csv" ` ```
```  --prices-csv "C:\path\sell_prices.csv" ` ```
```  --out-dir ".\m5_out" ```

---
## 📄 Outputs

After successful execution, your output directory (e.g., `m5_out/`) will contain:

| File / Folder | Description |
|----------------|--------------|
| **m5_clean_long.csv** | Cleaned long-format data (one row per `store_id`, `item_id`, `date`) |
| **dq_report.md** | Data-quality summary – shapes, null counts, out-of-bounds fixes |
| **m5_clean_long.parquet** | Single-file Parquet export *(if not partitioned)* |
| **m5_parquet/** | Partitioned Parquet export *(if `--partition-by` used)* |
| **m5.duckdb** | DuckDB database containing the cleaned table |
| **sample_100000.csv** | First N rows *(if `--sample-csv` used)* |

---

## ⚙️ CLI Flags Reference

| Flag | Type | Required | Description |
|------|------|-----------|-------------|
| `--m5-zip` | path | One of ZIP **or** all 3 CSVs | Path to Kaggle bundle ZIP |
| `--sales-csv` | path | One of ZIP **or** all 3 CSVs | Path to `sales_train_validation.csv` |
| `--calendar-csv` | path | One of ZIP **or** all 3 CSVs | Path to `calendar.csv` |
| `--prices-csv` | path | One of ZIP **or** all 3 CSVs | Path to `sell_prices.csv` |
| `--out-dir` | path | ✅ Yes | Output directory |
| `--to-parquet` | flag | No | Write Parquet export |
| `--parquet-path` | path | No | File (single) or directory (if partitioned) |
| `--partition-by` | list | No | Columns to partition Parquet (e.g. `state_id,store_id`) |
| `--sample-csv` | int | No | Write sample CSV with first *N* rows |
| `--to-duckdb` | flag | No | Create DuckDB database |
| `--duckdb-path` | path | No | Path to `.duckdb` file (default: `<out_dir>\m5.duckdb`) |
| `--duckdb-table` | str | No | Table name inside DuckDB (default: `m5_clean_long`) |

---

## 🧪 Example Success Log

```
Cleaning complete.
Wide sales rows: 30490
Final long rows: 58327370
Duplicates removed: 0
Report: .\m5_out\dq_report.md
Clean CSV: .\m5_out\m5_clean_long.csv
Parquet saved (duckdb): .\m5_out\m5_clean_long.parquet
DuckDB written: .\m5_out\m5.duckdb (table=m5_clean_long)
Sample CSV written: .\m5_out\sample_100000.csv
```

---

## 🛠️ Troubleshooting

### ❌ “unrecognized arguments: \”
You used backslashes for line continuations in PowerShell.  
Use **backticks (`)** instead, or run the command as a single line.

### 📁 No such file or directory (script path)
Check the script path:
```powershell
Test-Path .\scripts\backroom_clean_m5.py
```

### 📦 No such file or directory (ZIP path)
Check the ZIP path:
```powershell
Test-Path "C:\Users\<You>\Downloads\m5-forecasting-accuracy.zip"
```

### 🧠 Memory Pressure on Full Melt (~58 M rows)
- Close heavy applications; **16–32 GB RAM** recommended.  
- Prefer Parquet or DuckDB outputs (they’re more efficient).  
- *(Advanced)* Filter the dataset upstream if you only need a few states/stores.

---

## 📦 Suggested Workflow

1. **Create and activate a virtual environment**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

2. **Install dependencies**
   ```powershell
   pip install pandas duckdb pyarrow
   ```

3. **Run the cleaner (PowerShell, single line)**
   ```powershell
   python .\scripts\backroom_clean_m5.py --m5-zip "C:\Users\<You>\Downloads\m5-forecasting-accuracy.zip" --out-dir ".\m5_out" --to-parquet --partition-by state_id,store_id --sample-csv 100000 --to-duckdb --duckdb-path ".\m5_out\m5.duckdb"
   ```

4. **Open** `m5_out\dq_report.md` to review data quality,  
   then load `m5_clean_long.parquet` or `m5.duckdb` in your analytics stack.

---

## ❓ FAQ

**Q:** Can I pass CSVs instead of the ZIP?  
**A:** Yes — use `--sales-csv`, `--calendar-csv`, and `--prices-csv`.

**Q:** What’s in `dq_report.md`?  
**A:** Row counts, duplicates removed, null counts per column, and notes about any out-of-bounds replacements (e.g., prices beyond [0, 1e6]).

**Q:** Why both CSV and Parquet?  
**A:** CSV is universal; Parquet is compact and fast for analytics engines.  
Use whichever best fits your workflow.

---

✨ **Happy cleaning!**
