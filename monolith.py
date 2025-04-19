import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import pdfplumber
from groq import Groq
from flask import Flask, request, jsonify

# Constants for LLM
LLM_MODEL = "llama-3.3-70b-versatile"
LLM_TEMPERATURE = 0.2
DEFAULT_GROQ_API_KEY = "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"

app = Flask(__name__)

# -----------------------------
# LLM Client
# -----------------------------
class LLMClient:
    def __init__(self, api_key: str, model: str = LLM_MODEL, temperature: float = LLM_TEMPERATURE):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def complete(self, prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            max_tokens=1024,
            top_p=0.95,
            stream=False
        )
        return resp.choices[0].message.content.strip()

# -----------------------------
# Utility Functions
# -----------------------------
def parse_document(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        with pdfplumber.open(str(file_path)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    else:
        return file_path.read_text(encoding="utf-8")

def clean_text(raw_text: str) -> str:
    text = re.sub(r'\r\n?', "\n", raw_text)
    text = re.sub(r'\n{2,}', "\n\n", text)
    return text.strip()

# -----------------------------
# Requirement Extraction
# -----------------------------
def extract_requirements_llm(clean_txt: str, llm: LLMClient) -> Optional[List[Dict[str, Any]]]:
    prompt = (
        "Extract each functional requirement from the text below."
        " Output as a JSON array of objects with fields `id` (R1, R2, …) and `text`.\n\n"
        f"{clean_txt}"
    )
    try:
        raw = llm.complete(prompt)
        return json.loads(raw)
    except Exception:
        return None

def extract_requirements_regex(clean_txt: str) -> List[Dict[str, Any]]:
    lines = clean_txt.splitlines()
    reqs = []
    counter = 1
    for line in lines:
        if re.search(r'\b(shall|must|should|may|require)\b', line, re.IGNORECASE):
            reqs.append({"id": f"R{counter}", "text": line.strip()})
            counter += 1
    return reqs

# -----------------------------
# Scenario Generation
# -----------------------------
def generate_test_scenarios(requirements: List[Dict[str, Any]], llm: LLMClient) -> Dict[str, str]:
    scenarios = {}
    for req in requirements:
        prompt = (
            "You are a QA engineer. For the following requirement, list all possible test scenarios grouped by:\n"
            "1. Positive / Happy Path\n2. Negative / Edge Cases\n"
            "3. Error & Exception Handling\n4. Security & Performance Considerations\n\n"
            f"Requirement: \"{req['text']}\""
        )
        scenarios[req['id']] = llm.complete(prompt)
    return scenarios

def format_output(
    source_file: str,
    requirements: List[Dict[str, Any]],
    test_scenarios: Dict[str, str]
) -> Dict[str, Any]:
    output = {
        "source_file": source_file,
        "requirements_count": len(requirements),
        "results": {}
    }
    for req in requirements:
        rid = req['id']
        output['results'][rid] = {
            "requirement": req,
            "scenarios": test_scenarios.get(rid, "")
        }
    return output

# -----------------------------
# Flask API Endpoint
# -----------------------------
@app.route('/generate-test-scenarios', methods=['POST'])
def generate_test_scenarios_endpoint():
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({"error": "No file provided"}), 400

    upload_dir = Path("uploaded_requirements")
    upload_dir.mkdir(exist_ok=True)
    temp_path = upload_dir / file.filename
    file.save(str(temp_path))

    raw = parse_document(temp_path)
    clean = clean_text(raw)

    llm = LLMClient(api_key=DEFAULT_GROQ_API_KEY)
    reqs = extract_requirements_llm(clean, llm) or extract_requirements_regex(clean)
    scenarios = generate_test_scenarios(reqs, llm)
    result = format_output(str(temp_path), reqs, scenarios)

    return jsonify(result)

# -----------------------------
# Only Run Flask Server
# -----------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)