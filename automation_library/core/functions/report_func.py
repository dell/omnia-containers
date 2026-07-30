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
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import yaml

from .host_func import get_project_root, load_omnia_test_config


def _get_report_dir() -> str:
    report_dir = os.path.join(get_project_root(), "reports")
    os.makedirs(report_dir, exist_ok=True)
    return report_dir


def _get_server_info() -> Dict[str, str]:
    """Get current server IP and hostname from omnia_test_config.yml."""
    try:
        config = load_omnia_test_config()
        ip = config.get("oim_server_ip", "") or "localhost"
        hostname = config.get("oim_hostname", "")
        if not hostname:
            # Try to resolve hostname from IP
            try:
                hostname = socket.gethostbyaddr(ip)[0] if ip != "localhost" else "localhost"
            except (socket.herror, socket.gaierror, OSError):
                hostname = ip
        return {"ip": ip, "hostname": hostname}
    except (IOError, yaml.YAMLError, ValueError):
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



# ── Sensitive Data Redaction ─────────────────────────────────────────────────
_REDACT_PATTERNS = None


def _compile_redact_patterns():
    """Compile regex patterns for sensitive data redaction (lazy init)."""
    import re
    return [
        # IP addresses
        (re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'), '***REDACTED_IP***'),
        # Password / secret / key / token field values
        (re.compile(
            r'(?i)([\w]*(?:password|passwd|hashed_passwd|secret|_key|token|'
            r'credential|api_key|ssh_key|private_key|auth_token)[\w]*'
            r'\s*[:=]\s*)["\']?(\S+?)(?=["\',}\]\s]|$)'
        ), r'\1***REDACTED***'),
        # NFS share paths
        (re.compile(
            r'(?i)(nfs_server_share_path\s*[:=]\s*)["\']?[^"\'\s,}\]]+'),
         r'\1***REDACTED***'),
        # Domain / hostname field values
        (re.compile(
            r'(?i)((?:domain_name|hostname)\s*[:=]\s*)["\']?[^"\'\s,}\]]+'),
         r'\1***REDACTED***'),
    ]


def _redact_sensitive(text: str) -> str:
    """Redact sensitive data (IPs, passwords, secrets, paths) from text."""
    global _REDACT_PATTERNS
    if not text:
        return text
    if _REDACT_PATTERNS is None:
        _REDACT_PATTERNS = _compile_redact_patterns()
    for pattern, replacement in _REDACT_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


# ── Skip Classification ─────────────────────────────────────────────────────
def _classify_skip(details: str = "", error: str = "") -> str:
    """Classify a skipped test into expected / unexpected / framework.

    Returns one of: 'expected', 'unexpected', 'framework'.
    """
    text = ((details or "") + " " + (error or "")).lower()
    if not text.strip():
        return "unexpected"

    _FRAMEWORK_KW = [
        "fixture", "setup failed", "import error", "conftest",
        "collection error", "module not found", "no module named",
        "parametrize", "setup error", "teardown error",
    ]
    if any(kw in text for kw in _FRAMEWORK_KW):
        return "framework"

    _EXPECTED_KW = [
        "not enabled", "not configured", "disabled", "not supported",
        "not available", "not applicable", "not installed", "feature not",
        "requires", "only applies", "not present", "skipping",
        "condition", "marker", "prerequisite",
    ]
    if any(kw in text for kw in _EXPECTED_KW):
        return "expected"

    return "unexpected"


# ── Molecule / Playbook Log Analysis ────────────────────────────────────────
def _count_log_issues(logs: str) -> dict:
    """Count CRITICAL and WARNING occurrences in playbook/molecule logs."""
    if not logs:
        return {"critical": 0, "warning": 0}
    upper = logs.upper()
    lines = upper.split('\n')
    return {
        "critical": sum(1 for ln in lines if 'CRITICAL' in ln),
        "warning": sum(1 for ln in lines if 'WARNING' in ln or '[WARN]' in ln),
    }


# ── HTML Report Generator ──────────────────────────────────────────────────
def _generate_html(data: Dict[str, Any]) -> str:
    """Generate enterprise-grade HTML report with suite-based layout,
    dark/light theme, skip classification, and sensitive-data redaction."""

    # ── 1. Flatten data across all servers / runs / modules ─────────────
    servers = data.get("servers", {})
    all_tests: List[Dict[str, Any]] = []
    suite_stats: Dict[str, Dict] = defaultdict(
        lambda: {"pass": 0, "fail": 0, "skip": 0, "duration": 0.0}
    )
    playbook_logs_by_suite: Dict[str, Dict] = {}
    server_info_list: List[str] = []

    _FAILURE_INDICATORS = [
        "failed=1", "unreachable=1", "fatal:", "failed: [",
        "molecule ➜ converge: failed",
        "molecule ➜ verify: failed",
        "molecule ➜ test: failed",
    ]

    for server_ip, server_data in servers.items():
        hostname = server_data.get("hostname", server_ip)
        display = f"{server_ip} ({hostname})" if hostname != server_ip else server_ip
        server_info_list.append(_redact_sensitive(display))

        for run in server_data.get("runs", []):
            modules = run.get("modules", [])
            if not modules and "results" in run:
                modules = [{
                    "module": run.get("module", "unknown"),
                    "results": run["results"],
                    "summary": run.get("summary", {}),
                    "duration_seconds": run.get("total_duration_seconds", 0),
                    "playbook_logs": run.get("playbook_logs"),
                    "molecule_command": run.get("molecule_command"),
                }]

            for module in modules:
                suite = module.get("module", "unknown")

                # Capture playbook logs per suite (first occurrence)
                if module.get("playbook_logs") and suite not in playbook_logs_by_suite:
                    raw_logs = module["playbook_logs"]
                    log_lower = raw_logs.lower()
                    playbook_logs_by_suite[suite] = {
                        "logs": _redact_sensitive(raw_logs),
                        "command": (module.get("molecule_command") or "execution").upper(),
                        "failed": any(ind in log_lower for ind in _FAILURE_INDICATORS),
                        "issues": _count_log_issues(raw_logs),
                    }

                for result in module.get("results", []):
                    status_raw = (result.get("status") or "FAILED").upper()
                    if status_raw == "PASSED":
                        suite_stats[suite]["pass"] += 1
                    elif status_raw == "SKIPPED":
                        suite_stats[suite]["skip"] += 1
                    else:
                        suite_stats[suite]["fail"] += 1

                    dur = float(result.get("duration_seconds", 0))
                    suite_stats[suite]["duration"] += dur

                    all_tests.append({
                        "test_name": result.get("test_name", "<unknown>"),
                        "suite": suite,
                        "status": status_raw,
                        "duration": dur,
                        "details": _redact_sensitive(result.get("details", "")),
                        "error": _redact_sensitive(result.get("error", "")),
                        "server": server_ip,
                    })

    # ── 2. Compute summary ──────────────────────────────────────────────
    total_passed = sum(s["pass"] for s in suite_stats.values())
    total_failed = sum(s["fail"] for s in suite_stats.values())
    total_skipped = sum(s["skip"] for s in suite_stats.values())
    total_tests = total_passed + total_failed + total_skipped
    # Pass rate considers only passed + failed (excluding skipped)
    total_executed = total_passed + total_failed
    pass_rate = round(total_passed / max(total_executed, 1) * 100, 1)
    total_duration = sum(s["duration"] for s in suite_stats.values())
    duration_str = str(timedelta(seconds=int(total_duration)))
    overall_status = "PASSED" if total_failed == 0 else "FAILED"
    overall_class = "pass" if overall_status == "PASSED" else "fail"

    timestamp = datetime.now().strftime("%B %d, %Y %I:%M %p")
    servers_display = ", ".join(server_info_list) if server_info_list else "N/A"

    # Donut chart angles
    _t = max(total_tests, 1)
    deg_pass = round(total_passed / _t * 360)
    deg_fail = deg_pass + round(total_failed / _t * 360)
    deg_skip = deg_fail + round(total_skipped / _t * 360)

    # ── 3. Build suite breakdown rows ───────────────────────────────────
    suite_rows_html = ""
    suite_bar_html = ""
    for suite_name in sorted(suite_stats.keys()):
        s = suite_stats[suite_name]
        st = s["pass"] + s["fail"] + s["skip"]
        # Pass rate considers only passed + failed (excluding skipped)
        st_executed = s["pass"] + s["fail"]
        rate = round(s["pass"] / max(st_executed, 1) * 100, 1)
        bar_clr = "var(--clr-pass)" if rate >= 90 else "var(--clr-skip)" if rate >= 70 else "var(--clr-fail)"
        dur_str = f'{s["duration"]:.1f}s'
        esc_name = _escape_html(suite_name)

        suite_rows_html += f'''
            <tr>
              <td class="suite-name">{esc_name}</td>
              <td class="center">{st}</td>
              <td class="center td-pass">{s["pass"]}</td>
              <td class="center td-fail">{s["fail"]}</td>
              <td class="center td-skip">{s["skip"]}</td>
              <td><div class="progress-bar"><div class="progress-fill" style="width:{rate}%;background:{bar_clr}">{rate}%</div></div></td>
            </tr>'''

        suite_bar_html += f'''
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
              <span style="min-width:140px;font-size:13px;font-weight:500;">{esc_name}</span>
              <div class="progress-bar" style="flex:1;"><div class="progress-fill" style="width:{rate}%;background:{bar_clr}">{rate}%</div></div>
            </div>'''

    # ── 4. Build detailed test sections (grouped by scenario/suite) ────
    # Group tests by suite, preserving order
    tests_by_suite: Dict[str, List] = defaultdict(list)
    for idx, t in enumerate(all_tests):
        t["_idx"] = idx
        tests_by_suite[t["suite"]].append(t)

    detailed_sections_html = ""
    global_idx = 0
    for suite_name in sorted(tests_by_suite.keys()):
        suite_tests = tests_by_suite[suite_name]
        s = suite_stats[suite_name]
        st = s["pass"] + s["fail"] + s["skip"]
        suite_status = "pass" if s["fail"] == 0 else "fail"
        esc_name = _escape_html(suite_name)
        section_id = f"scenario-{suite_name.replace(' ', '_').replace('/', '_')}"

        # Build rows for this suite
        suite_rows = ""
        for t in suite_tests:
            idx = global_idx
            global_idx += 1
            status_raw = t["status"]
            if status_raw == "PASSED":
                sc = "pass"; sl = "PASS"
            elif status_raw == "SKIPPED":
                sc = "skip"; sl = "SKIP"
            else:
                sc = "fail"; sl = "FAIL"

            has_log = bool(t.get("details") or t.get("error"))
            log_icon = '<span class="log-link">View</span>' if has_log else '<span class="text-muted">&mdash;</span>'

            log_section = ""
            if has_log:
                log_parts = ""
                if t.get("details"):
                    det = _escape_html(t["details"])
                    det = det.replace("PASS:", "<span style='color:var(--clr-pass);font-weight:600;'>PASS:</span>")
                    det = det.replace("FAIL:", "<span style='color:var(--clr-fail);font-weight:600;'>FAIL:</span>")
                    det = det.replace("SKIP:", "<span style='color:var(--clr-skip);font-weight:600;'>SKIP:</span>")
                    log_parts += f'<pre class="log-pre">{det}</pre>'
                if t.get("error"):
                    err = _escape_html(t["error"][:1200])
                    log_parts += f'<div class="error-block"><strong>Error:</strong>\n{err}</div>'
                log_section = f'''
                    <tr class="log-row" id="log-{idx}" style="display:none;">
                      <td colspan="4"><div class="log-content">{log_parts}</div></td>
                    </tr>'''

            suite_rows += f'''
                <tr class="test-row {sc}" onclick="toggleLog('log-{idx}')"
                    data-status="{sc}" data-suite="{esc_name}">
                  <td>{_escape_html(t["test_name"])}</td>
                  <td class="center"><span class="badge badge-{sc}">{sl}</span></td>
                  <td class="center">{t["duration"]:.1f}s</td>
                  <td class="center">{log_icon}</td>
                </tr>{log_section}'''

        detailed_sections_html += f'''
          <div class="scenario-section" data-scenario="{esc_name}">
            <div class="scenario-header" onclick="toggleScenario('{section_id}')">
              <span class="pb-arrow" id="arrow-{section_id}">&#9660;</span>
              <strong>{esc_name}</strong>
              <span class="badge badge-{suite_status}" style="margin-left:6px;">{suite_status.upper()}</span>
              <span class="scenario-stats">
                <span class="td-pass">{s["pass"]} passed</span>
                <span class="td-fail">{s["fail"]} failed</span>
                <span class="td-skip">{s["skip"]} skipped</span>
                <span class="text-muted">{s["duration"]:.1f}s</span>
              </span>
            </div>
            <div class="scenario-body" id="{section_id}">
              <table class="scenario-table">
                <thead><tr>
                  <th>Test Name</th><th class="center">Status</th>
                  <th class="center">Duration</th><th class="center">Logs</th>
                </tr></thead>
                <tbody>{suite_rows}</tbody>
              </table>
            </div>
          </div>'''

    # ── 5. Build playbook logs accordion ────────────────────────────────
    playbook_html = ""
    if playbook_logs_by_suite:
        playbook_html = '''
        <div class="panel">
          <div class="panel-header"><h2>Playbook Execution Logs</h2></div>
          <div style="padding:16px;">'''
        for suite_name in sorted(playbook_logs_by_suite.keys()):
            pl = playbook_logs_by_suite[suite_name]
            pl_id = f"pb-{suite_name.replace(' ', '_').replace('/', '_')}"
            issues = pl.get("issues", {})
            crit_count = issues.get("critical", 0)
            warn_count = issues.get("warning", 0)

            status_badge = '<span class="badge badge-fail">FAILED</span>' if pl["failed"] else '<span class="badge badge-pass">PASSED</span>'
            warn_badges = ""
            if crit_count > 0:
                warn_badges += f' <span class="badge badge-fail">{crit_count} CRITICAL</span>'
            if warn_count > 0:
                warn_badges += f' <span class="badge badge-warn">{warn_count} WARNING{"S" if warn_count > 1 else ""}</span>'

            # Highlight CRITICAL / WARNING lines in the log
            log_escaped = _escape_html(pl["logs"])
            log_escaped = log_escaped.replace("CRITICAL", '<span class="log-critical">CRITICAL</span>')
            log_escaped = log_escaped.replace("WARNING", '<span class="log-warning">WARNING</span>')

            playbook_html += f'''
            <div class="pb-section">
              <div onclick="togglePlaybook('{pl_id}')" class="pb-header">
                <span class="pb-arrow" id="arrow-{pl_id}">&#9654;</span>
                <strong>{_escape_html(suite_name)}</strong>
                <span class="text-muted" style="font-size:12px;">({pl["command"]})</span>
                {status_badge}{warn_badges}
              </div>
              <div id="{pl_id}" style="display:none;">
                <pre class="log-pre" style="margin:0;border-radius:0;max-height:400px;">{log_escaped}</pre>
              </div>
            </div>'''
        playbook_html += '</div></div>'


    # ── 7. Assemble full HTML ───────────────────────────────────────────
    html = f'''<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Test Report - dell/omnia-containers</title>
<style>
  /* ===== CSS Variables (Light) ===== */
  :root {{
    --bg: #f0f2f5; --bg-card: #fff; --bg-panel: #f8f9fa;
    --text: #2c3e50; --text-sec: #6c757d; --text-muted: #adb5bd;
    --border: #e9ecef; --border-strong: #dee2e6;
    --shadow: 0 2px 8px rgba(0,0,0,0.06);
    --clr-pass: #27ae60; --clr-fail: #e74c3c; --clr-skip: #f39c12;
    --clr-brand: #0076CE; --clr-brand-dk: #003B64;
    --badge-pass-bg: #d4edda; --badge-pass-fg: #155724;
    --badge-fail-bg: #f8d7da; --badge-fail-fg: #721c24;
    --badge-skip-bg: #fff3cd; --badge-skip-fg: #856404;
    --badge-warn-bg: #fff3cd; --badge-warn-fg: #856404;
    --log-bg: #1e1e2e; --log-fg: #cdd6f4;
    --err-bg: #f8d7da; --err-fg: #721c24; --err-border: #f5c6cb;
    --banner-pass-bg: #d4edda; --banner-pass-fg: #155724;
    --banner-fail-bg: #f8d7da; --banner-fail-fg: #721c24;
    --row-hover: #f8f9fa; --card-hover: translateY(-3px);
  }}
  /* ===== CSS Variables (Dark) ===== */
  [data-theme="dark"] {{
    --bg: #0f1119; --bg-card: #1a1d2e; --bg-panel: #222538;
    --text: #e2e8f0; --text-sec: #94a3b8; --text-muted: #64748b;
    --border: #2d3348; --border-strong: #374151;
    --shadow: 0 2px 12px rgba(0,0,0,0.35);
    --clr-pass: #34d399; --clr-fail: #f87171; --clr-skip: #fbbf24;
    --clr-brand: #60a5fa; --clr-brand-dk: #1e3a5f;
    --badge-pass-bg: #064e3b; --badge-pass-fg: #6ee7b7;
    --badge-fail-bg: #7f1d1d; --badge-fail-fg: #fca5a5;
    --badge-skip-bg: #78350f; --badge-skip-fg: #fde68a;
    --badge-warn-bg: #78350f; --badge-warn-fg: #fde68a;
    --log-bg: #0d0f17; --log-fg: #cdd6f4;
    --err-bg: #450a0a; --err-fg: #fca5a5; --err-border: #7f1d1d;
    --banner-pass-bg: #064e3b; --banner-pass-fg: #6ee7b7;
    --banner-fail-bg: #7f1d1d; --banner-fail-fg: #fca5a5;
    --row-hover: #222538; --card-hover: translateY(-3px);
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif; background:var(--bg); color:var(--text); line-height:1.6; }}

  /* Header */
  .header {{ background:linear-gradient(135deg, var(--clr-brand), var(--clr-brand-dk)); color:#fff; padding:24px 40px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; }}
  .header h1 {{ font-size:22px; font-weight:600; }}
  .header .subtitle {{ font-size:13px; opacity:0.85; margin-top:2px; }}
  .header-right {{ display:flex; align-items:center; gap:20px; }}
  .header-meta {{ text-align:right; font-size:12px; opacity:0.9; }}
  .header-meta span {{ display:block; }}
  .theme-toggle {{ background:rgba(255,255,255,0.15); border:1px solid rgba(255,255,255,0.3); color:#fff; padding:5px 14px; border-radius:4px; font-size:11px; cursor:pointer; text-transform:uppercase; letter-spacing:0.5px; font-weight:600; }}
  .theme-toggle:hover {{ background:rgba(255,255,255,0.25); }}

  /* Banner */
  .overall-banner {{ text-align:center; padding:12px; font-size:16px; font-weight:700; letter-spacing:1px; }}
  .overall-banner.pass {{ background:var(--banner-pass-bg); color:var(--banner-pass-fg); }}
  .overall-banner.fail {{ background:var(--banner-fail-bg); color:var(--banner-fail-fg); }}

  /* Container */
  .container {{ max-width:1440px; margin:20px auto; padding:0 20px; }}

  /* Summary cards */
  .summary-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:14px; margin-bottom:24px; }}
  .card {{ background:var(--bg-card); border-radius:8px; padding:18px; text-align:center; box-shadow:var(--shadow); border-top:4px solid var(--clr-brand); transition:transform 0.2s; }}
  .card:hover {{ transform:var(--card-hover); }}
  .card.clickable {{ cursor:pointer; }}
  .card.clickable:hover {{ box-shadow:0 4px 16px rgba(0,0,0,0.12); }}
  .card .value {{ font-size:32px; font-weight:700; margin:4px 0; }}
  .card .label {{ font-size:11px; text-transform:uppercase; color:var(--text-sec); letter-spacing:0.5px; }}
  .card.total {{ border-top-color:var(--clr-brand); }}
  .card.passed {{ border-top-color:var(--clr-pass); }} .card.passed .value {{ color:var(--clr-pass); }}
  .card.failed {{ border-top-color:var(--clr-fail); }} .card.failed .value {{ color:var(--clr-fail); }}
  .card.skipped {{ border-top-color:var(--clr-skip); }} .card.skipped .value {{ color:var(--clr-skip); }}
  .card.rate .value {{ color:var(--clr-brand); }}
  .card.duration .value {{ font-size:22px; color:var(--text); }}

  /* Scenario sections */
  .scenario-section {{ border:1px solid var(--border); border-radius:6px; margin-bottom:10px; overflow:hidden; }}
  .scenario-header {{ display:flex; align-items:center; gap:10px; padding:12px 16px; background:var(--bg-panel); cursor:pointer; flex-wrap:wrap; }}
  .scenario-header:hover {{ opacity:0.9; }}
  .scenario-stats {{ display:flex; gap:12px; margin-left:auto; font-size:12px; }}
  .scenario-body {{ border-top:1px solid var(--border); }}
  .scenario-table {{ margin:0; }}

  /* Charts */
  .chart-section {{ display:flex; gap:20px; margin-bottom:24px; flex-wrap:wrap; }}
  .chart-card {{ flex:1; min-width:280px; background:var(--bg-card); border-radius:8px; padding:22px; box-shadow:var(--shadow); }}
  .chart-card h3 {{ margin-bottom:14px; font-size:15px; color:var(--text); }}
  .donut-container {{ display:flex; align-items:center; justify-content:center; gap:28px; }}
  .donut {{ width:150px; height:150px; border-radius:50%; position:relative; background:conic-gradient(var(--clr-pass) 0deg {deg_pass}deg, var(--clr-fail) {deg_pass}deg {deg_fail}deg, var(--clr-skip) {deg_fail}deg {deg_skip}deg, var(--border) {deg_skip}deg 360deg); }}
  .donut-center {{ position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:96px; height:96px; border-radius:50%; background:var(--bg-card); display:flex; align-items:center; justify-content:center; font-size:26px; font-weight:700; color:var(--text); }}
  .donut-legend {{ font-size:13px; color:var(--text); }}
  .donut-legend div {{ margin:5px 0; display:flex; align-items:center; gap:8px; }}
  .legend-color {{ width:12px; height:12px; border-radius:2px; display:inline-block; }}

  /* Panels */
  .panel {{ background:var(--bg-card); border-radius:8px; margin-bottom:20px; box-shadow:var(--shadow); overflow:hidden; }}
  .panel-header {{ padding:14px 22px; background:var(--bg-panel); border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; }}
  .panel-header h2 {{ font-size:16px; color:var(--text); }}

  /* Filter / search */
  .filter-controls {{ display:flex; gap:6px; flex-wrap:wrap; }}
  .filter-btn {{ padding:4px 12px; border:1px solid var(--border-strong); border-radius:4px; background:var(--bg-card); color:var(--text-sec); font-size:11px; cursor:pointer; transition:all 0.2s; font-weight:600; text-transform:uppercase; letter-spacing:0.3px; }}
  .filter-btn:hover, .filter-btn.active {{ background:var(--clr-brand); color:#fff; border-color:var(--clr-brand); }}
  .search-box {{ padding:6px 14px; border:1px solid var(--border-strong); border-radius:4px; font-size:13px; width:200px; background:var(--bg-card); color:var(--text); }}

  /* Tables */
  table {{ width:100%; border-collapse:collapse; }}
  th {{ background:var(--bg-panel); padding:10px 14px; text-align:left; font-size:11px; text-transform:uppercase; color:var(--text-sec); letter-spacing:0.5px; border-bottom:2px solid var(--border-strong); }}
  td {{ padding:10px 14px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text); }}
  .center {{ text-align:center; }}
  .suite-name {{ font-weight:600; }}
  .td-pass {{ color:var(--clr-pass); font-weight:600; }}
  .td-fail {{ color:var(--clr-fail); font-weight:600; }}
  .td-skip {{ color:var(--clr-skip); font-weight:600; }}
  tr.test-row {{ cursor:pointer; transition:background 0.15s; }}
  tr.test-row:hover {{ background:var(--row-hover); }}
  tr.test-row.fail {{ border-left:3px solid var(--clr-fail); }}
  .text-muted {{ color:var(--text-muted); }}

  /* Badges */
  .badge {{ padding:3px 10px; border-radius:4px; font-size:11px; font-weight:600; display:inline-block; white-space:nowrap; text-transform:uppercase; letter-spacing:0.3px; }}
  .badge-pass {{ background:var(--badge-pass-bg); color:var(--badge-pass-fg); }}
  .badge-fail {{ background:var(--badge-fail-bg); color:var(--badge-fail-fg); }}
  .badge-skip {{ background:var(--badge-skip-bg); color:var(--badge-skip-fg); }}
  .badge-warn {{ background:var(--badge-warn-bg); color:var(--badge-warn-fg); }}

  /* Progress bars */
  .progress-bar {{ background:var(--border); border-radius:6px; height:20px; overflow:hidden; min-width:80px; }}
  .progress-fill {{ height:100%; border-radius:6px; color:#fff; font-size:10px; font-weight:600; display:flex; align-items:center; justify-content:center; min-width:32px; transition:width 0.6s ease; }}

  /* Log rows */
  .log-row td {{ padding:0; }}
  .log-content {{ background:var(--log-bg); color:var(--log-fg); padding:14px 18px; font-family:'Cascadia Code','Fira Code',Consolas,monospace; font-size:12px; max-height:350px; overflow-y:auto; }}
  .log-pre {{ background:var(--log-bg); color:var(--log-fg); padding:12px 16px; border-radius:4px; font-family:'Cascadia Code','Fira Code',Consolas,monospace; font-size:11px; white-space:pre-wrap; word-break:break-word; max-height:300px; overflow-y:auto; line-height:1.5; }}
  .error-block {{ background:var(--err-bg); color:var(--err-fg); border:1px solid var(--err-border); border-radius:4px; padding:10px 14px; margin-top:6px; font-family:'Cascadia Code','Fira Code',Consolas,monospace; font-size:11px; white-space:pre-wrap; word-break:break-word; max-height:200px; overflow-y:auto; }}
  .log-link {{ color:var(--clr-brand); font-size:12px; font-weight:600; text-decoration:underline; cursor:pointer; }}
  .log-critical {{ color:var(--clr-fail); font-weight:700; }}
  .log-warning {{ color:var(--clr-skip); font-weight:700; }}

  /* Playbook sections */
  .pb-section {{ margin-bottom:10px; border:1px solid var(--border); border-radius:6px; overflow:hidden; }}
  .pb-header {{ display:flex; align-items:center; gap:10px; padding:10px 14px; background:var(--bg-panel); cursor:pointer; flex-wrap:wrap; }}
  .pb-header:hover {{ opacity:0.9; }}
  .pb-arrow {{ font-size:10px; color:var(--text-sec); transition:transform 0.2s; }}

  /* Footer */
  .footer {{ text-align:center; padding:18px; color:var(--text-muted); font-size:11px; }}

  /* Responsive */
  @media (max-width:768px) {{
    .header {{ padding:16px; flex-direction:column; text-align:center; }}
    .header-meta {{ text-align:center; }}
    .summary-grid {{ grid-template-columns:repeat(2,1fr); }}
    table {{ font-size:11px; }}
    td, th {{ padding:6px 8px; }}
  }}
  @media print {{
    body {{ background:#fff; }}
    .header {{ background:var(--clr-brand-dk) !important; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
    .filter-controls, .search-box, .theme-toggle {{ display:none; }}
    .card {{ break-inside:avoid; }}
  }}
</style>
</head>
<body>

<!-- HEADER -->
<div class="header">
  <div>
    <h1>Test Execution Report</h1>
    <div class="subtitle">dell/omnia-containers &nbsp;|&nbsp; automation-v2.2.0.0</div>
  </div>
  <div class="header-right">
    <div class="header-meta">
      <span><strong>Servers:</strong> {_escape_html(servers_display)}</span>
      <span><strong>Date:</strong> {timestamp}</span>
      <span><strong>Duration:</strong> {duration_str}</span>
    </div>
    <button class="theme-toggle" onclick="toggleTheme()" id="themeBtn">Dark Mode</button>
  </div>
</div>

<!-- OVERALL STATUS -->
<div class="overall-banner {overall_class}">OVERALL STATUS: {overall_status}</div>

<div class="container">

  <!-- SUMMARY CARDS -->
  <div class="summary-grid">
    <div class="card total"><div class="label">Total Tests</div><div class="value">{total_tests}</div></div>
    <div class="card passed clickable" onclick="filterFromCard('pass')"><div class="label">Passed</div><div class="value">{total_passed}</div></div>
    <div class="card failed clickable" onclick="filterFromCard('fail')"><div class="label">Failed</div><div class="value">{total_failed}</div></div>
    <div class="card skipped clickable" onclick="filterFromCard('skip')"><div class="label">Skipped</div><div class="value">{total_skipped}</div></div>
    <div class="card rate"><div class="label">Pass Rate</div><div class="value">{pass_rate}%</div></div>
  </div>

  <!-- CHARTS -->
  <div class="chart-section">
    <div class="chart-card">
      <h3>Results Distribution</h3>
      <div class="donut-container">
        <div class="donut"><div class="donut-center">{pass_rate}%</div></div>
        <div class="donut-legend">
          <div><span class="legend-color" style="background:var(--clr-pass)"></span> Passed ({total_passed})</div>
          <div><span class="legend-color" style="background:var(--clr-fail)"></span> Failed ({total_failed})</div>
          <div><span class="legend-color" style="background:var(--clr-skip)"></span> Skipped ({total_skipped})</div>
        </div>
      </div>
    </div>
    <div class="chart-card">
      <h3>Suite Pass Rates</h3>
      <div style="padding:8px 0;">{suite_bar_html if suite_bar_html else '<p class="text-muted">No suites.</p>'}</div>
    </div>
  </div>

  <!-- SUITE BREAKDOWN -->
  <div class="panel">
    <div class="panel-header"><h2>Suite Breakdown</h2></div>
    <table>
      <thead><tr>
        <th>Suite</th><th class="center">Total</th><th class="center">Pass</th>
        <th class="center">Fail</th><th class="center">Skip</th>
        <th class="center">Duration</th><th>Pass Rate</th>
      </tr></thead>
      <tbody>{suite_rows_html}</tbody>
    </table>
  </div>

  <!-- DETAILED RESULTS -->
  <div class="panel" id="detailedPanel">
    <div class="panel-header">
      <h2>Detailed Test Results</h2>
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
        <input type="text" class="search-box" id="searchBox" placeholder="Search tests..." onkeyup="filterTests()">
        <div class="filter-controls">
          <button class="filter-btn active" data-status="all" onclick="filterByStatus('all',this)">All</button>
          <button class="filter-btn" data-status="pass" onclick="filterByStatus('pass',this)">Pass</button>
          <button class="filter-btn" data-status="fail" onclick="filterByStatus('fail',this)">Fail</button>
          <button class="filter-btn" data-status="skip" onclick="filterByStatus('skip',this)">Skip</button>
        </div>
      </div>
    </div>
    <div style="padding:16px;" id="scenarioContainer">
      {detailed_sections_html}
    </div>
  </div>

  <!-- PLAYBOOK LOGS -->
  {playbook_html}

</div>

<!-- FOOTER -->
<div class="footer">Generated by Omnia Test Automation Framework &nbsp;|&nbsp; dell/omnia-containers &nbsp;|&nbsp; {timestamp}</div>

<script>
  /* Theme toggle */
  function toggleTheme() {{
    var html = document.documentElement;
    var next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    document.getElementById('themeBtn').textContent = next === 'dark' ? 'Light Mode' : 'Dark Mode';
    try {{ localStorage.setItem('report-theme', next); }} catch(e) {{}}
  }}
  (function() {{
    try {{
      var saved = localStorage.getItem('report-theme');
      if (saved) {{
        document.documentElement.setAttribute('data-theme', saved);
        var btn = document.getElementById('themeBtn');
        if (btn) btn.textContent = saved === 'dark' ? 'Light Mode' : 'Dark Mode';
      }}
    }} catch(e) {{}}
  }})();

  /* Toggle log rows */
  function toggleLog(id) {{
    var el = document.getElementById(id);
    if (el) el.style.display = el.style.display === 'none' ? 'table-row' : 'none';
  }}

  /* Filter by status (from buttons) */
  function filterByStatus(status, btn) {{
    document.querySelectorAll('.filter-btn').forEach(function(b) {{ b.classList.remove('active'); }});
    if (btn) btn.classList.add('active');
    else {{
      document.querySelectorAll('.filter-btn').forEach(function(b) {{
        if (b.getAttribute('data-status') === status) b.classList.add('active');
      }});
    }}
    document.querySelectorAll('#scenarioContainer .test-row').forEach(function(row) {{
      if (status === 'all' || row.getAttribute('data-status') === status) {{
        row.style.display = '';
      }} else {{
        row.style.display = 'none';
      }}
    }});
    document.querySelectorAll('#scenarioContainer .log-row').forEach(function(r) {{ r.style.display = 'none'; }});
    /* Show/hide scenario sections based on whether they have visible rows */
    document.querySelectorAll('.scenario-section').forEach(function(sec) {{
      var hasVisible = sec.querySelectorAll('.test-row:not([style*="display: none"])').length > 0
                    || sec.querySelectorAll('.test-row:not([style*="display:none"])').length > 0;
      if (status === 'all') hasVisible = true;
      sec.style.display = hasVisible ? '' : 'none';
    }});
  }}

  /* Filter from clicking a summary card */
  function filterFromCard(status) {{
    filterByStatus(status, null);
    var panel = document.getElementById('detailedPanel');
    if (panel) panel.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  }}

  /* Toggle scenario collapse */
  function toggleScenario(id) {{
    var el = document.getElementById(id);
    var arrow = document.getElementById('arrow-' + id);
    if (el.style.display === 'none') {{
      el.style.display = '';
      if (arrow) arrow.innerHTML = '&#9660;';
    }} else {{
      el.style.display = 'none';
      if (arrow) arrow.innerHTML = '&#9654;';
    }}
  }}

  /* Search tests */
  function filterTests() {{
    var query = document.getElementById('searchBox').value.toLowerCase();
    document.querySelectorAll('#scenarioContainer .test-row').forEach(function(row) {{
      row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
    }});
    document.querySelectorAll('.scenario-section').forEach(function(sec) {{
      var hasVisible = sec.querySelectorAll('.test-row:not([style*="display: none"])').length > 0
                    || sec.querySelectorAll('.test-row:not([style*="display:none"])').length > 0;
      sec.style.display = hasVisible ? '' : 'none';
    }});
  }}

  /* Toggle playbook logs */
  function togglePlaybook(id) {{
    var el = document.getElementById(id);
    var arrow = document.getElementById('arrow-' + id);
    if (el.style.display === 'none') {{
      el.style.display = 'block';
      if (arrow) arrow.innerHTML = '&#9660;';
    }} else {{
      el.style.display = 'none';
      if (arrow) arrow.innerHTML = '&#9654;';
    }}
  }}
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

