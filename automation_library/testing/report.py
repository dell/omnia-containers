"""
Test Report Generator for molecule/pytest tests.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional


def _get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _get_report_dir() -> str:
    report_dir = os.path.join(_get_project_root(), "reports")
    os.makedirs(report_dir, exist_ok=True)
    return report_dir


def _load_report() -> Dict[str, Any]:
    report_file = os.path.join(_get_report_dir(), "test_report.json")
    if os.path.exists(report_file):
        try:
            with open(report_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"runs": []}


def _save_json(data: Dict[str, Any]):
    with open(os.path.join(_get_report_dir(), "test_report.json"), "w") as f:
        json.dump(data, f, indent=2, default=str)


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _generate_html(data: Dict[str, Any]) -> str:
    """Generate professional HTML report with expandable test runs and output."""
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Omnia Test Report</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; background: #0d1117; color: #c9d1d9; line-height: 1.6; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header { background: linear-gradient(135deg, #238636 0%, #1f6feb 100%); padding: 30px; border-radius: 12px; margin-bottom: 30px; }
        header h1 { font-size: 2em; margin-bottom: 10px; }
        header .meta { opacity: 0.9; font-size: 0.9em; }
        .summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; text-align: center; }
        .card.passed { border-left: 4px solid #238636; }
        .card.failed { border-left: 4px solid #f85149; }
        .card.total { border-left: 4px solid #1f6feb; }
        .card .number { font-size: 2em; font-weight: bold; }
        .card.passed .number { color: #238636; }
        .card.failed .number { color: #f85149; }
        .card.total .number { color: #1f6feb; }
        .card .label { color: #8b949e; text-transform: uppercase; font-size: 0.75em; letter-spacing: 1px; }
        .run { background: #161b22; border: 1px solid #30363d; border-radius: 8px; margin-bottom: 15px; overflow: hidden; }
        .run-header { background: #21262d; padding: 15px 20px; cursor: pointer; transition: background 0.2s; }
        .run-header:hover { background: #30363d; }
        .run-header-top { display: flex; justify-content: space-between; align-items: center; }
        .run-header h3 { font-size: 1em; display: flex; align-items: center; gap: 10px; }
        .run-header .badge { padding: 4px 10px; border-radius: 20px; font-size: 0.75em; font-weight: 600; }
        .badge.passed { background: #238636; color: white; }
        .badge.failed { background: #f85149; color: white; }
        .run-meta { display: flex; gap: 15px; color: #8b949e; font-size: 0.8em; margin-top: 8px; flex-wrap: wrap; }
        .run-expand { color: #8b949e; font-size: 1.2em; transition: transform 0.3s; }
        .run.collapsed .run-expand { transform: rotate(-90deg); }
        .run.collapsed .run-body { display: none; }
        .run-body { padding: 0; border-top: 1px solid #30363d; }
        .test-item { border-bottom: 1px solid #21262d; }
        .test-item:last-child { border-bottom: none; }
        .test-row { display: flex; align-items: center; padding: 10px 20px; cursor: pointer; transition: background 0.2s; }
        .test-row:hover { background: #21262d; }
        .test-status { width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px; font-size: 11px; flex-shrink: 0; }
        .test-status.passed { background: #238636; }
        .test-status.failed { background: #f85149; }
        .test-name { flex: 1; font-family: 'SF Mono', Monaco, monospace; font-size: 0.85em; }
        .test-duration { color: #8b949e; font-size: 0.8em; min-width: 70px; text-align: right; }
        .test-time { color: #8b949e; font-size: 0.75em; min-width: 140px; text-align: right; margin-left: 10px; }
        .test-expand { color: #8b949e; margin-left: 10px; font-size: 0.8em; transition: transform 0.2s; }
        .test-item.expanded .test-expand { transform: rotate(180deg); }
        .test-output { display: none; background: #0d1117; border-top: 1px solid #21262d; padding: 12px 20px; }
        .test-item.expanded .test-output { display: block; }
        .output-box { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 12px; font-family: 'SF Mono', Monaco, monospace; font-size: 0.75em; white-space: pre-wrap; word-break: break-word; max-height: 350px; overflow-y: auto; line-height: 1.4; }
        .output-box .pass { color: #238636; }
        .output-box .fail { color: #f85149; }
        .output-box .check { color: #1f6feb; }
        .output-box .header { color: #8b949e; }
        .error-box { background: #f8514922; border: 1px solid #f85149; border-radius: 6px; padding: 12px; margin-top: 8px; font-family: monospace; font-size: 0.75em; white-space: pre-wrap; word-break: break-all; max-height: 150px; overflow-y: auto; color: #f85149; }
        footer { text-align: center; padding: 20px; color: #8b949e; font-size: 0.8em; }
        .run-count { background: #30363d; padding: 2px 8px; border-radius: 10px; font-size: 0.8em; margin-left: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧪 Omnia Test Report</h1>
            <div class="meta">Generated: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</div>
        </header>
'''
    
    total_passed = sum(r["summary"]["passed"] for r in data["runs"])
    total_failed = sum(r["summary"]["failed"] for r in data["runs"])
    total_tests = total_passed + total_failed
    
    html += f'''
        <div class="summary-cards">
            <div class="card total"><div class="number">{total_tests}</div><div class="label">Total Tests</div></div>
            <div class="card passed"><div class="number">{total_passed}</div><div class="label">Passed</div></div>
            <div class="card failed"><div class="number">{total_failed}</div><div class="label">Failed</div></div>
            <div class="card total"><div class="number">{len(data["runs"])}</div><div class="label">Test Runs</div></div>
        </div>
'''
    
    test_id = 0
    run_id = 0
    for run in reversed(data["runs"]):
        run_id += 1
        status = "passed" if run["summary"]["failed"] == 0 else "failed"
        badge_text = f'{run["summary"]["passed"]}/{run["summary"]["total"]} PASSED' if status == "passed" else f'{run["summary"]["failed"]} FAILED'
        collapsed = "collapsed" if run_id > 1 else ""  # First run expanded, others collapsed
        
        html += f'''
        <div class="run {collapsed}" id="run-{run_id}">
            <div class="run-header" onclick="toggleRun({run_id})">
                <div class="run-header-top">
                    <h3>
                        <span class="run-expand">▼</span>
                        📦 {run["module"]}
                        <span class="badge {status}">{badge_text}</span>
                        <span class="run-count">Run #{len(data["runs"]) - run_id + 1}</span>
                    </h3>
                </div>
                <div class="run-meta">
                    <span>🔖 {run["report_id"]}</span>
                    <span>⏱️ {run["total_duration_seconds"]}s</span>
                    <span>📅 {run["start_time"][:19].replace("T", " ")}</span>
                    <span>→ {run["end_time"][:19].replace("T", " ")}</span>
                </div>
            </div>
            <div class="run-body">
'''
        
        for test in run["results"]:
            test_id += 1
            test_status = "passed" if test["status"] == "PASSED" else "failed"
            icon = "✓" if test_status == "passed" else "✗"
            has_output = test.get("details") or test.get("error")
            
            html += f'''
                <div class="test-item" id="test-{test_id}">
                    <div class="test-row" onclick="toggleTest(event, {test_id})">
                        <div class="test-status {test_status}">{icon}</div>
                        <div class="test-name">{test["test_name"]}</div>
                        <div class="test-duration">{test["duration_seconds"]}s</div>
                        <div class="test-time">{test["timestamp"][11:19]}</div>
                        {"<div class='test-expand'>▼</div>" if has_output else ""}
                    </div>
'''
            if has_output:
                html += '''
                    <div class="test-output">
'''
                if test.get("details"):
                    output = _escape_html(test["details"])
                    output = output.replace("✔ PASS:", "<span class='pass'>✔ PASS:</span>")
                    output = output.replace("✘ FAIL:", "<span class='fail'>✘ FAIL:</span>")
                    output = output.replace("→", "<span class='check'>→</span>")
                    output = output.replace("=" * 70, "<span class='header'>" + "=" * 70 + "</span>")
                    html += f'''<div class="output-box">{output}</div>'''
                
                if test.get("error"):
                    error_text = _escape_html(test["error"][:1000])
                    html += f'''<div class="error-box">Error:\n{error_text}</div>'''
                
                html += '''
                    </div>
'''
            html += '''
                </div>
'''
        
        html += '''
            </div>
        </div>
'''
    
    html += '''
        <footer>
            Omnia Automation Framework | Dell Technologies
        </footer>
    </div>
    <script>
        function toggleRun(id) {
            const run = document.getElementById('run-' + id);
            run.classList.toggle('collapsed');
        }
        function toggleTest(event, id) {
            event.stopPropagation();
            const item = document.getElementById('test-' + id);
            item.classList.toggle('expanded');
        }
    </script>
</body>
</html>'''
    
    return html


class TestReport:
    """Test report generator."""
    
    def __init__(self, module_name: str, report_id: str = None):
        self.module_name = module_name
        self.report_id = report_id or str(uuid.uuid4())[:8]
        self.start_time = datetime.now()
        self.results: List[Dict[str, Any]] = []
        
        print(f"\n┌{'─'*68}┐")
        print(f"│  {'REPORT ID:':<12} {self.report_id:<52} │")
        print(f"│  {'MODULE:':<12} {module_name:<52} │")
        print(f"│  {'STARTED:':<12} {self.start_time.strftime('%Y-%m-%d %H:%M:%S'):<52} │")
        print(f"└{'─'*68}┘\n")
    
    def add_result(self, test_name: str, passed: bool, duration: float = 0.0, 
                   details: str = None, error: str = None):
        result = {
            "test_name": test_name,
            "status": "PASSED" if passed else "FAILED",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(duration, 3),
        }
        if details:
            result["details"] = details
        if error:
            result["error"] = error
        self.results.append(result)
    
    def save(self) -> str:
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        passed = sum(1 for r in self.results if r["status"] == "PASSED")
        failed = sum(1 for r in self.results if r["status"] == "FAILED")
        
        run_data = {
            "report_id": self.report_id,
            "module": self.module_name,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_duration_seconds": round(duration, 3),
            "summary": {"total": len(self.results), "passed": passed, "failed": failed},
            "results": self.results,
        }
        
        report = _load_report()
        
        # Find existing or append
        existing_idx = next((i for i, r in enumerate(report["runs"]) if r.get("report_id") == self.report_id), None)
        
        if existing_idx is not None:
            report["runs"][existing_idx]["results"].extend(self.results)
            report["runs"][existing_idx]["end_time"] = end_time.isoformat()
            all_results = report["runs"][existing_idx]["results"]
            report["runs"][existing_idx]["summary"] = {
                "total": len(all_results),
                "passed": sum(1 for r in all_results if r["status"] == "PASSED"),
                "failed": sum(1 for r in all_results if r["status"] == "FAILED"),
            }
        else:
            report["runs"].append(run_data)
        
        # Save JSON
        _save_json(report)
        
        # Generate HTML
        html_file = os.path.join(_get_report_dir(), "test_report.html")
        with open(html_file, "w") as f:
            f.write(_generate_html(report))
        
        # Print summary
        status_icon = "✓" if failed == 0 else "✗"
        status_color = "\033[92m" if failed == 0 else "\033[91m"
        reset = "\033[0m"
        
        print(f"\n┌{'─'*68}┐")
        print(f"│  {'REPORT SAVED':<64} │")
        print(f"├{'─'*68}┤")
        print(f"│  {'Report ID:':<14} {self.report_id:<50} │")
        print(f"│  {'Duration:':<14} {duration:.2f}s{'':<46} │")
        print(f"│  {'Results:':<14} {status_color}{passed} passed, {failed} failed{reset}{'':<36} │")
        print(f"├{'─'*68}┤")
        print(f"│  📄 JSON: reports/test_report.json{'':<30} │")
        print(f"│  🌐 HTML: reports/test_report.html{'':<30} │")
        print(f"└{'─'*68}┘\n")
        
        return html_file


_current_report: Optional[TestReport] = None

def get_current_report() -> Optional[TestReport]:
    return _current_report

def set_current_report(report: TestReport):
    global _current_report
    _current_report = report
