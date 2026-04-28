import pdfplumber
import re
import spacy
from spacy.matcher import PhraseMatcher
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# --- SETUP ---
@st.cache_resource
def load_nlp():
    return spacy.load("en_core_web_sm")

nlp = load_nlp()

# --- DATA ---
ROLE_CATEGORIES = {
    "Software Engineering": {
        "Python Developer": ["Python", "Django", "Flask", "SQL", "Git", "REST API", "Docker", "Unit Testing"],
        "Frontend Developer": ["JavaScript", "React", "HTML", "CSS", "TypeScript", "Tailwind", "Next.js", "Figma"],
        "Backend Developer": ["Node.js", "Java", "Spring Boot", "SQL", "PostgreSQL", "MongoDB", "Redis", "API Design"],
        "Fullstack Developer": ["Python", "JavaScript", "React", "Node.js", "SQL", "Git", "AWS", "API"],
        "DevOps Engineer": ["Docker", "Kubernetes", "AWS", "Terraform", "CI/CD", "Linux", "Jenkins", "Python"],
        "Mobile Developer": ["Swift", "Kotlin", "React Native", "Flutter", "iOS", "Android", "Git", "REST API"],
    },
    "Data & AI": {
        "Data Scientist": ["Python", "Machine Learning", "Data Analysis", "SQL", "Statistics", "Pandas", "NumPy", "Scikit-learn"],
        "Data Analyst": ["SQL", "Excel", "Tableau", "Power BI", "Python", "Statistics", "Data Cleaning"],
        "AI/ML Engineer": ["PyTorch", "TensorFlow", "Deep Learning", "NLP", "Python", "Computer Vision", "Math"],
        "Data Engineer": ["Apache Spark", "Airflow", "SQL", "Python", "AWS", "ETL", "Kafka", "dbt"],
    },
    "Business & Management": {
        "Project Manager": ["Leadership", "Communication", "Agile", "Scrum", "Risk Management", "Budgeting", "Excel", "Jira"],
        "Product Manager": ["Product Roadmap", "User Research", "Market Analysis", "Agile", "Jira", "Strategy", "Data Analysis"],
        "Marketing Manager": ["SEO", "Content Strategy", "Google Analytics", "Social Media", "Copywriting", "Email Marketing"],
        "Business Analyst": ["SQL", "Excel", "Requirements Gathering", "Data Analysis", "Stakeholder Management", "Agile"],
    },
    "Design & Creative": {
        "UI/UX Designer": ["Figma", "User Research", "Wireframing", "Prototyping", "Adobe XD", "CSS", "Design Systems"],
        "Graphic Designer": ["Photoshop", "Illustrator", "InDesign", "Typography", "Branding", "Figma"],
    }
}

CERT_SUGGESTIONS = {
    "Python": "Python Institute PCEP/PCAP",
    "Machine Learning": "Google ML Crash Course / Coursera ML Specialization",
    "AWS": "AWS Certified Cloud Practitioner",
    "Docker": "Docker Certified Associate",
    "Kubernetes": "Certified Kubernetes Administrator (CKA)",
    "SQL": "Oracle SQL Certification",
    "React": "Meta Front-End Developer Certificate",
    "Data Analysis": "Google Data Analytics Certificate",
    "Agile": "PMI-ACP or Scrum Master (PSM I)",
    "Tableau": "Tableau Desktop Specialist",
    "TensorFlow": "TensorFlow Developer Certificate",
    "Project Management": "PMP or PRINCE2",
}

# --- FUNCTIONS ---
def extract_text_from_pdf(file_obj):
    all_text = ""
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True)
            if text:
                all_text += text + "\n"
    return all_text

def extract_contact_info(text):
    email = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    phone = re.findall(r'(?:(?:\+|0{0,2})91[\s-]?)?[6789]\d{9}', text)
    name_match = re.search(r'^([A-Z][a-z]+ [A-Z][a-z]+)', text.strip(), re.MULTILINE)
    return {
        "email": email[0] if email else "Not found",
        "phone": phone[0] if phone else "Not found",
        "name": name_match.group(1) if name_match else "Candidate"
    }

def extract_skills(text, skill_list=None):
    if not skill_list:
        skill_list = [
            "Python", "Java", "C++", "JavaScript", "React", "Node.js", "SQL", "Excel",
            "AWS", "Docker", "Agile", "SEO", "Figma", "TensorFlow", "PyTorch", "Pandas",
            "Git", "Linux", "TypeScript", "Kubernetes", "MongoDB", "PostgreSQL", "Flask",
            "Django", "Machine Learning", "Deep Learning", "NLP", "Statistics", "Tableau",
            "Power BI", "Swift", "Kotlin", "Flutter", "Scrum", "Leadership", "Communication"
        ]
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(skill) for skill in skill_list]
    matcher.add("SKILL_LIST", patterns)
    doc = nlp(text)
    matches = matcher(doc)
    return list(set([doc[start:end].text for _, start, end in matches]))

def estimate_experience(text):
    years = re.findall(r'(\d+)\+?\s*years?\s*(?:of\s+)?experience', text, re.IGNORECASE)
    if years:
        return max(int(y) for y in years)
    # count job sections as a rough proxy
    jobs = len(re.findall(r'\b(20\d{2})\b', text))
    return min(jobs // 2, 10)

def get_cert_suggestions(missing_skills):
    suggestions = {}
    for skill in missing_skills:
        for key, cert in CERT_SUGGESTIONS.items():
            if key.lower() in skill.lower():
                suggestions[skill] = cert
    return suggestions

def get_best_role_matches(detected_skills):
    results = []
    skill_set = set(s.lower() for s in detected_skills)
    for category, roles in ROLE_CATEGORIES.items():
        for role, required in roles.items():
            matched = [s for s in required if s.lower() in skill_set]
            score = int((len(matched) / len(required)) * 100)
            results.append({"role": role, "category": category, "score": score, "matched": len(matched), "total": len(required)})
    return sorted(results, key=lambda x: x["score"], reverse=True)[:5]

# =====================
# --- UI STARTS HERE ---
# =====================

st.set_page_config(page_title="Resume Matcher Pro", layout="wide", page_icon="🎯")

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 16px 20px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 12px;
    }
    .skill-chip-green {
        display: inline-block;
        background: #d4edda;
        color: #155724;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        margin: 3px;
    }
    .skill-chip-red {
        display: inline-block;
        background: #f8d7da;
        color: #721c24;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        margin: 3px;
    }
    .skill-chip-blue {
        display: inline-block;
        background: #cce5ff;
        color: #004085;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        margin: 3px;
    }
    .section-header {
        font-size: 18px;
        font-weight: 600;
        margin: 20px 0 10px 0;
        padding-bottom: 6px;
        border-bottom: 2px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎯 Resume Matcher Pro")
st.caption("Upload your resume, pick a role, and get AI-powered feedback instantly.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    mode = st.radio("Analysis Mode", ["Role-Based", "Custom JD", "Auto-Match"])
    st.divider()
    
    target_skills = []
    selected_role = ""

    if mode == "Role-Based":
        category = st.selectbox("Category", list(ROLE_CATEGORIES.keys()))
        selected_role = st.selectbox("Role", list(ROLE_CATEGORIES[category].keys()))
        target_skills = ROLE_CATEGORIES[category][selected_role]
        st.info(f"**{len(target_skills)} skills** required for this role")
        
    elif mode == "Custom JD":
        jd_input = st.text_area("Paste Job Description", height=200)
        selected_role = st.text_input("Role Title", value="Custom Role")
        if jd_input:
            target_skills = extract_skills(jd_input)
            st.success(f"Extracted **{len(target_skills)}** skills from JD")
            
    else:
        st.info("Upload your resume and we'll find the best matching roles automatically.")
        selected_role = "Auto"

    st.divider()
    show_certs = st.toggle("Show Certification Suggestions", value=True)

# --- MAIN AREA ---
uploaded_file = st.file_uploader("📄 Upload PDF Resume", type="pdf")

if uploaded_file:
    content = extract_text_from_pdf(uploaded_file)
    contact = extract_contact_info(content)
    detected_skills = extract_skills(content)
    exp_years = estimate_experience(content)

    # ── TOP METRICS BAR ──
    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("👤 Candidate", contact["name"])
    m2.metric("📧 Email", contact["email"])
    m3.metric("📞 Phone", contact["phone"])
    m4.metric("🛠 Skills Detected", len(detected_skills))
    st.markdown("---")

    # ── AUTO MATCH MODE ──
    if mode == "Auto-Match":
        st.markdown('<div class="section-header">🏆 Best Role Matches for Your Resume</div>', unsafe_allow_html=True)
        matches = get_best_role_matches(detected_skills)
        
        cols = st.columns(len(matches))
        for i, match in enumerate(matches):
            with cols[i]:
                color = "#2ecc71" if match["score"] >= 70 else "#ffa500" if match["score"] >= 40 else "#e74c3c"
                st.markdown(f"""
                    <div style='text-align:center; padding:16px; border-radius:12px; border: 1px solid #dee2e6;'>
                        <div style='font-size:28px; font-weight:700; color:{color}'>{match["score"]}%</div>
                        <div style='font-weight:600; font-size:14px'>{match["role"]}</div>
                        <div style='color:#6c757d; font-size:12px'>{match["category"]}</div>
                        <div style='color:#6c757d; font-size:12px'>{match["matched"]}/{match["total"]} skills</div>
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown("#### 🛠 Your Detected Skills")
        chips = " ".join([f'<span class="skill-chip-blue">{s}</span>' for s in sorted(detected_skills)])
        st.markdown(chips, unsafe_allow_html=True)
        st.stop()

    # ── ROLE-BASED / CUSTOM JD ──
    if target_skills:
        res_lower = [s.lower() for s in detected_skills]
        matched = [s for s in target_skills if s.lower() in res_lower]
        missing = [s for s in target_skills if s.lower() not in res_lower]
        score = int((len(matched) / len(target_skills)) * 100)

        left, right = st.columns([1, 1])

        with left:
            # Gauge chart
            color = "#2ecc71" if score >= 80 else "#ffa500" if score >= 50 else "#e74c3c"
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=score,
                delta={"reference": 70, "increasing": {"color": "#2ecc71"}, "decreasing": {"color": "#e74c3c"}},
                title={"text": f"Match Score — {selected_role}", "font": {"size": 15}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1},
                    "bar": {"color": color},
                    "steps": [
                        {"range": [0, 50], "color": "#ffe0e0"},
                        {"range": [50, 80], "color": "#fff3cd"},
                        {"range": [80, 100], "color": "#d4edda"}
                    ],
                    "threshold": {"line": {"color": "black", "width": 3}, "thickness": 0.75, "value": 70}
                }
            ))
            fig.update_layout(height=280, margin=dict(t=40, b=0, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)

            # Radar chart
            if len(target_skills) >= 3:
                categories = target_skills[:8]
                values = [1 if s.lower() in res_lower else 0 for s in categories]
                fig2 = go.Figure(go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    fill='toself',
                    fillcolor='rgba(31,119,180,0.2)',
                    line=dict(color='#1f77b4')
                ))
                fig2.update_layout(
                    polar=dict(radialaxis=dict(visible=False, range=[0, 1])),
                    showlegend=False, height=280,
                    margin=dict(t=20, b=20, l=40, r=40),
                    title=dict(text="Skill Coverage", font=dict(size=13))
                )
                st.plotly_chart(fig2, use_container_width=True)

        with right:
            # Skills breakdown
            st.markdown('<div class="section-header">✅ Matched Skills</div>', unsafe_allow_html=True)
            if matched:
                st.markdown(" ".join([f'<span class="skill-chip-green">{s}</span>' for s in matched]), unsafe_allow_html=True)
            else:
                st.write("No matches found.")

            st.markdown('<div class="section-header">❌ Missing Skills</div>', unsafe_allow_html=True)
            if missing:
                st.markdown(" ".join([f'<span class="skill-chip-red">{s}</span>' for s in missing]), unsafe_allow_html=True)
            else:
                st.success("You have all required skills for this role!")

            st.markdown('<div class="section-header">🛠 All Detected Skills</div>', unsafe_allow_html=True)
            st.markdown(" ".join([f'<span class="skill-chip-blue">{s}</span>' for s in sorted(detected_skills)]), unsafe_allow_html=True)

        # ── CERTIFICATION SUGGESTIONS ──
        if show_certs and missing:
            st.markdown("---")
            st.markdown('<div class="section-header">🎓 Certification Roadmap</div>', unsafe_allow_html=True)
            certs = get_cert_suggestions(missing)
            if certs:
                cols = st.columns(min(len(certs), 3))
                for i, (skill, cert) in enumerate(certs.items()):
                    with cols[i % 3]:
                        st.markdown(f"""
                            <div style='padding:12px; border-radius:10px; border:1px solid #dee2e6; margin-bottom:8px;'>
                                <div style='font-weight:600; color:#e74c3c; font-size:13px'>Missing: {skill}</div>
                                <div style='font-size:13px; margin-top:4px'>📜 {cert}</div>
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No specific certifications mapped for missing skills.")

        # ── RAW TEXT ──
        st.markdown("---")
        with st.expander("📄 View Extracted Resume Text"):
            st.text_area("Raw Content", content, height=300)

else:
    st.info("👆 Upload a PDF resume to get started.")
    
    # Show sample roles while waiting
    st.markdown("### 📋 Supported Role Categories")
    for cat, roles in ROLE_CATEGORIES.items():
        with st.expander(cat):
            for role, skills in roles.items():
                st.markdown(f"**{role}**: {', '.join(skills)}")