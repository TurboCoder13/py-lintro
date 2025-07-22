import shutil
import tempfile
import json
import csv
import pytest
from lintro.utils.output_manager import OutputManager
from types import SimpleNamespace
from pathlib import Path


@pytest.fixture
def temp_output_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)


def make_tool_result(name, issues_count=0, issues=None):
    return SimpleNamespace(
        name=name,
        issues_count=issues_count,
        output=f"Output for {name}",
        issues=issues or [],
    )


def make_issue(file, line, code, message):
    return SimpleNamespace(
        file=file,
        line=line,
        code=code,
        message=message,
    )


def test_run_dir_creation(temp_output_dir):
    """Test that OutputManager creates a timestamped run directory."""
    om = OutputManager(base_dir=temp_output_dir, keep_last=2)
    assert om.get_run_dir().exists()
    assert om.get_run_dir().parent == Path(temp_output_dir)


def test_write_console_log(temp_output_dir):
    """Test writing console.log file."""
    om = OutputManager(base_dir=temp_output_dir)
    om.write_console_log("hello world")
    log_path = om.get_run_dir() / "console.log"
    assert log_path.exists()
    assert log_path.read_text() == "hello world"


def test_write_json(temp_output_dir):
    """Test writing results.json file."""
    om = OutputManager(base_dir=temp_output_dir)
    data = {"foo": 1, "bar": [2, 3]}
    om.write_json(data)
    json_path = om.get_run_dir() / "results.json"
    assert json_path.exists()
    with open(json_path) as f:
        loaded = json.load(f)
    assert loaded == data


def test_write_markdown(temp_output_dir):
    """Test writing report.md file."""
    om = OutputManager(base_dir=temp_output_dir)
    om.write_markdown("# Title\nBody")
    md_path = om.get_run_dir() / "report.md"
    assert md_path.exists()
    assert md_path.read_text().startswith("# Title")


def test_write_html(temp_output_dir):
    """Test writing report.html file."""
    om = OutputManager(base_dir=temp_output_dir)
    om.write_html("<h1>Title</h1>")
    html_path = om.get_run_dir() / "report.html"
    assert html_path.exists()
    assert "<h1>Title</h1>" in html_path.read_text()


def test_write_csv(temp_output_dir):
    """Test writing summary.csv file."""
    om = OutputManager(base_dir=temp_output_dir)
    rows = [["a", "1"], ["b", "2"]]
    header = ["col1", "col2"]
    om.write_csv(rows, header)
    csv_path = om.get_run_dir() / "summary.csv"
    assert csv_path.exists()
    with open(csv_path) as f:
        reader = list(csv.reader(f))
    assert reader[0] == header
    assert reader[1] == ["a", "1"]
    assert reader[2] == ["b", "2"]


def test_write_reports_from_results(temp_output_dir):
    """Test write_reports_from_results generates all report files with correct content."""
    om = OutputManager(base_dir=temp_output_dir)
    issues = [make_issue("foo.py", 1, "E001", "Test error")]
    results = [
        make_tool_result("tool1", 1, issues),
        make_tool_result("tool2", 0, []),
    ]
    om.write_reports_from_results(results)
    # Check markdown
    md = (om.get_run_dir() / "report.md").read_text()
    assert "tool1" in md and "foo.py" in md and "E001" in md
    # Check html
    html = (om.get_run_dir() / "report.html").read_text()
    assert "tool1" in html and "foo.py" in html and "E001" in html
    # Check csv
    csv_path = om.get_run_dir() / "summary.csv"
    with open(csv_path) as f:
        reader = list(csv.reader(f))
    assert reader[0][:2] == ["tool", "issues_count"]
    assert any("tool1" in row for row in reader)
    assert any("foo.py" in row for row in reader)
