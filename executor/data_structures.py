"""
Data structures for the executor module.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from evaluation.data_structures import (
    ExecutionResult,
    ComparisonResult,
    MultiDimensionalScore,
)


@dataclass
class Task:
    """
    Represents a single evaluation task.

    The sql_query is sent to SQLAgent for execution in sandbox.
    """
    task_id: str
    question: str
    sql_query: str = ""  # SQL to be evaluated by SQLAgent
    database_id: str = ""
    schema: Dict[str, Any] = field(default_factory=dict)
    expected_sql: Optional[str] = None
    expected_result: Optional[List[Dict[str, Any]]] = None  # For correctness comparison
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """
    Result of evaluating a single task.

    Contains:
        - Original task
        - SQL that was evaluated
        - Execution result from SQLAgent
        - Comparison result (if expected_result was provided)
        - Weighted multi-dimensional score
    """
    task: Task
    generated_sql: str
    execution: ExecutionResult
    comparison: ComparisonResult
    score: MultiDimensionalScore

    def is_successful(self) -> bool:
        """Check if the SQL execution was successful."""
        return self.execution.success

    def is_correct(self) -> bool:
        """Check if the result matches expected output."""
        return self.comparison.is_match

    def get_overall_score(self) -> float:
        """Get the final weighted overall score."""
        return self.score.overall

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_id": self.task.task_id,
            "question": self.task.question,
            "sql_query": self.task.sql_query,
            "execution": {
                "success": self.execution.success,
                "rows_returned": self.execution.rows_returned,
                "execution_time_ms": self.execution.execution_time_ms,
                "is_valid": self.execution.is_valid,
                "error": self.execution.error,
            },
            "comparison": {
                "is_match": self.comparison.is_match,
                "match_score": self.comparison.match_score,
            },
            "scores": {
                "correctness": self.score.correctness,
                "efficiency": self.score.efficiency,
                "safety": self.score.safety,
                "completeness": self.score.result_completeness,
                "overall": self.score.overall,
            },
            "weights": self.score.weights,
        }