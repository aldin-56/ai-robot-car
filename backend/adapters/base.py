from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class BaseAdapter(ABC):
    """Common interface for all LiteMind AI Provider Adapters."""

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        self.api_key = api_key
        self.config = config or {}

    @abstractmethod
    def authenticate(self) -> bool:
        """Verifies if the credentials are valid."""
        pass

    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validates input payload before calling API."""
        pass

    @abstractmethod
    def execute(self, task_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the task and returns standard structured result."""
        pass

    @abstractmethod
    def estimate_cost(self, input_data: Dict[str, Any]) -> float:
        """Estimates execution cost in USD."""
        pass

    @abstractmethod
    def estimate_time(self, input_data: Dict[str, Any]) -> int:
        """Estimates execution time in milliseconds."""
        pass

    @abstractmethod
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validates that output satisfies requirements."""
        pass
