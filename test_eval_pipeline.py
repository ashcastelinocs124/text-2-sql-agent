"""
Test script to verify the evaluation pipeline works end-to-end.
"""

from executor.simple_evaluation_runner import SimpleEvaluationRunner
from executor.data_structures import Task, TaskResult
from executor.sql_agent import SQLAgent
from evaluation.scorer import DefaultScorer
from evaluation.result_comparator import DefaultResultComparator


url = "postgresql://testuser:testpass@localhost:5432/testdb"

def test_basic_pipeline():
    """Test the basic pipeline without comparison."""
    print("\n" + "="*60)
    print("TEST 1: Basic Pipeline (No Comparison)")
    print("="*60)
    
    # Initialize components
    sql_agent = SQLAgent(url)  
    scorer = DefaultScorer()
    
    # Create runner (no comparator - skip comparison)
    runner = SimpleEvaluationRunner(
        sql_agent=sql_agent,
        scorer=scorer,
        comparator=None,
    )
    
    # Create a simple task
    task = Task(
        task_id="test_001",
        question="Get all users",
        sql_query="SELECT * FROM users LIMIT 10",
    )
    
    # Run evaluation
    result = runner.run_single(task, verbose=True)
    
    # Print results
    print(f"\n📊 Results:")
    print(f"   Success: {result.is_successful()}")
    print(f"   Overall Score: {result.get_overall_score():.2f}")
    print(f"   Scores: {result.to_dict()['scores']}")
    
    return result


def test_pipeline_with_comparison():
    """Test the pipeline with expected result comparison."""
    print("\n" + "="*60)
    print("TEST 2: Pipeline With Comparison")
    print("="*60)
    
    # Initialize components
    sql_agent = SQLAgent()  # May need connection string
    scorer = DefaultScorer()
    comparator = DefaultResultComparator(
        numeric_tolerance=0.001,
        ignore_row_order=True,
    )
    
    # Create runner with comparator
    runner = SimpleEvaluationRunner(
        sql_agent=sql_agent,
        scorer=scorer,
        comparator=comparator,
    )
    
    # Create task with expected result
    task = Task(
        task_id="test_002",
        question="Get user count",
        sql_query="SELECT COUNT(*) as count FROM users",
        expected_result=[{"count": 100}],  # Expected output
    )
    
    # Run evaluation
    result = runner.run_single(task, verbose=True)
    
    # Print results
    print(f"\n📊 Results:")
    print(f"   Success: {result.is_successful()}")
    print(f"   Correct: {result.is_correct()}")
    print(f"   Match Score: {result.comparison.match_score:.2f}")
    print(f"   Overall Score: {result.get_overall_score():.2f}")
    
    return result


def test_run_sql_directly():
    """Test running SQL directly without creating a Task."""
    print("\n" + "="*60)
    print("TEST 3: Run SQL Directly")
    print("="*60)
    
    sql_agent = SQLAgent()
    scorer = DefaultScorer()
    
    runner = SimpleEvaluationRunner(
        sql_agent=sql_agent,
        scorer=scorer,
    )
    
    # Run SQL directly
    result = runner.run_sql(
        sql="SELECT 1 as test",
        task_id="direct_test",
        verbose=True,
    )
    
    print(f"\n📊 Results:")
    print(f"   Success: {result.is_successful()}")
    print(f"   Overall Score: {result.get_overall_score():.2f}")
    
    return result


def test_custom_weights():
    """Test with custom scoring weights."""
    print("\n" + "="*60)
    print("TEST 4: Custom Weights")
    print("="*60)
    
    sql_agent = SQLAgent()
    
    # Custom weights - prioritize correctness
    custom_weights = {
        "correctness": 0.60,        # 60%
        "efficiency": 0.10,         # 10%
        "safety": 0.20,             # 20%
        "result_completeness": 0.10 # 10%
    }
    
    scorer = DefaultScorer(weights=custom_weights)
    
    runner = SimpleEvaluationRunner(
        sql_agent=sql_agent,
        scorer=scorer,
    )
    
    task = Task(
        task_id="test_004",
        question="Test custom weights",
        sql_query="SELECT 1",
    )
    
    result = runner.run_single(task, verbose=True)
    
    print(f"\n📊 Custom Weights Used: {custom_weights}")
    print(f"   Overall Score: {result.get_overall_score():.2f}")
    
    return result


def test_batch_evaluation():
    """Test running multiple tasks."""
    print("\n" + "="*60)
    print("TEST 5: Batch Evaluation")
    print("="*60)
    
    sql_agent = SQLAgent()
    scorer = DefaultScorer()
    
    runner = SimpleEvaluationRunner(
        sql_agent=sql_agent,
        scorer=scorer,
    )
    
    # Multiple tasks
    tasks = [
        Task(task_id="batch_001", question="Query 1", sql_query="SELECT 1"),
        Task(task_id="batch_002", question="Query 2", sql_query="SELECT 2"),
        Task(task_id="batch_003", question="Query 3", sql_query="SELECT 3"),
    ]
    
    # Run all tasks
    results = runner.run(tasks, verbose=False)
    
    # Get summary
    summary = runner.get_summary(results)
    
    print(f"\n📊 Batch Summary:")
    print(f"   Total Tasks: {summary['total_tasks']}")
    print(f"   Successful: {summary['successful_executions']}")
    print(f"   Success Rate: {summary['success_rate']:.2%}")
    print(f"   Average Scores: {summary['average_scores']}")
    
    return results, summary


if __name__ == "__main__":
    print("\n🚀 EVALUATION PIPELINE TEST SUITE")
    print("="*60)
    
    try:
        # Run tests
        test_basic_pipeline()
        # test_pipeline_with_comparison()  # Uncomment if you have expected results
        # test_run_sql_directly()
        # test_custom_weights()
        # test_batch_evaluation()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()