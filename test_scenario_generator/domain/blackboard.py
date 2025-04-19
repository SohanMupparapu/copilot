# test_scenario_generator/domain/blackboard.py

from typing import Any, Dict, Optional, List
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ProcessingResult:
    """
    Holds the final output of the blackboard processing:
    - source_file: path to the original input
    - requirements: list of Requirement objects
    - test_scenarios: mapping from requirement ID to TestScenario
    """
    source_file: str
    requirements: List[Any]        # ideally List[Requirement]
    test_scenarios: Dict[str, Any] # ideally Dict[str, TestScenario]


class Blackboard:
    """
    Simple blackboard for knowledge sources to share state.
    Internally uses a dict; you can extend with listeners or logging.
    """

    def __init__(self, file_path: Optional[Path] = None):
        self._data: Dict[str, Any] = {}
        if file_path:
            self._data['file_path'] = file_path

    def set(self, key: str, value: Any) -> None:
        """Store a value under the given key."""
        self._data[key] = value

    def get(self, key: str) -> Any:
        """
        Retrieve the value for `key`, or None if not set.
        Note: If you need to distinguish 'unset' vs 'None', adjust accordingly.
        """
        return self._data.get(key)

    def keys(self) -> List[str]:
        """List all keys currently stored."""
        return list(self._data.keys())

    def has(self, key: str) -> bool:
        """Check if a key exists in the blackboard."""
        return key in self._data
