# pyrefly: ignore [missing-import]
import pandas as pd
# pyrefly: ignore [missing-import]
from sklearn.model_selection import train_test_split
# pyrefly: ignore [missing-import]
from sklearn.ensemble import RandomForestRegressor
# pyrefly: ignore [missing-import]
from sklearn.metrics import mean_absolute_error, r2_score
# pyrefly: ignore [missing-import]
from flask import Flask, request, jsonify
from flask_cors import CORS
# pyrefly: ignore [missing-import]
import joblib
import os
from waitress import serve 

app = Flask(__name__)
CORS(app)

# ── Paths (all relative to this file's directory) ────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH   = os.path.join(BASE_DIR, "model.pkl")
COLUMNS_PATH = os.path.join(BASE_DIR, "columns.pkl")
DATA_PATH    = os.path.join(BASE_DIR, "Machine.xlsx")

# ── Global R² store (returned in /predict) ────────────────────────────────────
_r2_score = None

# ── 1. Load & Train ───────────────────────────────────────────────────────────
def train_model():
    global _r2_score
    try:
        if not os.path.exists(DATA_PATH):
            print(f"[ERROR] Dataset not found at: {DATA_PATH}")
            print("   Run: python generate_data.py  first to create Machine.xlsx")
            return False

        data = pd.read_excel(DATA_PATH, engine='openpyxl')

        print(f"[OK] Dataset loaded: {data.shape[0]:,} rows, {data.shape[1]} columns")
        print(f"[INFO] Columns: {list(data.columns)}")

        X = data.drop("Yield_tons_per_hectare", axis=1)
        Y = data["Yield_tons_per_hectare"]

        for col in X.select_dtypes(include=['object', 'string', 'category']).columns:
            print(f"  '{col}' unique: {X[col].unique()}")

        X_encoded    = pd.get_dummies(X)
        model_columns = list(X_encoded.columns)
        joblib.dump(model_columns, COLUMNS_PATH, compress=('gzip', 3))

        X_train, X_test, Y_train, Y_test = train_test_split(
            X_encoded, Y, test_size=0.2, random_state=100
        )

        model = RandomForestRegressor(
            n_estimators=50,
            max_depth=12,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, Y_train)

        preds = model.predict(X_test)
        mae   = mean_absolute_error(Y_test, preds)
        r2    = r2_score(Y_test, preds)
        _r2_score = round(float(r2), 4)

        print(f"[OK] Model trained -- MAE: {mae:.3f}, R2: {r2:.3f}")
        print(f"[INFO] Prediction range on test set: {preds.min():.2f} -> {preds.max():.2f}")

        joblib.dump(model, MODEL_PATH, compress=('gzip', 3))
        return True

    except Exception as e:
        print(f"[ERROR] Training failed: {e}")
        return False


train_model()


# ── 2. Build Input ─────────────────────────────────────────────────────────────
def build_input(rainfall, temperature, fertilizer, irrigation, days,
                region, soil, crop, weather):

    row = {
        "Rainfall_mm":         float(rainfall),
        "Temperature_Celsius": float(temperature),
        "Fertilizer_Used":     int(bool(fertilizer)),
        "Irrigation_Used":     int(bool(irrigation)),
        "Days_to_Harvest":     int(days),
        "Region":              str(region),
        "Soil_Type":           str(soil),
        "Crop":                str(crop),
        "Weather_Condition":   str(weather)
    }

    print(f"\n[INPUT] Raw row: {row}")

    df         = pd.DataFrame([row])
    df_encoded = pd.get_dummies(df)

    model_cols = joblib.load(COLUMNS_PATH)
    df_final   = df_encoded.reindex(columns=model_cols, fill_value=0)

    print(f"[ENCODED] Final input: {df_final.to_dict(orient='records')[0]}")
    return df_final


# ── 3. Suggestions ─────────────────────────────────────────────────────────────
def get_suggestions(data, yield_val):
    suggestions = []
    tips        = []

    rainfall = float(data.get("rainfall_mm", 0))
    temp     = float(data.get("temperature_celsius", 0))
    fert     = data.get("fertilizer_used", False)
    irr      = data.get("irrigation_used", False)
    crop     = str(data.get("crop_type", "")).strip()
    soil     = str(data.get("soil_type", "")).strip()
    days     = int(data.get("days_to_harvest", 0))

    if rainfall < 50:
        suggestions.append(f"🌧️ Rainfall ({rainfall}mm) is critically low — consider drip irrigation immediately.")
    elif rainfall < 100:
        suggestions.append(f"🌧️ Rainfall ({rainfall}mm) is below average — monitor soil moisture closely.")
    elif rainfall > 400:
        suggestions.append(f"🌊 Excessive rainfall ({rainfall}mm) detected — ensure proper field drainage.")
    elif rainfall > 250:
        suggestions.append(f"💧 High rainfall ({rainfall}mm) — watch for fungal diseases.")
    else:
        suggestions.append(f"✅ Rainfall ({rainfall}mm) is in a healthy range.")

    if temp < 10:
        suggestions.append(f"🥶 Temperature ({temp}°C) is too cold — risk of frost damage.")
    elif temp < 15:
        suggestions.append(f"🌡️ Temperature ({temp}°C) is cool — growth may be slower than optimal.")
    elif temp > 38:
        suggestions.append(f"🔥 Temperature ({temp}°C) is very high — heat stress risk, increase irrigation.")
    elif temp > 30:
        suggestions.append(f"☀️ Temperature ({temp}°C) is warm — ensure adequate water supply.")
    else:
        suggestions.append(f"✅ Temperature ({temp}°C) is ideal for most crops.")

    if not fert:
        suggestions.append("🌱 Fertilizer not used — applying a balanced NPK fertilizer can boost yield.")
    else:
        tips.append("👍 Fertilizer is being used — ensure you're applying the right ratio for your crop.")

    if not irr:
        if rainfall < 100:
            suggestions.append("💧 Irrigation is OFF and rainfall is low — high risk of water stress.")
        else:
            tips.append("💧 Irrigation is off — natural rainfall may be sufficient, but monitor closely.")
    else:
        tips.append("✅ Irrigation is active — good for yield stability.")

    if yield_val < 1.5:
        suggestions.append(f"🚨 Very low yield ({yield_val} t/ha) — check soil health, pest pressure, and nutrients.")
    elif yield_val < 3.0:
        suggestions.append(f"⚠️ Below-average yield ({yield_val} t/ha) — review fertilizer and irrigation strategy.")
    elif yield_val < 5.0:
        tips.append(f"📊 Moderate yield ({yield_val} t/ha) — small improvements could push you above 5 t/ha.")
    elif yield_val < 7.0:
        tips.append(f"👍 Good yield ({yield_val} t/ha) — maintain current practices and monitor for pests.")
    else:
        tips.append(f"🏆 Excellent yield ({yield_val} t/ha) — your conditions are near-optimal!")

    crop_tips = {
        "Rice":    "🌾 Rice: Needs standing water; ensure 1000–2000mm rainfall or full irrigation.",
        "Wheat":   "🌾 Wheat: Optimal temp 15–22°C, needs 300–450mm rainfall during growing season.",
        "Maize":   "🌽 Maize: Sensitive to drought at tasseling stage — keep irrigation steady.",
        "Cotton":  "🌿 Cotton: Prefers warm, dry weather at harvest. Avoid excess moisture late season.",
        "Soybean": "🫘 Soybean: Fix nitrogen naturally — reduce nitrogen fertilizer, focus on phosphorus.",
        "Barley":  "🌾 Barley: Tolerates dry conditions better than wheat — avoid waterlogging.",
    }
    if crop in crop_tips:
        tips.append(crop_tips[crop])

    soil_tips = {
        "Sandy":  "🪨 Sandy soil drains fast — irrigate more frequently in small amounts.",
        "Clay":   "🪨 Clay soil retains water — avoid overwatering, ensure drainage channels.",
        "Loam":   "🌱 Loam soil is ideal — maintain organic matter with compost.",
        "Silt":   "🌱 Silt soil is fertile but prone to compaction — avoid heavy machinery.",
        "Peaty":  "🌿 Peaty soil is acidic — test pH and lime if needed.",
        "Chalky": "🪨 Chalky soil is alkaline — add organic matter to improve structure.",
    }
    if soil in soil_tips:
        tips.append(soil_tips[soil])

    if days < 60:
        tips.append(f"⏱️ Short harvest window ({days} days) — plan labour and storage in advance.")
    elif days > 180:
        tips.append(f"📅 Long growing period ({days} days) — monitor for pest buildup over time.")

    return suggestions, tips


# ── 4. API Routes ──────────────────────────────────────────────────────────────
@app.route('/predict', methods=['POST'])
def predict():
    try:
        req = request.get_json()
        print(f"\n[REQUEST] {req}")

        input_df = build_input(
            rainfall    = req.get("rainfall_mm", 0),
            temperature = req.get("temperature_celsius", 0),
            fertilizer  = req.get("fertilizer_used", False),
            irrigation  = req.get("irrigation_used", False),
            days        = req.get("days_to_harvest", 0),
            region      = req.get("region", "North"),
            soil        = req.get("soil_type", "Loam"),
            crop        = req.get("crop_type", "Wheat"),
            weather     = req.get("weather_condition", "Sunny")
        )

        loaded_model = joblib.load(MODEL_PATH)
        prediction   = loaded_model.predict(input_df)[0]

        print(f"[PREDICTION] {prediction:.4f} tons/hectare")

        sugg, tips = get_suggestions(req, round(float(prediction), 2))

        return jsonify({
            "predicted_yield": round(float(prediction), 2),
            "r2_score":        _r2_score if _r2_score is not None else "N/A",
            "suggestions":     sugg,
            "tips":            tips
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route('/retrain', methods=['POST'])
def retrain():
    success = train_model()
    if success:
        return jsonify({"message": "Model retrained successfully."})
    return jsonify({"error": "Retraining failed. Check server logs."}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status":         "ok",
        "model_loaded":   os.path.exists(MODEL_PATH),
        "columns_loaded": os.path.exists(COLUMNS_PATH),
        "r2_score":       _r2_score
    })


if __name__ == '__main__':
    serve(app,host='0.0.0.0', port=5000)
