import pdfplumber
import re
import spacy
from spacy.matcher import PhraseMatcher
import streamlit as st
import plotly.graph_objects as go

# --- SETUP ---
@st.cache_resource
def load_nlp():
    return spacy.load("en_core_web_sm")

nlp = load_nlp()

# --- DATA: Expanded Role Library ---
ROLE_CATEGORIES = {
    "Technical": {
        "Python Developer": ["Python", "Django", "Flask", "SQL", "Git", "REST API", "Docker"],
        "Data Scientist": ["Python", "Machine Learning", "SQL", "Statistics", "Pandas", "Scikit-learn"],
        "Frontend Developer": ["JavaScript", "React", "HTML", "CSS", "TypeScript", "Tailwind"],
    },
    "Management": {
        "Project Manager": ["Leadership", "Agile", "Scrum", "Risk Management", "Budgeting", "Jira"],
        "Product Manager": ["Roadmap", "User Research", "Strategy", "Agile", "Market Analysis"],
    }
}

# --- STYLING (The "Beautiful" Part) ---
st.set_page_config(page_title="Resume Intelligence", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .info-card { background-color: #ffffff; padding: 25px; border-radius: 15px; border-left: 5px solid #4F46E5; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .skill-tag { display: inline-block; padding: 5px 12px; margin: 4px; border-radius: 20px; background: #EEF2FF; color: #4F46E5; font-size: 0.85rem; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCTIONS ---
def extract_text_from_pdf(file_obj):
    text = ""
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            content = page.extract_text()
            if content: text += content + "\n"
    return text

def extract_contact(text):
    email = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    phone = re.findall(r'(?:(?:\+|0{0,2})91[\s-]?)?[6789]\d{9}', text)
    return {"email": email[0] if email else "Not found", "phone": phone[0] if phone else "Not found"}

def extract_skills(text, skill_list):
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(skill) for skill in skill_list]
    matcher.add("SKILLS", patterns)
    doc = nlp(text)
    matches = matcher(doc)
    return list(set([doc[start:end].text for _, start, end in matches]))

# --- UI HEADER ---
st.title("🚀 Resume Intelligence AI")
st.caption("Deep-scan your resume against industry standards or specific job descriptions.")

# --- MODE SELECTOR SLIDER ---
# Using a toggle as a "slider" for a modern feel
is_custom_mode = st.toggle("Switch to Custom Job Description Mode", value=False)

with st.container():
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("⚙️ Analysis Settings")
        if not is_custom_mode:
            cat = st.selectbox("Industry", list(ROLE_CATEGORIES.keys()))
            role = st.selectbox("Target Role", list(ROLE_CATEGORIES[cat].keys()))
            target_skills = ROLE_CATEGORIES[cat][role]
        else:
            jd_text = st.text_area("Paste Job Description here...", height=200)
            target_skills = extract_skills(jd_text, ["Python", "SQL", "React", "Java", "Management", "Agile"]) if jd_text else [] # Expanded base list
            role = "Custom JD"

    with c2:
        uploaded_file = st.file_uploader("Drop your Resume (PDF)", type="pdf")

if uploaded_file and (not is_custom_mode or (is_custom_mode and target_skills)):
    resume_text = extract_text_from_pdf(uploaded_file)
    contact = extract_contact(resume_text)
    detected = extract_skills(resume_text, target_skills + ["Python", "Java", "Communication", "Teamwork"]) # Helper scan

    # --- CANDIDATE CARDS ---
    st.divider()
    st.subheader("📋 Analysis Results")
    
    col_left, col_right = st.columns([1, 1.5])
    
    with col_left:
        # Candidate Info Card
        st.markdown(f"""
        <div class="info-card">
            <h4>Candidate Profile</h4>
            <p>📧 <b>Email:</b> {contact['email']}</p>
            <p>📞 <b>Phone:</b> {contact['phone']}</p>
            <hr>
            <h5>Extracted Skills</h5>
            <div>{"".join([f'<span class="skill-tag">{s}</span>' for s in detected if s in target_skills])}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        # Match Score Card
        res_lower = [s.lower() for s in detected]
        matched = [s for s in target_skills if s.lower() in res_lower]
        missing = [s for s in target_skills if s.lower() not in res_lower]
        score = int((len(matched)/len(target_skills))*100) if target_skills else 0

        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = score,
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1},
                'bar': {'color': "#4F46E5"},
                'steps': [
                    {'range': [0, 50], 'color': "#FEE2E2"},
                    {'range': [50, 80], 'color': "#FEF3C7"},
                    {'range': [80, 100], 'color': "#D1FAE5"}]
            }
        ))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)

    # --- DETAILED FEEDBACK ---
    f1, f2 = st.columns(2)
    with f1:
        st.success(f"**Skills found:** {', '.join(matched) if matched else 'None'}")
    with f2:
        st.error(f"**Missing skills:** {', '.join(missing) if missing else 'None'}")