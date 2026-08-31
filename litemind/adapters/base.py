from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAdapter(ABC):
    """
    Common interface for all provider adapters in LiteMind.
    This allows LiteMind to seamlessly interact with different AI providers without hardcoding.
    """

    @abstractmethod
    def authenticate(self, api_key: str) -> bool:
        """Validate if the provided API key is valid."""
        pass

    @abstractmethod
    def validate_input(self, payload: Dict[str, Any]) -> bool:
        """Validate whether the task input matches the provider requirement."""
        pass

    @abstractmethod
    def execute(self, payload: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the task against the provider API.
        Must return a structured dictionary containing 'success', 'data', 'cost', and 'error' (if any).
        """
        pass

    @abstractmethod
    def estimate_cost(self, payload: Dict[str, Any]) -> float:
        """Estimate execution cost in USD."""
        pass

    @abstractmethod
    def estimate_time(self, payload: Dict[str, Any]) -> float:
        """Estimate execution time in seconds."""
        pass
