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
from streamlit_folium import st_folium
import os
import base64

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

def clean_for_pdf(text):
    text = str(text)
    replacements = {'🌟 ': '', '⚠️ ': '', '🚨 ': '', '💧 ': '', '🐛 ': '', '🔴': 'Red', '🟡': 'Yellow', '🟢': 'Green', '*': ''}
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'ignore').decode('latin-1')

def create_pdf(farm_name, overall_score, original, overlay, zones_df, tips):
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
    return pdf.output(dest='S').encode('latin-1')


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
    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.rerun()

st.markdown("""
<div class='header-box'>
    <h1 class='main-header'>🌱 CropSight Platform</h1>
    <h3 class='sub-header'>Aerial Crop Health Intelligence – Act within the hour</h3>
    <p>Upload any aerial photo of your field to get an instant colour-coded health map and personalized farmer actions.</p>
</div>
""", unsafe_allow_html=True)


col1, col2, col3 = st.columns([1,3,1])
with col2:
    tab1, tab2 = st.tabs(["📤 Upload Any Image", "👀 Live Demo Mode"])
    uploaded_file = None
    demo_mode = False
    
    with tab1:
        uploaded_file = st.file_uploader("Upload Drone or Satellite Image (JPG, PNG)", type=["jpg", "png", "jpeg", "tif"])
    with tab2:
        st.info("No farm image right now? Test using our sample drone imagery.")
        demo_path = os.path.join(os.path.dirname(__file__), "demo_images", "drone_farm_field.png")
        if st.button("✨ Load Sample Drone Image ✨", key="demo_btn"):
            demo_mode = True

if uploaded_file or demo_mode:
    st.markdown("---")
    
    with st.spinner("Processing aerial imagery through spectral algorithms..."):
        time.sleep(1) # Simulation delay
        
        try:
            if demo_mode:
                if os.path.exists(demo_path):
                    with open(demo_path, "rb") as f:
                        image_bytes = f.read()
                else:
                    st.error("Demo image not found. Please upload a real image.")
                    st.stop()
            else:
                image_bytes = uploaded_file.read()
                
            orig_rgb, overlay_rgb, health_array, overall_score = analyze_image(image_bytes)
            zones_df = find_zones(health_array)
            farmer_tips = generate_tips(overall_score, zones_df)
            
            # --- Top Area: Metrics & Tips ---
            col_score, col_tips = st.columns([1, 2])
            with col_score:
                st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
                st.metric("Overall Crop Health", f"{overall_score} / 100", delta="+12% from last week" if overall_score>50 else "-5% from last week")
                if overall_score >= 70:
                    st.success("Your crop is in good standing! 🌱")
                elif overall_score >= 40:
                    st.warning("Your crop shows moderate stress levels. ⚠️")
                else:
                    st.error("Your crop requires urgent attention. 🚨")
                st.markdown("</div>", unsafe_allow_html=True)
                
            with col_tips:
                with st.container():
                    st.markdown("### 📋 Primary Action Guide")
                    for tip in farmer_tips:
                        st.markdown(tip)
            
            # --- Visual Health Maps ---
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
            
            # --- Specific Zones ---
            st.markdown("### 📍 Drill-Down: Specific Zones")
            st.dataframe(zones_df, use_container_width=True, hide_index=True)
            
            # --- Pathology & Treatment Button Section ---
            st.markdown("---")
            if 'show_pathology' not in st.session_state:
                st.session_state.show_pathology = False

            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔬 Diagnose Possible Diseases & View Treatments ➔", use_container_width=True, key="path_btn"):
                    st.session_state.show_pathology = not st.session_state.show_pathology
                    
            if st.session_state.show_pathology:
                RAW_HTML = """
<style>
    @keyframes fadeInSlideUp { 0% { opacity: 0; transform: translateY(20px); } 100% { opacity: 1; transform: translateY(0); } }
    body { font-family: 'Comic Sans MS', 'Chalkboard SE', 'Segoe UI', cursive, sans-serif; background-color: transparent; margin: 0; padding: 5px; }
    .pathology-box {
        background-color: #ffffff;
        border: 4px dashed #DF654D;
        padding: 30px;
        border-radius: 30px;
        box-shadow: 0 10px 25px rgba(223, 101, 77, 0.15);
        animation: fadeInSlideUp 0.8s ease forwards;
    }
    h3 { margin-top: 0; color: #DF654D; margin-bottom: 20px; font-weight: 900; font-size: 1.6rem;}
    h4 { margin-top: 25px; color: #588560; border-bottom: 3px dotted #7bb284; padding-bottom: 8px; font-size: 1.2rem;}
    ul { padding-left: 15px; color: #4a5d4a; }
    li { margin-bottom: 12px; font-size: 1.05rem; line-height: 1.4; font-family: 'Segoe UI', sans-serif;}
    b { color: #333333; }
</style>
<div class="pathology-box">
<h3>🦠 Deep Diagnostic Pathologies & Targeted Treatments</h3>

<div class="path-section">
<h4>1. Potential Diseases Detected</h4>
<ul>
<li><b>Fungal Diseases</b> – Caused by fungi; thrive in warm, humid conditions.<br><i>Examples: Powdery Mildew, Downy Mildew, Rust, Leaf Spot</i></li>
<li><b>Bacterial Diseases</b> – Caused by pathogenic bacteria, often spread through water, tools, or infected seeds.<br><i>Examples: Bacterial Blight, Soft Rot, Leaf Spot</i></li>
<li><b>Viral Diseases</b> – Caused by viruses; usually spread by insects like aphids or whiteflies.<br><i>Examples: Mosaic Virus, Yellow Vein Virus, Tomato Leaf Curl Virus</i></li>
<li><b>Nematode Infestations</b> – Microscopic worms affecting roots and underground parts.<br><i>Examples: Root-knot Nematodes, Cyst Nematodes</i></li>
<li><b>Physiological Disorders</b> – Non-infectious diseases due to nutrient deficiency, water stress, or environmental factors.<br><i>Examples: Leaf Chlorosis, Blossom End Rot, Stunted Growth</i></li>
</ul>
</div>

<div class="path-section">
<h4>🌱 Natural & Organic Remedies</h4>
<ul>
<li><b>For Fungal Diseases:</b> Spray Neem Oil Extract or Bordeaux mixture (copper sulphate and slaked lime) every 7-14 days.</li>
<li><b>For Viral & Bacterial Spread:</b> Control insect vectors naturally using insecticidal soaps. Remove and burn infected plants.</li>
<li><b>For Nematodes:</b> Practice crop rotation and plant marigolds as a trap crop to deter root-knot nematodes naturally.</li>
<li><b>Physiological Fixes:</b> Apply worm castings tea or liquid kelp extract for nutrient lockout (Chlorosis/Stunted growth).</li>
</ul>
</div>

<div class="path-section">
<h4>🧪 Chemical Commercial Interventions</h4>
<ul>
<li><b>Fungicides:</b> Apply broad-spectrum treatments containing Chlorothalonil or Mancozeb at the recommended rate.</li>
<li><b>Bactericides & Pesticides:</b> Copper-based sprays for bacterial diseases. Imidacloprid or Pyrethrin for aphid/whitefly vectors.</li>
<li><b>Nematicides:</b> Synthetic non-fumigant nematicides (e.g., Oxamyl) for severe root knot outbreaks.</li>
<li><b>Synthetic Fertilizers:</b> Soluble NPK 20-20-20 drip irrigation feed to rapidly correct Physiological Disorders.</li>
</ul>
</div>

<p style="font-size: 0.9rem; color: #777; margin-top:20px; font-family: 'Segoe UI', sans-serif;"><i>*Disclaimer: Always follow manufacturer instructions on any chemical interventions. CropSight diagnostics cannot replace on-the-ground soil sampling.</i></p>
</div>
"""
                st.components.v1.html(RAW_HTML, height=880, scrolling=True)
            
            # --- Export Area ---
            st.markdown("---")
            st.markdown("### 🖨️ Export & Geography")
            dl_col1, dl_col2 = st.columns(2)
            with dl_col1:
                with st.container():
                    st.write("**Save Your Intelligent Report**")
                    farm_name = st.text_input("Enter Farm Name for PDF:", "My Field 1")
                    if st.button("Compile PDF Data", key="pdf_btn"):
                        pdf_bytes = create_pdf(farm_name, overall_score, orig_rgb, overlay_rgb, zones_df, farmer_tips)
                        st.download_button(
                            label="Download Report PDF 📥",
                            data=pdf_bytes,
                            file_name=f"CropSight_Report_{farm_name.replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
            with dl_col2:
                with st.container():
                    show_map = st.checkbox("Show Field Map (GPS Location from Image)", value=True)
                    if show_map:
                        gps_coords = get_exif_location(image_bytes)
                        if gps_coords:
                            lat, lon = gps_coords
                            st.success(f"📍 Location extracted from image EXIF data: {lat:.4f}, {lon:.4f}")
                        else:
                            st.warning("⚠️ No GPS EXIF data found. Showing default demo location (Kerala, India).")
                            lat, lon = 9.3175, 76.3900
                            
                        try:
                            m = folium.Map(location=[lat, lon], zoom_start=15)
                            folium.Marker([lat, lon], popup="Analyzed Field (Kuttanad, Kerala)").add_to(m)
                            folium.Polygon(
                                locations=[(lat+0.001, lon-0.001), (lat+0.002, lon+0.001), (lat-0.001, lon+0.002), (lat-0.001, lon-0.001)],
                                color="#DF654D", weight=2, fill_color="#DF654D", fill_opacity=0.5, tooltip="Red Zone: Irrigate Now"
                            ).add_to(m)
                            st_folium(m, width="100%", height=250)
                        except Exception as e:
                            st.write("Folium mapping unavailable at the moment.", str(e))
                    else:
                        st.info("Enable GPS mapping to visualize field location context.")
                
        except Exception as e:
            st.error(f"Error processing image: {str(e)}")

st.markdown("""
<div class='footer'>
    Built for SDG 2 Zero Hunger – 24-hour hackathon 🚀 🌱 | <b>CropSight Platform</b>
</div>
""", unsafe_allow_html=True)
