import pdfplumber
import re
import spacy
from spacy.matcher import PhraseMatcher
import streamlit as st
import plotly.graph_objects as go # New for charts!

# --- SETUP ---
@st.cache_resource
def load_nlp():
    return spacy.load("en_core_web_sm")

nlp = load_nlp()

# --- DATA: Massive Role Library ---
ROLE_CATEGORIES = {
    "Software Engineering": {
        "Python Developer": ["Python", "Django", "Flask", "SQL", "Git", "REST API", "Docker", "Unit Testing"],
        "Frontend Developer": ["JavaScript", "React", "HTML", "CSS", "TypeScript", "Tailwind", "Next.js", "Figma"],
        "Backend Developer": ["Node.js", "Java", "Spring Boot", "SQL", "PostgreSQL", "MongoDB", "Redis", "API Design"],
        "Fullstack Developer": ["Python", "JavaScript", "React", "Node.js", "SQL", "Git", "AWS", "API"],
        "DevOps Engineer": ["Docker", "Kubernetes", "AWS", "Terraform", "CI/CD", "Linux", "Jenkins", "Python"]
    },
    "Data & AI": {
        "Data Scientist": ["Python", "Machine Learning", "Data Analysis", "SQL", "Statistics", "Pandas", "NumPy", "Scikit-learn"],
        "Data Analyst": ["SQL", "Excel", "Tableau", "Power BI", "Python", "Statistics", "Data Cleaning"],
        "AI/ML Engineer": ["PyTorch", "TensorFlow", "Deep Learning", "NLP", "Python", "Computer Vision", "Math"]
    },
    "Business & Management": {
        "Project Manager": ["Leadership", "Communication", "Agile", "Scrum", "Risk Management", "Budgeting", "Excel", "Jira"],
        "Product Manager": ["Product Roadmap", "User Research", "Market Analysis", "Agile", "Jira", "Strategy", "Data Analysis"],
        "Marketing Manager": ["SEO", "Content Strategy", "Google Analytics", "Social Media", "Copywriting", "Email Marketing"]
    }
}

# --- FUNCTIONS ---
def extract_text_from_pdf(file_obj):
    all_text = ""
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True)
            if text: all_text += text + "\n"
    return all_text

def extract_contact_info(text):
    email = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    phone = re.findall(r'(?:(?:\+|0{0,2})91[\s-]?)?[6789]\d{9}', text)
    return {"email": email[0] if email else "Not found", "phone": phone[0] if phone else "Not found"}

def extract_skills(text, skill_list=None):
    if not skill_list:
        skill_list = ["Python", "Java", "C++", "JavaScript", "React", "Node.js", "SQL", "Excel", "AWS", "Docker", "Agile", "SEO"]
    
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(skill) for skill in skill_list]
    matcher.add("SKILL_LIST", patterns)
    doc = nlp(text)
    matches = matcher(doc)
    return list(set([doc[start:end].text for _, start, end in matches]))

# --- UI ---
st.set_page_config(page_title="Resume Matcher Pro", layout="wide")
st.title("🎯 Resume Matcher & Skill Analytics")

# --- SIDEBAR ---
st.sidebar.header("Configuration")
mode = st.sidebar.radio("Analysis Mode", ["Role-Based", "Custom JD"])

target_skills = []
selected_role = ""

if mode == "Role-Based":
    category = st.sidebar.selectbox("Select Category", list(ROLE_CATEGORIES.keys()))
    selected_role = st.sidebar.selectbox("Select Role", list(ROLE_CATEGORIES[category].keys()))
    target_skills = ROLE_CATEGORIES[category][selected_role]
else:
    jd_input = st.sidebar.text_area("Paste Job Description")
    selected_role = "Custom Role"
    if jd_input: target_skills = extract_skills(jd_input)

# --- MAIN ---
uploaded_file = st.file_uploader("Upload PDF Resume", type="pdf")

if uploaded_file:
    content = extract_text_from_pdf(uploaded_file)
    contact = extract_contact_info(content)
    
    # 1. Dashboard Layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("👤 Candidate Info")
        st.write(f"**Email:** {contact['email']}")
        st.write(f"**Phone:** {contact['phone']}")
        
        detected_all = extract_skills(content)
        st.subheader("🛠 Your Skill Map")
        st.write(", ".join(detected_all))

    with col2:
        if target_skills:
            res_lower = [s.lower() for s in detected_all]
            matched = [s for s in target_skills if s.lower() in res_lower]
            missing = [s for s in target_skills if s.lower() not in res_lower]
            score = int((len(matched) / len(target_skills)) * 100)

            # --- Visual Chart ---
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = score,
                title = {'text': f"Match Score for {selected_role}"},
                gauge = {'axis': {'range': [0, 100]},
                         'bar': {'color': "#1f77b4"},
                         'steps' : [
                             {'range': [0, 50], 'color': "#ff4b4b"},
                             {'range': [50, 80], 'color': "#ffa500"},
                             {'range': [80, 100], 'color': "#2ecc71"}]}
            ))
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    
    # 2. Detailed Breakdown
    m1, m2 = st.columns(2)
    with m1:
        st.success(f"✅ Matched ({len(matched)})")
        for s in matched: st.write(f"- {s}")
    with m2:
        st.error(f"❌ Missing ({len(missing)})")
        for s in missing: st.write(f"- {s}")