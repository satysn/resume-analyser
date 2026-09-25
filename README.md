# 📄 AI Resume Analysis & Optimization Platform

An intelligent, web-based application designed to help candidates evaluate and optimize their resumes for targeted job roles. This tool leverages **Natural Language Processing (NLP)** to extract structured information from resumes and compare them against job requirements, providing actionable insights for improvement.


🚀 Live Demo
🔗 https://resumeanalyser-s9.streamlit.app


✨ Key Features

**📑 PDF Resume Parsing**
  Extracts structured text from PDF resumes using robust parsing techniques.

**📬 Contact Information Extraction**
  Automatically identifies email addresses and phone numbers using regex-based pattern matching.

**🧠 NLP-Based Skill Detection**
  Utilizes **SpaCy** and PhraseMatcher to identify relevant technical and professional skills.

**🎯 Role-Based Matching System**
  Compare resumes against:

  * Predefined industry roles (e.g., Data Scientist, Python Developer)
  * Custom job descriptions entered by the user

**📊 Resume Match Scoring**
  Computes a relevance score based on overlap between candidate skills and job requirements.

**❌ Gap Analysis**
  Clearly highlights:

  * Matched skills
  * Missing skills required for the role

**💡 Resume Optimization Suggestions**
  Provides actionable recommendations to improve alignment with target roles.

**🏆 Auto-Match Mode**
  Scores your resume against every predefined role at once and surfaces your best-fitting matches.

**🩺 Resume Health Check**
  Flags length, bullet-point usage, quantified achievements, action-verb strength, and contact completeness.

**🎓 Certification Roadmap**
  Suggests relevant certifications for each missing skill.

**⬇️ Downloadable Report**
  Export the full analysis — score, matched/missing skills, and health check — as a Markdown report.

**🤖 AI Career Coach (optional)**
  Generates a blunt, specific critique via Gemini — concrete edits, a 30-word elevator pitch, and an underselling strength — gated behind your own free `GEMINI_API_KEY`, called only when you click the button.

🛠️ Tech Stack
* **Language:** Python 3.11
* **Frontend / Interface:** Streamlit
* **NLP Library:** SpaCy (`en_core_web_sm`)
* **PDF Processing:** pdfplumber
* **Deployment:** Streamlit Cloud

## 📂 Project Structure
resume-analyser/
│
├── main.py
├── requirements.txt
└── README.md

⚙️ Installation & Setup
To run this project locally:

1. Clone the repository
git clone https://github.com/satysn/resume-analyser.git
cd resume-analyser
2. Install dependencies
pip install -r requirements.txt
3. (Optional) Enable AI feedback
Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and add a free
Gemini key from https://aistudio.google.com/apikey. Skip this and the app still
works fully — AI feedback is opt-in.
4. Run the application
streamlit run main.py


🧠 How It Works
1. User uploads a resume (PDF format)
2. Text is extracted and processed using NLP techniques
3. Skills are identified using predefined and extracted patterns
4. Resume is compared against selected role or custom job description
5. System outputs:

   * Match Score
   * Matched Skills
   * Missing Skills
   * Improvement Suggestions

📌 Use Cases
* Resume optimization for placements and internships
* Understanding ATS-style screening mechanisms
* Skill gap identification for targeted roles
* Career preparation and self-assessment

🤝 Contributing
Contributions are welcome! Feel free to:
* Fork the repository
* Create feature branches
* Submit pull requests
* Report issues or improvements


📬 Contact
**Satyam Smitodaya Nayak**
BITS Pilani
📧 [f20230843@pilani.bits-pilani.ac.in](mailto:f20230843@pilani.bits-pilani.ac.in)
⭐ If you found this project useful, consider giving it a star!
