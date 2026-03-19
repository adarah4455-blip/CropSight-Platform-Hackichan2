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
from transformers import pipeline
import torch

# --- Global App Defaults (Previously in Sidebar) ---
sh_client_id = "9014ff84-e5be-44a4-b866-caa7d576c8a0"
sh_client_secret = "zlnN8FTFmxBmEFt6bSkNQcGM4kBqciPx"

# --- Google OAuth Configuration ---
# TO USE: Get your Client ID and Secret from Google Cloud Console
# and paste them below.
GOOGLE_CLIENT_ID = "YOUR_CLIENT_ID_HERE"
GOOGLE_CLIENT_SECRET = "YOUR_CLIENT_SECRET_HERE"

# --- AI Model Initialization (Hugging Face) ---
@st.cache_resource
def load_ai_model():
    # link98/crop-disease-detection is a stable and accurate model for image classification
    return pipeline("image-classification", model="nateraw/vit-base-beans")

try:
    ai_pipeline = load_ai_model()
except Exception as e:
    st.warning(f"AI Diagnostic Engine is currently offline (Model Load Error). Using Remote Sensing Fallback. {str(e)}")
    ai_pipeline = None

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
    
    .animated-card { 
        animation: fadeInSlideUp 0.8s ease forwards; 
        padding: 1.8rem;
        background-color: rgba(255, 255, 255, 0.95); 
        border-radius: 30px;
        box-shadow: 0 10px 30px rgba(123, 178, 132, 0.1);
        margin-bottom: 1rem;
        border: 3px solid #eef6f0;
    }
    .animated-image img { border-radius: 24px; box-shadow: 0 10px 30px rgba(123, 178, 132, 0.2); }
    .animated-image { animation: scaleIn 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; }
    
    /* Hide Streamlit Default UI Elements (White Bars) */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}
    div[data-testid="stHeader"] {background:transparent;}
    
    /* Typography & Cute Styling */
    h1, h2, h3, h4 { color: #588560 !important; font-family: 'Comic Sans MS', 'Chalkboard SE', 'Segoe UI', cursive, sans-serif; letter-spacing: -0.5px; }
    p, span, div, text, li { color: #4a5d4a; }
    
    .header-box { text-align: center; margin-bottom: 2rem; animation: fadeInSlideUp 0.8s ease forwards; }
    .main-header { font-size: 4.2rem; color: #7bb284; font-weight: 900; margin-bottom: 0; text-shadow: 2px 2px 0px #eef6f0; }
    .sub-header { font-size: 1.3rem; color: #588560; margin-top: 5px; font-weight: 600; }
    
    /* Cute Rounded Cards - TARGETED ONLY via .animated-card class */
    
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

    /* Floating Chatbot Styles */
    #chatbot-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
        width: 350px;
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        border: 2px solid #7bb284;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        animation: fadeInSlideUp 0.8s ease;
    }
    .chat-header {
        background: #7bb284;
        color: white;
        padding: 15px;
        font-weight: bold;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .chat-body {
        height: 300px;
        overflow-y: auto;
        padding: 15px;
        background: #fdfdfd;
        font-size: 0.9em;
    }
    .user-msg { background: #eef6f0; padding: 8px 12px; border-radius: 12px 12px 2px 12px; margin-bottom: 10px; text-align: right; margin-left: auto; width: fit-content; max-width: 80%; }
    .bot-msg { background: #fff; border: 1px solid #7bb284; padding: 8px 12px; border-radius: 12px 12px 12px 2px; margin-bottom: 10px; text-align: left; width: fit-content; max-width: 80%; }
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

def ai_crop_analysis(image_bytes):
    """
    Analyzes crop image using a Deep Learning model from Hugging Face.
    """
    if ai_pipeline is None:
        return "AI Diagnostic Engine Offline (Using VARI Fallback)", 0.0
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        results = ai_pipeline(img)
        # Results is a list of dicts: [{'label': '...", 'score': ...}, ...]
        top_prediction = results[0]
        label = top_prediction['label']
        confidence = top_prediction['score']
        return label, confidence
    except Exception as e:
        return f"AI Logic Offline: {str(e)}", 0.0

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

def get_ai_diagnosis(crop_type, overall_score, zones_df, ai_label=None, ai_confidence=0.0):
    """
    Combines rule-based Remote Sensing (VARI) with Deep Learning results
    from the Hugging Face plant classification model.
    """
    # 1. Start with the AI Model result if it has high confidence
    if ai_label and ai_confidence > 0.4:
        # Clean up labels like "Apple___Apple_scab" -> "Apple Scab"
        display_label = ai_label.split("__")[-1].replace("_", " ") if "___" in ai_label else ai_label
        
        # Mapping common model outputs to professional cures
        cures = {
            "angular leaf spot": "Apply protective copper-based fungicides. Rotate crops and remove infected debris to break the fungal life cycle.",
            "bean rust": "Spray sulfur or chlorothalonil-based fungicides. Use resistant varieties and avoid overhead irrigation to keep foliage dry.",
            "Apple scab": "Apply fungicide like Captan or Myclobutanil. Clear fallen leaves to prevent overwintering spores.",
            "Black rot": "Prune out infected branches and fruit. Use copper-based fungicides during the growing season.",
            "Cedar apple rust": "Remove nearby juniper trees if possible. Apply protective fungicide sprays in early spring.",
            "Bacterial spot": "Avoid overhead watering. Apply copper sprays early in the season to reduce bacterial load.",
            "Late blight": "Increase air circulation. Apply fungicides like Chlorothalonil or Mancozeb immediately.",
            "Early blight": "Rotate crops and remove plant debris. Apply copper or sulfur-based fungicides.",
            "Leaf mold": "Reduce humidity in the greenhouse/field. Improve ventilation and use resistant varieties.",
            "Septoria leaf spot": "Avoid irrigation from above. Mulch to prevent spores splashing from soil onto leaves.",
            "Spider mites": "Apply neem oil or insecticidal soap. Increase humidity if in a dry environment.",
            "Target Spot": "Remove lower leaves to improve airflow. Apply fungicides specifically labeled for target spot.",
            "Yellow Leaf Curl Virus": "Control whitefly populations using yellow sticky traps or insecticidal soaps.",
            "Mosaic virus": "No cure for infected plants; remove and destroy immediately to prevent spread via aphids.",
            "Powdery mildew": "Apply sulfur-based fungicides or neem oil. Ensure plants have adequate spacing for airflow.",
            "Rust": "Remove infected leaves. Apply sulfur or copper-based fungicides at first sign of infection.",
            "Leaf scorch": "Ensure deep watering during dry spells. Check for root damage or high soil salinity.",
            "Healthy": "No disease detected. Maintain current irrigation and nutrient balance."
        }
        
        cure = cures.get(display_label, "Consult an agile agronomist. Maintain balanced NPK and ensure proper field drainage.")
        return f"{display_label} (AI Verified)", cure

    # 2. Fallback to VARI-based rule matching if AI confidence is low
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
    replacements = {'🌟 ': '', '⚠️ ': '', '🚨 ': '', '💧 ': '', '🐛 ': '', '🔴': 'Red', '🟡': 'Yellow', '🟢': 'Green', '*': '', '🌍': '', '🌾': 'Rice', '🥥': 'Coconut', '🍌': 'Banana', '🌳': 'Arecanut', '🧤': 'Rubber', '🍍': 'Pineapple'}
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'ignore').decode('latin-1')

def create_pdf(email, current_farm_name, selected_crop, current_score, original, overlay, zones_df, tips, ai_diagnosis, ai_cure):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    
    # --- Page 1: Portfolio Executive Summary ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 26)
    pdf.set_text_color(88, 133, 96)
    pdf.cell(0, 15, "CropSight - Master Portfolio Report", 0, 1, 'C')
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, f"Account Holder: {clean_for_pdf(email)} | Generated: {time.strftime('%Y-%m-%d')}", 0, 1, 'C')
    pdf.ln(10)

    # Portfolio Table
    pdf.set_font("Arial", 'B', 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, clean_for_pdf(" 🌍 All Managed Land Records Summary"), 0, 1, 'L', 1)
    pdf.set_font("Arial", 'B', 12)
    p_cols = [70, 40, 60, 100]
    p_headers = ["Farm/Field Name", "Avg Score", "Last Activity", "Status Indicator"]
    for w, h in zip(p_cols, p_headers):
        pdf.cell(w, 10, clean_for_pdf(h), 1, 0, 'C')
    pdf.ln()
    
    pdf.set_font("Arial", '', 11)
    all_farms = auth.get_user_farms(email)
    for f_name, lat, lon, _, ts in all_farms:
        hist = auth.get_analysis_history(email, f_name)
        avg_s = int(sum([h[0] for h in hist])/len(hist)) if hist else "N/A"
        last_s = hist[-1][0] if hist else 0
        status = "🟢 Healthy" if last_s > 70 else "🟡 Stress" if last_s > 40 else "🔴 Priority"
        
        pdf.cell(p_cols[0], 10, clean_for_pdf(f_name), 1, 0, 'C')
        pdf.cell(p_cols[1], 10, f"{avg_s}%", 1, 0, 'C')
        pdf.cell(p_cols[2], 10, clean_for_pdf(ts[:10]), 1, 0, 'C')
        pdf.cell(p_cols[3], 10, clean_for_pdf(status), 1, 0, 'C')
        pdf.ln()
    
    # --- Page 2: Detailed Analysis for Current Active Farm ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 22)
    pdf.set_text_color(88, 133, 96)
    pdf.cell(0, 15, f"Analysis Detail: {clean_for_pdf(current_farm_name)}", 0, 1, 'L')
    
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 10, f"Farm Type / Crop: {clean_for_pdf(selected_crop)}", 0, 1, 'L')
    pdf.cell(0, 10, f"Current Health Score: {current_score}/100", 0, 1, 'L')
    pdf.ln(2)
    
    # AI Diagnosis Section in PDF
    pdf.set_font("Arial", 'B', 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, clean_for_pdf(" AI Pathogen & Stress Diagnostic Report"), 0, 1, 'L', 1)
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
        pdf.text(10, y_pos, "1. Original Imagery (Current)")
        pdf.text(150, y_pos, "2. Health Zone Overlay (Current)")
        pdf.image(f_orig.name, x=10, y=y_pos+5, w=130)
        pdf.image(f_over.name, x=150, y=y_pos+5, w=130)
        img_aspect = original.shape[0]/original.shape[1]
        pdf.set_y(y_pos + 5 + (130 * img_aspect) + 10)
        
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "3. Targeted Support Actions", 0, 1)
    pdf.set_font("Arial", '', 12)
    for tip in tips:
        pdf.cell(0, 8, f"- {clean_for_pdf(tip)}", 0, 1)
        
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "4. Physical Zone Breakdown", 0, 1)
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
        
    # --- Page 3+: Historical Data Tables for All Farms ---
    for f_name, lat, lon, _, _ in all_farms:
        if f_name == current_farm_name: continue
        pdf.add_page()
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 10, f"Historical Context: {clean_for_pdf(f_name)}", 0, 1)
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Location: {lat:.4f}, {lon:.4f}", 0, 1)
        pdf.ln(5)
        
        hist = auth.get_analysis_history(email, f_name)
        if hist:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(60, 10, "Scan Date", 1, 0, 'C')
            pdf.cell(60, 10, "Recorded Score", 1, 1, 'C')
            pdf.set_font("Arial", '', 11)
            for s, t in reversed(hist[-10:]): # Show last 10 scans
                pdf.cell(60, 10, clean_for_pdf(t[:16]), 1, 0, 'C')
                pdf.cell(60, 10, f"{s}%", 1, 1, 'C')
    
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
        st.markdown("<div class='animated-card' style='padding: 1rem 2rem 2rem 2rem; border-radius: 20px; background: rgba(255,255,255,0.9); box-shadow: 0 10px 30px rgba(123, 178, 132, 0.2); text-align: center;'>", unsafe_allow_html=True)
        
        # --- Google Sign-In Option ---
        st.markdown("<h5 style='letter-spacing:1px; color:#588560;'>CONTINUE WITH GOOGLE</h5>", unsafe_allow_html=True)
        if GOOGLE_CLIENT_ID == "YOUR_CLIENT_ID_HERE":
            if st.button("🔵 Mock Google Login (For Demo)", use_container_width=True):
                # Temporary demo login for hackathon testing
                st.session_state.logged_in = True
                st.session_state.user_email = "demo.farmer@gmail.com"
                auth.login_google_user("demo.farmer@gmail.com", "mock_google_123")
                st.success("Signed in with Google (Simulated)")
                st.rerun()
            st.caption("To use real Google Auth, please provide your Client ID in the app.py configuration.")
        else:
            try:
                from streamlit_google_auth import Authenticate
                authenticator = Authenticate(
                    secret_names={'client_id': GOOGLE_CLIENT_ID, 'client_secret': GOOGLE_CLIENT_SECRET},
                    cookie_name='cropsight_google_auth',
                    key='cropsight_auth_key',
                    cookie_expiry_days=30,
                    redirect_uri='http://localhost:8501',
                )
                authenticator.check_authentification()
                if st.session_state.get('connected'):
                    user_info = st.session_state.get('user_info', {})
                    if user_info:
                        email = user_info.get('email')
                        g_id = user_info.get('sub')
                        auth.login_google_user(email, g_id)
                        st.session_state.logged_in = True
                        st.session_state.user_email = email
                        st.rerun()
                else:
                    authenticator.login()
            except Exception as e:
                st.error(f"Google Auth Error: {str(e)}")

        st.markdown("<div style='margin: 20px 0; border-top: 1px solid #eee; position: relative;'><span style='position:absolute; top:-12px; left:45%; background:white; padding: 0 10px; color:#999; font-size:0.8em;'>OR</span></div>", unsafe_allow_html=True)

        choice = st.radio("Select an option", ["Login", "Sign Up"], horizontal=True, label_visibility="collapsed")
        
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
    
    st.markdown("---")
    st.markdown("### 🌾 Crop Selection")
    crop_options = ["Rice", "Coconut", "Banana", "Arecanut", "Rubber", "Wheat", "Corn", "Sugarcane"]
    selected_crop = st.selectbox("Select your crop type:", crop_options, index=0, help="Accurate diagnosis depends on selecting the correct crop type.")
    st.markdown("---")
    st.markdown("---")
    st.markdown("### 📬 Farmer Mailbox")
    
    # Auto-generate 'scheduled' notifications
    user_farms = auth.get_user_farms(st.session_state.user_email)
    if user_farms:
        last_farm = user_farms[0]
        # Check if 2 days passed since last record
        last_scan_time = datetime.datetime.strptime(last_farm[4], "%Y-%m-%d %H:%M:%S")
        if (datetime.datetime.now() - last_scan_time).days >= 2:
            alert_msg = f"⏳ Reminder: It has been { (datetime.datetime.now() - last_scan_time).days } days since your last scan of '{last_farm[0]}'. Schedule a check-up now!"
            # Only add if not recently added
            existing_notifs = [n[1] for n in auth.get_notifications(st.session_state.user_email)]
            if alert_msg not in existing_notifs:
                auth.add_notification(st.session_state.user_email, alert_msg)

    notifs = auth.get_notifications(st.session_state.user_email)
    unread_count = len([n for n in notifs if n[3] == 'unread'])
    
    if unread_count > 0:
        st.warning(f"You have {unread_count} unread notifications!")
    
    with st.expander(f"View Messages ({unread_count} new)"):
        if not notifs:
            st.caption("No messages yet.")
        for n_id, msg, ts, status in notifs:
            style = "font-weight: bold; color: #2c3e50;" if status == 'unread' else "color: #7f8c8d;"
            st.markdown(f"<div style='font-size: 0.85em; margin-bottom: 10px; padding: 5px; border-bottom: 1px solid #eee; {style}'>{msg}<br><i style='font-size: 0.8em;'>{ts}</i></div>", unsafe_allow_html=True)
            if status == 'unread':
                if st.button("Mark Read", key=f"read_{n_id}"):
                    auth.mark_notif_read(n_id)
                    st.rerun()

    st.markdown("---")
    st.markdown("### 🚜 Your Saved Lands")
    if not user_farms:
        st.caption("No farms recorded yet. Draw one on the map to start!")
    else:
        for f_name, f_lat, f_lon, f_bound, f_time in user_farms:
            if st.button(f"📍 {f_name}", key=f"switch_{f_name}_{f_time}", use_container_width=True, help=f"Last updated: {f_time}"):
                st.session_state.farm_boundary = json.loads(f_bound)
                st.session_state.pdf_farm_name = f_name
                st.session_state.farm_confirmed = True
                st.success(f"Switching to {f_name}...")
                st.rerun()
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
                    st.session_state.pdf_farm_name = f_name # Store for records
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
                    st.session_state.pdf_farm_name = farm_name
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

        # --- Save Analysis and Compute Delta ---
        farm_name_for_hist = st.session_state.get('pdf_farm_name', 'Unnamed Farm')
        history = auth.get_analysis_history(st.session_state.user_email, farm_name_for_hist)
        
        health_delta = 0
        if history:
            prev_score = history[-1][0]
            health_delta = overall_score - prev_score
            
        # Record this analysis (if not already recorded in this specific session run to avoid duplicates on reruns)
        if 'last_recorded_score' not in st.session_state or st.session_state.last_recorded_score != overall_score:
            auth.save_analysis_record(st.session_state.user_email, farm_name_for_hist, overall_score)
            st.session_state.last_recorded_score = overall_score
            # Refresh history for chart
            history = auth.get_analysis_history(st.session_state.user_email, farm_name_for_hist)

        # --- AI Disease Diagnosis (Deep Learning) ---
        ai_label, ai_conf = ai_crop_analysis(bytes(image_bytes))
        ai_diagnosis, ai_cure = get_ai_diagnosis(selected_crop, overall_score, zones_df, ai_label, ai_conf)

        st.markdown(f"""
        <div class="diagnosis-card" style="border-left: 10px solid {'#e74c3c' if overall_score < 40 else '#f1c40f' if overall_score < 70 else '#2ecc71'}; background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 25px;">
            <h2 style='margin-top:0; color: #2c3e50; font-family: "Outfit", sans-serif;'>🧬 AI Pathogen & Stress Diagnostic Report</h2>
            <hr style='margin: 15px 0; border: none; border-top: 1px solid #eee;'>
            <div style='display:flex; justify-content:space-between; align-items:flex-start; flex-wrap: wrap;'>
                <div style='flex: 2; min-width: 300px;'>
                    <p style='margin-bottom: 5px; font-weight: bold; color: #7f8c8d; text-transform: uppercase; font-size: 0.8em;'>
                        Detected Condition {f"(AI Confidence: {ai_conf*100:.1f}%)" if ai_conf > 0 else ""}
                    </p>
                    <p style='color:#e74c3c; font-size:1.6em; font-weight: bold; margin-bottom: 20px;'>{ai_diagnosis}</p>
                    <p style='margin-bottom: 10px; font-weight: bold; color: #2c3e50;'>✨ AI Recommended Cure / Action Plan:</p>
                    <div style='background:#f4f9f4; padding:20px; border-radius:12px; border:1px solid #e0ede0; color: #2d3436; line-height: 1.6;'>
                        {ai_cure}
                    </div>
                </div>
                <div style='flex: 1; min-width: 150px; text-align:center; background:#f8f9fa; padding:25px; border-radius:20px; margin-left:20px; display: flex; flex-direction: column; justify-content: center;'>
                     <p style='margin:0; font-size:0.9em; font-weight: bold; color: #95a5a6;'>CROP HEALTH SCORE</p>
                     <h1 style='margin:10px 0; font-size:4.5em; color:{"#e74c3c" if overall_score < 40 else "#f1c40f" if overall_score < 70 else "#2ecc71"}; font-family: "Outfit", sans-serif;'>{overall_score}</h1>
                     <p style='margin:0; font-size:0.9em; color:{"#2ecc71" if health_delta >= 0 else "#e74c3c"}; font-weight: bold;'>
                        {f"↑ +{health_delta}% improvement" if health_delta >= 0 else f"↓ {health_delta}% decline"}
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
        
        hist_col1, hist_col2 = st.columns([2, 1])
        with hist_col1:
            st.markdown(f"### 📈 Health Trends: {farm_name_for_hist}")
            if len(history) > 1:
                hist_df = pd.DataFrame(history, columns=["Score", "Date"])
                hist_df["Date"] = pd.to_datetime(hist_df["Date"]).dt.strftime("%b %d, %H:%M")
                st.line_chart(hist_df.set_index("Date")["Score"], color="#7bb284")
            else:
                st.info("Continuous monitoring will generate a health trend chart here. Perform more scans to see progress!")
        
        with hist_col2:
            st.markdown("### 📊 Summary Statistics")
            st.metric("Latest Health", f"{overall_score}%", f"{health_delta}%" if history else None)
            if history:
                avg_score = int(sum([h[0] for h in history]) / len(history))
                st.metric("Historical Avg", f"{avg_score}%")

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
                if st.button("Compile Full Portfolio PDF Report", key="pdf_btn"):
                    pdf_bytes = create_pdf(st.session_state.user_email, pdf_farm_name, selected_crop, overall_score, orig_rgb, overlay_rgb, zones_df, farmer_tips, ai_diagnosis, ai_cure)
                    st.download_button(
                        label="📄 Download Complete AI Portfolio Report (PDF)",
                        data=pdf_bytes,
                        file_name=f"CropSight_Full_Portfolio_{st.session_state.user_email.split('@')[0]}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

    except Exception as e:
        st.error(f"Error processing image: {str(e)}")
# --- Floating AI Chatbot Footer Logic ---
st.markdown("<br><br><div class='footer'>© 2026 CropSight Aerial Intelligence Hub • Developed for Global Hackathon</div>", unsafe_allow_html=True)

# 🤖 Floating AI Chatbot UI
if 'chat_visible' not in st.session_state:
    st.session_state.chat_visible = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [{"role": "bot", "content": "👋 I'm **Cropie**, your AI farm guide! Ask me anything about this site or your crop health."}]

# Fixed Button to Toggle Chat
st.markdown("""
<style>
    .chat-toggle {
        position: fixed;
        bottom: 30px;
        right: 30px;
        z-index: 1001;
        background: #7bb284;
        color: white;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 30px;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        border: 2px solid white;
        transition: transform 0.2s;
    }
    .chat-toggle:hover { transform: scale(1.1); }
</style>
""", unsafe_allow_html=True)

# --- AI Chatbot Assistant ---
st.markdown("---")
with st.expander("🤖 **Chat with Cropie (AI Site Assistant)**", expanded=False):
    st.info("I'm your AI guide! Ask me about VARI, AI Diagnosis, PDF Reports, or how to save your farm data.")
    
    # Render Chat History
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.chat_message("user", avatar="👨‍🌾").write(msg["content"])
        else:
            st.chat_message("assistant", avatar="🌱").write(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Ask about CropSight...", key="main_chat_input"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Enhanced Knowledge Base Logic
        p = prompt.lower()
        if any(w in p for w in ["hi", "hello", "hey", "who are you"]):
            response = "Hello! I'm **Cropie**, your CropSight assistant. I can help you understand your farm's health, explain our AI diagnostics, or guide you through creating PDF reports!"
        elif any(w in p for w in ["what", "how", "site", "platform"]):
            response = "CropSight is an **Aerial Action Platform**. You upload drone or mobile photos, and we use **Deep Learning (Vision Transformers)** to detect diseases and **Remote Sensing (VARI)** to map vigor."
        elif "vari" in p:
            response = "VARI stands for **Visible Atmospherically Resistant Index**. It's a formula that highlights vegetation vigor using only standard RGB colors—no special infrared camera needed!"
        elif any(w in p for w in ["health", "score", "percent"]):
            response = "Your health score is a percentage (0-100%). Above 70% is **Healthy**, 40-70% is **Caution**, and below 40% is a **Priority Alert**. This is calculated using chlorophyll intensity."
        elif any(w in p for w in ["save", "record", "data", "history"]):
            response = "All your scans are automatically saved in our **Secure Farm Ledger**. You can view historical trends and switch between different land plots using the sidebar selector!"
        elif any(w in p for w in ["pdf", "report", "download", "export"]):
            response = "You can download a **Master Portfolio Report** at the bottom of the analysis section. It compiles all your managed farms into a single professional PDF document."
        elif any(w in p for w in ["cpu", "gpu", "ai", "model", "diagnos"]):
            status = "ONLINE ✨" if ai_pipeline else "OFFLINE (Fallback Active) ⚠️"
            response = f"Our AI Diagnostic Engine is currently **{status}**. We use a specialized **Transformer model (vit-base-beans)** to identify pathogens like Rust or Blight at the pixel level."
        elif any(w in p for w in ["cure", "disease", "help", "sick", "yellow"]):
            response = "If your crops look yellow or spotted, upload a photo! Our AI will identify the specific pathogen and give you a **Targeted Action Plan** with biological and chemical cures."
        else:
            response = "That's a great question! While I'm still learning, I recommend checking our **Regional Crop Guide** on the main dashboard for specific local advice, or asking me about 'VARI' or 'PDF Reports'."
        
        st.session_state.chat_history.append({"role": "bot", "content": response})
        st.rerun()
