"""
Knowledge Graph Generator
=========================

Generates visualizations of the agent's knowledge base.
"""

import json
import html
from pathlib import Path
from typing import List, Dict, Any, Optional

from shared.knowledge import KnowledgeManager
from shared.models import AgentKnowledge

def generate_knowledge_graph(project_dir: Path, output_format: str = "html", output_file: Optional[Path] = None) -> str:
    """
    Generates a knowledge graph in the specified format.
    Returns the content (or path to file) as a string.
    """
    manager = KnowledgeManager()
    items = manager.list_knowledge()

    if not items:
        return "No knowledge items found."

    if output_format == "json":
        return _generate_json(items, output_file)
    elif output_format == "mermaid":
        return _generate_mermaid(items, output_file)
    elif output_format == "html":
        return _generate_html(items, project_dir, output_file)
    else:
        raise ValueError(f"Unknown format: {output_format}")

def _generate_json(items: List[AgentKnowledge], output_file: Optional[Path]) -> str:
    data = [
        {
            "id": item.id,
            "category": item.category,
            "content": item.content,
            "source": item.source_agent,
            "created_at": str(item.created_at)
        }
        for item in items
    ]
    json_str = json.dumps(data, indent=2)

    if output_file:
        output_file.write_text(json_str)
        return f"JSON graph saved to {output_file}"
    return json_str

def _generate_mermaid(items: List[AgentKnowledge], output_file: Optional[Path]) -> str:
    """Generates a Mermaid graph with subgraphs for categories."""
    lines = ["graph TD"]

    # Group by category
    by_category: Dict[str, List[AgentKnowledge]] = {}
    for item in items:
        cat = item.category or "Uncategorized"
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)

    for cat, cat_items in by_category.items():
        # Sanitize category name for ID
        cat_id = cat.replace(" ", "_").replace("-", "_")
        lines.append(f"    subgraph {cat_id} [{cat}]")
        for item in cat_items:
            # Truncate content for display
            display_content = (item.content[:40] + "...") if len(item.content) > 40 else item.content
            # Escape quotes
            display_content = display_content.replace('"', "'")
            # Node
            lines.append(f"        k{item.id}(\"{display_content}\")")
        lines.append("    end")

    mermaid_str = "\n".join(lines)

    if output_file:
        output_file.write_text(mermaid_str)
        return f"Mermaid graph saved to {output_file}"
    return mermaid_str

def _generate_html(items: List[AgentKnowledge], project_dir: Path, output_file: Optional[Path]) -> str:
    """Generates an interactive HTML graph using vis-network."""

    nodes = []
    edges = []

    # Track categories to create central nodes
    categories = set()

    for item in items:
        cat = item.category or "Uncategorized"
        categories.add(cat)

        # Item Node
        # Truncate content for label, full content in title (tooltip)
        label = (item.content[:30] + "...") if len(item.content) > 30 else item.content
        nodes.append({
            "id": f"item_{item.id}",
            "label": label,
            "title": html.escape(item.content),
            "group": "item",
            "shape": "box"
        })

        # Edge to Category
        edges.append({
            "from": f"cat_{cat}",
            "to": f"item_{item.id}"
        })

    # Category Nodes
    for cat in categories:
        nodes.append({
            "id": f"cat_{cat}",
            "label": cat,
            "group": "category",
            "shape": "ellipse",
            "font": {"size": 20}
        })

    # Default output path if not provided
    if not output_file:
        output_file = project_dir / "knowledge_graph.html"

    # HTML Template
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Agent Knowledge Graph</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        #mynetwork {{
            width: 100%;
            height: 800px;
            border: 1px solid lightgray;
        }}
        body {{ font-family: sans-serif; }}
    </style>
</head>
<body>
    <h2>Agent Knowledge Graph</h2>
    <div id="mynetwork"></div>
    <script type="text/javascript">
        var nodes = new vis.DataSet({json.dumps(nodes)});
        var edges = new vis.DataSet({json.dumps(edges)});

        var container = document.getElementById('mynetwork');
        var data = {{
            nodes: nodes,
            edges: edges
        }};
        var options = {{
            groups: {{
                category: {{
                    color: {{ background: '#97C2FC', border: '#2B7CE9' }},
                    font: {{ size: 18 }}
                }},
                item: {{
                    color: {{ background: '#FFFF00', border: '#FFA500' }}
                }}
            }},
            layout: {{
                improvedLayout: true
            }},
            physics: {{
                stabilization: false,
                barnesHut: {{
                    gravitationalConstant: -8000,
                    springConstant: 0.04,
                    springLength: 95
                }}
            }}
        }};
        var network = new vis.Network(container, data, options);
    </script>
</body>
</html>
"""
    output_file.write_text(html_content)
    return f"Interactive graph saved to {output_file}"
