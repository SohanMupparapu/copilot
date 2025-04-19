# test_scenario_generator/blackboard/knowledge_sources.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, List, Dict, Optional, Any

import re
import json
import pdfminer.high_level
import docx

from domain.entities import Requirement, TestScenario
from domain.blackboard import Blackboard, ProcessingResult
import pdfplumber



class KnowledgeSource(ABC):
    """Base class for all knowledge sources in the blackboard architecture."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this knowledge source."""
        pass
    
    @abstractmethod
    def can_contribute(self, blackboard: Blackboard) -> bool:
        """Determine if this knowledge source can contribute to the blackboard."""
        pass
    
    @abstractmethod
    def contribute(self, blackboard: Blackboard) -> None:
        """Contribute knowledge to the blackboard."""
        pass


class DocumentParser(KnowledgeSource):
    """Knowledge source that parses documents into raw text."""
    
    @property
    def name(self) -> str:
        return "DocumentParser"
    
    def can_contribute(self, blackboard: Blackboard) -> bool:
        return (blackboard.get('file_path') is not None 
                and blackboard.get('raw_text') is None)
    
    def contribute(self, blackboard: Blackboard) -> None:
        file_path = Path(blackboard.get('file_path'))
        
        if file_path.suffix.lower() == ".pdf":
            # text = pdfminer.high_level.extract_text(str(file_path))
            with pdfplumber.open(str(file_path)) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        elif file_path.suffix.lower() in {".docx", ".doc"}:
            doc = docx.Document(str(file_path))
            text = "\n".join(p.text for p in doc.paragraphs)
        else:
            text = file_path.read_text(encoding="utf-8")
        
        blackboard.set('raw_text', text)
        blackboard.set('file_type', file_path.suffix.lower())


class TextCleaner(KnowledgeSource):
    """Knowledge source that cleans raw text."""
    
    @property
    def name(self) -> str:
        return "TextCleaner"
    
    def can_contribute(self, blackboard: Blackboard) -> bool:
        return (blackboard.get('raw_text') is not None 
                and blackboard.get('clean_text') is None)
    
    def contribute(self, blackboard: Blackboard) -> None:
        raw_text = blackboard.get('raw_text')
        text = re.sub(r'\r\n?', '\n', raw_text)
        text = re.sub(r'\n{2,}', '\n\n', text)
        clean_text = text.strip()
        
        blackboard.set('clean_text', clean_text)


class LLMRequirementExtractor(KnowledgeSource):
    """Knowledge source that extracts requirements using an LLM."""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    @property
    def name(self) -> str:
        return "LLMRequirementExtractor"
    
    def can_contribute(self, blackboard: Blackboard) -> bool:
        return (blackboard.get('clean_text') is not None 
                and blackboard.get('llm_client_error') is None
                and blackboard.get('requirements') is None)
    
    def contribute(self, blackboard: Blackboard) -> None:
        clean_text = blackboard.get('clean_text')
        prompt = (
            "Extract each functional requirement from the text below.\n"
            "Output as a JSON array of objects with fields `id` (R1, R2, …) and `text`.\n\n"
            f"{clean_text}"
        )
        try:
            raw_response = self.llm_client.complete(prompt)
            requirements_data = json.loads(raw_response)
            requirements = [Requirement(id=item["id"], text=item["text"]) for item in requirements_data]
            blackboard.set('requirements', requirements)
            blackboard.set('requirements_method', 'llm')
        except (json.JSONDecodeError, RuntimeError) as e:
            blackboard.set('llm_client_error', str(e))


class RegexRequirementExtractor(KnowledgeSource):
    """Fallback knowledge source that extracts requirements using regex."""
    
    @property
    def name(self) -> str:
        return "RegexRequirementExtractor"
    
    def can_contribute(self, blackboard: Blackboard) -> bool:
        return (blackboard.get('clean_text') is not None 
                and blackboard.get('requirements') is None)
    
    def contribute(self, blackboard: Blackboard) -> None:
        clean_text = blackboard.get('clean_text')
        lines = clean_text.splitlines()
        requirements = []
        counter = 1
        for line in lines:
            if re.search(r'\b(shall|must|should|may|require)\b', line, re.IGNORECASE):
                requirements.append(Requirement(id=f"R{counter}", text=line.strip()))
                counter += 1
        blackboard.set('requirements', requirements)
        blackboard.set('requirements_method', 'regex')


class TestScenarioGenerator(KnowledgeSource):
    """Knowledge source that generates test scenarios for requirements."""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    @property
    def name(self) -> str:
        return "TestScenarioGenerator"
    
    def can_contribute(self, blackboard: Blackboard) -> bool:
        return (blackboard.get('requirements') is not None 
                and blackboard.get('test_scenarios') is None)
    
    def contribute(self, blackboard: Blackboard) -> None:
        requirements = blackboard.get('requirements')
        test_scenarios = {}
        for req in requirements:
            prompt = (
                "You are a QA engineer. For the following requirement, list all possible test scenarios grouped by:\n"
                "1. Positive / Happy Path\n"
                "2. Negative / Edge Cases\n"
                "3. Error & Exception Handling\n"
                "4. Security & Performance Considerations\n\n"
                f"Requirement: \"{req.text}\""
            )
            scenario_text = self.llm_client.complete(prompt)
            test_scenarios[req.id] = TestScenario(requirement=req, scenarios=scenario_text)
        blackboard.set('test_scenarios', test_scenarios)


class ResultFormatter(KnowledgeSource):
    """Knowledge source that formats the final result."""
    
    @property
    def name(self) -> str:
        return "ResultFormatter"
    
    def can_contribute(self, blackboard: Blackboard) -> bool:
        return (blackboard.get('requirements') is not None 
                and blackboard.get('test_scenarios') is not None
                and blackboard.get('result') is None)
    
    def contribute(self, blackboard: Blackboard) -> None:
        file_path = blackboard.get('file_path')
        requirements = blackboard.get('requirements')
        test_scenarios = blackboard.get('test_scenarios')
        result = ProcessingResult(
            source_file=str(file_path),
            requirements=requirements,
            test_scenarios=test_scenarios
        )
        blackboard.set('result', result)
