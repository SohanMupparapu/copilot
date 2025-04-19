# test_scenario_generator/facade.py
from pathlib import Path
from typing import List, Dict, Any

from blackboard.blackboard import Blackboard
from blackboard.controller import Controller
from blackboard.knowledge_sources import (
    DocumentParser,
    TextCleaner,
    LLMRequirementExtractor,
    RegexRequirementExtractor,
    TestScenarioGenerator, 
    ResultFormatter
)
from domain.entities import ProcessingResult
from infrastructure.llm_client import LLMClient
from services.output_service import OutputService


class TestScenarioGeneratorFacade:
    """
    Facade for the test scenario generator system.
    Provides a simple interface for clients to use the system.
    """
    
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile", temperature: float = 0.2):
        self.llm_client = LLMClient(api_key=api_key, model=model, temperature=temperature)
        
        # Create knowledge sources
        self.knowledge_sources = [
            DocumentParser(),
            TextCleaner(),
            LLMRequirementExtractor(self.llm_client),
            RegexRequirementExtractor(),
            TestScenarioGenerator(self.llm_client),
            ResultFormatter()
        ]
        
        # Create controller
        self.controller = Controller(self.knowledge_sources)
    
    def generate_test_scenarios(self, file_path: str) -> ProcessingResult:
        """
        Generate test scenarios from a requirements document.
        
        Args:
            file_path: Path to the requirements document
            
        Returns:
            ProcessingResult object containing the generated test scenarios
        """
        # Initialize the blackboard with the file path
        self.controller.blackboard = Blackboard()
        self.controller.blackboard.set('file_path', file_path)
        
        # Run the controller
        final_blackboard = self.controller.run()
        
        # Get the result
        result = final_blackboard.get('result')
        
        if not result:
            raise RuntimeError("Failed to generate test scenarios")
        
        return result
    
    def generate_and_save(self, file_path: str, output_path: str = "output.json") -> None:
        """
        Generate test scenarios and save to a file.
        
        Args:
            file_path: Path to the requirements document
            output_path: Path to save the output JSON
        """
        result = self.generate_test_scenarios(file_path)
        OutputService.to_json(result, Path(output_path))
