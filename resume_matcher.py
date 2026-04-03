"""
resume_matcher.py
-----------------
Helpers for:
  - Extracting plain text from an uploaded resume (PDF / DOCX)
  - Analysing the resume with LM Studio to derive job-search terms
  - Scoring individual job vacancies against the resume

LM Studio exposes an OpenAI-compatible REST API, so we use the `openai`
library directly instead of the `lmstudio` SDK (which has an anyio 4.x
incompatibility).
"""

import io
import json
import re

from openai import OpenAI

# ── LM Studio connection ───────────────────────────────────────────────────────
LMS_BASE_URL = "http://spark-ehv.ehv.ict.nl:1234/v1"
MODEL_ID     = "openai/gpt-oss-120b"

def _get_client() -> OpenAI:
    return OpenAI(base_url=LMS_BASE_URL, api_key="lm-studio")


def _chat(prompt: str) -> str:
    """Send a single-turn chat request and return the response text."""
    client = _get_client()
    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


# ── Text extraction ────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    import pdfplumber
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    import docx
    doc = docx.Document(io.BytesIO(file_bytes))
    lines = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(lines).strip()


def extract_resume_text(file_bytes: bytes, filename: str) -> str:
    """Dispatch to the right extractor based on file extension."""
    name_lower = filename.lower()
    if name_lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif name_lower.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    elif name_lower.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="replace").strip()
    else:
        raise ValueError(f"Unsupported file type: {filename}. Please upload PDF, DOCX, or TXT.")


# ── LLM helpers ────────────────────────────────────────────────────────────────

def _parse_json(text: str) -> dict:
    """Extract the first JSON object from an LLM response."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


def analyze_resume(resume_text: str) -> dict:
    """
    Ask the LLM to analyse the resume and return structured metadata.

    Returns a dict with keys:
      job_titles, skills, experience_level, summary, search_terms
    """
    prompt = f"""You are a recruitment assistant. Carefully analyse the resume below and extract key information.

--- RESUME START ---
{resume_text[:5000]}
--- RESUME END ---

Reply ONLY with a valid JSON object — no markdown, no explanation — in exactly this format:
{{
  "job_titles": ["Most fitting job title 1", "Most fitting job title 2", "Most fitting job title 3"],
  "skills": ["skill1", "skill2", "skill3", "skill4", "skill5"],
  "experience_level": "junior | mid | senior",
  "summary": "2-sentence professional summary of the candidate.",
  "search_terms": ["best job-board search query 1", "best job-board search query 2", "best job-board search query 3"]
}}

Make search_terms short and specific — they will be used directly in a job-board search."""

    raw = _chat(prompt)
    result = _parse_json(raw)

    # Provide safe defaults if parsing failed
    result.setdefault("job_titles", [])
    result.setdefault("skills", [])
    result.setdefault("experience_level", "unknown")
    result.setdefault("summary", "")
    result.setdefault("search_terms", [])
    return result


def score_job(resume_text: str, job_title: str, job_description: str, company: str = "") -> dict:
    """
    Score how well the resume matches a single job vacancy.

    Returns a dict with keys:
      score (int 0-100), strengths (list), gaps (list), explanation (str)
    """

    desc_snippet = (job_description or "No description available.")[:2500]

    prompt = f"""You are a recruitment AI. Score how well the resume matches the job vacancy below.

JOB TITLE : {job_title}
COMPANY   : {company or "Unknown"}
DESCRIPTION:
{desc_snippet}

--- RESUME START ---
{resume_text[:3500]}
--- RESUME END ---

Reply ONLY with a valid JSON object — no markdown, no explanation:
{{
  "score": <integer 0-100>,
  "strengths": ["reason the candidate is a good fit 1", "reason 2"],
  "gaps": ["missing requirement or gap 1", "gap 2"],
  "explanation": "2-3 sentence overall assessment."
}}"""

    raw = _chat(prompt)
    result = _parse_json(raw)

    result.setdefault("score", 0)
    result.setdefault("strengths", [])
    result.setdefault("gaps", [])
    result.setdefault("explanation", "Could not analyse this vacancy.")
    # Clamp score
    try:
        result["score"] = max(0, min(100, int(result["score"])))
    except (ValueError, TypeError):
        result["score"] = 0
    return result

