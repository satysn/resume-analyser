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

DEFAULT_SKILLS = [
    "Python", "Java", "C++", "JavaScript", "React", "Node.js", "SQL", "Excel",
    "AWS", "Docker", "Agile", "SEO", "Figma", "TensorFlow", "PyTorch", "Pandas",
    "Git", "Linux", "TypeScript", "Kubernetes", "MongoDB", "PostgreSQL", "Flask",
    "Django", "Machine Learning", "Deep Learning", "NLP", "Statistics", "Tableau",
    "Power BI", "Swift", "Kotlin", "Flutter", "Scrum", "Leadership", "Communication",
    "HTML", "CSS",
]

# Master skill vocabulary used to detect skills present in a resume: every skill
# named anywhere in ROLE_CATEGORIES, plus the general defaults above. Without this,
# skill detection would only ever look for the 35 default skills, so anything a
# specific role needs (e.g. Terraform, Kafka, Jira) could never be found in a
# resume even when it's clearly there, silently corrupting every match score.
ALL_SKILLS = sorted(set(
    DEFAULT_SKILLS
    + [skill for roles in ROLE_CATEGORIES.values() for reqs in roles.values() for skill in reqs]
))

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

NAME_STOPWORDS = {
    "curriculum vitae", "resume", "cv", "profile", "summary", "objective",
    "contact", "personal details", "professional summary", "career objective",
}

def extract_contact_info(text):
    email = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    phone = re.findall(r'(?:(?:\+|0{0,2})91[\s-]?)?[6789]\d{9}', text)
    if not phone:
        phone = re.findall(r'(?:\+?\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b', text)

    name = "Candidate"
    for line in text.strip().splitlines()[:8]:
        line = line.strip()
        if not line or line.lower() in NAME_STOPWORDS:
            continue
        if "@" in line or any(ch.isdigit() for ch in line):
            continue
        match = re.match(r'^([A-Z][a-zA-Z.\'-]+(?:\s+[A-Z][a-zA-Z.\'-]+){1,3})$', line)
        if match and len(match.group(1)) <= 40:
            name = match.group(1)
            break

    return {
        "email": email[0] if email else "Not found",
        "phone": phone[0] if phone else "Not found",
        "name": name
    }

def extract_skills(text, skill_list=None):
    if not skill_list:
        skill_list = ALL_SKILLS
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(skill) for skill in skill_list]
    matcher.add("SKILL_LIST", patterns)
    doc = nlp(text)
    matches = matcher(doc)
    return list(set([doc[start:end].text for _, start, end in matches]))

def estimate_experience(text):
    years = re.findall(r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?experience', text, re.IGNORECASE)
    if years:
        return max(int(y) for y in years)
    # count job sections as a rough proxy
    jobs = len(re.findall(r'\b(20\d{2})\b', text))
    return min(jobs // 2, 10)

ACTION_VERBS = [
    "led", "built", "developed", "designed", "implemented", "created", "managed",
    "launched", "improved", "increased", "reduced", "optimized", "architected",
    "automated", "delivered", "drove", "spearheaded", "streamlined", "achieved",
    "collaborated", "coordinated", "analyzed", "engineered", "deployed", "mentored",
]

def analyze_resume_quality(text):
    words = re.findall(r'\b\w+\b', text)
    word_count = len(words)
    bullets = re.findall(r'(?m)^[\s]*[•▪●·\-\*]\s*(.+)$', text)
    quantified = [b for b in bullets if re.search(r'\d', b)]
    verb_bullets = [b for b in bullets if re.match(r'^\s*(?:\w+ed|\w+d)\b', b, re.IGNORECASE)
                     or any(b.strip().lower().startswith(v) for v in ACTION_VERBS)]

    checks = []
    checks.append({
        "label": "Resume length",
        "passed": 200 <= word_count <= 1200,
        "detail": f"{word_count} words. Recruiters skim, they don't read — 300–800 words keeps it to one or two pages."
    })
    checks.append({
        "label": "Uses bullet points",
        "passed": len(bullets) >= 3,
        "detail": f"{len(bullets)} bullet points found. Dense paragraphs get skipped; bullets get read."
    })
    checks.append({
        "label": "Quantified achievements",
        "passed": len(quantified) >= max(1, len(bullets) // 3),
        "detail": f"{len(quantified)}/{len(bullets) or 0} bullets include a number (e.g. \"cut load time by 30%\") instead of just a claim."
    })
    checks.append({
        "label": "Starts bullets with action verbs",
        "passed": len(verb_bullets) >= max(1, len(bullets) // 2),
        "detail": f"{len(verb_bullets)}/{len(bullets) or 0} bullets open with a strong verb like \"built\" or \"led\" instead of \"responsible for\"."
    })
    checks.append({
        "label": "Has an email address",
        "passed": bool(re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)),
        "detail": "If a recruiter can't find your email in five seconds, they're not going to look for it."
    })

    score = int(100 * sum(1 for c in checks if c["passed"]) / len(checks))
    return {"score": score, "checks": checks, "word_count": word_count, "bullet_count": len(bullets)}

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

def render_quality_section(quality):
    st.markdown("---")
    st.markdown('<div class="section-header">🩺 Resume Health Check</div>', unsafe_allow_html=True)
    color = "#10B981" if quality["score"] >= 80 else "#F59E0B" if quality["score"] >= 50 else "#F43F5E"
    st.markdown(f"**Overall score: <span style='color:{color}'>{quality['score']}/100</span>**", unsafe_allow_html=True)
    cols = st.columns(2)
    for i, check in enumerate(quality["checks"]):
        icon = "✅" if check["passed"] else "⚠️"
        with cols[i % 2]:
            st.markdown(f"""
                <div class="health-card" style="padding:12px 14px; animation-delay:{i * 0.05}s">
                    <div style='font-weight:600; font-size:13px'>{icon} {check['label']}</div>
                    <div style='font-size:12px; opacity:0.75; margin-top:2px'>{check['detail']}</div>
                </div>
            """, unsafe_allow_html=True)

def build_report_markdown(contact, exp_years, detected_skills, quality, selected_role=None, matched=None, missing=None, score=None):
    lines = [f"# Resume Analysis Report — {contact['name']}", ""]
    lines.append(f"- **Email:** {contact['email']}")
    lines.append(f"- **Phone:** {contact['phone']}")
    lines.append(f"- **Estimated experience:** {exp_years} year(s)")
    lines.append("")
    if selected_role and score is not None:
        lines.append(f"## Match Score — {selected_role}: {score}%")
        lines.append("")
        lines.append(f"**Matched skills:** {', '.join(matched) if matched else 'None'}")
        lines.append("")
        lines.append(f"**Missing skills:** {', '.join(missing) if missing else 'None'}")
        lines.append("")
    lines.append(f"## Detected Skills ({len(detected_skills)})")
    lines.append(", ".join(sorted(detected_skills)) or "None detected")
    lines.append("")
    lines.append(f"## Resume Health Check — {quality['score']}/100")
    for check in quality["checks"]:
        mark = "x" if check["passed"] else " "
        lines.append(f"- [{mark}] {check['label']} — {check['detail']}")
    return "\n".join(lines)

# =====================
# --- UI STARTS HERE ---
# =====================

st.set_page_config(page_title="Resume Matcher Pro", layout="wide", page_icon="🎯")

# Custom theme. Streamlit's own widgets (radio, uploader, buttons, alerts...) are
# targeted through their data-testid attributes, which are stable across Streamlit
# releases even though the generated class names underneath are not.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');

/* Only retarget text we fully control. Streamlit's own widgets render icon
   ligatures (e.g. "upload", "arrow_right") through span font-families — a
   blanket font-family override anywhere near them renders those as literal
   text instead of glyphs, so headings/labels/spans are deliberately left alone. */
h1, h2, h3, .app-hero-title, .section-header,
.app-tagline, .app-badge, .stat-card, .role-card, .health-card {
    font-family: 'Inter', sans-serif;
}
h1, h2, h3, .app-hero-title, .section-header {
    font-family: 'Sora', sans-serif !important;
}

[data-testid="stAppViewContainer"] .block-container { padding-top: 2.2rem; max-width: 1180px; }

/* ---------- Hero ---------- */
.app-hero-title {
    font-size: 40px;
    font-weight: 800;
    background: linear-gradient(135deg, #8B5CF6 0%, #10B981 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    line-height: 1.2;
    margin-bottom: 2px;
}
.app-tagline {
    font-size: 15.5px;
    opacity: 0.72;
    max-width: 640px;
    margin: 0 0 14px 0;
    line-height: 1.5;
}
.app-badges { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.app-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(127,127,127,0.07);
    border: 1px solid rgba(127,127,127,0.18);
    padding: 5px 12px; border-radius: 999px;
    font-size: 12.5px; font-weight: 500; opacity: 0.85;
}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] { border-right: 1px solid rgba(127,127,127,0.14); }
[data-testid="stSidebar"] h2 { font-family: 'Sora', sans-serif !important; font-size: 18px; }

/* ---------- Mode selector as pill tabs ---------- */
div[data-testid="stRadio"] > div[role="radiogroup"] { display: flex; flex-direction: column; gap: 6px; }
div[data-testid="stRadio"] label {
    background: rgba(127,127,127,0.06);
    border: 1px solid rgba(127,127,127,0.16);
    border-radius: 10px;
    padding: 10px 14px !important;
    margin: 0 !important;
    cursor: pointer;
    transition: background 0.16s ease, border-color 0.16s ease;
}
div[data-testid="stRadio"] label:hover { background: rgba(16,185,129,0.10); border-color: rgba(16,185,129,0.4); }
div[data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(135deg, rgba(139,92,246,0.18), rgba(16,185,129,0.18));
    border-color: rgba(16,185,129,0.55);
}
div[data-testid="stRadio"] label:has(input:checked) p { font-weight: 700; }
div[data-testid="stRadio"] label > div:first-child { display: none; }

/* ---------- File uploader ---------- */
section[data-testid="stFileUploaderDropzone"] {
    background: rgba(127,127,127,0.05);
    border: 1.5px dashed rgba(127,127,127,0.3);
    border-radius: 14px;
    transition: border-color 0.2s ease, background 0.2s ease;
}
section[data-testid="stFileUploaderDropzone"]:hover { border-color: #10B981; background: rgba(16,185,129,0.06); }

/* ---------- Buttons ---------- */
button[data-testid^="stBaseButton"] { border-radius: 10px !important; transition: transform 0.15s ease, box-shadow 0.15s ease; }
button[data-testid^="stBaseButton"]:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(0,0,0,0.15); }
button[data-testid="stBaseButton-primary"] { background: linear-gradient(135deg, #10B981, #059669) !important; border: none !important; }

/* ---------- Alerts & expanders ---------- */
div[data-testid="stAlert"] { border-radius: 12px; }
div[data-testid="stExpander"] details { border-radius: 12px !important; border: 1px solid rgba(127,127,127,0.16) !important; }

/* ---------- Cards ---------- */
.stat-card {
    background: rgba(127,127,127,0.05);
    border: 1px solid rgba(127,127,127,0.15);
    border-radius: 14px;
    padding: 14px 16px;
    animation: fadeInUp 0.4s ease both;
}
.stat-card .stat-icon { font-size: 19px; }
.stat-card .stat-label { font-size: 12px; opacity: 0.62; margin-top: 3px; }
.stat-card .stat-value { font-size: 17px; font-weight: 700; margin-top: 2px; overflow-wrap: anywhere; }

.role-card, .health-card {
    background: rgba(127,127,127,0.05);
    border: 1px solid rgba(127,127,127,0.15);
    border-radius: 14px;
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
    animation: fadeInUp 0.45s ease both;
}
.role-card:hover, .health-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 24px rgba(0,0,0,0.12);
    border-color: rgba(16,185,129,0.4);
}

.section-header {
    font-size: 17px;
    font-weight: 700;
    margin: 22px 0 12px 0;
    padding-left: 12px;
    border-left: 4px solid #10B981;
}

/* ---------- Skill chips ---------- */
.skill-chip-green, .skill-chip-red, .skill-chip-blue {
    display: inline-flex; align-items: center;
    padding: 5px 13px; border-radius: 999px;
    font-size: 13px; font-weight: 500; margin: 3px;
    transition: transform 0.15s ease;
}
.skill-chip-green:hover, .skill-chip-red:hover, .skill-chip-blue:hover { transform: scale(1.06); }
.skill-chip-green { background: rgba(16,185,129,0.16); color: #10B981; border: 1px solid rgba(16,185,129,0.35); }
.skill-chip-red { background: rgba(244,63,94,0.14); color: #F43F5E; border: 1px solid rgba(244,63,94,0.35); }
.skill-chip-blue { background: rgba(139,92,246,0.14); color: #8B5CF6; border: 1px solid rgba(139,92,246,0.35); }

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

textarea::-webkit-scrollbar { width: 8px; }
textarea::-webkit-scrollbar-thumb { background: rgba(127,127,127,0.35); border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="app-hero-title">🎯 Resume Matcher Pro</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-tagline">A resume gets about six seconds from a human, and a screening bot before that. '
    "This tells you what both of them will actually see.</div>",
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="app-badges">
        <span class="app-badge">🧠 spaCy NLP, no GPT calls</span>
        <span class="app-badge">⚡ Results in seconds</span>
        <span class="app-badge">🎯 16 roles across 4 fields</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎛 Set Up the Comparison")

    mode = st.radio("Check your resume against", ["A specific role", "A job description", "Every role at once"])
    st.divider()

    target_skills = []
    selected_role = ""

    if mode == "A specific role":
        category = st.selectbox("Field", list(ROLE_CATEGORIES.keys()))
        selected_role = st.selectbox("Role", list(ROLE_CATEGORIES[category].keys()))
        target_skills = ROLE_CATEGORIES[category][selected_role]
        st.info(f"This role typically wants **{len(target_skills)} skills**. Let's see how many you've got.")

    elif mode == "A job description":
        jd_file = st.file_uploader("Upload the JD (PDF or .txt)", type=["pdf", "txt"])
        jd_pasted = st.text_area("...or just paste it in", height=170, placeholder="Paste the job description here.")
        selected_role = st.text_input("What should we call this role?", value="Target Role")

        jd_text = ""
        if jd_file is not None:
            if jd_file.name.lower().endswith(".pdf"):
                jd_text = extract_text_from_pdf(jd_file)
            else:
                jd_text = jd_file.read().decode("utf-8", errors="ignore")
        elif jd_pasted:
            jd_text = jd_pasted

        if jd_text.strip():
            target_skills = extract_skills(jd_text)
            st.success(f"Found **{len(target_skills)}** skills mentioned in that posting.")
        elif jd_file is not None:
            st.warning("Couldn't pull any text out of that file — try pasting the description instead.")

    else:
        st.info("Skip picking a role. Upload your resume below and we'll rank it against everything we track.")
        selected_role = "Auto"

    st.divider()
    show_certs = st.toggle("Suggest certifications for gaps", value=True)

# --- MAIN AREA ---
uploaded_file = st.file_uploader("📄 Drop your resume in (PDF)", type="pdf")

if uploaded_file:
    content = extract_text_from_pdf(uploaded_file)

    if len(content.strip()) < 50:
        st.error(
            "⚠️ Couldn't pull any real text out of this PDF. It's probably a scanned "
            "image or a design-heavy layout with no actual text layer — and if we can't "
            "read it, neither can an ATS. Try exporting straight from Word or Google Docs instead."
        )
        st.stop()

    contact = extract_contact_info(content)
    detected_skills = extract_skills(content)
    exp_years = estimate_experience(content)
    quality = analyze_resume_quality(content)

    # ── TOP STATS ──
    st.markdown("<br>", unsafe_allow_html=True)
    stats = [
        ("👤", "Name", contact["name"]),
        ("📧", "Email", contact["email"]),
        ("📞", "Phone", contact["phone"]),
        ("🛠", "Skills Found", str(len(detected_skills))),
    ]
    cols = st.columns(4)
    for i, (icon, label, value) in enumerate(stats):
        with cols[i]:
            st.markdown(f"""
                <div class="stat-card" style="animation-delay:{i * 0.05}s">
                    <div class="stat-icon">{icon}</div>
                    <div class="stat-label">{label}</div>
                    <div class="stat-value">{value}</div>
                </div>
            """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── AUTO MATCH MODE ──
    if mode == "Every role at once":
        st.markdown('<div class="section-header">🏆 Where You Rank</div>', unsafe_allow_html=True)
        matches = get_best_role_matches(detected_skills)

        cols = st.columns(len(matches))
        for i, match in enumerate(matches):
            with cols[i]:
                color = "#10B981" if match["score"] >= 70 else "#F59E0B" if match["score"] >= 40 else "#F43F5E"
                st.markdown(f"""
                    <div class="role-card" style='text-align:center; padding:16px; animation-delay:{i * 0.06}s'>
                        <div style='font-size:28px; font-weight:700; color:{color}'>{match["score"]}%</div>
                        <div style='font-weight:600; font-size:14px'>{match["role"]}</div>
                        <div style='opacity:0.7; font-size:12px'>{match["category"]}</div>
                        <div style='opacity:0.7; font-size:12px'>{match["matched"]}/{match["total"]} skills</div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("#### 🛠 Skills We Spotted On Your Resume")
        chips = " ".join([f'<span class="skill-chip-blue">{s}</span>' for s in sorted(detected_skills)])
        st.markdown(chips, unsafe_allow_html=True)

        render_quality_section(quality)
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
            color = "#10B981" if score >= 80 else "#F59E0B" if score >= 50 else "#F43F5E"
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=score,
                delta={"reference": 70, "increasing": {"color": "#10B981"}, "decreasing": {"color": "#F43F5E"}},
                title={"text": f"{selected_role} Fit", "font": {"size": 15}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1},
                    "bar": {"color": color},
                    "steps": [
                        {"range": [0, 50], "color": "rgba(244,63,94,0.15)"},
                        {"range": [50, 80], "color": "rgba(245,158,11,0.15)"},
                        {"range": [80, 100], "color": "rgba(16,185,129,0.15)"}
                    ],
                    "threshold": {"line": {"color": "#8B5CF6", "width": 3}, "thickness": 0.75, "value": 70}
                }
            ))
            fig.update_layout(
                height=280, margin=dict(t=40, b=0, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)", font={"color": "#888"},
            )
            st.plotly_chart(fig, use_container_width=True)

            # Radar chart
            if len(target_skills) >= 3:
                categories = target_skills[:8]
                values = [1 if s.lower() in res_lower else 0 for s in categories]
                fig2 = go.Figure(go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    fill='toself',
                    fillcolor='rgba(139,92,246,0.25)',
                    line=dict(color='#8B5CF6')
                ))
                fig2.update_layout(
                    polar=dict(radialaxis=dict(visible=False, range=[0, 1])),
                    showlegend=False, height=280,
                    margin=dict(t=20, b=20, l=40, r=40),
                    title=dict(text="Skill Coverage", font=dict(size=13)),
                    paper_bgcolor="rgba(0,0,0,0)", font={"color": "#888"},
                )
                st.plotly_chart(fig2, use_container_width=True)

        with right:
            # Skills breakdown
            st.markdown('<div class="section-header">✅ You\'ve Got These</div>', unsafe_allow_html=True)
            if matched:
                st.markdown(" ".join([f'<span class="skill-chip-green">{s}</span>' for s in matched]), unsafe_allow_html=True)
            else:
                st.write("None of the required skills showed up here — worth checking if that's accurate.")

            st.markdown('<div class="section-header">❌ Still Missing</div>', unsafe_allow_html=True)
            if missing:
                st.markdown(" ".join([f'<span class="skill-chip-red">{s}</span>' for s in missing]), unsafe_allow_html=True)
            else:
                st.success("Every required skill shows up. You won't get filtered out on skills alone.")

            st.markdown('<div class="section-header">🛠 Everything We Found</div>', unsafe_allow_html=True)
            st.markdown(" ".join([f'<span class="skill-chip-blue">{s}</span>' for s in sorted(detected_skills)]), unsafe_allow_html=True)

        # ── CERTIFICATION SUGGESTIONS ──
        if show_certs and missing:
            st.markdown("---")
            st.markdown('<div class="section-header">🎓 Ways to Close the Gap</div>', unsafe_allow_html=True)
            certs = get_cert_suggestions(missing)
            if certs:
                cols = st.columns(min(len(certs), 3))
                for i, (skill, cert) in enumerate(certs.items()):
                    with cols[i % 3]:
                        st.markdown(f"""
                            <div class="health-card" style="padding:12px 14px; animation-delay:{i * 0.05}s">
                                <div style='font-weight:600; color:#F43F5E; font-size:13px'>Missing: {skill}</div>
                                <div style='font-size:13px; margin-top:4px'>📜 {cert}</div>
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("Nothing's mapped to a certification here — but they're still worth learning either way.")

        render_quality_section(quality)

        # ── DOWNLOAD REPORT ──
        st.markdown("---")
        report = build_report_markdown(contact, exp_years, detected_skills, quality, selected_role, matched, missing, score)
        st.download_button(
            "⬇️ Get the Full Report",
            data=report,
            file_name=f"{contact['name'].replace(' ', '_')}_resume_report.md",
            mime="text/markdown",
        )

        # ── RAW TEXT ──
        with st.expander("📄 See What We Actually Read From Your PDF"):
            st.text_area("Raw Content", content, height=300)

    else:
        st.warning("Pick a role or drop in a job description on the left — we need something to compare against.")
        render_quality_section(quality)

else:
    st.info("👈 Nothing to check yet. Upload a resume above and pick how you want it compared on the left.")

    # Show sample roles while waiting
    st.markdown("### 📋 What We Can Check You Against")
    for cat, roles in ROLE_CATEGORIES.items():
        with st.expander(cat):
            for role, skills in roles.items():
                st.markdown(f"**{role}**: {', '.join(skills)}")