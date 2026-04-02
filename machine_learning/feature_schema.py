"""Canonical feature schema for training and inference.

Usage:
    from feature_schema import (
        FEATURE_SCHEMA,
        normalize_from_csv,
        normalize_from_api,
        normalize_from_db,
        align_features,
    )

    df_train = normalize_from_csv(df_csv)
    df_pred = normalize_from_api(df_api)
    X_train = align_features(df_train)
    X_pred = align_features(df_pred)
"""

from __future__ import annotations

from typing import Dict, Iterable

import pandas as pd


# 1) The single source of truth for model input columns.
# Keep names/order stable once your model is trained.
FEATURE_SCHEMA = [
    "number",
    "capacity",
    "day",
    "hour",
    "minute",
    "temp",
    "pressure",
    "humidity",
    "bikes_1d_mean",
    "bikes_same_slot_mean",
]

TARGET_COLUMN = "num_bikes_available"


# 2) Optional dtypes for extra safety.
# Adjust as needed (e.g., int64/float64/category).
FEATURE_DTYPES: Dict[str, str] = {
    "number": "int64",
    "capacity": "float64",
    "day": "int64",
    "hour": "int64",
    "minute": "int64",
    "temp": "float64",
    "pressure": "float64",
    "humidity": "int64",
    "bikes_1d_mean": "float64",
    "bikes_same_slot_mean": "float64",
}


# 3) Shared helpers used by both training and inference.


def _coerce_dtypes(df: pd.DataFrame, dtype_map: Dict[str, str]) -> pd.DataFrame:
    """Cast known feature columns to expected dtypes when present."""
    out = df.copy()
    for col, dtype in dtype_map.items():
        if col in out.columns:
            out[col] = out[col].astype(dtype)
    return out


def _derive_time_and_humidity(df: pd.DataFrame) -> pd.DataFrame:
    """Derive day/hour/minute when last_update exists."""
    out = df.copy()

    if "last_update" in out.columns:
        ts = pd.to_datetime(out["last_update"], errors="coerce", utc=True)
        out["day"] = out.get("day", ts.dt.weekday)
        out["hour"] = out.get("hour", ts.dt.hour)
        out["minute"] = out.get("minute", ts.dt.minute)

    return out


def align_features(
    df: pd.DataFrame,
    required_features: Iterable[str] = FEATURE_SCHEMA,
    allow_extra: bool = True,
) -> pd.DataFrame:
    """Validate and align dataframe to canonical model features.

    - Ensures all required columns exist.
    - Reorders columns exactly as FEATURE_SCHEMA.
    - Optionally drops extra columns.
    """
    required = list(required_features)

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required model features: {missing}")

    out = df.copy()
    if not allow_extra:
        out = out[required]
    else:
        out = out[required + [c for c in out.columns if c not in required]]

    # Model input should usually only contain the required features.
    return out[required]


def normalize_from_csv(df_csv: pd.DataFrame) -> pd.DataFrame:
    """Validate CSV-derived dataframe already built with canonical names."""
    out = df_csv.copy()
    out = _derive_time_and_humidity(out)
    out = _coerce_dtypes(out, FEATURE_DTYPES)
    return align_features(out)


def normalize_from_api(df_api: pd.DataFrame) -> pd.DataFrame:
    """Validate API-derived dataframe already built with canonical names."""
    out = df_api.copy()
    out = _derive_time_and_humidity(out)
    out = _coerce_dtypes(out, FEATURE_DTYPES)
    return align_features(out)


def normalize_from_db(df_db: pd.DataFrame) -> pd.DataFrame:
    """Validate DB-derived dataframe already built with canonical names."""
    out = df_db.copy()
    out = _derive_time_and_humidity(out)
    out = _coerce_dtypes(out, FEATURE_DTYPES)
    return align_features(out)


def prepare_inference_features(
    *,
    number: int,
    capacity: float,
    dt: pd.Timestamp,
    temp: float,
    pressure: float,
    humidity: float,
    bikes_1d_mean: float,
    bikes_same_slot_mean: float,
) -> pd.DataFrame:
    """Build one-row canonical inference dataframe."""
    ts = pd.Timestamp(dt)
    row = {
        "number": number,
        "capacity": capacity,
        "day": int(ts.weekday()),
        "hour": int(ts.hour),
        "minute": int(ts.minute),
        "temp": temp,
        "pressure": pressure,
        "humidity": humidity,
        "bikes_1d_mean": bikes_1d_mean,
        "bikes_same_slot_mean": bikes_same_slot_mean,
    }
    out = pd.DataFrame([row])
    out = _coerce_dtypes(out, FEATURE_DTYPES)
    return align_features(out)
