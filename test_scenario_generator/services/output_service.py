# test_scenario_generator/services/output_service.py
import json
from pathlib import Path
from typing import Dict, Any

from domain.entities import ProcessingResult


class OutputService:
    """Service for outputting processing results."""
    
    @staticmethod
    def to_json(result: ProcessingResult, output_path: Path) -> None:
        """Convert the processing result to JSON and write to a file."""
        
        output_dict = {
            "source_file": result.source_file,
            "requirements_count": len(result.requirements),
            "results": {}
        }
        
        for req_id, scenario in result.test_scenarios.items():
            output_dict["results"][req_id] = {
                "requirement": {
                    "id": scenario.requirement.id,
                    "text": scenario.requirement.text
                },
                "scenarios": scenario.scenarios
            }
        
        with open(output_path, 'w') as f:
            json.dump(output_dict, f, indent=2)

