import json
import shutil
import subprocess
import html
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import defaultdict
from shared.map import scan_project

class NetworkBuilder:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir.resolve()
        self.nodes: Dict[str, Dict[str, Any]] = {}  # id -> node_data
        self.edges: List[Dict[str, Any]] = []
        self.file_to_id: Dict[str, str] = {}
        self._next_id = 0

    def _get_id(self, key: str) -> str:
        if key not in self.file_to_id:
            self.file_to_id[key] = str(self._next_id)
            self._next_id += 1
        return self.file_to_id[key]

    def add_file_nodes(self):
        """Scans the project for files and adds them as nodes."""
        # reusing map logic to get python files, but we can also just walk
        map_data = scan_project(self.project_dir)

        for rel_path, node in map_data.items():
            node_id = self._get_id(rel_path)
            self.nodes[node_id] = {
                "id": node_id,
                "label": Path(rel_path).name,
                "title": rel_path,
                "group": "file",
                "shape": "box",
                "color": "#97C2FC" # Blue
            }

        return map_data

    def add_import_edges(self, map_data: Dict[str, Any]):
        """Adds edges based on imports."""
        # Create a map of "module.path" -> "file/path.py" for resolution
        module_map = {}
        for rel_path in map_data.keys():
            # Convert shared/utils.py -> shared.utils
            module_name = rel_path.replace("/", ".").replace(".py", "")
            module_map[module_name] = rel_path

        for rel_path, node in map_data.items():
            source_id = self._get_id(rel_path)

            for dep in node.dependencies:
                # Try to resolve dep (e.g. 'shared.utils') to a file
                target_file = None

                # Direct match
                if dep in module_map:
                    target_file = module_map[dep]
                else:
                    # Try finding it as a prefix?
                    # For now, strict matching or matching known files
                    # If dep is 'os' or 'sys', it won't match, which is correct (we ignore stdlib)
                    pass

                if target_file:
                    target_id = self._get_id(target_file)
                    self.edges.append({
                        "from": source_id,
                        "to": target_id,
                        "arrows": "to",
                        "color": {"color": "#848484", "opacity": 0.5},
                        "title": "imports"
                    })

    def add_git_history(self, limit: int = 100, include_authors: bool = True):
        """Analyzes git history for co-editing and authorship."""
        git_path = shutil.which("git")
        if not git_path or not (self.project_dir / ".git").is_dir():
            return

        # Get log with files and authors
        # Format: Hash|Author|Date
        # file1
        # file2
        # ...
        try:
            cmd = [git_path, "-C", str(self.project_dir), "log", f"-n{limit}", "--name-only", "--pretty=format:COMMIT|%H|%an"]
            result = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")

            current_commit = None
            current_author = None
            commit_files = []

            co_edits: Dict[Tuple[str, str], int] = defaultdict(int)
            author_edits: Dict[Tuple[str, str], int] = defaultdict(int)

            lines = result.stdout.strip().split('\n')
            for line in lines:
                if not line:
                    if commit_files:
                        self._process_commit_files(commit_files, current_author, co_edits, author_edits)
                        commit_files = []
                    continue

                if line.startswith("COMMIT|"):
                    if commit_files:
                        self._process_commit_files(commit_files, current_author, co_edits, author_edits)
                    _, _, author = line.split("|")
                    current_author = author
                    commit_files = []
                else:
                    # It's a file path
                    file_path = line.strip()
                    # Only include if it's a file we know about (exists in map)
                    # or just include it if it exists on disk now?
                    # Let's check existence relative to project root
                    if (self.project_dir / file_path).exists():
                         commit_files.append(file_path)

            # Process last commit
            if commit_files:
                self._process_commit_files(commit_files, current_author, co_edits, author_edits)

            # Add Author Nodes and Edges
            if include_authors:
                for (author, file_path), count in author_edits.items():
                    if file_path not in self.file_to_id:
                        continue # Skip files not in our graph (e.g. ignored ones)

                    file_id = self._get_id(file_path)
                    author_id = self._get_id(f"author:{author}")

                    if author_id not in self.nodes:
                        self.nodes[author_id] = {
                            "id": author_id,
                            "label": author,
                            "group": "author",
                            "shape": "ellipse",
                            "color": "#FB7E81" # Red/Pink
                        }

                    # Weight based on edits
                    self.edges.append({
                        "from": author_id,
                        "to": file_id,
                        "color": {"color": "#FB7E81", "opacity": 0.3},
                        "value": count,
                        "title": f"Edited {count} times"
                    })

            # Add Co-edit Edges
            for (f1, f2), count in co_edits.items():
                if f1 in self.file_to_id and f2 in self.file_to_id:
                    id1 = self._get_id(f1)
                    id2 = self._get_id(f2)

                    # Check if edge already exists (e.g. import)
                    # We can add a separate edge or merge? Vis.js supports multiple edges if ID is different
                    # But simpler is to add a distinct "co-edit" edge
                    self.edges.append({
                        "from": id1,
                        "to": id2,
                        "color": {"color": "#7BE141", "opacity": 0.3}, # Green
                        "value": count,
                        "dashes": True,
                        "title": f"Co-edited {count} times"
                    })

        except Exception as e:
            print(f"Error processing git history: {e}")

    def _process_commit_files(self, files: List[str], author: str, co_edits, author_edits):
        # Record author edits
        for f in files:
            author_edits[(author, f)] += 1

        # Record co-edits (all pairs)
        # Sort to ensure consistent keys
        sorted_files = sorted(files)
        for i in range(len(sorted_files)):
            for j in range(i + 1, len(sorted_files)):
                f1, f2 = sorted_files[i], sorted_files[j]
                co_edits[(f1, f2)] += 1

    def to_json(self):
        return {
            "nodes": list(self.nodes.values()),
            "edges": self.edges
        }

class NetworkVisualizer:
    def generate_html(self, data: Dict[str, Any]) -> str:
        json_data = json.dumps(data)

        return f"""<!DOCTYPE HTML>
<html>
<head>
  <title>Codebase Network Graph</title>
  <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style type="text/css">
    body, html {{ font-family: sans-serif; height: 100%; margin: 0; overflow: hidden; }}
    #network {{ width: 100%; height: 100%; }}
    .legend {{
        position: absolute;
        top: 10px;
        right: 10px;
        background: rgba(255, 255, 255, 0.8);
        padding: 10px;
        border: 1px solid #ccc;
        border-radius: 5px;
        z-index: 100;
    }}
    .legend-item {{ margin-bottom: 5px; }}
    .dot {{ display: inline-block; width: 10px; height: 10px; margin-right: 5px; }}
  </style>
</head>
<body>
<div class="legend">
  <div class="legend-item"><span class="dot" style="background: #97C2FC;"></span>File</div>
  <div class="legend-item"><span class="dot" style="background: #FB7E81; border-radius: 50%;"></span>Author</div>
  <div class="legend-item"><span class="dot" style="background: #848484;"></span>Import (Solid)</div>
  <div class="legend-item"><span class="dot" style="background: #7BE141;"></span>Co-edit (Dashed)</div>
</div>
<div id="network"></div>
<script type="text/javascript">
  var container = document.getElementById('network');
  var data = {json_data};

  var options = {{
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
      keyboard: true
    }}
  }};

  var network = new vis.Network(container, data, options);
</script>
</body>
</html>
"""

def run_network_logic(project_dir: Path, output_file: Path, include_authors: bool = False, include_git: bool = True, limit: int = 100):
    builder = NetworkBuilder(project_dir)

    print("Scanning files...")
    map_data = builder.add_file_nodes()

    print("Building import graph...")
    builder.add_import_edges(map_data)

    if include_git:
        print("Analyzing git history...")
        builder.add_git_history(limit=limit, include_authors=include_authors)

    visualizer = NetworkVisualizer()
    html_content = visualizer.generate_html(builder.to_json())

    output_file.write_text(html_content, encoding="utf-8")
    print(f"✅ Network graph saved to: {output_file}")
