# test_scenario_generator/domain/entities.py
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class Requirement:
    id: str
    text: str


@dataclass
class TestScenario:
    requirement: Requirement
    scenarios: str


@dataclass
class ProcessingResult:
    source_file: str
    requirements: List[Requirement]
    test_scenarios: Dict[str, TestScenario]
