# Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test Report Generator for molecule/pytest tests.
Organizes reports by server (IP/hostname).
"""

import json
import os
import socket
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml

from .host_func import get_project_root


def _get_report_dir() -> str:
    report_dir = os.path.join(get_project_root(), "reports")
    os.makedirs(report_dir, exist_ok=True)
    return report_dir


def _get_server_info() -> Dict[str, str]:
    """Get current server IP and hostname from omnia_test_config.yml."""
    config_path = os.path.join(get_project_root(), "omnia_test_config.yml")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        ip = config.get("oim_server_ip", "localhost")
        hostname = config.get("oim_hostname", "")
        if not hostname:
            # Try to resolve hostname from IP
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except (socket.herror, socket.gaierror, OSError):
                hostname = ip
        return {"ip": ip, "hostname": hostname}
    except (IOError, yaml.YAMLError):
        return {"ip": "localhost", "hostname": "localhost"}


def _load_report() -> Dict[str, Any]:
    report_file = os.path.join(_get_report_dir(), "test_report.json")
    if os.path.exists(report_file):
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"servers": {}}


def _save_json(data: Dict[str, Any]):
    with open(os.path.join(_get_report_dir(), "test_report.json"), "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _generate_html(data: Dict[str, Any]) -> str:
    """Generate professional HTML report organized by server."""
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Omnia Test Report</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; background: #0d1117; color: #c9d1d9; line-height: 1.6; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        header { background: linear-gradient(135deg, #1a1f35 0%, #0d1117 100%); padding: 30px; border-radius: 12px; margin-bottom: 30px; border: 1px solid #30363d; }
        header h1 { font-size: 1.8em; margin-bottom: 8px; display: flex; align-items: center; gap: 12px; }
        header .logo { width: 36px; height: 36px; background: linear-gradient(135deg, #238636, #1f6feb); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
        header .meta { opacity: 0.7; font-size: 0.85em; }
        .layout { display: flex; gap: 20px; }
        .sidebar { width: 280px; flex-shrink: 0; }
        .main { flex: 1; min-width: 0; }
        .server-list { background: #161b22; border: 1px solid #30363d; border-radius: 8px; overflow: hidden; position: sticky; top: 20px; }
        .server-list h3 { padding: 15px; background: #21262d; font-size: 0.9em; border-bottom: 1px solid #30363d; display: flex; align-items: center; gap: 8px; }
        .server-item { padding: 12px 15px; border-bottom: 1px solid #21262d; cursor: pointer; transition: background 0.2s; }
        .server-item:last-child { border-bottom: none; }
        .server-item:hover { background: #21262d; }
        .server-item.active { background: #1f6feb22; border-left: 3px solid #1f6feb; }
        .server-ip { font-family: 'SF Mono', Monaco, monospace; font-size: 0.9em; color: #58a6ff; }
        .server-hostname { font-size: 0.8em; color: #8b949e; margin-top: 2px; }
        .server-stats { display: flex; gap: 10px; margin-top: 5px; font-size: 0.75em; }
        .server-stats .passed { color: #238636; }
        .server-stats .failed { color: #f85149; }
        .server-stats .skipped { color: #d29922; }
        .server-content { display: none; }
        .server-content.active { display: block; }
        .summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; margin-bottom: 20px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px; text-align: center; }
        .card.passed { border-left: 4px solid #238636; }
        .card.failed { border-left: 4px solid #f85149; }
        .card.skipped { border-left: 4px solid #d29922; }
        .card.total { border-left: 4px solid #1f6feb; }
        .card .number { font-size: 1.8em; font-weight: bold; }
        .card.passed .number { color: #238636; }
        .card.failed .number { color: #f85149; }
        .card.skipped .number { color: #d29922; }
        .card.total .number { color: #1f6feb; }
        .card .label { color: #8b949e; text-transform: uppercase; font-size: 0.7em; letter-spacing: 1px; }
        .run { background: #161b22; border: 1px solid #30363d; border-radius: 8px; margin-bottom: 12px; overflow: hidden; }
        .run-header { background: #21262d; padding: 12px 15px; cursor: pointer; transition: background 0.2s; }
        .run-header:hover { background: #30363d; }
        .run-header h4 { font-size: 0.9em; display: flex; align-items: center; gap: 8px; }
        .run-header .badge { padding: 3px 8px; border-radius: 12px; font-size: 0.75em; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
        .badge { padding: 3px 8px; border-radius: 12px; font-size: 0.75em; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
        .badge.passed { background: #238636; color: white; }
        .badge.failed { background: #f85149; color: white; }
        .badge.skipped { background: #d29922; color: #0d1117; }
        .run-meta { display: flex; gap: 12px; color: #8b949e; font-size: 0.75em; margin-top: 6px; flex-wrap: wrap; }
        .run-expand { color: #8b949e; font-size: 1em; transition: transform 0.3s; }
        .run.collapsed .run-expand { transform: rotate(-90deg); }
        .run.collapsed .run-body { display: none; }
        .run-body { border-top: 1px solid #30363d; }
        .module { border-bottom: 1px solid #30363d; }
        .module:last-child { border-bottom: none; }
        .module-header { display: flex; align-items: center; padding: 10px 15px; cursor: pointer; background: #1c2128; transition: background 0.2s; gap: 8px; }
        .module-header:hover { background: #21262d; }
        .module-expand { color: #8b949e; font-size: 0.8em; transition: transform 0.2s; }
        .module.collapsed .module-expand { transform: rotate(-90deg); }
        .module.collapsed .module-body { display: none; }
        .module-name { font-family: 'SF Mono', Monaco, monospace; font-size: 0.85em; color: #58a6ff; }
        .module-body { background: #0d1117; }
        .test-item { border-bottom: 1px solid #21262d; }
        .test-item:last-child { border-bottom: none; }
        .test-row { display: flex; align-items: center; padding: 8px 15px; cursor: pointer; transition: background 0.2s; padding-left: 30px; }
        .test-row:hover { background: #21262d; }
        .test-status { width: 18px; height: 18px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 10px; font-size: 9px; flex-shrink: 0; }
        .test-status.passed { background: #238636; }
        .test-status.failed { background: #f85149; }
        .test-status.skipped { background: #d29922; color: #0d1117; }
        .test-name { flex: 1; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 0.82em; }
        .test-duration { color: #8b949e; font-size: 0.75em; min-width: 60px; text-align: right; display: flex; align-items: center; gap: 4px; }
        .test-time { color: #8b949e; font-size: 0.75em; min-width: 85px; text-align: right; margin-left: 8px; display: flex; align-items: center; gap: 4px; }
        .test-expand { color: #8b949e; margin-right: 8px; font-size: 0.75em; transition: transform 0.2s; }
        .test-item.expanded .test-expand { transform: rotate(90deg); }
        .test-output { display: none; background: #0d1117; border-top: 1px solid #21262d; padding: 10px 15px; margin-left: 30px; }
        .test-item.expanded .test-output { display: block !important; }
        .output-box { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 10px; font-family: 'SF Mono', Monaco, monospace; font-size: 0.7em; white-space: pre-wrap; word-break: break-word; max-height: 300px; overflow-y: auto; line-height: 1.4; }
        .error-box { background: #2d1b1b; border: 1px solid #f85149; border-radius: 6px; padding: 10px; font-family: 'SF Mono', Monaco, monospace; font-size: 0.7em; white-space: pre-wrap; word-break: break-word; max-height: 200px; overflow-y: auto; color: #f85149; line-height: 1.4; }
        .playbook-logs { border-top: 1px solid #30363d; }
        .logs-header { display: flex; align-items: center; padding: 10px 15px; cursor: pointer; background: #1c2128; transition: background 0.2s; gap: 8px; }
        .playbook-title { flex: 1; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 0.82em; }
        .logs-header:hover { background: #21262d; }
        .logs-expand { color: #8b949e; font-size: 0.8em; transition: transform 0.2s; }
        .playbook-logs.collapsed .logs-expand { transform: rotate(0deg); }
        .playbook-logs:not(.collapsed) .logs-expand { transform: rotate(90deg); }
        .playbook-logs.collapsed .logs-body { display: none !important; }
        .logs-content { background: #0d1117; border: 1px solid #30363d; border-radius: 6px; padding: 12px; font-family: 'SF Mono', Monaco, monospace; font-size: 0.65em; white-space: pre-wrap; word-break: break-word; max-height: 400px; overflow-y: auto; line-height: 1.3; color: #c9d1d9; }
        .output-box .pass { color: #238636; }
        .output-box .fail { color: #f85149; }
        .output-box .skip { color: #d29922; }
        .output-box .check { color: #1f6feb; }
        .output-box .header { color: #8b949e; }
        .error-box { background: #f8514922; border: 1px solid #f85149; border-radius: 6px; padding: 10px; margin-top: 6px; font-family: monospace; font-size: 0.7em; white-space: pre-wrap; word-break: break-all; max-height: 120px; overflow-y: auto; color: #f85149; }
        footer { text-align: center; padding: 20px; color: #8b949e; font-size: 0.8em; border-top: 1px solid #21262d; margin-top: 30px; }
        .no-servers { text-align: center; padding: 40px; color: #8b949e; }
        .icon { display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; border-radius: 4px; font-size: 11px; margin-right: 4px; }
        .icon-server { background: #1f6feb33; color: #58a6ff; }
        .icon-run { background: #8b5cf633; color: #a78bfa; }
        .icon-module { background: #f59e0b33; color: #fbbf24; }
        .icon-id { background: #6b728033; color: #9ca3af; }
        .icon-time { background: #10b98133; color: #34d399; }
        @media (max-width: 900px) { .layout { flex-direction: column; } .sidebar { width: 100%; } }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1><div class="logo">⚡</div> Omnia Test Report</h1>
            <div class="meta">Generated: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</div>
        </header>
'''

    servers = data.get("servers", {})
    if not servers:
        html += '<div class="no-servers">No test results yet. Run tests to generate report.</div>'
    else:
        html += '<div class="layout"><div class="sidebar"><div class="server-list"><h3><span class="icon icon-server">⬡</span> Targets</h3>'

        # Server list sidebar
        first_server = True
        for server_ip, server_data in servers.items():
            runs = server_data.get("runs", [])
            total_passed = sum((r.get("summary") or {}).get("passed", 0) for r in runs)
            total_failed = sum((r.get("summary") or {}).get("failed", 0) for r in runs)
            total_skipped = sum((r.get("summary") or {}).get("skipped", 0) for r in runs)
            active = "active" if first_server else ""

            html += f'''
            <div class="server-item {active}" onclick="showServer('{server_ip}')">
                <div class="server-ip">{server_ip}</div>
                <div class="server-stats">
                    <span class="passed">✓ {total_passed}</span>
                    <span class="failed">✗ {total_failed}</span>
                    <span class="skipped">↷ {total_skipped}</span>
                    <span>{len(runs)} runs</span>
                </div>
            </div>'''
            first_server = False

        html += '</div></div><div class="main">'

        # Server content panels
        first_server = True
        test_id = 0
        for server_ip, server_data in servers.items():
            runs = server_data.get("runs", [])
            total_passed = sum((r.get("summary") or {}).get("passed", 0) for r in runs)
            total_failed = sum((r.get("summary") or {}).get("failed", 0) for r in runs)
            total_skipped = sum((r.get("summary") or {}).get("skipped", 0) for r in runs)
            total_tests = total_passed + total_failed + total_skipped
            active = "active" if first_server else ""

            html += f'''
            <div class="server-content {active}" id="server-{server_ip.replace('.', '-')}">
                <h2 style="margin-bottom: 15px; display: flex; align-items: center; gap: 10px;">
                    <span class="icon icon-server" style="width: 28px; height: 28px; font-size: 14px;">⬡</span>
                    {server_ip}
                </h2>
                <div class="summary-cards">
                    <div class="card total"><div class="number">{total_tests}</div><div class="label">Tests</div></div>
                    <div class="card passed"><div class="number">{total_passed}</div><div class="label">Passed</div></div>
                    <div class="card failed"><div class="number">{total_failed}</div><div class="label">Failed</div></div>
                    <div class="card skipped"><div class="number">{total_skipped}</div><div class="label">Skipped</div></div>
                    <div class="card total"><div class="number">{len(runs)}</div><div class="label">Test Runs</div></div>
                </div>
'''

            run_id = 0
            for run in reversed(runs):
                run_id += 1
                run_summary = run.get("summary") or {}
                run_failed = run_summary.get("failed", 0)
                run_passed = run_summary.get("passed", 0)
                run_skipped = run_summary.get("skipped", 0)
                run_total = run_summary.get("total", run_passed + run_failed + run_skipped)
                status = "passed" if run_failed == 0 else "failed"
                # Build individual colored badges for pass/fail/skip
                run_badges = f'<span class="badge passed" style="margin-right: 4px;">✓ {run_passed} PASS</span>'
                if run_failed > 0:
                    run_badges += f'<span class="badge failed" style="margin-right: 4px;">✗ {run_failed} FAIL</span>'
                if run_skipped > 0:
                    run_badges += f'<span class="badge skipped" style="margin-right: 4px;">↷ {run_skipped} SKIP</span>'
                collapsed = "collapsed" if run_id > 1 else ""
                unique_run_id = f"{server_ip.replace('.', '-')}-{run_id}"

                # Get modules list (new format) or create from old format
                modules = run.get("modules", [])
                if not modules and "results" in run:
                    # Old format - single module
                    modules = [{
                        "module": run.get("module", "unknown"),
                        "results": run["results"],
                        "summary": run["summary"],
                        "duration_seconds": run.get("total_duration_seconds", 0)
                    }]

                num_modules = len(modules)

                # Calculate total duration for run
                total_duration = sum(m.get("duration_seconds", 0) for m in modules)

                html += f'''
                <div class="run {collapsed}" id="run-{unique_run_id}">
                    <div class="run-header" onclick="toggleRun('{unique_run_id}')">
                        <h4>
                            <span class="run-expand">▼</span>
                            <span class="icon icon-run">▶</span>
                            <span>Test Run #{run["report_id"]}</span>
                            {run_badges}
                            <span style="color: #8b949e; font-size: 0.8em; margin-left: 10px;">{num_modules} scenario(s)</span>
                        </h4>
                        <div class="run-meta">
                            <span style="color: #58a6ff;">⏱ {total_duration:.2f}s</span>
                            <span style="color: #8b949e;">📅 {run["start_time"][:16].replace("T", " ")}</span>
                        </div>
                    </div>
                    <div class="run-body">
'''

                # Render each module
                for mod_idx, module in enumerate(modules):
                    mod_summary = module.get("summary") or {}
                    mod_failed = mod_summary.get("failed", 0)
                    mod_passed = mod_summary.get("passed", 0)
                    mod_skipped = mod_summary.get("skipped", 0)
                    mod_total = mod_summary.get("total", mod_passed + mod_failed + mod_skipped)
                    mod_status = "passed" if mod_failed == 0 else "failed"
                    # Build individual colored badges for module pass/fail/skip
                    mod_badges = f'<span class="badge passed" style="margin-right: 4px;">✓ {mod_passed} PASS</span>'
                    if mod_failed > 0:
                        mod_badges += f'<span class="badge failed" style="margin-right: 4px;">✗ {mod_failed} FAIL</span>'
                    if mod_skipped > 0:
                        mod_badges += f'<span class="badge skipped" style="margin-right: 4px;">↷ {mod_skipped} SKIP</span>'
                    mod_id = f"{unique_run_id}-mod-{mod_idx}"

                    html += f'''
                        <div class="module" id="module-{mod_id}">
                            <div class="module-header" onclick="toggleModule('{mod_id}')">
                                <span class="module-expand">▼</span>
                                <span class="icon icon-module">◆</span>
                                <span class="module-name">{module["module"]}</span>
                                <span style="margin-left: 8px;">{mod_badges}</span>
                                <span style="color: #8b949e; font-size: 0.75em; margin-left: auto;">
                            ⏱ {module.get("duration_seconds", 0)}s
                        </span>
                            </div>
                            <div class="module-body">
'''

                    # Add playbook execution logs section FIRST
                    if module.get("playbook_logs"):
                        logs_id = f"{mod_id}-logs"
                        command_type = module.get("molecule_command", "execution").upper()

                        # Detect if playbook execution failed
                        playbook_failed = False
                        if module.get("playbook_logs"):
                            logs_content = module["playbook_logs"].lower()
                            # More specific failure detection - look for actual Ansible failure indicators
                            failure_indicators = [
                                "failed=1",
                                "unreachable=1",
                                "fatal:",
                                "failed: [",
                                "molecule ➜ converge: failed",
                                "molecule ➜ verify: failed",
                                "molecule ➜ test: failed"
                            ]
                            playbook_failed = any(indicator in logs_content for indicator in failure_indicators)

                        status_class = "failed" if playbook_failed else "passed"
                        status_icon = "✗" if playbook_failed else "✓"

                        html += f'''
                            <div class="playbook-logs collapsed">
                                <div class="logs-header" onclick="toggleLogs('{logs_id}')">
                                    <span class="logs-expand">▶</span>
                                    <span class="icon">📋</span>
                                    <span class="playbook-title">
                                        Playbook Execution Logs ({command_type})
                                    </span>
                                    <div class="test-status {status_class}">{status_icon}</div>
                                </div>
                                <div class="logs-body" id="logs-{logs_id}" style="display: none;">
                                    <pre class="logs-content">
                                        {_escape_html(module["playbook_logs"])}
                                    </pre>
                                </div>
                            </div>
                        '''

                    # Then add test cases
                    for test in module["results"]:
                        test_id += 1
                        if test.get("status") == "PASSED":
                            test_status = "passed"
                            icon = "✓"
                        elif test.get("status") == "SKIPPED":
                            test_status = "skipped"
                            icon = "↷"
                        else:
                            test_status = "failed"
                            icon = "✗"
                        has_output = test.get("details") or test.get("error")

                        html += f'''
                            <div class="test-item" id="test-{test_id}">
                                <div class="test-row" onclick="toggleTest(event, {test_id})">
                                    <div class="test-expand">▶</div>
                                    <div class="test-status {test_status}">{icon}</div>
                                    <div class="test-name">{test["test_name"]}</div>
                                    <div class="test-duration">{test["duration_seconds"]}s</div>
                                </div>
'''
                        # Always add test output section, but show details if available
                        html += '<div class="test-output" style="display: none;">'
                        if has_output:
                            if test.get("details"):
                                output = _escape_html(test["details"])
                                output = output.replace("✔ PASS:", "<span class='pass'>✔ PASS:</span>")
                                output = output.replace("✘ FAIL:", "<span class='fail'>✘ FAIL:</span>")
                                output = output.replace("↷ SKIP:", "<span class='skip'>↷ SKIP:</span>")
                                output = output.replace("SKIP:", "<span class='skip'>SKIP:</span>")
                                output = output.replace("→", "<span class='check'>→</span>")
                                output = output.replace("=" * 70, "<span class='header'>" + "=" * 70 + "</span>")
                                html += f'<div class="output-box">{output}</div>'
                            if test.get("error"):
                                error_text = _escape_html(test["error"][:800])
                                html += f'<div class="error-box">Error:\n{error_text}</div>'
                        else:
                            html += '<div class="output-box">No detailed output available</div>'
                        html += '</div>'
                        html += '</div>'

                    html += '</div></div>'

                html += '</div></div>'

            html += '</div>'
            first_server = False

        html += '</div></div>'

    html += '''
        <footer>Omnia Automation Framework</footer>
    </div>
    <script>
        function showServer(ip) {
            document.querySelectorAll('.server-item').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.server-content').forEach(el => el.classList.remove('active'));
            document.querySelector(`.server-item[onclick="showServer('${ip}')"]`).classList.add('active');
            document.getElementById('server-' + ip.replace(/\\./g, '-')).classList.add('active');
        }
        function toggleRun(id) {
            document.getElementById('run-' + id).classList.toggle('collapsed');
        }
        function toggleModule(id) {
            document.getElementById('module-' + id).classList.toggle('collapsed');
        }
        function toggleTest(event, id) {
            event.stopPropagation();
            document.getElementById('test-' + id).classList.toggle('expanded');
        }
        function toggleLogs(id) {
            const logsContainer = document.getElementById('logs-' + id).parentElement;
            const logsBody = document.getElementById('logs-' + id);

            logsContainer.classList.toggle('collapsed');

            if (logsContainer.classList.contains('collapsed')) {
                logsBody.style.display = 'none';
            } else {
                logsBody.style.display = 'block';
            }
        }
    </script>
</body>
</html>'''

    return html


class TestReport:
    """Test report generator - organizes by server."""

    def __init__(self, module_name: str, report_id: str = None):
        self.module_name = module_name
        self.report_id = report_id or str(uuid.uuid4())[:8]
        self.start_time = datetime.now()
        self.results: List[Dict[str, Any]] = []
        self.server_info = _get_server_info()
        self.playbook_logs = None
        self.molecule_command = None
        self.playbook_duration = None

        print(f"\n┌{'─'*68}┐")
        print(f"│  {'SERVER:':<12} {self.server_info['ip']:<52} │")
        print(f"│  {'MODULE:':<12} {module_name:<52} │")
        print(f"│  {'REPORT ID:':<12} {self.report_id:<52} │")
        print(f"└{'─'*68}┘\n")

    def _get_playbook_logs(self) -> tuple[Optional[str], Optional[str]]:
        """Get molecule playbook execution logs and command type."""
        log_file = os.environ.get('MOLECULE_LOG_FILE')
        command_type = os.environ.get('MOLECULE_COMMAND', 'execution')
        if log_file and os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Filter out ANSI escape codes for cleaner logs
                    import re
                    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                    clean_content = ansi_escape.sub('', content)
                    # Split logs: only molecule execution (exclude pytest output)
                    test_start_markers = [
                        "test session starts",
                        "collecting ...",
                        "┌────────────────────────────────────────────────────────────────────┐"
                    ]

                    molecule_logs = clean_content
                    for marker in test_start_markers:
                        if marker in clean_content:
                            molecule_logs = clean_content.split(marker)[0].strip()
                            break
                    return molecule_logs, command_type
            except Exception as e:
                print(f"Warning: Could not read playbook logs from {log_file}: {e}")
                return None, command_type
        return None, command_type

    def add_result(self, test_name: Any, passed: bool = False, duration: float = 0.0,
                   details: str = None, error: str = None, status: str = None):
        if isinstance(test_name, dict):
            payload = test_name
            normalized_status = str(payload.get("status") or "").strip().upper()
            if normalized_status not in {"PASSED", "FAILED", "SKIPPED"}:
                payload_passed = bool(payload.get("passed"))
                normalized_status = "PASSED" if payload_passed else "FAILED"

            duration_seconds = payload.get("duration_seconds")
            if duration_seconds is None:
                duration_seconds = payload.get("duration", 0.0)

            result = {
                "test_name": payload.get("test_name") or payload.get("name") or "<unknown>",
                "status": normalized_status,
                "timestamp": payload.get("timestamp") or datetime.now().isoformat(),
                "duration_seconds": round(float(duration_seconds or 0.0), 3),
            }
            if payload.get("details"):
                result["details"] = payload.get("details")
            if payload.get("error"):
                result["error"] = payload.get("error")
            self.results.append(result)
            return

        normalized_status = (status or "").strip().upper()
        if normalized_status not in {"PASSED", "FAILED", "SKIPPED"}:
            normalized_status = "PASSED" if passed else "FAILED"
        result = {
            "test_name": test_name,
            "status": normalized_status,
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
        skipped = sum(1 for r in self.results if r["status"] == "SKIPPED")

        # Capture playbook logs and command type before saving
        if self.playbook_logs is None:
            self.playbook_logs, self.molecule_command = self._get_playbook_logs()

        # Module data (tests grouped by module)
        module_data = {
            "module": self.module_name,
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": round(duration, 3),
            "summary": {"total": len(self.results), "passed": passed, "failed": failed, "skipped": skipped},
            "results": self.results,
            "playbook_logs": self.playbook_logs,
            "molecule_command": self.molecule_command,
        }

        report = _load_report()
        server_ip = self.server_info["ip"]

        # Initialize server entry if not exists
        if "servers" not in report:
            report["servers"] = {}

        if server_ip not in report["servers"]:
            report["servers"][server_ip] = {
                "runs": []
            }

        # Update hostname in case it changed
        report["servers"][server_ip]["hostname"] = self.server_info["hostname"]

        # Find existing run with same report_id
        runs = report["servers"][server_ip]["runs"]
        existing_run_idx = next(
            (i for i, r in enumerate(runs) if r.get("report_id") == self.report_id),
            None
        )

        if existing_run_idx is not None:
            # Same report_id - add/update module within run
            run = runs[existing_run_idx]
            if "modules" not in run:
                # Migrate old format to new format
                run["modules"] = []

            # Find existing module or add new
            existing_mod_idx = next(
                (i for i, m in enumerate(run["modules"]) if m.get("module") == self.module_name),
                None
            )

            if existing_mod_idx is not None:
                # Extend existing module results
                run["modules"][existing_mod_idx]["results"].extend(self.results)
                run["modules"][existing_mod_idx]["playbook_logs"] = self.playbook_logs
                run["modules"][existing_mod_idx]["molecule_command"] = self.molecule_command
                all_results = run["modules"][existing_mod_idx]["results"]
                run["modules"][existing_mod_idx]["summary"] = {
                    "total": len(all_results),
                    "passed": sum(1 for r in all_results if r["status"] == "PASSED"),
                    "failed": sum(1 for r in all_results if r["status"] == "FAILED"),
                    "skipped": sum(1 for r in all_results if r["status"] == "SKIPPED"),
                }
            else:
                # Add new module to run
                run["modules"].append(module_data)

            # Update run summary
            run["end_time"] = end_time.isoformat()
            all_passed = sum(m["summary"]["passed"] for m in run["modules"])
            all_failed = sum(m["summary"]["failed"] for m in run["modules"])
            all_skipped = sum((m.get("summary") or {}).get("skipped", 0) for m in run["modules"])
            run["summary"] = {
                "total": all_passed + all_failed + all_skipped,
                "passed": all_passed,
                "failed": all_failed,
                "skipped": all_skipped,
            }
        else:
            # New run
            run_data = {
                "report_id": self.report_id,
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "summary": {"total": len(self.results), "passed": passed, "failed": failed, "skipped": skipped},
                "modules": [module_data],
            }
            runs.append(run_data)

        # Save JSON
        _save_json(report)

        # Generate HTML
        html_file = os.path.join(_get_report_dir(), "test_report.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(_generate_html(report))

        # Print summary
        status_color = "\033[92m" if failed == 0 else "\033[91m"
        reset = "\033[0m"

        print(f"\n┌{'─'*68}┐")
        print(f"│  {'REPORT SAVED':<64} │")
        print(f"├{'─'*68}┤")
        print(f"│  {'Server:':<14} {server_ip:<50} │")
        print(f"│  {'Report ID:':<14} {self.report_id:<50} │")
        print(f"│  {'Duration:':<14} {duration:.2f}s{'':<46} │")
        print(f"│  {'Results:':<14} {status_color}{passed} passed, {failed} failed{reset}, {skipped} skipped{'':<26} │")
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
