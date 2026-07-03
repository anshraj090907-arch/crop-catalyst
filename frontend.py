# pyrefly: ignore [missing-import]
import streamlit as st
import requests

st.set_page_config(page_title="Crop Catalyst", layout="wide")

BACKEND_URL = "http://localhost:5000"

# ── Initialize session state ──────────────────────────────
if "prediction_success" not in st.session_state:
    st.session_state["prediction_success"] = False
if "yield_val" not in st.session_state:
    st.session_state["yield_val"] = None
if "suggestions" not in st.session_state:
    st.session_state["suggestions"] = []
if "tips" not in st.session_state:
    st.session_state["tips"] = []
if "crop" not in st.session_state:
    st.session_state["crop"] = ""
if "r2" not in st.session_state:
    st.session_state["r2"] = "N/A"

# ── HEADER ────────────────────────────────────────────────
st.markdown("""
    <h1 style='text-align: center; color: #4CAF50;'>🌾 Crop Catalyst</h1>
    <h4 style='text-align: center;'>AI Powered Crop Yield Prediction & Smart Farming Advisor</h4>
    <hr>
""", unsafe_allow_html=True)

# ── BACKEND CHECK ─────────────────────────────────────────
try:
    requests.get(f"{BACKEND_URL}/health", timeout=3)
    st.success("✅ Backend connected successfully!")
except:
    st.error("❌ Backend not connected! Please run backend.py first.")

# ── SIDEBAR ───────────────────────────────────────────────
st.sidebar.header("🌱 Farm Inputs")

region = st.sidebar.selectbox(
    "📍 Select Region",
    ["North", "South", "East", "West"]
)

crop = st.sidebar.selectbox(
    "🌾 Select Crop",
    ["Wheat", "Rice", "Maize", "Cotton", "Barley", "Soybean"]
)

soil_type = st.sidebar.selectbox(
    "🌍 Soil Type",
    ["Sandy", "Loam", "Silt", "Chalky", "Peaty", "Clay"]
)

weather = st.sidebar.selectbox(
    "🌤 Weather Condition",
    ["Sunny", "Rainy", "Cloudy"]
)

rainfall = st.sidebar.slider("🌧 Rainfall (mm)", 0, 500, 100)
temperature = st.sidebar.slider("🌡 Temperature (°C)", 0, 50, 25)
days_to_harvest = st.sidebar.slider("⏱ Days to Harvest", 60, 200, 120)

fertilizer_used = st.sidebar.radio("🧴 Fertilizer Used?", ["Yes", "No"])
irrigation_used = st.sidebar.radio("💧 Irrigation Used?", ["Yes", "No"])

predict_btn = st.sidebar.button("🚀 Predict Yield")

# ── MAIN LAYOUT ───────────────────────────────────────────
st.divider()
col1, col2 = st.columns(2)

# ── INPUT SUMMARY ─────────────────────────────────────────
with col1:
    st.markdown("### 📊 Input Summary")
    st.info(f"""
    📍 Region: {region}\n
    🌾 Crop: {crop}\n
    🌍 Soil Type: {soil_type}\n
    🌤 Weather: {weather}\n
    🌧 Rainfall: {rainfall} mm\n
    🌡 Temperature: {temperature} °C\n
    ⏱ Days to Harvest: {days_to_harvest}\n
    🧴 Fertilizer Used: {fertilizer_used}\n
    💧 Irrigation Used: {irrigation_used}\n
    """)

# ── PREDICTION ────────────────────────────────────────────
with col2:
    st.markdown("### 📈 Prediction Result")

    if predict_btn:
        payload = {
            "rainfall_mm": rainfall,
            "temperature_celsius": temperature,
            "fertilizer_used": True if fertilizer_used == "Yes" else False,
            "irrigation_used": True if irrigation_used == "Yes" else False,
            "region": region,
            "crop_type": crop,
            "soil_type": soil_type,
            "weather_condition": weather,
            "days_to_harvest": days_to_harvest
        }

        try:
            with st.spinner("🤖 Analyzing your farm data..."):
                response = requests.post(
                    f"{BACKEND_URL}/predict",
                    json=payload,
                    timeout=10
                )
                result = response.json()

            if "error" in result:
                st.error(f"❌ Error: {result['error']}")
            else:
                st.session_state["prediction_success"] = True
                st.session_state["yield_val"] = result["predicted_yield"]
                st.session_state["r2"] = result.get("r2_score", "N/A")
                st.session_state["suggestions"] = result.get("suggestions", [])
                st.session_state["tips"] = result.get("tips", [])
                st.session_state["crop"] = crop

        except requests.exceptions.ConnectionError:
            st.error("🔌 Cannot connect to backend! Make sure backend.py is running.")
        except Exception as e:
            st.error(f"Something went wrong: {e}")

    # ── Always show results from session state ──
    if st.session_state["prediction_success"]:
        yield_val = st.session_state["yield_val"]
        r2 = st.session_state["r2"]

        st.success(f"🌾 Predicted Yield: **{yield_val} tons/hectare**")
        st.progress(min(int(yield_val * 10), 100))

        st.markdown("#### 🧠 Model Performance")
        st.metric("📊 R² Score", f"{r2}")

# ── SUGGESTIONS SECTION ───────────────────────────────────
if st.session_state["prediction_success"]:

    suggestions = st.session_state["suggestions"]
    tips = st.session_state["tips"]
    crop_name = st.session_state["crop"]

    st.divider()
    st.markdown("## 🎯 Smart Farming Suggestions")
    st.markdown("*Personalized recommendations based on your farm data:*")

    # ── Immediate Actions ──
    if suggestions:
        st.markdown("### ⚡ Immediate Actions")
        for s in suggestions:
            st.warning(s)
    else:
        st.info("No immediate actions needed.")

    st.divider()

    # ── Expert Tips ──
    if tips:
        st.markdown("### 💡 Expert Farming Tips to Increase Production")
        col3, col4 = st.columns(2)
        half = len(tips) // 2
        with col3:
            for tip in tips[:half]:
                st.success(f"✅ {tip}")
        with col4:
            for tip in tips[half:]:
                st.success(f"✅ {tip}")
    else:
        st.info("No tips available.")

    st.divider()

    # ── Crop Guide ──
    st.markdown("### 📚 Complete Crop Guide")
    crop_guides = {
        "Wheat":   {"season": "October - March",  "water": "450-650mm",   "temp": "15-25°C", "harvest": "120-150 days"},
        "Rice":    {"season": "June - November",  "water": "1200-2000mm", "temp": "20-35°C", "harvest": "90-150 days"},
        "Maize":   {"season": "June - October",   "water": "500-800mm",   "temp": "18-27°C", "harvest": "60-100 days"},
        "Cotton":  {"season": "April - November", "water": "700-1300mm",  "temp": "21-35°C", "harvest": "150-180 days"},
        "Barley":  {"season": "October - April",  "water": "400-600mm",   "temp": "12-25°C", "harvest": "90-120 days"},
        "Soybean": {"season": "June - October",   "water": "450-700mm",   "temp": "20-30°C", "harvest": "90-120 days"},
    }

    if crop_name in crop_guides:
        guide = crop_guides[crop_name]
        st.markdown(f"#### 🌾 {crop_name} Complete Guide")
        g1, g2, g3, g4 = st.columns(4)
        g1.metric("📅 Season", guide["season"])
        g2.metric("💧 Water Need", guide["water"])
        g3.metric("🌡️ Temp Need", guide["temp"])
        g4.metric("⏱️ Days to Harvest", guide["harvest"])
# ── FOOTER ────────────────────────────────────────────────
st.divider()
st.markdown("""
<div style='text-align:center;'>
<h3>🌱 About Crop Catalyst</h3>
<p>An AI-powered smart farming advisor that predicts crop yield and gives
personalized suggestions to maximize production.</p>
<p>🔹 AI Yield Prediction &nbsp;|&nbsp; 🔹 Smart Suggestions &nbsp;|&nbsp;
🔹 Crop Guides &nbsp;|&nbsp; 🔹 Expert Tips</p>
</div>
<hr>
<div style='text-align:center'>
<h2>🙏 Thank You</h2>
<p>Thank you for using <b>Crop Catalyst</b> 🌾</p>
<p>🚜 Smart Farming • 🌍 Better Future • 📈 Higher Productivity</p>
</div>
""", unsafe_allow_html=True)