#!/usr/bin/env python3
"""
HTML Report Generator with Clickable Links (file:// URLs) for Fixed Issues
Generates an interactive HTML report with direct links to view each fixed issue in the rendered documentation
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from urllib.parse import quote


class FixedIssuesHTMLReporter:
    """Generates HTML report with clickable links (file:// URLs) for fixed issues"""
    
    def __init__(self, baseline_path, after_path, output_path, docs_path):
        self.baseline_path = Path(baseline_path)
        self.after_path = Path(after_path)
        self.output_path = Path(output_path)
        self.docs_path = Path(docs_path)
        self.baseline_data = None
        self.after_data = None
        self.fixed_issues = []
        
    def load_reports(self):
        """Load both baseline and current status reports"""
        with open(self.baseline_path, 'r', encoding='utf-8') as f:
            self.baseline_data = json.load(f)
        print(f"Loaded baseline report: {self.baseline_data['summary']['total_issues']} issues")
        
        with open(self.after_path, 'r', encoding='utf-8') as f:
            self.after_data = json.load(f)
        print(f"Loaded current status report: {self.after_data['summary']['total_issues']} issues")
    
    def convert_md_path_to_url(self, md_path):
        """Convert markdown file path to file:// URL for local build"""
        # Handle both relative paths (../docs/) and absolute paths
        if md_path.startswith("..\\docs\\") or md_path.startswith("../docs/"):
            # Remove ../docs/ prefix
            md_path = md_path.replace("..\\docs\\", "").replace("../docs/", "")
        else:
            # Handle absolute paths - extract relative path from docs directory
            md_path_obj = Path(md_path)
            try:
                # Get the relative path from the docs directory
                md_path = str(md_path_obj.relative_to(self.docs_path))
            except ValueError:
                # If not relative to docs, use the filename only
                md_path = md_path_obj.name
        
        # Convert .md to .html
        html_path = md_path.replace(".md", ".html")
        
        # Get absolute path to the HTML file in the local build directory
        # The build is in the parent directory (same level as docs)
        local_build_path = self.docs_path.parent / "site" / html_path
        local_build_path = local_build_path.resolve()
        
        # Convert to file:// URL
        file_url = f"file:///{local_build_path.as_posix()}"
        
        return file_url
    
    def identify_fixed_issues(self):
        """Identify issues that were fixed by comparing baseline and current reports"""
        baseline_issues = {}  # (file_path, line, type) -> issue
        current_issues = {}   # (file_path, line, type) -> issue
        
        # Build baseline issues index
        for file_path, file_data in self.baseline_data.get('files', {}).items():
            for issue in file_data.get('issues', []):
                key = (file_path, issue['line'], issue['type'])
                baseline_issues[key] = issue
        
        # Build current issues index
        for file_path, file_data in self.after_data.get('files', {}).items():
            for issue in file_data.get('issues', []):
                key = (file_path, issue['line'], issue['type'])
                current_issues[key] = issue
        
        # Identify fixed issues (in baseline but not in current)
        for key, issue in baseline_issues.items():
            if key not in current_issues:
                # Get the actual current file content to show what was fixed
                file_path, line_num, issue_type = key
                # Remove ..\\docs\\ or ../docs/ prefix and resolve relative to docs_path
                relative_path = file_path.replace('..\\docs\\', '').replace('../docs/', '').replace('..\\', '').replace('../', '')
                actual_file_path = self.docs_path / relative_path
                
                before_line = issue.get('original_line', '')
                after_line = self.get_current_line_content(actual_file_path, line_num)
                
                self.fixed_issues.append({
                    'file_path': key[0],
                    'line': key[1],
                    'type': key[2],
                    'severity': issue['severity'],
                    'message': issue['message'],
                    'suggestion': issue['suggestion'],
                    'url': self.convert_md_path_to_url(key[0]),
                    'before': before_line,
                    'after': after_line
                })
        
        print(f"Identified {len(self.fixed_issues)} fixed issues")
    
    def get_current_line_content(self, file_path, line_number):
        """Get the actual current line content from the file"""
        try:
            # Convert to absolute path if needed
            if not file_path.is_absolute():
                file_path = file_path.resolve()
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if 0 < line_number <= len(lines):
                    return lines[line_number - 1].rstrip()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
        return "Unable to read current line content"
    
    def generate_html_report(self):
        """Generate HTML report with clickable links"""
        baseline_total = self.baseline_data['summary']['total_issues']
        after_total = self.after_data['summary']['total_issues']
        # Use arithmetic calculation for consistency with visual report
        fixed_count = baseline_total - after_total
        improvement_percent = (fixed_count / baseline_total * 100) if baseline_total > 0 else 0
        
        # Group fixed issues by file
        fixed_by_file = defaultdict(list)
        for issue in self.fixed_issues:
            fixed_by_file[issue['file_path']].append(issue)
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fixed Issues Report - Clickable Links to Documentation</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f7fa;
            color: #333;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 4px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }}
        .header-info {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .header-info p {{
            margin: 5px 0;
            font-size: 16px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            opacity: 0.9;
        }}
        .stat-card .value {{
            font-size: 36px;
            font-weight: bold;
        }}
        .file-section {{
            margin-bottom: 30px;
            border: 1px solid #e1e8ed;
            border-radius: 8px;
            overflow: hidden;
        }}
        .file-header {{
            background-color: #34495e;
            color: white;
            padding: 15px 20px;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .file-header .file-link {{
            color: #3498db;
            text-decoration: none;
            background-color: white;
            padding: 5px 15px;
            border-radius: 4px;
            font-size: 14px;
        }}
        .file-header .file-link:hover {{
            background-color: #ecf0f1;
        }}
        .issue-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .issue-table th {{
            background-color: #ecf0f1;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #bdc3c7;
        }}
        .issue-table td {{
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
            vertical-align: top;
        }}
        .issue-table tr:hover {{
            background-color: #f8f9fa;
        }}
        .severity-error {{
            color: #e74c3c;
            font-weight: bold;
            background-color: #fadbd8;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .severity-warning {{
            color: #f39c12;
            font-weight: bold;
            background-color: #fdebd0;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .severity-suggestion {{
            color: #3498db;
            font-weight: bold;
            background-color: #d6eaf8;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .view-link {{
            display: inline-block;
            background-color: #3498db;
            color: white;
            padding: 6px 12px;
            text-decoration: none;
            border-radius: 4px;
            font-size: 13px;
            transition: background-color 0.3s;
        }}
        .view-link:hover {{
            background-color: #2980b9;
        }}
        .issue-type {{
            font-family: 'Courier New', monospace;
            background-color: #f4f6f7;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 12px;
        }}
        .instructions {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }}
        .instructions h3 {{
            margin-top: 0;
            color: #856404;
        }}
        .instructions code {{
            background-color: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 Fixed Issues Report - Clickable Links to Documentation</h1>
        
        <div class="header-info">
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Documentation Path:</strong> {self.docs_path}</p>
            <p><strong>Site Path:</strong> {self.docs_path.parent / 'site'}</p>
        </div>
        
        <div class="instructions">
            <h3>📋 How to Use This Report</h3>
            <ol>
                <li>Click the "View in Docs" links to navigate to the specific page where each issue was fixed</li>
                <li>Verify the fixes by reviewing the rendered documentation</li>
                <li>Links use file:// URLs and work directly from the built site directory</li>
            </ol>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Baseline Issues</h3>
                <div class="value">{baseline_total}</div>
            </div>
            <div class="stat-card">
                <h3>Issues Fixed</h3>
                <div class="value">{fixed_count}</div>
            </div>
            <div class="stat-card">
                <h3>Current Issues</h3>
                <div class="value">{after_total}</div>
            </div>
            <div class="stat-card">
                <h3>Improvement</h3>
                <div class="value">{improvement_percent:.1f}%</div>
            </div>
        </div>
        
        <h2>📁 Fixed Issues by File ({len(fixed_by_file)} files)</h2>
"""
        
        # Generate sections for each file
        for file_path in sorted(fixed_by_file.keys()):
            issues = fixed_by_file[file_path]
            file_url = self.convert_md_path_to_url(file_path)
            
            html_content += f"""
        <div class="file-section">
            <div class="file-header">
                <span>{file_path}</span>
                <a href="{file_url}" target="_blank" class="file-link">📄 View Page in Docs</a>
            </div>
            <table class="issue-table">
                <thead>
                    <tr>
                        <th style="width: 80px;">Line</th>
                        <th style="width: 120px;">Severity</th>
                        <th style="width: 200px;">Issue Type</th>
                        <th>Before Fix</th>
                        <th>After Fix</th>
                        <th style="width: 120px;">Action</th>
                    </tr>
                </thead>
                <tbody>
"""
            
            for issue in issues:
                severity_class = f"severity-{issue['severity'].lower()}"
                before_content = issue.get('before', 'N/A')
                after_content = issue.get('after', 'N/A')
                
                html_content += f"""
                    <tr>
                        <td><strong>{issue['line']}</strong></td>
                        <td><span class="{severity_class}">{issue['severity']}</span></td>
                        <td><span class="issue-type">{issue['type']}</span></td>
                        <td><code style="background-color: #f8f9fa; padding: 2px 6px; border-radius: 3px; font-size: 12px;">{before_content}</code></td>
                        <td><code style="background-color: #d4edda; padding: 2px 6px; border-radius: 3px; font-size: 12px;">{after_content}</code></td>
                        <td><a href="{file_url}" target="_blank" class="view-link">👁️ View in Docs</a></td>
                    </tr>
"""
            
            html_content += """
                </tbody>
            </table>
        </div>
"""
        
        html_content += f"""
        <div class="instructions" style="margin-top: 30px;">
            <h3>📊 Summary</h3>
            <p><strong>Total Files Modified:</strong> {len(fixed_by_file)}</p>
            <p><strong>Total Issues Fixed:</strong> {fixed_count}</p>
            <p><strong>Improvement:</strong> {improvement_percent:.1f}%</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML report with clickable links generated: {self.output_path}")


def main():
    if len(sys.argv) < 5:
        print("Usage: python generate_fixed_issues_html_report.py <baseline_json> <after_json> <output_html> <docs_path>")
        print("Example: python generate_fixed_issues_html_report.py baseline.json after.json fixed_issues.html ../docs")
        sys.exit(1)
    
    baseline_path = sys.argv[1]
    after_path = sys.argv[2]
    output_path = sys.argv[3]
    docs_path = sys.argv[4]
    
    reporter = FixedIssuesHTMLReporter(baseline_path, after_path, output_path, docs_path)
    reporter.load_reports()
    reporter.identify_fixed_issues()
    reporter.generate_html_report()


if __name__ == "__main__":
    main()
