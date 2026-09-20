import re
import json
import logging
from typing import Dict, Any, List

from app.core.config import settings


logger = logging.getLogger("resumelab.gemini_service")


# ============================================================
# SKILL CATALOG
# ============================================================

SKILL_CATALOG = [
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "C",
    "Go", "Golang", "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala",
    "R", "Dart", "MATLAB", "Perl", "Bash", "Shell",

    "React", "React.js", "Next.js", "Vue", "Vue.js", "Angular", "Svelte",
    "HTML", "HTML5", "CSS", "CSS3", "Sass", "Tailwind CSS", "Bootstrap",
    "Redux", "Webpack", "Vite", "jQuery",

    "Node.js", "Express", "Express.js", "FastAPI", "Flask", "Django",
    "Spring", "Spring Boot", "ASP.NET", ".NET Core", "Ruby on Rails",
    "NestJS", "GraphQL", "REST API", "gRPC", "Microservices",

    "PostgreSQL", "MySQL", "MongoDB", "SQLite", "Redis", "Elasticsearch",
    "Cassandra", "DynamoDB", "Oracle", "SQL Server", "Firebase",
    "Supabase", "Prisma", "SQLAlchemy", "Hibernate", "Neo4j",

    "AWS", "Amazon Web Services", "Azure", "Microsoft Azure",
    "Google Cloud", "GCP", "Docker", "Kubernetes", "Terraform",
    "CI/CD", "GitHub Actions", "GitLab CI", "Jenkins", "Ansible",
    "Nginx", "Linux", "Serverless", "Lambda", "Cloudflare", "Helm",
    "Prometheus", "Grafana",

    "Machine Learning", "Deep Learning", "Artificial Intelligence",
    "NLP", "Natural Language Processing", "Computer Vision", "LLM",
    "Generative AI", "PyTorch", "TensorFlow", "Keras", "Scikit-Learn",
    "Pandas", "NumPy", "OpenCV", "Hugging Face", "LangChain",
    "LlamaIndex", "BERT", "Transformers",

    "Data Analysis", "Data Science", "Tableau", "Power BI", "BigQuery",
    "Spark", "Kafka",

    "Git", "GitHub", "GitLab", "Bitbucket", "Jira", "Confluence",
    "Postman", "Swagger", "Figma",

    "Agile", "Scrum", "Kanban", "TDD", "Unit Testing", "Jest",
    "Pytest", "Selenium", "Cypress",

    "Leadership", "Project Management", "Problem Solving",
    "Communication", "Team Collaboration", "Time Management",
    "Critical Thinking", "Adaptability", "Mentorship",
    "Public Speaking"
]


# ============================================================
# GEMINI SERVICE
# ============================================================

class GeminiService:

    # --------------------------------------------------------
    # Clean Gemini JSON response
    # --------------------------------------------------------

    @classmethod
    def _clean_json_response(cls, response_text: str) -> str:
        if not response_text:
            return ""

        text = response_text.strip()

        # Remove markdown code fences
        if text.startswith("```"):
            text = re.sub(
                r"^```(?:json)?\s*",
                "",
                text,
                flags=re.IGNORECASE
            )

            text = re.sub(
                r"\s*```$",
                "",
                text
            )

        # Sometimes Gemini adds text before/after JSON.
        # Try to isolate the JSON object.
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1 and end > start:
            text = text[start:end + 1]

        return text.strip()

    # --------------------------------------------------------
    # Empty resume structure
    # --------------------------------------------------------

    @classmethod
    def empty_resume_data(cls) -> Dict[str, Any]:
        return {
            "name": "",
            "email": "",
            "phone": "",
            "summary": "",
            "skills": [],
            "education": [],
            "experience": [],
            "projects": [],
            "certifications": []
        }

    # --------------------------------------------------------
    # Validate / normalize resume response
    # --------------------------------------------------------

    @classmethod
    def _normalize_resume_data(
        cls,
        parsed: Dict[str, Any]
    ) -> Dict[str, Any]:

        result = cls.empty_resume_data()

        if not isinstance(parsed, dict):
            return result

        # Simple fields
        result["name"] = str(parsed.get("name") or "").strip()
        result["email"] = str(parsed.get("email") or "").strip()
        result["phone"] = str(parsed.get("phone") or "").strip()
        result["summary"] = str(parsed.get("summary") or "").strip()

        # ----------------------------------------------------
        # Skills
        # ----------------------------------------------------

        skills = parsed.get("skills", [])

        if isinstance(skills, list):
            result["skills"] = [
                str(skill).strip()
                for skill in skills
                if str(skill).strip()
            ]

        # ----------------------------------------------------
        # Education
        # ----------------------------------------------------

        education = parsed.get("education", [])

        if isinstance(education, list):
            cleaned_education = []

            for item in education:
                if not isinstance(item, dict):
                    continue

                cleaned_education.append({
                    "degree": str(item.get("degree") or "").strip(),
                    "institution": str(
                        item.get("institution") or ""
                    ).strip(),
                    "year": str(item.get("year") or "").strip(),
                    "gpa": str(item.get("gpa") or "").strip()
                })

            result["education"] = cleaned_education

        # ----------------------------------------------------
        # Experience
        # ----------------------------------------------------

        experience = parsed.get("experience", [])

        if isinstance(experience, list):
            cleaned_experience = []

            for item in experience:
                if not isinstance(item, dict):
                    continue

                highlights = item.get("highlights", [])

                if not isinstance(highlights, list):
                    highlights = []

                cleaned_experience.append({
                    "title": str(item.get("title") or "").strip(),
                    "company": str(item.get("company") or "").strip(),
                    "duration": str(item.get("duration") or "").strip(),
                    "location": str(item.get("location") or "").strip(),
                    "highlights": [
                        str(h).strip()
                        for h in highlights
                        if str(h).strip()
                    ]
                })

            result["experience"] = cleaned_experience

        # ----------------------------------------------------
        # Projects
        # ----------------------------------------------------

        projects = parsed.get("projects", [])

        if isinstance(projects, list):
            cleaned_projects = []

            for item in projects:
                if not isinstance(item, dict):
                    continue

                cleaned_projects.append({
                    "name": str(item.get("name") or "").strip(),
                    "tech_stack": str(
                        item.get("tech_stack") or ""
                    ).strip(),
                    "description": str(
                        item.get("description") or ""
                    ).strip(),
                    "link": str(item.get("link") or "").strip()
                })

            result["projects"] = cleaned_projects

        # ----------------------------------------------------
        # Certifications
        # ----------------------------------------------------

        certifications = parsed.get("certifications", [])

        if isinstance(certifications, list):
            result["certifications"] = [
                str(cert).strip()
                for cert in certifications
                if str(cert).strip()
            ]

        return result

    # ========================================================
    # RESUME PARSER
    # ========================================================

    @classmethod
    def parse_resume(cls, resume_text: str) -> Dict[str, Any]:

        if not resume_text or not resume_text.strip():
            logger.warning("Resume text is empty.")
            return cls.empty_resume_data()

        resume_text = resume_text.strip()

        api_key = (settings.GEMINI_API_KEY or "").strip()

        if not api_key:
            logger.error(
                "GEMINI_API_KEY is missing. "
                "Returning empty resume data instead of fake data."
            )

            return cls.fallback_parse_resume(resume_text)

        # ----------------------------------------------------
        # STRICT GEMINI PROMPT
        # ----------------------------------------------------

        prompt = f"""
You are a strict ATS resume parser.

Your job is to extract ONLY information that is explicitly
present in the provided resume text.

DO NOT INVENT ANY INFORMATION.

CRITICAL RULES:

1. Never invent a company name.
2. Never invent a job title.
3. Never invent employment dates.
4. Never invent a location.
5. Never invent a university or college.
6. Never invent a degree.
7. Never invent GPA.
8. Never invent a project.
9. Never invent a certification.
10. Never invent a skill.
11. Never assume information that is not present.
12. Do not use generic/sample information.
13. Do not use information from this instruction as candidate data.
14. If a field is not present, return an empty string.
15. If a list section is not present, return an empty array.
16. Preserve actual company names, job titles and dates from
    the resume.
17. Do not create duplicate experience records.
18. Do not convert unrelated text into work experience.
19. Do not convert skills into experience.
20. Do not convert education into experience.
21. Return ONLY valid JSON.
22. Do not return markdown.
23. Do not return ```json.
24. Do not add explanations outside JSON.

IMPORTANT:
The resume text may have been extracted using OCR.
There may be spelling mistakes or broken lines.
Use context from nearby text to understand OCR errors,
but DO NOT invent missing information.

Return exactly this JSON structure:

{{
    "name": "",
    "email": "",
    "phone": "",
    "summary": "",

    "skills": [],

    "education": [
        {{
            "degree": "",
            "institution": "",
            "year": "",
            "gpa": ""
        }}
    ],

    "experience": [
        {{
            "title": "",
            "company": "",
            "duration": "",
            "location": "",
            "highlights": []
        }}
    ],

    "projects": [
        {{
            "name": "",
            "tech_stack": "",
            "description": "",
            "link": ""
        }}
    ],

    "certifications": []
}}

RESUME TEXT START
-----------------
{resume_text}
-----------------
RESUME TEXT END
"""

        try:

            # ------------------------------------------------
            # NEW GOOGLE GENAI SDK
            # ------------------------------------------------

            from google import genai

            client = genai.Client(api_key=api_key)

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )

            raw_reply = response.text or ""

            logger.info(
                "Gemini resume parsing response received."
            )

            # ------------------------------------------------
            # JSON CLEANING
            # ------------------------------------------------

            clean_json = cls._clean_json_response(raw_reply)

            if not clean_json:
                raise ValueError(
                    "Gemini returned an empty response."
                )

            parsed = json.loads(clean_json)

            result = cls._normalize_resume_data(parsed)

            logger.info(
                "Resume successfully parsed by Gemini."
            )

            return result

        except json.JSONDecodeError as e:

            logger.exception(
                "Gemini returned invalid JSON: %s",
                e
            )

            # IMPORTANT:
            # Do NOT return fake resume data.
            return cls.fallback_parse_resume(resume_text)

        except Exception as e:

            logger.exception(
                "Gemini resume parsing failed: %s",
                e
            )

            # IMPORTANT:
            # Do NOT return fake data.
            return cls.fallback_parse_resume(resume_text)

    # ========================================================
    # SAFE FALLBACK PARSER
    # ========================================================

    @classmethod
    def fallback_parse_resume(
        cls,
        text: str
    ) -> Dict[str, Any]:

        result = cls.empty_resume_data()

        if not text:
            return result

        text = text.strip()

        # ----------------------------------------------------
        # EMAIL
        # ----------------------------------------------------

        email_match = re.search(
            r"\b[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            text
        )

        if email_match:
            result["email"] = email_match.group(0)

        # ----------------------------------------------------
        # PHONE
        # ----------------------------------------------------

        phone_patterns = [
            r"\+\d{1,3}[\s-]?\d{10}",
            r"\+\d{1,3}[\s-]?\d{3}[\s-]?\d{3}[\s-]?\d{4}",
            r"\b\d{10}\b"
        ]

        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)

            if phone_match:
                result["phone"] = phone_match.group(0)
                break

        # ----------------------------------------------------
        # NAME
        # ----------------------------------------------------

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        for line in lines[:10]:

            if "@" in line:
                continue

            if re.search(r"\d", line):
                continue

            if re.search(
                r"\b(resume|cv|curriculum vitae|profile|"
                r"objective|summary)\b",
                line,
                re.IGNORECASE
            ):
                continue

            words = line.split()

            if 2 <= len(words) <= 5:
                result["name"] = line
                break

        # ----------------------------------------------------
        # SKILLS
        # ----------------------------------------------------

        found_skills = []

        for skill in SKILL_CATALOG:

            pattern = (
                r"(?<!\w)"
                + re.escape(skill)
                + r"(?!\w)"
            )

            if re.search(
                pattern,
                text,
                re.IGNORECASE
            ):

                if skill not in found_skills:
                    found_skills.append(skill)

        result["skills"] = found_skills

        # ----------------------------------------------------
        # IMPORTANT
        #
        # Do NOT fabricate:
        #
        # education
        # experience
        # projects
        # certifications
        #
        # They remain empty if Gemini is unavailable.
        # ----------------------------------------------------

        result["education"] = []
        result["experience"] = []
        result["projects"] = []
        result["certifications"] = []

        return result

    # ========================================================
    # ATS ANALYSIS
    # ========================================================

    @classmethod
    def analyze_ats(
        cls,
        resume_text: str,
        resume_data: Dict[str, Any],
        job_description: str
    ) -> Dict[str, Any]:

        api_key = (settings.GEMINI_API_KEY or "").strip()

        if not api_key:
            return cls.fallback_ats_analysis(
                resume_text,
                resume_data,
                job_description
            )

        prompt = f"""
You are an ATS algorithm and technical recruiter.

Compare the candidate resume against the job description.

Use ONLY the information actually present in the resume.

Do not invent candidate skills or experience.

RESUME:

Name:
{resume_data.get("name", "")}

Skills:
{", ".join(resume_data.get("skills", []))}

Experience:
{json.dumps(resume_data.get("experience", []))}

Education:
{json.dumps(resume_data.get("education", []))}

Projects:
{json.dumps(resume_data.get("projects", []))}

Resume Text:
{resume_text[:8000]}


JOB DESCRIPTION:

{job_description}


Return ONLY valid JSON:

{{
    "ats_score": 0,
    "job_title_detected": "",
    "matched_skills": [],
    "missing_skills": [],
    "matched_keywords": [],
    "missing_keywords": [],
    "strengths": [],
    "improvement_suggestions": [],
    "summary_assessment": ""
}}
"""

        try:

            from google import genai

            client = genai.Client(api_key=api_key)

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )

            raw_reply = response.text or ""

            clean_json = cls._clean_json_response(
                raw_reply
            )

            parsed = json.loads(clean_json)

            score = int(
                parsed.get("ats_score", 0)
            )

            parsed["ats_score"] = max(
                0,
                min(100, score)
            )

            return parsed

        except Exception as e:

            logger.exception(
                "Gemini ATS analysis failed: %s",
                e
            )

            return cls.fallback_ats_analysis(
                resume_text,
                resume_data,
                job_description
            )

    # ========================================================
    # FALLBACK ATS
    # ========================================================

    @classmethod
    def fallback_ats_analysis(
        cls,
        resume_text: str,
        resume_data: Dict[str, Any],
        job_description: str
    ) -> Dict[str, Any]:

        jd_lower = (
            job_description or ""
        ).lower()

        resume_lower = (
            resume_text or ""
        ).lower()

        resume_lower += " " + " ".join(
            resume_data.get("skills", [])
        ).lower()

        # ----------------------------------------------------
        # Detect skills from JD
        # ----------------------------------------------------

        jd_skills = []

        for skill in SKILL_CATALOG:

            pattern = (
                r"(?<!\w)"
                + re.escape(skill.lower())
                + r"(?!\w)"
            )

            if re.search(
                pattern,
                jd_lower
            ):
                jd_skills.append(skill)

        # ----------------------------------------------------
        # Candidate skills
        # ----------------------------------------------------

        candidate_skills = set(
            resume_data.get("skills", [])
        )

        for skill in SKILL_CATALOG:

            pattern = (
                r"(?<!\w)"
                + re.escape(skill.lower())
                + r"(?!\w)"
            )

            if re.search(
                pattern,
                resume_lower
            ):
                candidate_skills.add(skill)

        # ----------------------------------------------------
        # Matched / missing skills
        # ----------------------------------------------------

        matched_skills = [
            skill
            for skill in jd_skills
            if (
                skill in candidate_skills
                or skill.lower() in resume_lower
            )
        ]

        missing_skills = [
            skill
            for skill in jd_skills
            if skill not in matched_skills
        ]

        # ----------------------------------------------------
        # Keywords
        # ----------------------------------------------------

        keywords_pool = [
            "scalability",
            "performance",
            "architecture",
            "security",
            "optimization",
            "collaboration",
            "cross-functional",
            "mentorship",
            "deliverables",
            "stakeholders",
            "lifecycle",
            "compliance",
            "automation",
            "debugging",
            "system design",
            "best practices"
        ]

        jd_keywords = [
            keyword
            for keyword in keywords_pool
            if keyword in jd_lower
        ]

        matched_keywords = [
            keyword
            for keyword in jd_keywords
            if keyword in resume_lower
        ]

        missing_keywords = [
            keyword
            for keyword in jd_keywords
            if keyword not in matched_keywords
        ]

        # ----------------------------------------------------
        # Score
        # ----------------------------------------------------

        skill_ratio = (
            len(matched_skills)
            / max(len(jd_skills), 1)
        )

        keyword_ratio = (
            len(matched_keywords)
            / max(len(jd_keywords), 1)
            if jd_keywords
            else 0
        )

        ats_score = int(
            (skill_ratio * 70)
            + (keyword_ratio * 20)
            + 10
        )

        ats_score = max(
            0,
            min(100, ats_score)
        )

        # ----------------------------------------------------
        # Suggestions
        # ----------------------------------------------------

        suggestions = []

        if missing_skills:

            suggestions.append(
                "Consider adding relevant missing skills: "
                + ", ".join(missing_skills[:5])
                + "."
            )

        if missing_keywords:

            suggestions.append(
                "Consider naturally incorporating relevant "
                "job-description keywords: "
                + ", ".join(missing_keywords[:5])
                + "."
            )

        suggestions.append(
            "Quantify achievements with measurable results."
        )

        suggestions.append(
            "Align the professional summary with the target role."
        )

        # ----------------------------------------------------
        # Strengths
        # ----------------------------------------------------

        strengths = []

        if matched_skills:

            strengths.append(
                "Technical skill overlap includes: "
                + ", ".join(matched_skills[:5])
                + "."
            )

        if resume_data.get("experience"):

            strengths.append(
                "Work experience is available for ATS analysis."
            )

        if resume_data.get("projects"):

            strengths.append(
                "Projects provide additional technical evidence."
            )

        if not strengths:

            strengths.append(
                "Resume text is available for keyword analysis."
            )

        # ----------------------------------------------------
        # Job title
        # ----------------------------------------------------

        jd_lines = [
            line.strip()
            for line in job_description.splitlines()
            if line.strip()
        ]

        job_title = (
            jd_lines[0][:100]
            if jd_lines
            else "Target Position"
        )

        return {
            "ats_score": ats_score,
            "job_title_detected": job_title,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "strengths": strengths,
            "improvement_suggestions": suggestions,
            "summary_assessment": (
                f"The candidate matches "
                f"{len(matched_skills)} of "
                f"{len(jd_skills)} detected technical "
                f"skills with an estimated ATS score "
                f"of {ats_score}%."
            )
        }

    # ========================================================
    # CAREER CHAT ASSISTANT
    # ========================================================

    @classmethod
    def chat_career_assistant(
        cls,
        user_message: str,
        resume_context: Dict[str, Any],
        history: List[Dict[str, str]]
    ) -> str:

        api_key = (settings.GEMINI_API_KEY or "").strip()

        if not api_key:
            return cls.fallback_chat_assistant(
                user_message,
                resume_context
            )

        system_instruction = f"""
You are ResumeLab AI.

You are an expert:
- Career Coach
- Technical Recruiter
- ATS Specialist
- Resume Writer

You are helping this candidate.

Candidate Name:
{resume_context.get("name", "Candidate")}

Skills:
{", ".join(resume_context.get("skills", []))}

Summary:
{resume_context.get("summary", "")}

Experience:
{json.dumps(resume_context.get("experience", []))[:5000]}

Education:
{json.dumps(resume_context.get("education", []))[:3000]}

Projects:
{json.dumps(resume_context.get("projects", []))[:3000]}

IMPORTANT:
Use only the candidate information provided above.
Do not invent experience, companies, degrees, projects,
certifications or achievements.

Give practical and actionable career advice.

When rewriting resume bullets:
- Use strong action verbs.
- Use STAR where appropriate.
- Never invent metrics.
- If metrics are unavailable, use placeholders such as [X%].
"""

        messages_prompt = (
            system_instruction
            + "\n\nCONVERSATION HISTORY:\n"
        )

        for history_item in history[-6:]:

            role = history_item.get(
                "role",
                "user"
            )

            content = history_item.get(
                "content",
                ""
            )

            messages_prompt += (
                f"{role.upper()}: {content}\n"
            )

        messages_prompt += (
            f"\nUSER: {user_message}\n"
            f"ASSISTANT:"
        )

        try:

            from google import genai

            client = genai.Client(api_key=api_key)

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=messages_prompt
            )

            return (
                response.text or ""
            ).strip()

        except Exception as e:

            logger.exception(
                "Gemini career assistant failed: %s",
                e
            )

            return cls.fallback_chat_assistant(
                user_message,
                resume_context
            )

    # ========================================================
    # FALLBACK CAREER CHAT
    # ========================================================

    @classmethod
    def fallback_chat_assistant(
        cls,
        message: str,
        resume_context: Dict[str, Any]
    ) -> str:

        msg_lower = (
            message or ""
        ).lower()

        name = (
            resume_context.get("name")
            or "there"
        )

        skills = resume_context.get(
            "skills",
            []
        )

        if (
            "star" in msg_lower
            or "bullet" in msg_lower
            or "rewrite" in msg_lower
        ):

            return f"""
### STAR Resume Bullet Guidance

For {name}, use this structure:

**Action Verb + Challenge/Task + Action + Result**

Do not invent metrics.

Example:

**Before:**
Worked on backend APIs.

**Better:**
Developed and maintained backend APIs using
[TECHNOLOGY], improving [METRIC/RESULT].

Replace the placeholders with real information
from your experience.
"""

        if (
            "skill" in msg_lower
            or "learn" in msg_lower
        ):

            skill_list = (
                ", ".join(skills[:5])
                if skills
                else "your current technical skills"
            )

            return f"""
### Skill Development

Your currently detected skills include:

{skill_list}

Focus your next learning choices on skills that
appear frequently in the job descriptions for
your target role.

Do not add a skill to your resume until you
actually have experience with it.
"""

        if (
            "interview" in msg_lower
            or "prep" in msg_lower
        ):

            return f"""
### Interview Preparation

For {name}, prepare:

1. A 60-second introduction.
2. 3 technical project explanations.
3. 3 STAR behavioral examples.
4. Questions about your strongest technical skills.
5. Questions about trade-offs and debugging.
6. Questions about your actual project architecture.

Do not memorize fake metrics or technologies.
Use only things you actually worked with.
"""

        skill_list = (
            ", ".join(skills[:4])
            if skills
            else "your detected skills"
        )

        return f"""
Hello {name}.

I can help you with:

- Resume bullet rewriting
- ATS optimization
- Job-description matching
- Interview preparation
- Career planning
- Technical skill development

Your currently detected skills include:
{skill_list}

Ask me what you want to improve.
"""