import json
import shutil
from pathlib import Path
from datetime import datetime
from shared.cost import CostCalculator
from shared.security import SecurityAuditor
from shared.network import NetworkBuilder
from shared.cli_utils import get_workflow_stage, get_project_summary, get_suggestions, WORKFLOW_STAGES

def generate_html_dashboard(project_dir: Path) -> str:
    """
    Generates a comprehensive HTML dashboard for the project.
    """
    project_dir = project_dir.resolve()

    # --- Data Collection ---

    # 1. Project Overview
    workflow_stage = get_workflow_stage(project_dir)
    stage_name = WORKFLOW_STAGES[workflow_stage]['name']

    # 2. Cost & Usage
    cost_calc = CostCalculator(project_dir)
    cost_data = cost_calc.calculate_total_cost()
    total_cost = cost_data.get("total_cost", 0.0)

    # Prepare cost data for chart (Group by Model)
    usage_by_model = {}
    for run in cost_data.get("details", []):
        if "error" in run: continue
        model = run.get("model", "unknown")
        if model not in usage_by_model:
            usage_by_model[model] = 0.0
        usage_by_model[model] += run.get("total_cost", 0.0)

    cost_chart_labels = list(usage_by_model.keys())
    cost_chart_data = list(usage_by_model.values())

    # 3. Security
    auditor = SecurityAuditor(project_dir)
    security_findings = auditor.run_all(scan_type="all", severity="low")
    security_summary = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in security_findings:
        sev = str(f.get("severity", "LOW")).upper()
        if sev in security_summary:
            security_summary[sev] += 1
        else:
            # Handle unknown severity
            security_summary["LOW"] += 1

    # 4. Network Graph
    network_builder = NetworkBuilder(project_dir)
    map_data = network_builder.add_file_nodes() # Need map_data for edges
    network_builder.add_import_edges(map_data)
    network_builder.add_git_history(limit=50, include_authors=True)
    network_json = json.dumps(network_builder.to_json())

    # 5. Suggestions
    suggestions = get_suggestions(project_dir)

    # --- HTML Generation ---
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Dashboard - {project_dir.name}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f6f8; color: #333; }}
        header {{ background-color: #2c3e50; color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }}
        h1 {{ margin: 0; font-size: 1.5rem; }}
        .container {{ padding: 2rem; max-width: 1200px; margin: 0 auto; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }}
        .card {{ background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 1.5rem; }}
        .card h2 {{ margin-top: 0; border-bottom: 2px solid #ecf0f1; padding-bottom: 0.5rem; font-size: 1.2rem; color: #2c3e50; }}

        .stat-value {{ font-size: 2rem; font-weight: bold; color: #2980b9; }}
        .stat-label {{ color: #7f8c8d; font-size: 0.9rem; }}

        .badge {{ padding: 0.25rem 0.5rem; border-radius: 4px; font-weight: bold; font-size: 0.8rem; }}
        .badge-high {{ background-color: #e74c3c; color: white; }}
        .badge-medium {{ background-color: #f39c12; color: white; }}
        .badge-low {{ background-color: #3498db; color: white; }}
        .badge-status {{ background-color: #27ae60; color: white; }}

        #network {{ height: 400px; border: 1px solid #ddd; background: #fafafa; }}

        table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background-color: #f8f9fa; color: #2c3e50; }}

        .suggestion {{ background-color: #e8f6f3; border-left: 4px solid #1abc9c; padding: 1rem; margin-bottom: 0.5rem; }}
        .suggestion code {{ background: rgba(0,0,0,0.05); padding: 2px 4px; border-radius: 3px; font-family: monospace; }}
    </style>
</head>
<body>
    <header>
        <div>
            <h1>Project Dashboard: {project_dir.name}</h1>
            <small>{project_dir}</small>
        </div>
        <div>{timestamp}</div>
    </header>

    <div class="container">

        <!-- Overview Stats -->
        <div class="grid">
            <div class="card">
                <h2>Workflow Status</h2>
                <div class="stat-value"><span class="badge badge-status">{stage_name}</span></div>
            </div>
            <div class="card">
                <h2>Total Cost (Est.)</h2>
                <div class="stat-value">${total_cost:.4f}</div>
                <div class="stat-label">Based on token usage</div>
            </div>
            <div class="card">
                <h2>Security Issues</h2>
                <div style="display: flex; gap: 1rem; margin-top: 0.5rem;">
                    <div style="text-align: center;">
                        <div class="stat-value" style="color: #e74c3c; font-size: 1.5rem;">{security_summary['HIGH']}</div>
                        <div class="stat-label">High</div>
                    </div>
                    <div style="text-align: center;">
                        <div class="stat-value" style="color: #f39c12; font-size: 1.5rem;">{security_summary['MEDIUM']}</div>
                        <div class="stat-label">Medium</div>
                    </div>
                    <div style="text-align: center;">
                        <div class="stat-value" style="color: #3498db; font-size: 1.5rem;">{security_summary['LOW']}</div>
                        <div class="stat-label">Low</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="grid" style="grid-template-columns: 1fr 1fr;">
            <!-- Cost Chart -->
            <div class="card">
                <h2>Cost by Model</h2>
                <canvas id="costChart"></canvas>
            </div>

            <!-- Suggestions -->
            <div class="card">
                <h2>Suggested Actions</h2>
                {_render_suggestions(suggestions)}
            </div>
        </div>

        <!-- Network Graph -->
        <div class="card">
            <h2>Codebase Network</h2>
            <div id="network"></div>
        </div>

        <!-- Security Findings Table -->
        <div class="card" style="margin-top: 2rem;">
            <h2>Security Findings</h2>
            {_render_security_table(security_findings)}
        </div>

    </div>

    <script>
        // Cost Chart
        const ctx = document.getElementById('costChart').getContext('2d');
        new Chart(ctx, {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(cost_chart_labels)},
                datasets: [{{
                    data: {json.dumps(cost_chart_data)},
                    backgroundColor: ['#3498db', '#e74c3c', '#f1c40f', '#2ecc71', '#9b59b6'],
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{ position: 'right' }}
                }}
            }}
        }});

        // Network Graph
        const networkData = {network_json};
        const container = document.getElementById('network');
        const options = {{
            nodes: {{
                shape: 'dot',
                size: 16,
                font: {{ size: 14 }}
            }},
            edges: {{
                width: 1,
                smooth: {{ type: 'continuous' }}
            }},
            physics: {{
                stabilization: false,
                barnesHut: {{
                    gravitationalConstant: -8000,
                    springConstant: 0.04,
                    springLength: 95
                }}
            }},
            interaction: {{
                navigationButtons: true,
                keyboard: false
            }}
        }};
        new vis.Network(container, networkData, options);
    </script>
</body>
</html>
"""
    return html_content

def _render_suggestions(suggestions):
    if not suggestions:
        return "<p>No specific suggestions. Project seems healthy.</p>"

    html = ""
    for s in suggestions:
        html += f"""
        <div class="suggestion">
            <strong>{s['reason']}</strong><br>
            <code>{s['command']}</code>
        </div>
        """
    return html

def _render_security_table(findings):
    if not findings:
        return "<p>No security issues found.</p>"

    html = """
    <table>
        <thead>
            <tr>
                <th>Severity</th>
                <th>Type</th>
                <th>Description</th>
                <th>Location</th>
            </tr>
        </thead>
        <tbody>
    """

    for f in findings:
        sev = str(f.get('severity', 'LOW')).upper()
        badge_class = "badge-low"
        if sev == "HIGH": badge_class = "badge-high"
        elif sev == "MEDIUM": badge_class = "badge-medium"

        file_loc = f"{f.get('file', 'N/A')}"
        if f.get('line'):
            file_loc += f":{f['line']}"

        html += f"""
        <tr>
            <td><span class="badge {badge_class}">{sev}</span></td>
            <td>{f.get('type', 'Unknown')}</td>
            <td>{f.get('description', '')}</td>
            <td><code>{file_loc}</code></td>
        </tr>
        """

    html += "</tbody></table>"
    return html
