
# test_scenario_generator/blackboard/blackboard.py
from typing import Dict, Any, Optional, List


class Blackboard:
    """
    The Blackboard serves as the central knowledge repository for the system.
    Knowledge sources read from and write to this repository.
    """
    
    def __init__(self):
        self._knowledge: Dict[str, Any] = {}
    
    def get(self, key: str) -> Any:
        """Get a piece of knowledge from the blackboard."""
        return self._knowledge.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Set a piece of knowledge on the blackboard."""
        self._knowledge[key] = value
    
    def get_all(self) -> Dict[str, Any]:
        """Get all knowledge on the blackboard."""
        return self._knowledge.copy()

