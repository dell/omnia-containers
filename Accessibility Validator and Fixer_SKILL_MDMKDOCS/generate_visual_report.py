#!/usr/bin/env python3
"""
Generate HTML report with CSS-based visual charts and graphs
Uses only standard library - no external dependencies
"""

import json
import sys

def generate_visual_report(baseline_report_path, after_report_path, output_path):
    """Generate HTML report with CSS-based visual charts"""
    
    # Load baseline report
    with open(baseline_report_path, 'r') as f:
        baseline_data = json.load(f)
    
    # Load after report (for comparison after manual fixes)
    with open(after_report_path, 'r') as f:
        after_data = json.load(f)
    
    # Calculate chart data from baseline
    baseline_severity_data = [
        baseline_data['summary']['by_severity'].get('ERROR', 0),
        baseline_data['summary']['by_severity'].get('WARNING', 0),
        baseline_data['summary']['by_severity'].get('SUGGESTION', 0)
    ]
    after_severity_data = [
        after_data['summary']['by_severity'].get('ERROR', 0),
        after_data['summary']['by_severity'].get('WARNING', 0),
        after_data['summary']['by_severity'].get('SUGGESTION', 0)
    ]
    severity_labels = ['Critical', 'Important', 'Optional']
    severity_colors = ['#FF6B6B', '#FFD93D', '#6BCB77']
    baseline_severity_total = sum(baseline_severity_data)
    after_severity_total = sum(after_severity_data)
    
    # Calculate priority data from baseline
    critical_count = baseline_data['summary']['by_issue_type'].get('MISSING_IMAGE_ALT', 0) + baseline_data['summary']['by_issue_type'].get('EMPTY_SECTION_TITLE', 0)
    important_count = baseline_data['summary']['by_issue_type'].get('MISSING_DIRECTIVE_OPTION', 0) + baseline_data['summary']['by_issue_type'].get('NON_DESCRIPTIVE_LINK', 0)
    optional_count = baseline_data['summary']['total_issues'] - critical_count - important_count
    
    priority_data = [critical_count, important_count, optional_count]
    priority_total = sum(priority_data)
    
    # Issue type data from baseline
    issue_types = sorted(baseline_data['summary']['by_issue_type'].keys())
    issue_counts = [baseline_data['summary']['by_issue_type'].get(t, 0) for t in issue_types]
    max_count = max(issue_counts) if issue_counts else 1
    
    # Top files data from baseline
    baseline_files = baseline_data['files']
    sorted_files = sorted(baseline_files.items(), key=lambda x: len(x[1]['issues']), reverse=True)[:10]
    top_file_names = [file_data.get('relative_path', file_path).split('/')[-1][:30] for file_path, file_data in sorted_files]
    top_file_counts = [len(file_data['issues']) for file_path, file_data in sorted_files]
    max_file_count = max(top_file_counts) if top_file_counts else 1
    
    # Generate CSS conic gradients for pie charts
    def create_pie_chart_css(data, colors):
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
    
    baseline_severity_pie_css = create_pie_chart_css(baseline_severity_data, severity_colors)
    after_severity_pie_css = create_pie_chart_css(after_severity_data, severity_colors)
    priority_pie_css = create_pie_chart_css(priority_data, severity_colors)
    
    # Generate HTML with CSS charts
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Accessibility Assessment - Visual Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            font-size: 32px;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 4px solid #667eea;
        }}
        h2 {{
            color: #34495e;
            font-size: 24px;
            margin: 40px 0 20px 0;
            padding-left: 15px;
            border-left: 5px solid #667eea;
        }}
        .summary-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 15px;
            margin: 30px 0;
            color: white;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .stat {{
            background: rgba(255,255,255,0.2);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            backdrop-filter: blur(10px);
        }}
        .stat-value {{
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .chart-section {{
            margin: 40px 0;
        }}
        .chart-container {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 15px;
            margin: 20px 0;
            border: 2px solid #e9ecef;
        }}
        .chart-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 30px;
            margin: 20px 0;
        }}
        .pie-chart {{
            width: 300px;
            height: 300px;
            border-radius: 50%;
            margin: 20px auto;
            position: relative;
        }}
        .pie-chart::after {{
            content: '';
            position: absolute;
            width: 150px;
            height: 150px;
            background: white;
            border-radius: 50%;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }}
        .bar-chart {{
            display: flex;
            flex-direction: column;
            gap: 15px;
            margin: 20px 0;
        }}
        .bar-row {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .bar-label {{
            width: 200px;
            font-size: 12px;
            text-align: right;
            padding-right: 10px;
        }}
        .bar-container {{
            flex: 1;
            background: #e9ecef;
            height: 30px;
            border-radius: 5px;
            overflow: hidden;
            position: relative;
        }}
        .bar {{
            height: 100%;
            display: flex;
            align-items: center;
            padding: 0 10px;
            color: white;
            font-size: 12px;
            font-weight: bold;
            border-radius: 5px;
            transition: width 0.3s ease;
        }}
        .bar-baseline {{
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }}
        .bar-after {{
            background: linear-gradient(90deg, #50E3C2 0%, #38B2AC 100%);
        }}
        .legend {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .data-table th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: bold;
        }}
        .data-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e9ecef;
        }}
        .data-table tr:hover {{
            background-color: #f8f9fa;
        }}
        .priority-critical {{
            color: #FF6B6B;
            font-weight: bold;
        }}
        .priority-important {{
            color: #FFD93D;
            font-weight: bold;
        }}
        .priority-optional {{
            color: #6BCB77;
            font-weight: bold;
        }}
        .next-steps {{
            background: #e8f4f8;
            padding: 25px;
            border-radius: 10px;
            border-left: 5px solid #17a2b8;
            margin: 30px 0;
        }}
        .next-steps ul {{
            margin-left: 20px;
            margin-top: 10px;
        }}
        .next-steps li {{
            margin: 10px 0;
            line-height: 1.6;
        }}
        .footer {{
            text-align: center;
            color: #7f8c8d;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
        }}
        @media (max-width: 768px) {{
            .container {{
                padding: 20px;
            }}
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            .bar-label {{
                width: 120px;
                font-size: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>ACCESSIBILITY ASSESSMENT - VISUAL REPORT</h1>
        
        <div class="summary-box">
            <h2 style="color: white; border: none; padding: 0; margin: 0 0 20px 0;">Current Assessment</h2>
            <div class="stats-grid">
                <div class="stat">
                    <div class="stat-value">{baseline_data['summary']['total_issues']}</div>
                    <div class="stat-label">Total Issues</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{baseline_data['summary']['files_with_issues']}</div>
                    <div class="stat-label">Files with Issues</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{baseline_data['summary']['by_severity'].get('ERROR', 0)}</div>
                    <div class="stat-label">Critical Issues</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{baseline_data['summary']['by_severity'].get('WARNING', 0)}</div>
                    <div class="stat-label">Important Issues</div>
                </div>
            </div>
            <p style="margin-top: 20px; font-size: 14px; opacity: 0.9;">
                <strong>Assessment Status:</strong> This represents the current state of accessibility issues in the Omnia documentation.
                The automatic fixer fixed 0 issues - all {baseline_data['summary']['total_issues']} issues require manual intervention.
            </p>
        </div>
        
        <h2>Severity Distribution</h2>
        <div class="chart-row">
            <div class="chart-container">
                <h3 style="text-align: center; color: #34495e; margin-bottom: 20px;">Baseline (Before Fix)</h3>
                <div class="pie-chart" style="{baseline_severity_pie_css}"></div>
                <div class="legend">
                    <div class="legend-item">
                        <div class="legend-color" style="background: #FF6B6B;"></div>
                        <span>Critical ({baseline_severity_data[0]})</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #FFD93D;"></div>
                        <span>Important ({baseline_severity_data[1]})</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #6BCB77;"></div>
                        <span>Optional ({baseline_severity_data[2]})</span>
                    </div>
                </div>
            </div>
            <div class="chart-container">
                <h3 style="text-align: center; color: #34495e; margin-bottom: 20px;">After Fix</h3>
                <div class="pie-chart" style="{after_severity_pie_css}"></div>
                <div class="legend">
                    <div class="legend-item">
                        <div class="legend-color" style="background: #FF6B6B;"></div>
                        <span>Critical ({after_severity_data[0]})</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #FFD93D;"></div>
                        <span>Important ({after_severity_data[1]})</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #6BCB77;"></div>
                        <span>Optional ({after_severity_data[2]})</span>
                    </div>
                </div>
            </div>
        </div>
        
        <h2>Issue Priority Distribution</h2>
        <div class="chart-container">
            <div class="pie-chart" style="{priority_pie_css}"></div>
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color" style="background: #FF6B6B;"></div>
                    <span>Critical ({critical_count})</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #FFD93D;"></div>
                    <span>Important ({important_count})</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #6BCB77;"></div>
                    <span>Optional ({optional_count})</span>
                </div>
            </div>
        </div>
        
        <h2>Issue Type Distribution</h2>
        <div class="chart-container">
            <div class="bar-chart">
    """
    
    # Add issue type bars
    for issue_type, issue_count in zip(issue_types, issue_counts):
        width = (issue_count / max_count) * 100 if max_count > 0 else 0
        
        html_content += f"""
                <div class="bar-row">
                    <div class="bar-label">{issue_type}</div>
                    <div class="bar-container">
                        <div class="bar bar-baseline" style="width: {width}%;">{issue_count}</div>
                    </div>
                </div>
        """
    
    html_content += """
            </div>
        </div>
        
        <h2>Top 10 Files with Most Issues</h2>
        <div class="chart-container">
            <div class="bar-chart">
    """
    
    # Add top files bars
    for file_name, count in zip(top_file_names, top_file_counts):
        width = (count / max_file_count) * 100 if max_file_count > 0 else 0
        
        html_content += f"""
                <div class="bar-row">
                    <div class="bar-label">{file_name}</div>
                    <div class="bar-container">
                        <div class="bar bar-baseline" style="width: {width}%;">{count}</div>
                    </div>
                </div>
        """
    
    html_content += """
            </div>
        </div>
        
        <h2>Detailed Data Table</h2>
        <table class="data-table">
            <tr>
                <th>Issue Type</th>
                <th>Count</th>
                <th>Priority</th>
            </tr>
    """
    
    # Add table rows
    for issue_type in sorted(issue_types):
        issue_count = baseline_data['summary']['by_issue_type'].get(issue_type, 0)
        
        if issue_type in ['MISSING_IMAGE_ALT', 'EMPTY_SECTION_TITLE']:
            priority = 'Critical'
            priority_class = 'priority-critical'
        elif issue_type in ['MISSING_DIRECTIVE_OPTION', 'NON_DESCRIPTIVE_LINK']:
            priority = 'Important'
            priority_class = 'priority-important'
        else:
            priority = 'Optional'
            priority_class = 'priority-optional'
        
        html_content += f"""
            <tr>
                <td>{issue_type}</td>
                <td>{issue_count}</td>
                <td class="{priority_class}">{priority}</td>
            </tr>
        """
    
    html_content += """
        </table>
        
        <div class="next-steps">
            <h2>Next Steps</h2>
            <ul>
                <li>Address Critical issues first (Missing Alt Text, Empty Sections)</li>
                <li>Focus on Important issues (Directive Options, Link Text)</li>
                <li>Review Optional improvements if time permits</li>
                <li>Re-run validation after manual fixes to track progress</li>
                <li>Generate comparison report after manual fixes to measure improvement</li>
            </ul>
        </div>
        
        <div class="footer">
            Report generated on 2026-07-06 | Omnia Documentation Accessibility Assessment
            <br>Baseline assessment - represents current state before manual fixes
        </div>
    </div>
</body>
</html>
    """
    
    # Change output to HTML if it's .xlsx
    if output_path.endswith('.xlsx'):
        output_path = output_path.replace('.xlsx', '.html')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Visual HTML report generated: {output_path}")
    print("Open this file in a web browser to view interactive CSS charts and visualizations")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python generate_visual_report.py <baseline_report.json> <after_report.json> <output.html>")
        sys.exit(1)
    
    baseline_report = sys.argv[1]
    after_report = sys.argv[2]
    output_file = sys.argv[3]
    
    generate_visual_report(baseline_report, after_report, output_file)
