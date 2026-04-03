"""
resume_matcher.py
-----------------
Helpers for:
  - Extracting plain text from an uploaded resume (PDF / DOCX / TXT)
  - Analysing the resume with Azure OpenAI (gpt-4.1)
  - Scoring individual job vacancies against the resume

Authentication: API key (read from AZURE_OPENAI_API_KEY env var / Streamlit secret).
"""

import io
import json
import os
import re

# ── Config (env vars / Streamlit secrets) ─────────────────────────────────────
endpoint         = os.getenv("ENDPOINT_URL",         "https://centerofexcellence.openai.azure.com/")
deployment       = os.getenv("DEPLOYMENT_NAME",       "gpt-4.1")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY",  "REPLACE_WITH_YOUR_KEY_VALUE_HERE")


def _get_client():
    """Build the AzureOpenAI client with key-based authentication (lazy import)."""
    from openai import AzureOpenAI
    return AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=subscription_key,
        api_version="2025-01-01-preview",
    )


# ── LLM helper ─────────────────────────────────────────────────────────────────

def _chat(prompt: str) -> str:
    """Send a single-turn chat request and return the response text."""
    client = _get_client()

    chat_prompt = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": "You are an AI assistant that helps people find information.",
                }
            ],
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    completion = client.chat.completions.create(
        model=deployment,
        messages=chat_prompt,
        max_tokens=32768,
        temperature=0.7,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
        stream=False,
    )
    return completion.choices[0].message.content or ""



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

