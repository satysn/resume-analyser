import pdfplumber
import re
import spacy
from spacy.matcher import PhraseMatcher
import streamlit as st

@st.cache_resource
def load_nlp():
    return spacy.load("en_core_web_sm")

nlp = load_nlp()
# --- DATA: Expanded Role Library ---
SAMPLE_JDS = {
    "Python Developer": ["Python", "Django", "Flask", "SQL", "Git", "REST API", "Docker", "Unit Testing"],
    "Data Scientist": ["Python", "Machine Learning", "Data Analysis", "SQL", "Statistics", "Pandas", "NumPy", "Scikit-learn", "Tableau"],
    "Frontend Developer": ["JavaScript", "React", "HTML", "CSS", "TypeScript", "Tailwind", "Next.js", "Figma"],
    "Backend Developer": ["Node.js", "Java", "Spring Boot", "SQL", "PostgreSQL", "MongoDB", "Redis", "API Design"],
    "Project Manager": ["Leadership", "Communication", "Agile", "Scrum", "Risk Management", "Budgeting", "Excel", "Jira"],
    "Marketing Manager": ["SEO", "Content Strategy", "Google Analytics", "Social Media", "Copywriting", "Email Marketing", "Leadership"]
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
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'(?:(?:\+|0{0,2})91[\s-]?)?[6789]\d{9}|(?:\d{3}[-.\s]??\d{3}[-.\s]??\d{4})'
    emails = re.findall(email_pattern, text)
    phones = re.findall(phone_pattern, text)
    return {
        "email": emails[0] if emails else "Not found",
        "phone": phones[0].strip() if phones else "Not found"
    }

def extract_skills(text, skill_list=None):
    # This function now accepts a specific list to look for, or uses a broad default
    if not skill_list:
        skill_list = [
            "Python", "Java", "C++", "JavaScript", "React", "Node.js", "SQL", "Excel", 
            "Machine Learning", "Data Analysis", "Communication", "Leadership", "Marketing",
            "HTML", "CSS", "Django", "Flask", "Git", "Docker", "Statistics", "Pandas", "Jira"
        ]
    
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(skill) for skill in skill_list]
    matcher.add("SKILL_LIST", patterns)
    
    doc = nlp(text)
    matches = matcher(doc)
    
    found_skills = set()
    for match_id, start, end in matches:
        found_skills.add(doc[start:end].text)
        
    return list(found_skills)

# --- WEBSITE INTERFACE ---

st.set_page_config(page_title="Resume Analyser Pro", layout="wide")
st.title("📄 AI Resume Analyser & Matcher")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("Matching Configuration")
mode = st.sidebar.radio("How would you like to compare?", ["Select a Pre-defined Role", "Paste a Custom JD"])

target_skills = []
selected_role_name = ""

if mode == "Select a Pre-defined Role":
    selected_role_name = st.sidebar.selectbox("Choose Role", list(SAMPLE_JDS.keys()))
    target_skills = SAMPLE_JDS[selected_role_name]
    st.sidebar.info(f"Targeting: {', '.join(target_skills)}")
else:
    jd_input = st.sidebar.text_area("Paste the Job Description here:")
    selected_role_name = "Custom Role"
    if jd_input:
        # Extract skills from the JD text the user pasted
        target_skills = extract_skills(jd_input)
        st.sidebar.success(f"Extracted {len(target_skills)} skills from your JD.")

# --- MAIN AREA ---
uploaded_file = st.file_uploader("Upload your Resume (PDF)", type="pdf")

if uploaded_file is not None:
    try:
        content = extract_text_from_pdf(uploaded_file)
        
        # STEP 1: Full Text
        with st.expander("Step 1: View Raw Extracted Text"):
            st.text_area("Resume Content", content, height=250)

        # STEP 2: Contact Info
        contact_data = extract_contact_info(content)
        st.header("Step 2: Contact Details")
        c1, c2 = st.columns(2)
        c1.metric("Email Address", contact_data['email'])
        c2.metric("Phone Number", contact_data['phone'])

        # STEP 3: Detailed Skills Analysis
        st.header("Step 3: Skills Analysis")
        
        # 3.1 All Skills found in Resume
        all_detected_skills = extract_skills(content)
        st.subheader("📊 Your Skill Map")
        st.write("These are all the professional skills we detected in your resume:")
        st.info(", ".join(all_detected_skills) if all_detected_skills else "No broad skills detected.")

        # 3.2 Matching Logic
        if target_skills:
            # We compare lowercase to lowercase for accuracy
            resume_lower = [s.lower() for s in all_detected_skills]
            matched = [s for s in target_skills if s.lower() in resume_lower]
            missing = [s for s in target_skills if s.lower() not in resume_lower]
            
            score = int((len(matched) / len(target_skills)) * 100)
            
            st.divider()
            st.subheader(f"🎯 Match Results for: {selected_role_name}")
            st.write(f"### Score: {score}%")
            st.progress(score / 100)

            # Creating three columns for the breakdown
            m1, m2 = st.columns(2)
            
            with m1:
                st.success(f"✅ Matched Skills ({len(matched)})")
                for s in matched:
                    st.write(f"- {s}")
            
            with m2:
                st.error(f"❌ Missing Skills ({len(missing)})")
                for s in missing:
                    st.write(f"- {s}")
        else:
            st.warning("Select a role or paste a JD in the sidebar to see your Match Score.")

    except Exception as e:
        st.error(f"Something went wrong: {e}")