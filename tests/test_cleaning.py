# tests/test_cleaning.py
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Make "from src.cleaning import ..." work without __init__.py packages
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKROOM_ROOT = REPO_ROOT / "backroom"
sys.path.insert(0, str(BACKROOM_ROOT))

from src.cleaning import clean_inventory_df, REQUIRED_COLS  # noqa: E402


def test_clean_inventory_df_basic():
    # Use header variants to exercise rename logic
    raw = pd.DataFrame(
        {
            "sku": ["00123", "ABC-9"],
            "product_name": [" Widget A ", "Gadget B"],
            "onhand": [10, 0],               # -> on_hand
            "backroom": [5, 2],              # -> backroom_units
            "shelf": [1, 4],                 # -> shelf_units
            "avg_dly_sales": [2.0, 1.0],     # -> avg_daily_sales
            "lead_time": [3, 7],             # -> lead_time_days
        }
    )

    df = clean_inventory_df(raw, shelf_low_threshold=3)

    # Required columns present
    for c in REQUIRED_COLS:
        assert c in df.columns

    # Derived columns
    assert "days_of_cover" in df.columns
    assert "restock_needed" in df.columns
    assert "safety_stock" in df.columns  # default injected

    # SKU stays string with leading zeros preserved
    assert df.loc[0, "sku"] == "00123"
    assert df["sku"].dtype == object

    # product_name trimmed
    assert df.loc[0, "product_name"] == "Widget A"

    # Numeric coercion and non-negative
    for c in ["on_hand","backroom_units","shelf_units","avg_daily_sales","lead_time_days","days_of_cover"]:
        assert pd.api.types.is_numeric_dtype(df[c])
        assert (df[c] >= 0).all()

    # days_of_cover = on_hand / avg_daily_sales (row-wise)
    expected = np.array([10/2.0, 0/1.0], dtype=float)
    np.testing.assert_allclose(df["days_of_cover"].to_numpy(), expected, rtol=1e-6)

    # restock_needed: shelf (1) < 3 and backroom (5) > 0 -> True for row 0; row 1 shelf 4 -> False
    assert df.loc[0, "restock_needed"] is True
    assert df.loc[1, "restock_needed"] is False

    # safety_stock default value
    assert float(df.loc[0, "safety_stock"]) == 2.0


def test_threshold_parameter_changes_flag():
    raw = pd.DataFrame(
        {
            "sku": ["x"],
            "product_name": ["p"],
            "onhand": [10],
            "backroom": [1],
            "shelf": [2],
            "avg_dly_sales": [1.0],
            "lead_time": [1],
        }
    )
    # threshold=3 → shelf 2 is low
    df1 = clean_inventory_df(raw, shelf_low_threshold=3)
    assert df1.loc[0, "restock_needed"] is True

    # threshold=2 → shelf 2 is NOT low
    df2 = clean_inventory_df(raw, shelf_low_threshold=2)
    assert df2.loc[0, "restock_needed"] is False


def test_missing_columns_raises():
    bad = pd.DataFrame({"sku": ["1"], "product_name": ["p"]})
    with pytest.raises(ValueError):
        clean_inventory_df(bad)
