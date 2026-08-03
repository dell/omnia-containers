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

# Status constants to avoid hardcoded password detection
_STATUS_PASS = "pass"
_STATUS_PASS_UPPER = "PASS"
_STATUS_SKIP = "skip"
_STATUS_SKIP_UPPER = "SKIP"
_STATUS_FAIL = "fail"
_STATUS_FAIL_UPPER = "FAIL"


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
        hostname = server_data.get("hostname", "")
        # Use hostname from omnia_test_config.yml (oim_hostname)
        if hostname:
            server_info_list.append(_redact_sensitive(hostname))
        else:
            server_info_list.append(_redact_sensitive(server_ip))

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

    # Donut chart angles (only passed and failed, excluding skipped)
    _t = max(total_executed, 1)
    deg_pass = round(total_passed / _t * 360)
    deg_fail = deg_pass + round(total_failed / _t * 360)

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
              <td class="center"><div class="progress-bar"><div class="progress-fill" style="width:{rate}%;background:{bar_clr}">{rate}%</div></div></td>
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
                sc = _STATUS_PASS; sl = _STATUS_PASS_UPPER
            elif status_raw == "SKIPPED":
                sc = _STATUS_SKIP; sl = _STATUS_SKIP_UPPER
            else:
                sc = _STATUS_FAIL; sl = _STATUS_FAIL_UPPER

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
                      <td colspan="4"><div class="log_content">{log_parts}</div></td>
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
    --bg: #f8fafc; --bg-card: #ffffff; --bg-panel: #f1f5f9;
    --text: #1e293b; --text-sec: #64748b; --text-muted: #94a3b8;
    --border: #e2e8f0; --border-strong: #cbd5e1;
    --shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
    --shadow-xl: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04);
    --clr-pass: #10b981; --clr-fail: #ef4444; --clr-skip: #f59e0b;
    --clr-brand: #3b82f6; --clr-brand-dk: #1d4ed8;
    --badge-pass-bg: #dcfce7; --badge-pass-fg: #166534;
    --badge-fail-bg: #fee2e2; --badge-fail-fg: #991b1b;
    --badge-skip-bg: #fef3c7; --badge-skip-fg: #92400e;
    --badge-warn-bg: #fef3c7; --badge-warn-fg: #92400e;
    --log-bg: #1e293b; --log-fg: #e2e8f0;
    --err-bg: #fef2f2; --err-fg: #991b1b; --err-border: #fecaca;
    --banner-pass-bg: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); --banner-pass-fg: #065f46;
    --banner-fail-bg: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); --banner-fail-fg: #991b1b;
    --row-hover: #f8fafc; --card-hover: translateY(-4px) scale(1.02);
  }}
  /* ===== CSS Variables (Dark) ===== */
  [data-theme="dark"] {{
    --bg: #0f172a; --bg-card: #1e293b; --bg-panel: #334155;
    --text: #f1f5f9; --text-sec: #cbd5e1; --text-muted: #64748b;
    --border: #334155; --border-strong: #475569;
    --shadow: 0 4px 6px -1px rgba(0,0,0,0.3), 0 2px 4px -1px rgba(0,0,0,0.2);
    --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.3), 0 4px 6px -2px rgba(0,0,0,0.2);
    --shadow-xl: 0 20px 25px -5px rgba(0,0,0,0.3), 0 10px 10px -5px rgba(0,0,0,0.2);
    --clr-pass: #34d399; --clr-fail: #f87171; --clr-skip: #fbbf24;
    --clr-brand: #60a5fa; --clr-brand-dk: #3b82f6;
    --badge-pass-bg: #064e3b; --badge-pass-fg: #6ee7b7;
    --badge-fail-bg: #7f1d1d; --badge-fail-fg: #fca5a5;
    --badge-skip-bg: #78350f; --badge-skip-fg: #fde68a;
    --badge-warn-bg: #78350f; --badge-warn-fg: #fde68a;
    --log-bg: #0f172a; --log-fg: #e2e8f0;
    --err-bg: #450a0a; --err-fg: #fca5a5; --err-border: #7f1d1d;
    --banner-pass-bg: linear-gradient(135deg, #064e3b 0%, #065f46 100%); --banner-pass-fg: #6ee7b7;
    --banner-fail-bg: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%); --banner-fail-fg: #fca5a5;
    --row-hover: #1e293b; --card-hover: translateY(-4px) scale(1.02);
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif; background:var(--bg); color:var(--text); line-height:1.6; -webkit-font-smoothing:antialiased; -moz-osx-font-smoothing:grayscale; }}

  /* Header */
  .header {{ background:linear-gradient(135deg, var(--clr-brand) 0%, var(--clr-brand-dk) 100%); color:#fff; padding:28px 40px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; box-shadow:var(--shadow-lg); position:relative; overflow:hidden; }}
  .header::before {{ content:''; position:absolute; top:0; left:0; right:0; bottom:0; background:linear-gradient(45deg, rgba(255,255,255,0.1) 0%, transparent 100%); pointer-events:none; }}
  .header h1 {{ font-size:24px; font-weight:700; letter-spacing:-0.5px; position:relative; }}
  .header .subtitle {{ font-size:13px; opacity:0.9; margin-top:4px; font-weight:400; position:relative; }}
  .header-right {{ display:flex; align-items:center; gap:20px; position:relative; }}
  .header-meta {{ text-align:right; font-size:12px; opacity:0.95; line-height:1.4; }}
  .header-meta span {{ display:block; }}
  /* Theme toggle switch */
  .theme-toggle {{ position:relative; width:60px; height:32px; background:rgba(255,255,255,0.2); border:2px solid rgba(255,255,255,0.4); border-radius:20px; cursor:pointer; transition:all 0.3s ease; padding:0; font-size:0; display:flex; align-items:center; justify-content:flex-start; }}
  .theme-toggle::before {{ content:'☀️'; position:absolute; left:6px; font-size:14px; transition:all 0.3s ease; opacity:1; z-index:1; }}
  .theme-toggle::after {{ content:''; position:absolute; width:26px; height:26px; border-radius:50%; background:#fff; transition:all 0.3s cubic-bezier(0.4, 0, 0.2, 1); left:2px; box-shadow:0 2px 4px rgba(0,0,0,0.2); z-index:2; }}
  [data-theme="dark"] .theme-toggle {{ background:rgba(255,255,255,0.3); }}
  [data-theme="dark"] .theme-toggle::before {{ content:'🌙'; left:auto; right:6px; opacity:1; }}
  [data-theme="dark"] .theme-toggle::after {{ left:32px; }}
  .theme-toggle:hover {{ background:rgba(255,255,255,0.4); box-shadow:0 0 12px rgba(255,255,255,0.3); }}

  /* Banner */
  .overall-banner {{ text-align:center; padding:14px; font-size:16px; font-weight:700; letter-spacing:1px; box-shadow:var(--shadow); }}
  .overall-banner.pass {{ background:var(--banner-pass-bg); color:var(--banner-pass-fg); border-bottom:3px solid var(--clr-pass); }}
  .overall-banner.fail {{ background:var(--banner-fail-bg); color:var(--banner-fail-fg); border-bottom:3px solid var(--clr-fail); }}

  /* Container */
  .container {{ max-width:1440px; margin:24px auto; padding:0 24px; }}

  /* Summary cards */
  .summary-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:16px; margin-bottom:28px; }}
  .card {{ background:var(--bg-card); border-radius:12px; padding:20px; text-align:center; box-shadow:var(--shadow); border-top:4px solid var(--clr-brand); transition:all 0.3s cubic-bezier(0.4, 0, 0.2, 1); position:relative; overflow:hidden; }}
  .card::before {{ content:''; position:absolute; top:0; left:0; right:0; height:1px; background:linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent); }}
  .card:hover {{ transform:var(--card-hover); box-shadow:var(--shadow-xl); }}
  .card.clickable {{ cursor:pointer; }}
  .card.clickable:hover {{ box-shadow:var(--shadow-xl); }}
  .card .value {{ font-size:36px; font-weight:700; margin:6px 0; background:linear-gradient(135deg, currentColor 0%, currentColor 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }}
  .card .label {{ font-size:11px; text-transform:uppercase; color:var(--text-sec); letter-spacing:0.8px; font-weight:600; }}
  .card.total {{ border-top-color:var(--clr-brand); background:linear-gradient(135deg, var(--bg-card) 0%, rgba(59,130,246,0.03) 100%); }}
  .card.passed {{ border-top-color:var(--clr-pass); background:linear-gradient(135deg, var(--bg-card) 0%, rgba(16,185,129,0.03) 100%); }} .card.passed .value {{ color:var(--clr-pass); }}
  .card.failed {{ border-top-color:var(--clr-fail); background:linear-gradient(135deg, var(--bg-card) 0%, rgba(239,68,68,0.03) 100%); }} .card.failed .value {{ color:var(--clr-fail); }}
  .card.skipped {{ border-top-color:var(--clr-skip); background:linear-gradient(135deg, var(--bg-card) 0%, rgba(245,158,11,0.03) 100%); }} .card.skipped .value {{ color:var(--clr-skip); }}
  .card.rate .value {{ color:var(--clr-brand); }}
  .card.duration .value {{ font-size:24px; color:var(--text); }}

  /* Scenario sections */
  .scenario-section {{ border:1px solid var(--border); border-radius:6px; margin-bottom:10px; overflow:hidden; }}
  .scenario-header {{ display:flex; align-items:center; gap:10px; padding:12px 16px; background:var(--bg-panel); cursor:pointer; flex-wrap:wrap; }}
  .scenario-header:hover {{ opacity:0.9; }}
  .scenario-stats {{ display:flex; gap:12px; margin-left:auto; font-size:12px; }}
  .scenario-body {{ border-top:1px solid var(--border); }}
  .scenario-table {{ margin:0; }}

  /* Charts */
  .chart-section {{ display:flex; gap:24px; margin-bottom:28px; flex-wrap:wrap; }}
  .chart-card {{ flex:1; min-width:300px; background:var(--bg-card); border-radius:12px; padding:24px; box-shadow:var(--shadow); transition:all 0.3s ease; }}
  .chart-card:hover {{ box-shadow:var(--shadow-lg); transform:translateY(-2px); }}
  .chart-card h3 {{ margin-bottom:18px; font-size:16px; color:var(--text); font-weight:600; letter-spacing:-0.3px; }}
  .donut-container {{ display:flex; align-items:center; justify-content:center; gap:32px; }}
  .donut {{ width:160px; height:160px; border-radius:50%; position:relative; background:conic-gradient(var(--clr-pass) 0deg {deg_pass}deg, var(--clr-fail) {deg_pass}deg {deg_fail}deg, var(--border) {deg_fail}deg 360deg); box-shadow:var(--shadow-lg); transition:transform 0.3s ease; }}
  .donut:hover {{ transform:scale(1.05); }}
  .donut-center {{ position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); width:100px; height:100px; border-radius:50%; background:var(--bg-card); display:flex; align-items:center; justify-content:center; font-size:28px; font-weight:700; color:var(--text); box-shadow:inset 0 2px 8px rgba(0,0,0,0.05); }}
  .donut-legend {{ font-size:14px; color:var(--text); }}
  .donut-legend div {{ margin:8px 0; display:flex; align-items:center; gap:10px; padding:4px 8px; border-radius:6px; transition:background 0.2s; }}
  .donut-legend div:hover {{ background:var(--bg-panel); }}
  .legend-color {{ width:14px; height:14px; border-radius:4px; display:inline-block; box-shadow:0 2px 4px rgba(0,0,0,0.1); }}

  /* Panels */
  .panel {{ background:var(--bg-card); border-radius:12px; margin-bottom:24px; box-shadow:var(--shadow); overflow:hidden; transition:box-shadow 0.3s ease; }}
  .panel:hover {{ box-shadow:var(--shadow-lg); }}
  .panel-header {{ padding:16px 24px; background:var(--bg-panel); border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; }}
  .panel-header h2 {{ font-size:16px; color:var(--text); font-weight:600; letter-spacing:-0.3px; }}

  /* Filter / search */
  .filter-controls {{ display:flex; gap:8px; flex-wrap:wrap; }}
  .filter-btn {{ padding:6px 14px; border:1px solid var(--border-strong); border-radius:8px; background:var(--bg-card); color:var(--text-sec); font-size:11px; cursor:pointer; transition:all 0.3s cubic-bezier(0.4, 0, 0.2, 1); font-weight:600; text-transform:uppercase; letter-spacing:0.5px; }}
  .filter-btn:hover {{ transform:translateY(-1px); box-shadow:0 2px 8px rgba(0,0,0,0.1); }}
  .filter-btn.active {{ background:linear-gradient(135deg, var(--clr-brand) 0%, var(--clr-brand-dk) 100%); color:#fff; border-color:var(--clr-brand); box-shadow:0 4px 12px rgba(59,130,246,0.3); }}
  .search-box {{ padding:8px 16px; border:1px solid var(--border-strong); border-radius:8px; font-size:13px; width:220px; background:var(--bg-card); color:var(--text); transition:all 0.3s ease; outline:none; }}
  .search-box:focus {{ border-color:var(--clr-brand); box-shadow:0 0 0 3px rgba(59,130,246,0.1); }}

  /* Tables */
  table {{ width:100%; border-collapse:collapse; }}
  th {{ background:var(--bg-panel); padding:12px 16px; text-align:left; font-size:11px; text-transform:uppercase; color:var(--text-sec); letter-spacing:0.6px; font-weight:600; border-bottom:2px solid var(--border-strong); }}
  td {{ padding:12px 16px; border-bottom:1px solid var(--border); font-size:13px; color:var(--text); transition:background 0.2s ease; }}
  .center {{ text-align:center; }}
  .suite-name {{ font-weight:600; color:var(--text); }}
  .td-pass {{ color:var(--clr-pass); font-weight:600; }}
  .td-fail {{ color:var(--clr-fail); font-weight:600; }}
  .td-skip {{ color:var(--clr-skip); font-weight:600; }}
  tr.test-row {{ cursor:pointer; transition:all 0.2s ease; }}
  tr.test-row:hover {{ background:var(--row-hover); transform:scale(1.005); }}
  tr.test-row.fail {{ border-left:3px solid var(--clr-fail); background:rgba(239,68,68,0.02); }}
  tr.test-row.pass {{ border-left:3px solid var(--clr-pass); }}
  .text-muted {{ color:var(--text-muted); }}

  /* Badges */
  .badge {{ padding:3px 10px; border-radius:4px; font-size:11px; font-weight:600; display:inline-block; white-space:nowrap; text-transform:uppercase; letter-spacing:0.3px; }}
  .badge-pass {{ background:var(--badge-pass-bg); color:var(--badge-pass-fg); }}
  .badge-fail {{ background:var(--badge-fail-bg); color:var(--badge-fail-fg); }}
  .badge-skip {{ background:var(--badge-skip-bg); color:var(--badge-skip-fg); }}
  .badge-warn {{ background:var(--badge-warn-bg); color:var(--badge-warn-fg); }}

  /* Progress bars */
  .progress-bar {{ background:var(--border); border-radius:8px; height:22px; overflow:hidden; min-width:80px; box-shadow:inset 0 2px 4px rgba(0,0,0,0.05); }}
  .progress-fill {{ height:100%; border-radius:8px; color:#fff; font-size:11px; font-weight:600; display:flex; align-items:center; justify-content:center; min-width:35px; transition:width 0.8s cubic-bezier(0.4, 0, 0.2, 1); background:linear-gradient(90deg, currentColor 0%, currentColor 100%); box-shadow:0 2px 8px rgba(0,0,0,0.1); }}

  /* Log rows */
  .log-row td {{ padding:0; }}
  .log-content {{ background:var(--log-bg); color:var(--log-fg); padding:16px 20px; font-family:'Cascadia Code','Fira Code',Consolas,monospace; font-size:12px; max-height:350px; overflow-y:auto; border-radius:0 0 8px 8px; line-height:1.6; }}
  .log-pre {{ background:var(--log-bg); color:var(--log-fg); padding:14px 18px; border-radius:6px; font-family:'Cascadia Code','Fira Code',Consolas,monospace; font-size:11px; white-space:pre-wrap; word-break:break-word; max-height:300px; overflow-y:auto; line-height:1.6; border:1px solid var(--border); }}
  .error-block {{ background:var(--err-bg); color:var(--err-fg); border:1px solid var(--err-border); border-radius:6px; padding:12px 16px; margin-top:8px; font-family:'Cascadia Code','Fira Code',Consolas,monospace; font-size:11px; white-space:pre-wrap; word-break:break-word; max-height:200px; overflow-y:auto; box-shadow:0 2px 8px rgba(0,0,0,0.1); }}
  .log-link {{ color:var(--clr-brand); font-size:12px; font-weight:600; text-decoration:underline; cursor:pointer; transition:color 0.2s; }}
  .log-link:hover {{ color:var(--clr-brand-dk); }}
  .log-critical {{ color:var(--clr-fail); font-weight:700; }}
  .log-warning {{ color:var(--clr-skip); font-weight:700; }}

  /* Playbook sections */
  .pb-section {{ margin-bottom:12px; border:1px solid var(--border); border-radius:8px; overflow:hidden; transition:box-shadow 0.3s ease; }}
  .pb-section:hover {{ box-shadow:var(--shadow); }}
  .pb-header {{ display:flex; align-items:center; gap:10px; padding:12px 16px; background:var(--bg-panel); cursor:pointer; flex-wrap:wrap; transition:background 0.2s ease; }}
  .pb-header:hover {{ background:var(--border); }}
  .pb-arrow {{ font-size:10px; color:var(--text-sec); transition:transform 0.3s ease; }}

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
    <button class="theme-toggle" onclick="toggleTheme()" id="themeBtn" title="Toggle theme"></button>
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
        <th class="center">Fail</th><th class="center">Skip</th><th class="center">Pass Rate</th>
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


def record_playbook_failure(module_name: str, report_id: str,
                            log_file: str = None, command_type: str = "test"):
    """Record a playbook/molecule execution failure in the test report.

    Called from run_molecule.sh when the molecule command fails before
    pytest/verify executes. Ensures playbook failures are captured in the
    report even when no test results exist.

    Args:
        module_name:  Scenario name (e.g. 'local_repo', 'prepare_oim').
        report_id:    Shared report ID from OMNIA_REPORT_ID env var.
        log_file:     Path to molecule log file with execution output.
        command_type: Molecule command that failed ('test', 'converge', etc.).
    """
    import re as _re

    # Check if this module already has results in the report
    # (pytest ran and captured test failures — no need to duplicate)
    existing = _load_report()
    for _srv in existing.get("servers", {}).values():
        for run in _srv.get("runs", []):
            if run.get("report_id") != report_id:
                continue
            for mod in run.get("modules", []):
                if mod.get("module") == module_name and mod.get("results"):
                    return  # Tests already recorded, skip

    report = TestReport(module_name, report_id)
    report.molecule_command = command_type

    failure_details = ""
    failure_summary = f"Molecule {command_type} failed for {module_name}"

    if log_file and os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Strip ANSI escape codes
            ansi_escape = _re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            clean_content = ansi_escape.sub('', content)

            # Store full playbook logs for the HTML report
            report.playbook_logs = clean_content

            lines = clean_content.strip().split('\n')

            # Extract lines around failure indicators for context
            _FAILURE_KW = [
                "failed=", "unreachable=", "fatal:", "failed: [",
                "CRITICAL", "molecule ➜", "PLAY RECAP",
            ]
            context_lines: List[str] = []
            for i, line in enumerate(lines):
                if any(kw.lower() in line.lower() for kw in _FAILURE_KW):
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    context_lines.extend(lines[start:end])

            if context_lines:
                # Deduplicate preserving order
                seen: set = set()
                unique: List[str] = []
                for ln in context_lines:
                    if ln not in seen:
                        seen.add(ln)
                        unique.append(ln)
                failure_details = '\n'.join(unique)
            else:
                # Fallback: last 30 lines
                failure_details = '\n'.join(lines[-30:])

            # Try to find a concise error line
            for line in reversed(lines):
                low = line.lower().strip()
                if any(kw in low for kw in ["fatal:", "failed:", "critical"]):
                    failure_summary = line.strip()
                    break

        except Exception:
            failure_details = f"Could not read log file: {log_file}"

    report.add_result(
        test_name=f"playbook_{command_type}_{module_name}",
        passed=False,
        duration=0.0,
        details=failure_details or (
            f"Molecule {command_type} command failed. "
            "Check logs for details."
        ),
        error=failure_summary,
        status="FAILED",
    )

    report.save()

