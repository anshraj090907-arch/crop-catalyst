"""
generate_data.py — Synthetic Crop Yield Dataset Generator
Generates 30,000 rows of realistic agronomic data and saves as Machine.xlsx
Run this once before starting backend.py
"""

# pyrefly: ignore [missing-import]
import numpy as np
import pandas as pd
import os

np.random.seed(42)

N = 30000  # number of rows

# ── 1. Core categorical columns ──────────────────────────────────────────────
regions   = ["North", "South", "East", "West"]
crops     = ["Wheat", "Rice", "Maize", "Cotton", "Barley", "Soybean"]
soils     = ["Sandy", "Loam", "Silt", "Chalky", "Peaty", "Clay"]
weathers  = ["Sunny", "Rainy", "Cloudy"]

Region            = np.random.choice(regions,  N)
Crop              = np.random.choice(crops,    N)
Soil_Type         = np.random.choice(soils,    N)
Weather_Condition = np.random.choice(weathers, N)

# ── 2. Numeric inputs with realistic per-crop ranges ─────────────────────────
# Crop ideal temperature ranges
crop_temp_mean = {
    "Wheat":   20, "Rice":   28, "Maize":  23,
    "Cotton":  28, "Barley": 18, "Soybean":25
}
# Crop ideal rainfall ranges (mm)
crop_rain_mean = {
    "Wheat":  350, "Rice":  1500, "Maize":  650,
    "Cotton": 900, "Barley":450, "Soybean":550
}
# Crop days to harvest range
crop_days_range = {
    "Wheat":  (110, 155), "Rice":   (90, 150), "Maize":  (60, 100),
    "Cotton": (150, 185), "Barley": (90, 125), "Soybean":(90, 125)
}

Temperature_Celsius = np.zeros(N)
Rainfall_mm         = np.zeros(N)
Days_to_Harvest     = np.zeros(N, dtype=int)

for i in range(N):
    c = Crop[i]
    Temperature_Celsius[i] = np.clip(
        np.random.normal(crop_temp_mean[c], 7), 0, 50
    )
    Rainfall_mm[i] = np.clip(
        np.random.normal(crop_rain_mean[c], 250), 0, 500
    )
    lo, hi = crop_days_range[c]
    Days_to_Harvest[i] = int(np.random.uniform(lo, hi))

Fertilizer_Used = np.random.choice([0, 1], N, p=[0.35, 0.65])
Irrigation_Used = np.random.choice([0, 1], N, p=[0.40, 0.60])

# ── 3. Yield computation (agronomic rules + noise) ───────────────────────────
# Base yield per crop (tons/hectare)
crop_base_yield = {
    "Wheat":   3.5, "Rice":   5.0, "Maize":  4.5,
    "Cotton":  2.5, "Barley": 3.0, "Soybean":2.8
}

Yield = np.zeros(N)

for i in range(N):
    c    = Crop[i]
    base = crop_base_yield[c]

    # Rainfall factor (too little or too much hurts)
    ideal_rain = crop_rain_mean[c]
    rain_dev   = abs(Rainfall_mm[i] - ideal_rain)
    rain_factor = max(0.4, 1.0 - rain_dev / (ideal_rain + 1) * 0.8)

    # Temperature factor
    ideal_temp = crop_temp_mean[c]
    temp_dev   = abs(Temperature_Celsius[i] - ideal_temp)
    temp_factor = max(0.4, 1.0 - temp_dev / 20.0)

    # Management factors
    fert_boost = 0.30 if Fertilizer_Used[i] else 0.0
    irr_boost  = 0.25 if Irrigation_Used[i] else 0.0

    # Weather factor
    w = Weather_Condition[i]
    if w == "Sunny":
        weather_factor = 1.05
    elif w == "Rainy":
        weather_factor = 1.0 if ideal_rain > 500 else 0.90
    else:  # Cloudy
        weather_factor = 0.95

    # Soil factor
    s = Soil_Type[i]
    soil_factor = {
        "Loam": 1.10, "Silt": 1.05, "Clay": 0.95,
        "Sandy": 0.85, "Chalky": 0.90, "Peaty": 0.92
    }.get(s, 1.0)

    # Region factor (slight variation)
    r = Region[i]
    region_factor = {
        "North": 1.00, "South": 1.05, "East": 0.98, "West": 1.02
    }.get(r, 1.0)

    computed = (
        base
        * rain_factor
        * temp_factor
        * weather_factor
        * soil_factor
        * region_factor
        * (1 + fert_boost + irr_boost)
    )

    # Add realistic noise (±10%)
    noise = np.random.normal(0, computed * 0.10)
    Yield[i] = max(0.3, round(computed + noise, 2))

# ── 4. Assemble DataFrame ────────────────────────────────────────────────────
df = pd.DataFrame({
    "Rainfall_mm":           np.round(Rainfall_mm, 1),
    "Temperature_Celsius":   np.round(Temperature_Celsius, 1),
    "Fertilizer_Used":       Fertilizer_Used.astype(int),
    "Irrigation_Used":       Irrigation_Used.astype(int),
    "Days_to_Harvest":       Days_to_Harvest,
    "Region":                Region,
    "Soil_Type":             Soil_Type,
    "Crop":                  Crop,
    "Weather_Condition":     Weather_Condition,
    "Yield_tons_per_hectare": Yield
})

# ── 5. Save ──────────────────────────────────────────────────────────────────
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Machine.xlsx")
df.to_excel(out_path, index=False, engine="openpyxl")

print(f"[OK] Dataset generated: {len(df):,} rows x {len(df.columns)} columns")
print(f"[SAVED] {out_path}")
print("\n[STATS] Yield_tons_per_hectare:")
print(df["Yield_tons_per_hectare"].describe().round(3))
print("\n[CROP COUNTS]")
print(df["Crop"].value_counts())
