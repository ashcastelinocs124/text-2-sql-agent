"""
AgentX Green Agent - AgentBeats-compatible SQL Benchmark Evaluator.

This module implements a Green Agent that orchestrates SQL benchmark
assessments for Purple Agents (SQL-generating AI agents) using the
A2A protocol.
"""

from .config import AssessmentConfig, TaskUpdate, AssessmentArtifact
from .sql_benchmark_agent import SQLBenchmarkGreenAgent
from .artifact_builder import ArtifactBuilder

__all__ = [
    "SQLBenchmarkGreenAgent",
    "AssessmentConfig",
    "TaskUpdate",
    "AssessmentArtifact",
    "ArtifactBuilder",
]
