"""Tests for report generation."""
import pytest
from src.models import Task, Priority, Status
from src.reports import generate_daily_report, generate_weekly_report, format_report_text, format_report_markdown

@pytest.fixture
def tasks():
    return [Task(id=1, title="Fix bug", priority=Priority.HIGH, status=Status.DONE), Task(id=2, title="Write docs", priority=Priority.LOW, status=Status.TODO), Task(id=3, title="Review PR", priority=Priority.CRITICAL, status=Status.IN_PROGRESS), Task(id=4, title="Deploy", priority=Priority.MEDIUM, status=Status.DONE)]

class TestDailyReport:
    def test_generates(self, tasks):
        report = generate_daily_report(tasks)
        assert report["type"] == "daily"
        assert report["total_tasks"] == 4
        assert report["completed"] == 2
        assert report["completion_rate"] == 50.0
    def test_high_priority_pending(self, tasks):
        report = generate_daily_report(tasks)
        assert report["high_priority_pending"] == 0

class TestWeeklyReport:
    def test_generates(self, tasks):
        report = generate_weekly_report(tasks)
        assert report["type"] == "weekly"
        assert "priority_breakdown" in report

class TestFormatReportText:
    def test_formats(self, tasks):
        text = format_report_text(generate_daily_report(tasks))
        assert "DAILY REPORT" in text
        assert "Total tasks: 4" in text

class TestFormatReportMarkdown:
    def test_formats(self, tasks):
        md = format_report_markdown(generate_daily_report(tasks))
        assert "## Daily Report" in md
        assert "| Total tasks | 4 |" in md
