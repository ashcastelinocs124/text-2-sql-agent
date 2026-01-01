"""
SimpleEvaluationRunner - Evaluation orchestrator.

Takes SQL query → sends to SQLAgent → computes weighted score.

Flow:
    1. Receive SQL query (from Task)
    2. Send to SQLAgent (agent executes in sandbox, returns data)
    3. Convert SQLAgent output to ExecutionResult
    4. Optionally compare with expected results
    5. Compute weighted MultiDimensionalScore
    6. Return TaskResult

SQLAgent handles all execution in sandbox.
"""

from typing import Iterable, List, Optional, Any, Dict

from executor.data_structures import Task, TaskResult
from evaluation.data_structures import (
    ExecutionResult,
    ComparisonResult,
    MultiDimensionalScore,
    AgentResult,
)

from evaluation.result_comparator import ResultComparator
from evaluation.scorer import Scorer
from executor.sql_agent import SQLAgent 



class SimpleEvaluationRunner:
    """
    Evaluation runner that:
        1. Sends SQL to SQLAgent (executes in sandbox)
        2. Takes returned data
        3. Computes weighted scores from that data
        4. Optionally compares with expected output
    
    We do NOT execute SQL ourselves.
    """

    def __init__(
        self,
        sql_agent: Any,
        scorer: Scorer,
        comparator: Optional[ResultComparator] = None,
    ) -> None:
        """
        Initialize the runner.

        Parameters:
            sql_agent  -> SQLAgent instance (executes SQL in sandbox, returns data).
            scorer     -> Computes weighted multi-dimensional scores from SQLAgent output.
            comparator -> Optional. Compares actual vs expected results for correctness.
        """
        self.sql_agent = sql_agent
        self.scorer = scorer
        self.comparator = comparator

    def run(self, tasks: Iterable[Task], verbose: bool = False) -> List[TaskResult]:
        """
        Evaluate all tasks and return results.

        Parameters:
            tasks   -> Iterable of Task objects (each contains sql_query).
            verbose -> Print detailed output during processing.

        Returns:
            List of TaskResult objects with weighted scores.
        """
        results: List[TaskResult] = []

        for task in tasks:
            task_result = self._process_task(task, verbose)
            results.append(task_result)

        return results

    def run_single(self, task: Task, verbose: bool = False) -> TaskResult:
        """Evaluate a single task and return weighted scores."""
        return self._process_task(task, verbose)

    def run_sql(
        self,
        sql: str,
        task_id: str = "direct",
        expected_result: Optional[List[Dict[str, Any]]] = None,
        verbose: bool = False,
    ) -> TaskResult:
        """
        Evaluate a SQL query directly (without creating a Task).

        Parameters:
            sql             -> SQL query to evaluate.
            task_id         -> Identifier for this evaluation.
            expected_result -> Optional expected output for correctness comparison.
            verbose         -> Print detailed output.

        Returns:
            TaskResult with weighted scores.
        """
        task = Task(
            task_id=task_id,
            question="Direct SQL evaluation",
            sql_query=sql,
            expected_result=expected_result,
        )
        return self._process_task(task, verbose)

    def _process_task(self, task: Task, verbose: bool = False) -> TaskResult:
        """
        Process a single task through the evaluation pipeline.

        Steps:
            1. Get SQL from task
            2. Send to SQLAgent (executes in sandbox)
            3. Convert response to ExecutionResult
            4. Optionally compare with expected output
            5. Compute weighted score using Scorer
            6. Return TaskResult
        """
        sql = task.sql_query

        if verbose:
            print(f"\n{'='*60}")
            print(f"📝 Task: {task.task_id}")
            print(f"{'='*60}")
            print(f"Question: {task.question}")
            print(f"\n🔧 SQL:\n{sql}")

        # Step 1: Send SQL to SQLAgent (it executes in sandbox)
        agent_result = self._call_sql_agent(sql, verbose)

        # Step 2: Convert to ExecutionResult
        execution_result = agent_result.to_execution_result()

        if verbose:
            status = "✅ SUCCESS" if execution_result.success else "❌ FAILED"
            print(f"\n📊 Execution: {status}")
            if execution_result.error:
                print(f"   Error: {execution_result.error}")
            else:
                print(f"   Rows returned: {execution_result.rows_returned}")
                print(f"   Time: {execution_result.execution_time_ms:.2f}ms")
                print(f"   Valid: {execution_result.is_valid}")

        # Step 3: Compare with expected output (optional)
        comparison = self._compare_results(execution_result, task, verbose)

        # Step 4: Compute weighted score
        score = self._compute_score(comparison, execution_result, verbose)

        # Step 5: Return TaskResult
        return TaskResult(
            task=task,
            generated_sql=sql,
            execution=execution_result,
            comparison=comparison,
            score=score,
        )

    def _call_sql_agent(self, sql: str, verbose: bool) -> AgentResult:
        """
        Call SQLAgent to execute SQL in sandbox.

        We do NOT execute SQL ourselves - SQLAgent does it.
        We just receive the results.
        """
        if not sql:
            return AgentResult(
                query="",
                timestamp="",
                overall_status="FAILED",
                validation={"is_valid": False, "errors": ["No SQL provided"]},
                execution={"success": False, "error": "No SQL to execute"},
                analysis={},
            )

        try:
            # SQLAgent executes in sandbox and returns data
            agent_output = self.sql_agent.process_query(sql, verbose=verbose)
            return AgentResult.from_agent_output(agent_output)

        except Exception as e:
            if verbose:
                print(f"❌ SQLAgent error: {e}")
            return AgentResult(
                query=sql,
                timestamp="",
                overall_status="FAILED",
                validation={"is_valid": False, "errors": [str(e)]},
                execution={"success": False, "error": str(e)},
                analysis={},
            )

    def _compare_results(
        self,
        execution_result: ExecutionResult,
        task: Task,
        verbose: bool,
    ) -> ComparisonResult:
        """
        Compare actual results with expected results (optional).

        Only runs if:
            1. Comparator is provided
            2. Task has expected_result
            3. Execution was successful
        """
        expected_result = getattr(task, "expected_result", None)

        # Skip if no comparator or no expected result
        if not self.comparator or expected_result is None:
            if verbose and expected_result is None:
                print("\n⚠️  No expected result - skipping comparison")
            return ComparisonResult(
                is_match=False,
                match_score=0.0,
                details={"reason": "No expected result or comparator"},
            )

        # Skip if execution failed
        if not execution_result.success:
            if verbose:
                print("\n⚠️  Execution failed - cannot compare")
            return ComparisonResult(
                is_match=False,
                match_score=0.0,
                details={"reason": "Execution failed", "error": execution_result.error},
            )

        # Compare actual vs expected
        try:
            comparison = self.comparator.compare(
                actual=execution_result.data,
                expected=expected_result,
            )
            if verbose:
                status = "✅ MATCH" if comparison.is_match else "❌ NO MATCH"
                print(f"\n📊 Comparison: {status} (score: {comparison.match_score:.2f})")
            return comparison

        except Exception as e:
            if verbose:
                print(f"\n❌ Comparison error: {e}")
            return ComparisonResult(
                is_match=False,
                match_score=0.0,
                details={"reason": "Comparison error", "error": str(e)},
            )

    def _compute_score(
        self,
        comparison: ComparisonResult,
        execution_result: ExecutionResult,
        verbose: bool,
    ) -> MultiDimensionalScore:
        """
        Compute weighted multi-dimensional score from SQLAgent output.
        
        Uses Scorer to:
            1. Compute individual dimension scores
            2. Apply weights
            3. Calculate final overall score
        """
        try:
            score = self.scorer.score(
                comparison=comparison,
                execution_result=execution_result,
            )

            if verbose:
                print(f"\n🏆 Weighted Scores:")
                print(f"   Correctness (40%):    {score.correctness:.2f}")
                print(f"   Efficiency (20%):     {score.efficiency:.2f}")
                print(f"   Safety (25%):         {score.safety:.2f}")
                print(f"   Completeness (15%):   {score.result_completeness:.2f}")
                print(f"   ─────────────────────────────")
                print(f"   OVERALL SCORE:        {score.overall:.2f}")

            return score

        except Exception as e:
            if verbose:
                print(f"\n❌ Scoring error: {e}")
            return MultiDimensionalScore()

    def get_summary(self, results: List[TaskResult]) -> Dict[str, Any]:
        """
        Generate aggregate summary of evaluation results.

        Returns:
            Dictionary with totals, success rate, and average weighted scores.
        """
        if not results:
            return {"total_tasks": 0}

        total = len(results)
        successful = sum(1 for r in results if r.execution.success)
        correct = sum(1 for r in results if r.comparison.is_match)

        avg_correctness = sum(r.score.correctness for r in results) / total
        avg_efficiency = sum(r.score.efficiency for r in results) / total
        avg_safety = sum(r.score.safety for r in results) / total
        avg_completeness = sum(r.score.result_completeness for r in results) / total
        avg_overall = sum(r.score.overall for r in results) / total

        return {
            "total_tasks": total,
            "successful_executions": successful,
            "correct_results": correct,
            "success_rate": round(successful / total, 4),
            "accuracy": round(correct / total, 4) if self.comparator else None,
            "average_scores": {
                "correctness": round(avg_correctness, 4),
                "efficiency": round(avg_efficiency, 4),
                "safety": round(avg_safety, 4),
                "completeness": round(avg_completeness, 4),
                "overall": round(avg_overall, 4),
            },
        }