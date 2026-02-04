import fnmatch
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from shared.map import scan_project, CodeNode

def matches_pattern(text: str, pattern: str) -> bool:
    """Checks if text matches glob or regex pattern."""
    if not pattern:
        return True
    try:
        # Try regex first if it looks like one (e.g. starts with ^)
        if pattern.startswith("^") or pattern.endswith("$") or "\\" in pattern:
             return bool(re.search(pattern, text))
        # Fallback to glob
        return fnmatch.fnmatch(text, pattern)
    except re.error:
        # Fallback to glob if regex fails
        return fnmatch.fnmatch(text, pattern)

def filter_nodes(map_data: Dict[str, CodeNode],
                 type_filter: str = None,
                 name_filter: str = None,
                 import_filter: str = None,
                 base_filter: str = None,
                 decorator_filter: str = None) -> List[Dict[str, Any]]:
    """
    Traverses the map and returns matching nodes (flattened).
    """
    results = []

    def traverse(node: CodeNode, parent_file: str):
        # Check matching criteria
        match = True

        # 1. Type filter
        if type_filter and node.type != type_filter:
            match = False

        # 2. Name filter
        if match and name_filter:
            if not matches_pattern(node.name, name_filter):
                match = False

        # 3. Import filter
        if match and import_filter:
            # Check if any dependency matches
            has_imp = any(matches_pattern(dep, import_filter) for dep in node.dependencies)
            if not has_imp:
                match = False

        # 4. Bases filter (only for classes)
        if match and base_filter:
            if node.type == 'class':
                has_base = any(matches_pattern(base, base_filter) for base in node.bases)
                if not has_base:
                    match = False
            else:
                match = False # Non-classes can't match base filter

        # 5. Decorator filter (functions and classes)
        if match and decorator_filter:
            if node.type in ['class', 'function']:
                has_dec = any(matches_pattern(dec, decorator_filter) for dec in node.decorators)
                if not has_dec:
                    match = False
            else:
                match = False

        if match:
            # Flatten result
            results.append({
                "name": node.name,
                "type": node.type,
                "file": parent_file, # or node.file
                "lineno": node.lineno,
                "end_lineno": node.end_lineno,
                "bases": node.bases,
                "decorators": node.decorators,
                "dependencies": list(node.dependencies)
            })

        # Recurse
        for child in node.children:
            traverse(child, parent_file)

    for file_path, node in map_data.items():
        traverse(node, file_path)

    return results

def run_code_query(args):
    """
    Entry point for code-query command.
    """
    project_dir = args.project_dir.resolve()

    # Run scan
    map_data = scan_project(project_dir)

    # Filter
    results = filter_nodes(
        map_data,
        type_filter=args.type,
        name_filter=args.name,
        import_filter=args.imports,
        base_filter=args.bases,
        decorator_filter=args.decorator
    )

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"--- Code Query Results ({len(results)}) ---")
        for res in results:
            extra = ""
            if res['type'] == 'class' and res['bases']:
                extra += f" (bases: {', '.join(res['bases'])})"
            if res['decorators']:
                extra += f" @{', @'.join(res['decorators'])}"
            if args.imports and res['dependencies']:
                 extra += f" [deps: {len(res['dependencies'])}]"

            print(f"[{res['type']}] {res['name']} {extra}")
            print(f"  File: {res['file']}:{res['lineno']}")
