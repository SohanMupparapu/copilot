# test_scenario_generator/blackboard/controller.py
from typing import List

from .blackboard import Blackboard
from .knowledge_sources import KnowledgeSource


class Controller:
    """
    The Controller manages the process of knowledge sources contributing
    to the blackboard until a solution is reached.
    """
    
    def __init__(self, knowledge_sources: List[KnowledgeSource]):
        self.knowledge_sources = knowledge_sources
        self.blackboard = Blackboard()
    
    def run(self) -> Blackboard:
        """
        Execute the blackboard problem-solving process.
        Returns the blackboard when no more contributions can be made.
        """
        progress = True
        
        while progress:
            progress = False
            
            for source in self.knowledge_sources:
                if source.can_contribute(self.blackboard):
                    print(f"Source '{source.name}' contributing...")
                    source.contribute(self.blackboard)
                    progress = True
        
        return self.blackboard
