from strix.runtime.benchmark import run_benchmark


def test_run_benchmark_records_duration() -> None:
    def sample():
        return "ok"

    result = run_benchmark("sample", sample)
    assert result["name"] == "sample"
    assert result["duration_ms"] >= 0
    assert result["result"] == "ok"
