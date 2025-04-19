import os
import json
import requests
import re
from typing import List, Dict, Any, Tuple
import nltk
from nltk.tokenize import sent_tokenize
import itertools
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Ensure NLTK data is available and downloaded
nltk_data_path = os.environ.get('NLTK_DATA', os.path.join(os.path.expanduser('~'), 'nltk_data'))
nltk.data.path.append(nltk_data_path)
for pkg in ['punkt', 'punkt_tab']:
    try:
        nltk.data.find(f'tokenizers/{pkg}')
    except LookupError:
        nltk.download(pkg, quiet=True, download_dir=nltk_data_path)

class RequirementsConsistencyChecker:
    def __init__(self, api_key: str = None, model_name: str = "gpt2"):
        """
        Initialize the requirements consistency checker with API credentials.
        """
        self.api_key = api_key
        self.model_name = model_name
        self.api_url = f"https://api-inference.huggingface.co/models/{model_name}"
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self.token_limit = 1024  # Reduced token limit for smaller models
        self.max_chunk_size = 5  # Reduced chunk size for free tier
        self.use_mock = True  # Set to True to use mock responses instead of API calls

    def process_large_document(self, file_path: str) -> Dict[str, Any]:
        requirements = self.extract_requirements(file_path)
        if not requirements:
            return {"is_consistent": False, "error": "No valid requirements found in the document"}
        requirement_chunks = self.create_requirement_chunks(requirements)
        chunk_results = []
        for chunk in requirement_chunks:
            result = self.analyze_requirements(chunk)
            chunk_results.append(result)
        cross_chunk_results = self.analyze_cross_chunk_consistency(requirements)
        return self.consolidate_results(chunk_results, cross_chunk_results)

    def _read_file_safely(self, file_path: str) -> str:
        """Read a text file trying multiple encodings, normalize to UTF-8."""
        with open(file_path, 'rb') as f:
            raw = f.read()
        for enc in ('utf-8', 'latin-1', 'cp1252'):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        # Fallback, replace undecodable bytes
        return raw.decode('utf-8', errors='replace')

    def extract_requirements(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            text = self._read_file_safely(file_path)
            structured_requirements = []
            # Explicit numbering pattern
            req_pattern = re.compile(r'(?:REQ|R|Requirement)[-\s]?(\d+[\.\d]*)[:\s]+(.+?)(?=(?:REQ|R|Requirement)[-\s]?\d+|$)', re.DOTALL)
            matches = req_pattern.findall(text)
            if matches:
                for req_id, content in matches:
                    content = content.strip()
                    if content:
                        structured_requirements.append({"id": f"R{req_id}", "text": content})
            else:
                # Fallback: sentence tokenize
                try:
                    sentences = sent_tokenize(text)
                except LookupError:
                    nltk.download('punkt', quiet=True, download_dir=nltk_data_path)
                    sentences = sent_tokenize(text)
                keywords = ["shall", "must", "should", "will", "requires", "needs to", "has to"]
                for i, sentence in enumerate(sentences):
                    s = sentence.strip()
                    if any(k in s.lower() for k in keywords) and len(s) > 15:
                        structured_requirements.append({"id": f"R{i+1}", "text": s})
            return structured_requirements
        except Exception as e:
            print(f"Error extracting requirements: {e}")
            return []

    def create_requirement_chunks(self, requirements: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        return [requirements[i:i+self.max_chunk_size] for i in range(0, len(requirements), self.max_chunk_size)]

    def analyze_requirements(self, requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
        prompt = self._prepare_consistency_prompt(requirements)
        response = self._call_llm_api(prompt)
        return self._parse_results(response)

    def analyze_cross_chunk_consistency(self, requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
        related_pairs = self._identify_related_requirements(requirements)
        if not related_pairs:
            return {"is_consistent": True, "inconsistencies": []}
        inconsistencies = []
        for pair in related_pairs:
            prompt = self._prepare_pair_consistency_prompt(pair)
            response = self._call_llm_api(prompt)
            pair_result = self._parse_results(response)
            if not pair_result.get("is_consistent", True):
                inconsistencies.extend(pair_result.get("inconsistencies", []))
        return {"is_consistent": not inconsistencies, "inconsistencies": inconsistencies}

    def _identify_related_requirements(self, requirements: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        for req in requirements:
            words = req["text"].lower().split()
            keywords = [w for w in words if len(w) > 3 and w not in ["shall","should","must","will","the","and","that","with","from","this"]]
            req["keywords"] = set(keywords)
        pairs = []
        for i, r1 in enumerate(requirements):
            for r2 in requirements[i+1:]:
                if len(r1["keywords"].intersection(r2["keywords"])) >= 3:
                    pairs.append([r1, r2])
        return pairs[:20]

    def _prepare_consistency_prompt(self, requirements: List[Dict[str, Any]]) -> str:
        txt = "\n".join(f"{r['id']}: {r['text']}" for r in requirements)
        return f"""<s>[INST] You are a requirements analysis expert. Analyze these requirements for inconsistencies:\n\n{txt}\n\nOnly output valid JSON.[/INST]"""

    def _prepare_pair_consistency_prompt(self, req_pair: List[Dict[str, Any]]) -> str:
        pair = f"{req_pair[0]['id']}: {req_pair[0]['text']}\n{req_pair[1]['id']}: {req_pair[1]['text']}"
        return f"""<s>[INST] Analyze these two requirements for consistency:\n\n{pair}\n\nOnly output valid JSON.[/INST]"""

    def _call_llm_api(self, prompt: str) -> str:
        if self.use_mock:
            return self._get_mock_response(prompt)
        try:
            payload = {"inputs": prompt, "parameters": {"max_new_tokens": 500, "temperature": 0.3, "return_full_text": False}}
            res = requests.post(self.api_url, headers=self.headers, json=payload)
            res.raise_for_status()
            data = res.json()
            if isinstance(data, list) and data:
                return data[0].get("generated_text", "")
            return ""
        except Exception as e:
            print(f"API call failed: {e}")
            return self._get_mock_response(prompt)

    def _get_mock_response(self, prompt: str) -> str:
        # Simple mock for development
        return json.dumps({"is_consistent": True, "inconsistencies": []})

    def _parse_results(self, api_response: str) -> Dict[str, Any]:
        resp = api_response.strip().lstrip('```json').rstrip('```').strip()
        try:
            return json.loads(resp)
        except json.JSONDecodeError as e:
            return {"is_consistent": False, "error": str(e), "raw_response": api_response}

    def consolidate_results(self, chunk_results: List[Dict[str, Any]], cross_chunk_results: Dict[str, Any]) -> Dict[str, Any]:
        all_incs = []
        for r in chunk_results:
            if not r.get("is_consistent", True):
                all_incs.extend(r.get("inconsistencies", []))
        if not cross_chunk_results.get("is_consistent", True):
            all_incs.extend(cross_chunk_results.get("inconsistencies", []))
        seen = set()
        unique = []
        for inc in all_incs:
            key = tuple(sorted(inc.get("conflicting_reqs", [])))
            if key and key not in seen:
                seen.add(key)
                unique.append(inc)
        unique.sort(key=lambda x: ({"high":0,"medium":1,"low":2}.get(x.get("confidence","low")), x.get("conflicting_reqs",[''])[0]))
        return {"is_consistent": not unique, "inconsistencies": unique, "total_inconsistencies_found": len(unique)}

    def generate_report(self, results: Dict[str, Any], output_file: str = None) -> str:
        report = "# Requirements Consistency Analysis Report\n\n"
        if results.get("error"):
            report += f"## Error\n\n{results['error']}\n"
        elif results.get("is_consistent"):
            report += "No inconsistencies found.\n"
        else:
            report += f"Found {len(results.get('inconsistencies', []))} inconsistencies.\n"
            for i, inc in enumerate(results.get('inconsistencies', []), 1):
                reqs = ", ".join(inc.get("conflicting_reqs", []))
                report += f"### Inconsistency {i}\nConflicting: {reqs}\nDescription: {inc.get('description')}\nResolution: {inc.get('resolution')}\n\n"
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
        return report

# Example usage
if __name__ == "__main__":
    api_key = os.environ.get("HF_API_KEY")
    checker = RequirementsConsistencyChecker(api_key)
    input_file = "requirements_document.txt"
    output_file = "requirements_analysis_report.md"
    results = checker.process_large_document(input_file)
    report = checker.generate_report(results, output_file)
    print(f"Analysis complete. Report saved to {output_file}")
    if results.get("is_consistent"):
        print("No inconsistencies found in the requirements.")
    else:
        print(f"Found {len(results.get('inconsistencies', []))} inconsistencies.")
