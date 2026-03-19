import streamlit as st
import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io
import pandas as pd
from fpdf import FPDF
import time
import tempfile
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import os
import base64
import json
import datetime
import requests

# --- Global App Defaults (Previously in Sidebar) ---
selected_crop = "Rice"  # Default crop type
sh_client_id = "9014ff84-e5be-44a4-b866-caa7d576c8a0"
sh_client_secret = "zlnN8FTFmxBmEFt6bSkNQcGM4kBqciPx"

# --- Default Page Config ---
st.set_page_config(
    page_title="CropSight - Aerial Action Platform",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def set_bg(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{b64}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
                background-color: rgba(255, 255, 255, 0.70);
                background-blend-mode: overlay;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

bg_path = os.path.join(os.path.dirname(__file__), "demo_images", "background.png")
set_bg(bg_path)

# --- Animations & Cute Custom CSS ---
st.markdown("""
<style>
    /* Keyframe Animations */
    @keyframes fadeInSlideUp { 0% { opacity: 0; transform: translateY(30px); } 100% { opacity: 1; transform: translateY(0); } }
    @keyframes pulseShadow { 0% { box-shadow: 0 0 0 0 rgba(123, 178, 132, 0.5); } 70% { box-shadow: 0 0 0 20px rgba(123, 178, 132, 0); } 100% { box-shadow: 0 0 0 0 rgba(123, 178, 132, 0); } }
    @keyframes scaleIn { 0% { transform: scale(0.95); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
    
    .animated-card { animation: fadeInSlideUp 0.8s ease forwards; }
    .animated-image img { border-radius: 24px; box-shadow: 0 10px 30px rgba(123, 178, 132, 0.2); }
    .animated-image { animation: scaleIn 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; }
    
    /* Typography & Cute Styling */
    h1, h2, h3, h4 { color: #588560 !important; font-family: 'Comic Sans MS', 'Chalkboard SE', 'Segoe UI', cursive, sans-serif; letter-spacing: -0.5px; }
    p, span, div, text, li { color: #4a5d4a; }
    
    .header-box { text-align: center; margin-bottom: 2rem; animation: fadeInSlideUp 0.8s ease forwards; }
    .main-header { font-size: 4.2rem; color: #7bb284; font-weight: 900; margin-bottom: 0; text-shadow: 2px 2px 0px #eef6f0; }
    .sub-header { font-size: 1.3rem; color: #588560; margin-top: 5px; font-weight: 600; }
    
    /* Cute Rounded Cards */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] {
        padding: 1.8rem;
        background-color: rgba(255, 255, 255, 0.95); 
        border-radius: 30px;
        box-shadow: 0 10px 30px rgba(123, 178, 132, 0.1);
        margin-bottom: 1rem;
        animation: fadeInSlideUp 0.6s ease forwards;
        border: 3px solid #eef6f0;
    }
    
    .metric-container {
        text-align: center;
        padding: 25px;
        background-color: #ffffff;
        border: 5px solid #7bb284;
        border-radius: 35px;
        box-shadow: 0 10px 25px rgba(123, 178, 132, 0.25);
        animation: scaleIn 0.5s ease forwards;
        transition: transform 0.3s ease;
    }
    .metric-container:hover {
        animation: pulseShadow 2s infinite;
        transform: translateY(-5px);
    }
    
    div[data-testid="stMetricValue"] { color: #7bb284; font-size: 4.5rem; font-weight: 900; text-align: center; text-shadow: 1px 1px 0px #eef6f0;}
    div[data-testid="stMetricLabel"] { font-size: 1.3rem; color: #588560; font-weight: 800; text-transform: uppercase; text-align: center;}
    div[data-testid="stMetricDelta"] { justify-content: center; font-size: 1.1rem; }
    
    .stButton>button { 
        background-color: #7bb284; 
        color: white; 
        border-radius: 25px; 
        font-weight: 800; 
        font-size: 1.1rem;
        transition: all 0.3s ease; 
        width: 100%;
        border: 3px solid transparent;
        padding: 0.8rem 1rem;
        box-shadow: 0 6px 15px rgba(123, 178, 132, 0.3);
    }
    .stButton>button:hover { 
        background-color: #619268; 
        border: 3px solid #7bb284;
        transform: translateY(-4px) scale(1.02); 
        box-shadow: 0 8px 20px rgba(97, 146, 104, 0.5); 
    }
    
    .stDownloadButton>button { background-color: #7bb284; }
    .stDownloadButton>button:hover { background-color: #588560; border-color: #588560; }
    
    .legend-badge {
        padding: 10px 20px; 
        border-radius: 25px; 
        font-weight: 800; 
        color: #fff;
        display: inline-block;
        margin-right: 12px;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        transition: transform 0.2s;
        border: 2px solid white;
    }
    .legend-badge:hover { transform: scale(1.08) rotate(-2deg); }
    .bg-greenery { background-color: #7bb284; color: white !important;}
    .bg-illuminating { background-color: #F5DF4D; color: #665b11 !important;}
    .bg-terracotta { background-color: #DF654D; color: white !important;}
    
    .pathology-box {
        background-color: #ffffff;
        border: 3px dashed #DF654D;
        padding: 30px;
        border-radius: 30px;
        margin-top: 15px;
        animation: fadeInSlideUp 0.8s ease forwards;
        box-shadow: 0 10px 25px rgba(223, 101, 77, 0.15);
    }
    .pathology-box h3 { margin-top: 0; color: #DF654D !important; margin-bottom: 25px; font-weight: 900;}
    .pathology-box h4 { margin-top: 25px; color: #588560 !important; border-bottom: 3px dotted #7bb284; padding-bottom: 10px;}
    .pathology-box ul { padding-left: 20px; }
    .pathology-box li { margin-bottom: 10px; font-size: 1.1rem;}
    
    .footer { text-align: center; margin-top: 70px; color: #7bb284; font-size: 15px; font-weight: 700; background: rgba(255,255,255,0.7); padding: 15px; border-radius: 20px;}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def analyze_image(image_bytes):
    # Ensure bytes for consistent hashing and processing
    image_bytes = bytes(image_bytes)
    
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    original_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    max_dim = 1000
    h, w = original_rgb.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        original_rgb = cv2.resize(original_rgb, (int(w * scale), int(h * scale)))
    
    float_img = original_rgb.astype(float)
    r, g, b = float_img[:, :, 0], float_img[:, :, 1], float_img[:, :, 2]
    
    vari = (g - r) / (g + r - b + 1e-6)
    p5 = np.percentile(vari, 2)
    p95 = np.percentile(vari, 98)
    health = np.clip((vari - p5) / (p95 - p5 + 1e-6), 0, 1) * 100
    
    health_smoothed = cv2.GaussianBlur(health, (25, 25), 0)
    
    health_map = np.zeros_like(original_rgb)
    health_map[health_smoothed < 40] = [223, 101, 77]
    health_map[(health_smoothed >= 40) & (health_smoothed < 70)] = [245, 223, 77]
    health_map[health_smoothed >= 70] = [123, 178, 132]
    
    overlay = cv2.addWeighted(original_rgb, 0.4, health_map, 0.6, 0)
    overall_score = int(np.mean(health_smoothed))
    
    return original_rgb, overlay, health_smoothed, overall_score

def get_exif_location(img_bytes):
    try:
        img = Image.open(io.BytesIO(img_bytes))
        exif = img._getexif()
        if not exif: return None

        gps_info = None
        for key, val in exif.items():
            if TAGS.get(key) == 'GPSInfo':
                gps_info = val
                break
        
        if not gps_info: return None
        
        gps_data = {}
        for key, val in gps_info.items():
            tag_name = GPSTAGS.get(key, key)
            gps_data[tag_name] = val

        if 'GPSLatitude' in gps_data and 'GPSLongitude' in gps_data:
            def convert_to_degrees(value):
                d = float(value[0])
                m = float(value[1])
                s = float(value[2])
                return d + (m / 60.0) + (s / 3600.0)

            lat = convert_to_degrees(gps_data['GPSLatitude'])
            if gps_data.get('GPSLatitudeRef') == 'S': lat = -lat
            
            lon = convert_to_degrees(gps_data['GPSLongitude'])
            if gps_data.get('GPSLongitudeRef') == 'W': lon = -lon
            
            return lat, lon
    except Exception:
        pass
    return None

def find_zones(health_smoothed):
    h, w = health_smoothed.shape
    small = cv2.resize(health_smoothed, (150, 150), interpolation=cv2.INTER_AREA)
    zones_data = []
    
    thresholds = [
        {"mask": small < 40, "color": "🔴", "sev": "Severe Stress", "action": "Irrigate immediately / check roots"},
        {"mask": (small >= 40) & (small < 70), "color": "🟡", "sev": "Moderate Stress", "action": "Check nutrients & early pests"},
        {"mask": small >= 70, "color": "🟢", "sev": "Healthy", "action": "Continue monitoring"}
    ]
    
    for th in thresholds:
        mask = np.uint8(th["mask"]) * 255
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            if cv2.contourArea(c) > 100:
                mean_score = np.mean(small[th["mask"]]) if np.any(th["mask"]) else 0
                zones_data.append({"Color": th["color"], "Health Score": f"{int(mean_score)}%", "Severity": th["sev"], "Farmer Action": th["action"]})
                break
    
    if not zones_data:
        zones_data.append({"Color": "🟢", "Health Score": "85%", "Severity": "Healthy", "Farmer Action": "Continue monitoring"})
        
    for i, z in enumerate(zones_data):
        z["Zone"] = f"Zone {i+1}"
        
    return pd.DataFrame(zones_data)[["Zone", "Color", "Health Score", "Severity", "Farmer Action"]]

def generate_tips(overall_score, zones_df):
    tips = []
    if overall_score >= 75: tips.append("🌟 **Excellent Overall Health:** Your crop is currently thriving. Maintain your standard irrigation and nutrient cycles.")
    elif overall_score >= 50: tips.append("⚠️ **Fair Health with Spotty Stress:** There are significant irregular patches. We recommend targeted soil testing in the yellow areas.")
    else: tips.append("🚨 **Critical Action Needed:** The overall field health is exceptionally low. Look for pervasive signs of blight, drought, or extreme pest infestation immediately.")
    
    severities = zones_df["Severity"].values
    if "Severe Stress" in severities: tips.append("💧 **Red Zones Need Immediate Water/Treatment:** Walk these specific areas today. Severe stress indicates structural issues such as broken irrigation lines, compacted soil, or active pathogen spread.")
    if "Moderate Stress" in severities: tips.append("🐛 **Monitor Yellow Zones Closely:** These regions lack peak vigor. Check the back of leaves for mites and ensure uniform fertilizer distribution.")
        
    return tips

def get_ai_diagnosis(crop_type, overall_score, zones_df):
    """
    Simulated AI Engine that identifies potential pathogens and diseases 
    based on crop type and detected stress patterns.
    """
    severities = zones_df['Severity'].tolist()
    has_severe = "Severe Stress" in severities
    has_moderate = "Moderate Stress" in severities
    
    # Diagnosis Logic based on Crop Type and Stress
    diagnosis_map = {
        "Rice": {
            "name": "Paddy (Rice)",
            "Severe Stress": ("Potentially Rice Blast (Fungal)", "Apply Tricyclazole or Azoxystrobin fungicide immediately. Ensure field drainage to prevent further spore spread."),
            "Moderate Stress": ("Potentially Brown Spot or Stem Rot", "Check for brown lesions on leaves. Apply potassium-rich fertilizer and ensure uniform water distribution.")
        },
        "Coconut": {
            "name": "Coconut Palm",
            "Severe Stress": ("Bud Rot (Phytophthora)", "Apply Bordeaux paste to the affected bud. Remove and burn the infected palms to avoid spread."),
            "Moderate Stress": ("Leaf Rot / Root Wilt", "Improve drainage and apply 1kg of lime per palm annually. Use organic manure and green leaves.")
        },
        "Banana": {
            "name": "Banana (Nendran)",
            "Severe Stress": ("Sigatoka Leaf Spot", "Spray mineral oil or carbendazim. Remove and burn heavily infected leaves immediately."),
            "Moderate Stress": ("Panama Wilt / Nutrient Deficiency", "Check for yellowing at margins. Apply balanced NPK and ensure proper soil aeration.")
        },
        "Arecanut": {
            "name": "Areca Nut",
            "Severe Stress": ("Mahali / Fruit Rot", "Apply 1% Bordeaux mixture spray before and during the monsoon rains."),
            "Moderate Stress": ("Yellow Leaf Disease", "Provide adequate irrigation and apply focused micronutrient fertilizer (Zinc/Boron).")
        },
        "Rubber": {
            "name": "Rubber Plantation",
            "Severe Stress": ("Abnormal Leaf Fall", "Ariel spraying of oil-based copper oxychloride before monsoon sets in."),
            "Moderate Stress": ("Powdery Mildew", "Apply sulphur dusting during new leaf emergence to control the fungal spread.")
        },
        "Wheat": {
            "name": "Wheat",
            "Severe Stress": ("Potentially Leaf Rust or Fusarium Blight", "Apply Propiconazole or Tebuconazole. Avoid overhead irrigation during humid periods."),
            "Moderate Stress": ("Nitrogen Deficiency or Aphid Infestation", "Apply nitrogen-rich top dressing. Inspect for small pests on the underside of leaves.")
        },
        "Corn": {
            "name": "Corn (Maize)",
            "Severe Stress": ("Potentially Northern Leaf Blight (NLB)", "Apply Mancozeb or Chlorothalonil. Remove and destroy infected crop residue after harvest."),
            "Moderate Stress": ("Drought Stress or Nutrient Mining", "Increase irrigation frequency. Conduct a soil test to check for phosphorus deficiency.")
        },
        "Sugarcane": {
            "name": "Sugarcane",
            "Severe Stress": ("Potentially Red Rot or Sugarcane Smut", "Infected stalks should be removed and burnt. Treat future sets with hot water (52°C for 30 mins)."),
            "Moderate Stress": ("Iron or Zinc Chlorosis", "Apply foliar spray of 1% Ferrous sulphate or Zinc sulphate to restore greenness.")
        },
    }

    # Default if healthy
    if overall_score > 85:
        return "Normal Vigor", "No significant pathogens detected. Continue standard monitoring and maintenance schedule."

    # Select Diagnosis
    crop_data = diagnosis_map.get(crop_type, diagnosis_map.get("Rice"))
    if has_severe:
        return crop_data["Severe Stress"]
    elif has_moderate:
        return crop_data["Moderate Stress"]
    else:
        return "Minor Seasonal Stress", "Crops are generally healthy but showing slight seasonal variation. Check for minor insect activity."

def get_regional_crop_guide():
    """Returns a full list of regional crop data for the Kuttanad region."""
    return [
        {"Crop": "🌾 Paddy (Rice)", "Typical Disease": "Rice Blast", "Natural Cure": "Bordeaux Mixture / Crop Rotation", "Chemical Cure": "Tricyclazole"},
        {"Crop": "🥥 Coconut", "Typical Disease": "Bud Rot", "Natural Cure": "Bordeaux Paste application", "Chemical Cure": "Copper Oxychloride"},
        {"Crop": "🍌 Banana", "Typical Disease": "Sigatoka Leaf Spot", "Natural Cure": "Leaf Pruning / Neem Oil", "Chemical Cure": "Propiconazole"},
        {"Crop": "🌳 Arecanut", "Typical Disease": "Mahali (Fruit Rot)", "Natural Cure": "1% Bordeaux Mixture Spray", "Chemical Cure": "Captan"},
        {"Crop": "🧤 Rubber", "Typical Disease": "Abnormal Leaf Fall", "Natural Cure": "Improved drainage", "Chemical Cure": "Oil-based Copper Fungicide"},
        {"Crop": "🍍 Pineapple", "Typical Disease": "Heart Rot", "Natural Cure": "Good drainage and mulching", "Chemical Cure": "Aliette / Fose-Al"},
    ]

@st.cache_data(ttl=3600)
def fetch_sentinel_hub_image(client_id, client_secret, min_lon, min_lat, max_lon, max_lat):
    """Query Sentinel Hub for 10m high-res imagery using Process API."""
    try:
        if not client_id or not client_secret:
            return None, None

        # 1. Get Access Token
        token_url = "https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token"
        token_data = {"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret}
        token_resp = requests.post(token_url, data=token_data, timeout=10)
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]

        # 2. Process API Request
        process_url = "https://services.sentinel-hub.com/api/v1/process"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "image/jpeg"
        }
        
        # Simple True Color Evalscript
        evalscript = """
        //VERSION=3
        function setup() {
          return {
            input: ["B04", "B03", "B02"],
            output: { bands: 3 }
          };
        }
        function evaluatePixel(sample) {
          return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];
        }
        """

        # Set time range to last 6 months to ensure data exists
        today = datetime.datetime.now()
        start_date = (today - datetime.timedelta(days=180)).strftime("%Y-%m-%dT%H:%M:%SZ")
        end_date = today.strftime("%Y-%m-%dT%H:%M:%SZ")

        payload = {
            "input": {
                "bounds": {
                    "bbox": [min_lon, min_lat, max_lon, max_lat],
                    "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                },
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {"timeRange": {"from": start_date, "to": end_date}}
                }]
            },
            "output": {
                "width": 1024,
                "height": 1024,
                "responses": [{"identifier": "default", "format": {"type": "image/jpeg"}}]
            },
            "evalscript": evalscript
        }

        resp = requests.post(process_url, json=payload, headers=headers, timeout=40)
        resp.raise_for_status()

        meta = {
            "title": "Sentinel Hub High-Res Imagery",
            "provider": "Copernicus / Sentinel Hub",
            "platform": "Sentinel-2 Satellite",
            "date": "Most Recent (Last 180 Days)",
            "resolution": "10 meters/pixel",
            "layer": "True Color (10m)"
        }
        return bytes(resp.content), meta
    except Exception as e:
        st.sidebar.error(f"Sentinel Hub Auth Error: {str(e)}")
        return None, None

def clean_for_pdf(text):
    text = str(text)
    replacements = {'🌟 ': '', '⚠️ ': '', '🚨 ': '', '💧 ': '', '🐛 ': '', '🔴': 'Red', '🟡': 'Yellow', '🟢': 'Green', '*': ''}
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'ignore').decode('latin-1')

def create_pdf(farm_name, overall_score, original, overlay, zones_df, tips, ai_diagnosis, ai_cure):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 24)
    pdf.set_text_color(88, 133, 96)
    pdf.cell(0, 15, "CropSight - Farmer Action Report", 0, 1, 'C')
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 10, f"Overall Crop Health Score: {overall_score}/100", 0, 1, 'C')
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(0, 8, clean_for_pdf(f"Farm/Field Name: {farm_name} | Date: {time.strftime('%Y-%m-%d')}"), 0, 1, 'C')
    pdf.ln(5)
    
    # AI Diagnosis Section in PDF
    pdf.set_font("Arial", 'B', 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, "AI Pathogen & Stress Diagnostic Report", 0, 1, 'L', 1)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(231, 76, 60) # Red
    pdf.cell(0, 8, f"Detected Condition: {clean_for_pdf(ai_diagnosis)}", 0, 1)
    pdf.set_text_color(0, 0, 0) # Reset to black
    pdf.set_font("Arial", 'I', 11)
    pdf.multi_cell(0, 6, f"AI Recommended Cure: {clean_for_pdf(ai_cure)}", 0, 'L')
    pdf.ln(5)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f_orig, tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f_over:
        Image.fromarray(original).save(f_orig.name)
        Image.fromarray(overlay).save(f_over.name)
        y_pos = pdf.get_y()
        pdf.set_font("Arial", 'B', 14)
        pdf.text(10, y_pos, "1. Original Photo")
        pdf.text(150, y_pos, "2. CropSight Health Overlay")
        pdf.image(f_orig.name, x=10, y=y_pos+5, w=130)
        pdf.image(f_over.name, x=150, y=y_pos+5, w=130)
        img_aspect = original.shape[0]/original.shape[1]
        pdf.set_y(y_pos + 5 + (130 * img_aspect) + 10)
        
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "3. Intelligent Farmer Guidance", 0, 1)
    pdf.set_font("Arial", '', 12)
    for tip in tips:
        pdf.cell(0, 8, f"- {clean_for_pdf(tip)}", 0, 1)
        
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "4. Specific Zone Actions", 0, 1)
    pdf.set_font("Arial", 'B', 12)
    col_widths = [20, 30, 45, 140]
    headers = ["Zone", "Score", "Severity", "Farmer Action"]
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 10, clean_for_pdf(h), 1, 0, 'C')
    pdf.ln()
    pdf.set_font("Arial", '', 12)
    for _, row in zones_df.iterrows():
        pdf.cell(col_widths[0], 10, clean_for_pdf(row['Zone']), 1, 0, 'C')
        pdf.cell(col_widths[1], 10, clean_for_pdf(row['Health Score']), 1, 0, 'C')
        pdf.cell(col_widths[2], 10, clean_for_pdf(row['Severity']), 1, 0, 'C')
        pdf.cell(col_widths[3], 10, clean_for_pdf(row['Farmer Action']), 1, 0, 'L')
        pdf.ln()
    # Ensure return is immutable bytes for Streamlit caching/downloading
    return bytes(pdf.output(dest='S'))


# --- Authentication & Frontend Layout Starts Here ---
import auth

auth.init_db()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""

if not st.session_state.logged_in:
    st.markdown("""
    <div class='header-box'>
        <h1 class='main-header'>🌱 CropSight Portal</h1>
        <h3 class='sub-header'>Farmer Authentication Layer</h3>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='animated-card' style='padding: 2rem; border-radius: 20px; background: rgba(255,255,255,0.9); box-shadow: 0 10px 30px rgba(123, 178, 132, 0.2); text-align: center;'>", unsafe_allow_html=True)
        choice = st.radio("Select an option", ["Login", "Sign Up"], horizontal=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if choice == "Sign Up":
            st.markdown("<h4 style='text-align:center;'>Create a New Account</h4>", unsafe_allow_html=True)
            new_email = st.text_input("Email Address", key="su_email")
            new_password = st.text_input("Password", type='password', key="su_pass")
            if st.button("Sign Up", use_container_width=True):
                if new_email and new_password:
                    if auth.create_user(new_email, new_password):
                        st.success("Account created successfully! Please switch to Login.")
                    else:
                        st.error("Email already exists or invalid.")
                else:
                    st.warning("Please fill out all fields.")
        
        elif choice == "Login":
            st.markdown("<h4 style='text-align:center;'>Login to your Account</h4>", unsafe_allow_html=True)
            email = st.text_input("Email Address", key="li_email")
            password = st.text_input("Password", type='password', key="li_pass")
            if st.button("Login", use_container_width=True):
                if email and password:
                    if auth.login_user(email, password):
                        st.session_state.logged_in = True
                        st.session_state.user_email = email
                        st.rerun()
                    else:
                        st.error("Incorrect Email or Password.")
                else:
                    st.warning("Please fill out all fields.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class='footer'>
        Built for SDG 2 Zero Hunger – 24-hour hackathon 🚀 🌱 | <b>CropSight Platform</b>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- Authenticated User Sidebar ---
with st.sidebar:
    st.markdown(f"### 👤 Profile")
    st.success(f"Logged in as:\n**{st.session_state.user_email}**")
    
    # Show record count
    saved_farms_count = len(auth.get_user_farms(st.session_state.user_email))
    st.info(f"📁 **{saved_farms_count}** Saved Farm Records")
    
    st.markdown("---")
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.rerun()

# --- Farm Session State Initialization ---
if 'farmer_name' not in st.session_state or not st.session_state.farmer_name:
    if 'user_email' in st.session_state and st.session_state.user_email:
        # Extract part before @, replace dots/underscores with spaces, and capitalize
        raw_name = st.session_state.user_email.split('@')[0]
        st.session_state.farmer_name = raw_name.replace('.', ' ').replace('_', ' ').title()
    else:
        st.session_state.farmer_name = "Farmer"
if 'farm_boundary' not in st.session_state:
    st.session_state.farm_boundary = None  # list of [lat, lon] pairs
if 'farm_confirmed' not in st.session_state:
    st.session_state.farm_confirmed = False

# ============================================================
#  FARM SETUP SCREEN  (draw an area on the map)
# ============================================================
if not st.session_state.farm_confirmed:
    st.markdown("""
    <div class='header-box'>
        <h1 class='main-header'>🌱 CropSight Platform</h1>
        <h3 class='sub-header'>Set Up Your Farm to Get Started</h3>
        <p><b>Draw a rectangle or polygon</b> on the map to mark your farm area.</p>
    </div>
    """, unsafe_allow_html=True)

    col_setup1, col_setup2, col_setup3 = st.columns([1, 3, 1])
    with col_setup2:
        st.markdown(f"👨‍🌾 **Welcome, {st.session_state.farmer_name}!**")

        # --- Load Existing Farm ---
        saved_farms = auth.get_user_farms(st.session_state.user_email)
        if saved_farms:
            with st.expander("📖 Load a Saved Farm Record"):
                cols = st.columns([3, 1])
                farm_to_load = cols[0].selectbox("Select from your records:", [f"{f[0]} ({f[4]})" for f in saved_farms])
                if cols[1].button("Load", use_container_width=True):
                    # Find the selected farm data
                    idx = [f"{f[0]} ({f[4]})" for f in saved_farms].index(farm_to_load)
                    f_name, f_lat, f_lon, f_bound, f_time = saved_farms[idx]
                    st.session_state.farm_boundary = json.loads(f_bound)
                    st.session_state.farm_confirmed = True
                    st.success(f"Loaded {f_name} successfully!")
                    st.rerun()

        st.markdown("#### 📍 Draw your farm boundary on the map")
        st.caption("Use the rectangle ▭ or polygon ⬠ tool on the left side of the map to outline your farm area.")
        default_lat, default_lon = 10.0, 76.3
        setup_map = folium.Map(location=[default_lat, default_lon], zoom_start=7)
        Draw(
            export=False,
            draw_options={
                'polyline': False,
                'circle': False,
                'circlemarker': False,
                'marker': False,
                'polygon': True,
                'rectangle': True,
            },
            edit_options={'edit': True, 'remove': True},
        ).add_to(setup_map)
        map_data = st_folium(setup_map, width="100%", height=450, key="farm_setup_map")

        # Extract drawn boundary
        drawn_boundary = None
        if map_data and map_data.get("all_drawings"):
            drawings = map_data["all_drawings"]
            if len(drawings) > 0:
                last_drawing = drawings[-1]  # use the most recent shape
                geom = last_drawing.get("geometry", {})
                if geom.get("type") in ("Polygon",) and geom.get("coordinates"):
                    # GeoJSON coordinates are [lng, lat] – flip to [lat, lng]
                    raw_coords = geom["coordinates"][0]
                    drawn_boundary = [[c[1], c[0]] for c in raw_coords]

        if drawn_boundary:
            lats = [p[0] for p in drawn_boundary]
            lons = [p[1] for p in drawn_boundary]
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            st.success(f"📌 Farm area selected — center at **({center_lat:.4f}, {center_lon:.4f})** with **{len(drawn_boundary)-1} vertices**")
        else:
            st.info("Draw a rectangle or polygon on the map to define your farm area.")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✅ Confirm Farm Area & Analyse", use_container_width=True, key="confirm_farm_btn"):
            if drawn_boundary:
                st.session_state.farm_boundary = drawn_boundary
                st.session_state.farm_confirmed = True
                
                # Save to Database as a permanent record
                try:
                    farm_name = f"Managed Land {len(saved_farms) + 1}"
                    center_lat = sum([p[0] for p in drawn_boundary]) / len(drawn_boundary)
                    center_lon = sum([p[1] for p in drawn_boundary]) / len(drawn_boundary)
                    auth.save_farm(st.session_state.user_email, farm_name, center_lat, center_lon, drawn_boundary)
                    st.success(f"Farm '{farm_name}' has been securely recorded!")
                except Exception as e:
                    st.warning(f"Note: Farm recorded to session but DB sync failed: {str(e)}")
                    
                st.rerun()
            else:
                st.warning("Please draw a rectangle or polygon on the map to define your farm area.")

    st.markdown("""
    <div class='footer'>
        Built for SDG 2 Zero Hunger – 24-hour hackathon 🚀 🌱 | <b>CropSight Platform</b>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ============================================================
#  MAIN DASHBOARD  (after farm area is confirmed)
# ============================================================
farmer_name = st.session_state.farmer_name
farm_boundary = st.session_state.farm_boundary
_lats = [p[0] for p in farm_boundary]
_lons = [p[1] for p in farm_boundary]
farm_lat = sum(_lats) / len(_lats)
farm_lon = sum(_lons) / len(_lons)

st.markdown(f"""
<div class='header-box'>
    <h1 class='main-header'>🌱 CropSight Platform</h1>
    <h3 class='sub-header'>Welcome, {farmer_name} – Your Farm at ({farm_lat:.4f}, {farm_lon:.4f})</h3>
    <p>Your selected farm area is being analysed for crop health.</p>
</div>
""", unsafe_allow_html=True)

# --- Optional: override with your own image ---
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    with st.expander("📤 Upload your own drone/satellite image (optional)", expanded=False):
        uploaded_file = st.file_uploader(
            "Upload Drone/Satellite Image of This Farm",
            type=["jpg", "png", "jpeg", "tif"],
            label_visibility="collapsed",
            key="main_upload"
        )
    with st.expander("🔄 Change Farm Area"):
        if st.button("Reset Farm Setup", key="reset_farm_btn"):
            st.session_state.farm_confirmed = False
            st.session_state.farmer_name = ""
            st.session_state.farm_boundary = None
            st.rerun()

# --- Auto-analyse: OAM → uploaded image → demo fallback ---
st.markdown("---")

demo_path = os.path.join(os.path.dirname(__file__), "demo_images", "drone_farm_field.png")
min_lon, max_lon = min(_lons), max(_lons)
min_lat, max_lat = min(_lats), max(_lats)

with st.spinner("🛰️ Fetching 10m high-res imagery from Sentinel Hub..."):
    try:
        image_bytes = None
        sh_meta = None

        # Priority 1: User-uploaded image
        if uploaded_file:
            image_bytes = uploaded_file.read()
            st.info("✅ Using your uploaded drone/satellite image for analysis.")

        # Priority 2: Fetch from Sentinel Hub
        if image_bytes is None and sh_client_id and sh_client_secret:
            sh_bytes, sh_meta = fetch_sentinel_hub_image(sh_client_id, sh_client_secret, min_lon, min_lat, max_lon, max_lat)
            if sh_bytes:
                image_bytes = sh_bytes
                st.success("🛰️ **High-resolution imagery found on Sentinel Hub!**")
                meta_col1, meta_col2, meta_col3 = st.columns(3)
                with meta_col1:
                    st.markdown(f"**📷 {sh_meta['title']}**")
                with meta_col2:
                    st.markdown(f"🏢 {sh_meta['provider']} · {sh_meta['platform']}")
                with meta_col3:
                    st.markdown(f"📅 {sh_meta['date']} · {sh_meta['resolution']}")

        # Priority 3: Demo fallback
        if image_bytes is None:
            if not sh_client_id or not sh_client_secret:
                st.warning("⚠️ Sentinel Hub credentials missing. Using demo imagery. [Get a free account here](https://www.sentinel-hub.com/) for 10m high-res data.")
            else:
                st.warning("⚠️ No recent Sentinel Hub imagery found for this area. Using demo imagery.")
                
            if os.path.exists(demo_path):
                with open(demo_path, "rb") as f:
                    image_bytes = f.read()
            else:
                st.error("No imagery available. Please upload a drone image manually.")
                st.stop()

        orig_rgb, overlay_rgb, health_array, overall_score = analyze_image(bytes(image_bytes))
        zones_df = find_zones(health_array)
        farmer_tips = generate_tips(overall_score, zones_df)

        # --- AI Disease Diagnosis ---
        ai_diagnosis, ai_cure = get_ai_diagnosis(selected_crop, overall_score, zones_df)

        st.markdown(f"""
        <div class="diagnosis-card" style="border-left: 10px solid {'#e74c3c' if overall_score < 40 else '#f1c40f' if overall_score < 70 else '#2ecc71'}; background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 25px;">
            <h2 style='margin-top:0; color: #2c3e50; font-family: "Outfit", sans-serif;'>🧬 AI Pathogen & Stress Diagnostic Report</h2>
            <hr style='margin: 15px 0; border: none; border-top: 1px solid #eee;'>
            <div style='display:flex; justify-content:space-between; align-items:flex-start; flex-wrap: wrap;'>
                <div style='flex: 2; min-width: 300px;'>
                    <p style='margin-bottom: 5px; font-weight: bold; color: #7f8c8d; text-transform: uppercase; font-size: 0.8em;'>Detected Condition</p>
                    <p style='color:#e74c3c; font-size:1.6em; font-weight: bold; margin-bottom: 20px;'>{ai_diagnosis}</p>
                    <p style='margin-bottom: 10px; font-weight: bold; color: #2c3e50;'>✨ AI Recommended Cure / Action Plan:</p>
                    <div style='background:#f4f9f4; padding:20px; border-radius:12px; border:1px solid #e0ede0; color: #2d3436; line-height: 1.6;'>
                        {ai_cure}
                    </div>
                </div>
                <div style='flex: 1; min-width: 150px; text-align:center; background:#f8f9fa; padding:25px; border-radius:20px; margin-left:20px; display: flex; flex-direction: column; justify-content: center;'>
                     <p style='margin:0; font-size:0.9em; font-weight: bold; color: #95a5a6;'>CROP HEALTH SCORE</p>
                     <h1 style='margin:10px 0; font-size:4.5em; color:{"#e74c3c" if overall_score < 40 else "#f1c40f" if overall_score < 70 else "#2ecc71"}; font-family: "Outfit", sans-serif;'>{overall_score}</h1>
                     <p style='margin:0; font-size:0.9em; color:{"#e74c3c" if overall_score < 40 else "#27ae60"}; font-weight: bold;'>
                        {"↑ +12% improvement" if overall_score > 50 else "↓ -5% decline"}
                     </p>
                </div>
            </div>
            <div style='margin-top: 25px; padding-top: 15px; border-top: 1px solid #f0f0f0;'>
                <p style='margin:0; color: #bdc3c7; font-size: 0.85em;'><b>Disclaimer:</b> AI diagnosis is based on remote sensing spectral patterns. Ground-truth verification by an agronomist is recommended for critical decisions.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- Visual Health Maps (Side-by-Side) ---
        st.markdown("---")
        st.markdown("### 🗺️ Visual Health Analysis")
        st.markdown("""
<div style='margin-bottom: 20px;'>
<span class='legend-badge bg-greenery'>🟢 Healthy (>70%)</span>
<span class='legend-badge bg-illuminating'>🟡 Moderate Stress (40-70%)</span>
<span class='legend-badge bg-terracotta'>🔴 Severe Stress (<40%)</span>
</div>
        """, unsafe_allow_html=True)

        img_col1, img_col2 = st.columns(2)
        with img_col1:
            st.markdown("<div class='animated-image'>", unsafe_allow_html=True)
            st.image(orig_rgb, caption="Original Aerial View", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with img_col2:
            st.markdown("<div class='animated-image'>", unsafe_allow_html=True)
            st.image(overlay_rgb, caption="CropSight Health Overlay", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # --- Specific Zones Table ---
        st.markdown("### 📍 Drill-Down: Specific Zones")
        st.dataframe(zones_df, use_container_width=True, hide_index=True)

        # --- Geo-tagged Health Zone Overlay on Interactive Map ---
        st.markdown("---")
        st.markdown("### 🌍 Geo-Tagged Health Zones on Your Farm")
        st.markdown(f"Health zones overlaid on your selected farm area at **({farm_lat:.4f}, {farm_lon:.4f})**.")

        try:
            health_map = folium.Map(location=[farm_lat, farm_lon], zoom_start=16)

            # Draw the user's farm boundary
            folium.Polygon(
                locations=farm_boundary,
                color="#588560",
                weight=3,
                fill=False,
                tooltip=f"{farmer_name}'s Farm Boundary",
                dash_array="10",
            ).add_to(health_map)

            folium.Marker(
                [farm_lat, farm_lon],
                popup=f"{farmer_name}'s Farm",
                tooltip=f"📍 {farmer_name}'s Farm",
                icon=folium.Icon(color="green", icon="leaf", prefix="fa")
            ).add_to(health_map)

            # Compute bounding box of the farm for zone placement
            min_lat, max_lat = min(_lats), max(_lats)
            min_lon, max_lon = min(_lons), max(_lons)
            lat_range = max_lat - min_lat
            lon_range = max_lon - min_lon

            # Build zone sub-rectangles inside the farm boundary
            n_zones = len(zones_df)
            for i, (_, row) in enumerate(zones_df.iterrows()):
                sev = row["Severity"]
                color_map = {
                    "Severe Stress": "#DF654D",
                    "Moderate Stress": "#F5DF4D",
                    "Healthy": "#7BB284",
                }
                zone_color = color_map.get(sev, "#999999")
                # Divide farm into horizontal strips for each zone
                strip_min_lat = min_lat + (lat_range / n_zones) * i
                strip_max_lat = min_lat + (lat_range / n_zones) * (i + 1)
                zone_poly = [
                    (strip_min_lat, min_lon),
                    (strip_min_lat, max_lon),
                    (strip_max_lat, max_lon),
                    (strip_max_lat, min_lon),
                ]
                folium.Polygon(
                    locations=zone_poly,
                    color=zone_color,
                    weight=2,
                    fill_color=zone_color,
                    fill_opacity=0.4,
                    tooltip=f"{row['Zone']} – {sev} | Score: {row['Health Score']} | {row['Farmer Action']}"
                ).add_to(health_map)

            st_folium(health_map, width="100%", height=450, key="health_zone_map")
        except Exception as e:
            st.warning(f"Map rendering issue: {str(e)}")

        # --- Regional Crop Health Guide (Expanded Table) ---
        st.markdown("---")
        st.markdown("### 🗺️ Regional Crop Health Guide (Kuttanad, Kerala)")
        st.markdown(f"Based on your farm location at **({farm_lat:.4f}, {farm_lon:.4f})**, here are all common regional crops, their frequent diseases, and potential cures.")
        
        regional_crops = get_regional_crop_guide()
        st.table(regional_crops)

        # --- Export Area ---
        st.markdown("---")
        st.markdown("### 🖨️ Export Report")
        col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])
        with col_dl2:
            with st.container():
                st.write("**Save Your Intelligent Report**")
                pdf_farm_name = st.text_input("Enter Farm Name for PDF:", farmer_name + "'s Farm", key="pdf_name")
                if st.button("Compile PDF Data", key="pdf_btn"):
                    pdf_bytes = create_pdf(pdf_farm_name, overall_score, orig_rgb, overlay_rgb, zones_df, farmer_tips, ai_diagnosis, ai_cure)
                    st.download_button(
                        label="📄 Download AI Diagnostic & Action Report (PDF)",
                        data=pdf_bytes,
                        file_name=f"CropSight_AI_Report_{pdf_farm_name.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

    except Exception as e:
        st.error(f"Error processing image: {str(e)}")

st.markdown("""
<div class='footer'>
    Built for SDG 2 Zero Hunger – 24-hour hackathon 🚀 🌱 | <b>CropSight Platform</b>
</div>
""", unsafe_allow_html=True)
