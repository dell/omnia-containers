#!/usr/bin/env python3
"""
HTML Visual Report Generator for Markdown Accessibility
Generates interactive HTML report with CSS-based visual charts
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class VisualReporterMD:
    """Generates HTML visual reports with CSS-based charts"""
    
    def __init__(self, baseline_path, after_path, output_path):
        self.baseline_path = Path(baseline_path)
        self.after_path = Path(after_path)
        self.output_path = Path(output_path)
        self.baseline_data = None
        self.after_data = None
        
    def load_reports(self):
        """Load both baseline and current status reports"""
        with open(self.baseline_path, 'r') as f:
            self.baseline_data = json.load(f)
        print(f"Loaded baseline report: {self.baseline_data['summary']['total_issues']} issues")
        
        with open(self.after_path, 'r') as f:
            self.after_data = json.load(f)
        print(f"Loaded current status report: {self.after_data['summary']['total_issues']} issues")
    
    def create_pie_chart_css(self, data, colors):
        """Generate CSS conic gradient for pie chart"""
        if sum(data) == 0:
            return "background: conic-gradient(#ddd 0% 100%);"
        
        css_parts = []
        current_angle = 0
        total = sum(data)
        
        for i, (value, color) in enumerate(zip(data, colors)):
            if value == 0:
                continue
            percentage = (value / total) * 100
            end_angle = current_angle + percentage
            css_parts.append(f"{color} {current_angle}% {end_angle}%")
            current_angle = end_angle
        
        return f"background: conic-gradient({', '.join(css_parts)});"

    def generate_html_report(self):
        """Generate HTML visual report with CSS charts"""
        baseline_total = self.baseline_data['summary']['total_issues']
        after_total = self.after_data['summary']['total_issues']
        fixed_count = baseline_total - after_total
        improvement_percent = (fixed_count / baseline_total * 100) if baseline_total > 0 else 0
        
        # Calculate severity breakdown
        baseline_errors = self.baseline_data['summary']['by_severity']['ERROR']
        baseline_warnings = self.baseline_data['summary']['by_severity']['WARNING']
        baseline_suggestions = self.baseline_data['summary']['by_severity']['SUGGESTION']
        
        after_errors = self.after_data['summary']['by_severity']['ERROR']
        after_warnings = self.after_data['summary']['by_severity']['WARNING']
        after_suggestions = self.after_data['summary']['by_severity']['SUGGESTION']
        
        # Pie chart data and colors
        baseline_severity_data = [baseline_errors, baseline_warnings, baseline_suggestions]
        after_severity_data = [after_errors, after_warnings, after_suggestions]
        severity_colors = ['#dc3545', '#ffc107', '#17a2b8']
        severity_labels = ['Errors', 'Warnings', 'Suggestions']
        
        baseline_pie_css = self.create_pie_chart_css(baseline_severity_data, severity_colors)
        after_pie_css = self.create_pie_chart_css(after_severity_data, severity_colors)
        
        # Calculate issue type breakdown
        baseline_by_type = defaultdict(int)
        after_by_type = defaultdict(int)
        
        for file_data in self.baseline_data.get('files', {}).values():
            for issue in file_data.get('issues', []):
                baseline_by_type[issue['type']] += 1
        
        for file_data in self.after_data.get('files', {}).values():
            for issue in file_data.get('issues', []):
                after_by_type[issue['type']] += 1
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Omnia Markdown Accessibility Visual Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .summary-card.fixed {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
        }}
        .chart-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin: 30px 0;
        }}
        .pie-chart {{
            width: 250px;
            height: 250px;
            border-radius: 50%;
            margin: 20px auto;
            position: relative;
        }}
        .pie-chart::after {{
            content: '';
            position: absolute;
            width: 125px;
            height: 125px;
            background: white;
            border-radius: 50%;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }}
        .bar-chart {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .bar {{
            height: 30px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            padding: 0 10px;
            color: white;
            font-weight: bold;
        }}
        .bar.error {{ background-color: #dc3545; }}
        .bar.warning {{ background-color: #ffc107; color: #333; }}
        .bar.suggestion {{ background-color: #17a2b8; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #007bff;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .priority-high {{ color: #dc3545; font-weight: bold; }}
        .priority-medium {{ color: #ffc107; font-weight: bold; }}
        .priority-low {{ color: #17a2b8; font-weight: bold; }}
        .legend {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 20px 0;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .color-box {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Omnia Markdown Accessibility Visual Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Baseline Issues</h3>
                <div class="value">{baseline_total}</div>
            </div>
            <div class="summary-card fixed">
                <h3>Issues Fixed</h3>
                <div class="value">{fixed_count}</div>
            </div>
            <div class="summary-card">
                <h3>Current Issues</h3>
                <div class="value">{after_total}</div>
            </div>
            <div class="summary-card fixed">
                <h3>Improvement</h3>
                <div class="value">{improvement_percent:.1f}%</div>
            </div>
        </div>
        
        <h2>Severity Distribution</h2>
        <div class="chart-container">
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border: 2px solid #e9ecef;">
                <h3 style="text-align: center; color: #333; margin-bottom: 20px;">Baseline (Before Fix)</h3>
                <div class="pie-chart" style="{baseline_pie_css}"></div>
                <div class="legend">
                    <div class="legend-item">
                        <div class="color-box" style="background-color: #dc3545;"></div>
                        <span>Errors: {baseline_errors}</span>
                    </div>
                    <div class="legend-item">
                        <div class="color-box" style="background-color: #ffc107;"></div>
                        <span>Warnings: {baseline_warnings}</span>
                    </div>
                    <div class="legend-item">
                        <div class="color-box" style="background-color: #17a2b8;"></div>
                        <span>Suggestions: {baseline_suggestions}</span>
                    </div>
                </div>
            </div>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border: 2px solid #e9ecef;">
                <h3 style="text-align: center; color: #333; margin-bottom: 20px;">After Fix</h3>
                <div class="pie-chart" style="{after_pie_css}"></div>
                <div class="legend">
                    <div class="legend-item">
                        <div class="color-box" style="background-color: #dc3545;"></div>
                        <span>Errors: {after_errors}</span>
                    </div>
                    <div class="legend-item">
                        <div class="color-box" style="background-color: #ffc107;"></div>
                        <span>Warnings: {after_warnings}</span>
                    </div>
                    <div class="legend-item">
                        <div class="color-box" style="background-color: #17a2b8;"></div>
                        <span>Suggestions: {after_suggestions}</span>
                    </div>
                </div>
            </div>
        </div>
        
        <h2>Issue Type Breakdown</h2>
        <table>
            <tr>
                <th>Issue Type</th>
                <th>Baseline</th>
                <th>Current</th>
                <th>Fixed</th>
                <th>Priority</th>
            </tr>
"""
        
        # Priority mapping
        priority_mapping = {
            'MISSING_IMAGE_ALT': 'HIGH',
            'EMPTY_SECTION_TITLE': 'HIGH',
            'MISSING_DIRECTIVE_OPTION': 'MEDIUM',
            'NON_DESCRIPTIVE_LINK': 'MEDIUM',
            'INVALID_CODE_LANGUAGE': 'LOW',
            'INSECURE_EXTERNAL_LINK': 'LOW',
            'BARE_URL': 'OPTIONAL',
            'BARE_REF': 'OPTIONAL'
        }
        
        for issue_type in sorted(set(baseline_by_type.keys()) | set(after_by_type.keys())):
            baseline_count = baseline_by_type.get(issue_type, 0)
            after_count = after_by_type.get(issue_type, 0)
            fixed = baseline_count - after_count
            priority = priority_mapping.get(issue_type, 'UNKNOWN')
            
            html_content += f"""
            <tr>
                <td>{issue_type}</td>
                <td>{baseline_count}</td>
                <td>{after_count}</td>
                <td>{fixed}</td>
                <td class="priority-{priority.lower()}">{priority}</td>
            </tr>
"""
        
        html_content += """
        </table>
        
        <h2>Top Files with Issues</h2>
        <table>
            <tr>
                <th>File</th>
                <th>Baseline Issues</th>
                <th>Current Issues</th>
                <th>Fixed</th>
            </tr>
"""
        
        # Get top files by issue count
        file_stats = []
        for file_path in set(self.baseline_data.get('files', {}).keys()) | set(self.after_data.get('files', {}).keys()):
            baseline_count = len(self.baseline_data.get('files', {}).get(file_path, {}).get('issues', []))
            after_count = len(self.after_data.get('files', {}).get(file_path, {}).get('issues', []))
            fixed = baseline_count - after_count
            file_stats.append({
                'file': file_path,
                'baseline': baseline_count,
                'current': after_count,
                'fixed': fixed
            })
        
        # Sort by baseline count and show top 10
        file_stats.sort(key=lambda x: x['baseline'], reverse=True)
        for file_stat in file_stats[:10]:
            html_content += f"""
            <tr>
                <td>{file_stat['file']}</td>
                <td>{file_stat['baseline']}</td>
                <td>{file_stat['current']}</td>
                <td>{file_stat['fixed']}</td>
            </tr>
"""
        
        html_content += """
        </table>
        
        <div style="margin-top: 40px; padding: 20px; background-color: #e9ecef; border-radius: 8px;">
            <h2>Recommendations</h2>
"""
        if after_total > 0:
            html_content += f"""
            <ul>
                <li>{after_total} issues still need to be addressed</li>
                <li>Focus on HIGH_PRIORITY issues first</li>
                <li>Continue iterative fixing process</li>
                <li>Re-validate after manual fixes</li>
            </ul>
"""
        else:
            html_content += """
            <ul>
                <li>All accessibility issues have been resolved!</li>
                <li>Documentation is now fully accessible</li>
                <li>Consider running periodic checks</li>
            </ul>
"""
        
        html_content += """
        </div>
    </div>
</body>
</html>
"""
        
        with open(self.output_path, 'w') as f:
            f.write(html_content)
        print(f"HTML visual report generated: {self.output_path}")

def main():
    if len(sys.argv) != 4:
        print("Usage: python generate_visual_report_md.py <baseline_json> <after_json> <output_html>")
        sys.exit(1)
    
    baseline_path = sys.argv[1]
    after_path = sys.argv[2]
    output_path = sys.argv[3]
    
    reporter = VisualReporterMD(baseline_path, after_path, output_path)
    reporter.load_reports()
    reporter.generate_html_report()

if __name__ == "__main__":
    main()
