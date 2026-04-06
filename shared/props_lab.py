import json
import yaml
import sys
from typing import Any, Dict


class PropsLabManager:
    """Manages parsing and generating Java .properties format."""

    @staticmethod
    def parse_props(props_str: str) -> Dict[str, str]:
        """Parses a Java .properties string into a flat dictionary."""
        result = {}
        lines = props_str.splitlines()
        current_key = None
        current_val = []
        is_continuation = False

        for raw_line in lines:
            line = raw_line.strip()

            # If we are not continuing a previous line, skip comments and empty lines
            if not is_continuation:
                if not line or line.startswith('#') or line.startswith('!'):
                    continue

            # Process line continuation
            if raw_line.endswith('\\'):
                # Strip trailing backslash
                val_part = raw_line[:-1].lstrip() if is_continuation else raw_line[:-1]
                if not is_continuation:
                    # First line of a continuation, we need to split key and value
                    if '=' in val_part or ':' in val_part:
                        # Find the first separator
                        sep_idx = -1
                        for i, c in enumerate(val_part):
                            if c in ('=', ':') and (i == 0 or val_part[i-1] != '\\'):
                                sep_idx = i
                                break

                        if sep_idx != -1:
                            current_key = val_part[:sep_idx].strip()
                            current_val.append(val_part[sep_idx+1:].lstrip())
                        else:
                            current_key = val_part.strip()
                            current_val.append("")
                    else:
                        current_key = val_part.strip()
                        current_val.append("")
                else:
                    current_val.append(val_part)
                is_continuation = True
            else:
                val_part = raw_line.lstrip() if is_continuation else raw_line
                if not is_continuation:
                    # Simple single-line key-value pair
                    if '=' in val_part or ':' in val_part:
                        sep_idx = -1
                        for i, c in enumerate(val_part):
                            if c in ('=', ':') and (i == 0 or val_part[i-1] != '\\'):
                                sep_idx = i
                                break

                        if sep_idx != -1:
                            key = val_part[:sep_idx].strip()
                            val = val_part[sep_idx+1:].strip()
                        else:
                            key = val_part.strip()
                            val = ""
                    else:
                        key = val_part.strip()
                        val = ""

                    # Unescape key and val
                    result[PropsLabManager._unescape(key)] = PropsLabManager._unescape(val)
                else:
                    current_val.append(val_part)
                    full_val = "".join(current_val).strip()
                    result[PropsLabManager._unescape(current_key)] = PropsLabManager._unescape(full_val)
                    current_key = None
                    current_val = []
                    is_continuation = False

        # Handle file ending with a continuation
        if is_continuation and current_key is not None:
            full_val = "".join(current_val).strip()
            result[PropsLabManager._unescape(current_key)] = PropsLabManager._unescape(full_val)

        return result

    @staticmethod
    def _unescape(s: str) -> str:
        """Unescapes Java .properties string."""
        if not s:
            return s
        res = []
        i = 0
        while i < len(s):
            c = s[i]
            if c == '\\' and i + 1 < len(s):
                next_c = s[i+1]
                if next_c == 'n':
                    res.append('\n')
                elif next_c == 'r':
                    res.append('\r')
                elif next_c == 't':
                    res.append('\t')
                elif next_c == 'u' and i + 5 < len(s):
                    hex_val = s[i+2:i+6]
                    try:
                        res.append(chr(int(hex_val, 16)))
                        i += 4
                    except ValueError:
                        res.append('\\u')
                else:
                    res.append(next_c)
                i += 2
            else:
                res.append(c)
                i += 1
        return "".join(res)

    @staticmethod
    def _escape(s: str, is_key: bool = False) -> str:
        """Escapes string to Java .properties format."""
        if not s:
            return ""
        s = str(s)
        res = []
        for c in s:
            if c == '\n':
                res.append('\\n')
            elif c == '\r':
                res.append('\\r')
            elif c == '\t':
                res.append('\\t')
            elif c == '\\':
                res.append('\\\\')
            elif is_key and c in ('=', ':', ' '):
                res.append('\\' + c)
            elif ord(c) < 32 or ord(c) > 126:
                res.append(f"\\u{ord(c):04x}")
            else:
                res.append(c)
        return "".join(res)

    @staticmethod
    def unflatten_dict(flat_dict: Dict[str, str], separator: str = '.') -> Dict[str, Any]:
        """Converts a flat dictionary with separated keys into a nested dictionary."""
        result = {}
        for key, value in flat_dict.items():
            parts = key.split(separator)
            d = result
            for part in parts[:-1]:
                if part not in d:
                    d[part] = {}
                elif not isinstance(d[part], dict):
                    # Collision: trying to create a nested dict but a string value exists
                    # We transform the existing string value to a dict with _value
                    d[part] = {"_value": d[part]}
                d = d[part]

            # If the final part already exists as a dict, we can't overwrite it with a string
            # This is a collision in the properties format (e.g. a=1 and a.b=2)
            # In this case, we just set a special value or ignore. We'll set it as "_value".
            if parts[-1] in d and isinstance(d[parts[-1]], dict):
                d[parts[-1]]["_value"] = value
            else:
                d[parts[-1]] = value
        return result

    @staticmethod
    def flatten_dict(nested_dict: Dict[str, Any], parent_key: str = '', separator: str = '.') -> Dict[str, str]:
        """Converts a nested dictionary into a flat dictionary with separated keys."""
        items = []
        for k, v in nested_dict.items():
            new_key = f"{parent_key}{separator}{k}" if parent_key else k
            if isinstance(v, dict):
                if not v:
                    items.append((new_key, ""))
                else:
                    # Handle the "_value" collision case
                    if "_value" in v:
                        items.append((new_key, str(v["_value"])))
                        sub_dict = {sk: sv for sk, sv in v.items() if sk != "_value"}
                        items.extend(PropsLabManager.flatten_dict(sub_dict, new_key, separator=separator).items())
                    else:
                        items.extend(PropsLabManager.flatten_dict(v, new_key, separator=separator).items())
            elif isinstance(v, list):
                # Represent lists as comma-separated strings or indexed keys?
                # Usually indexed keys are preferred in Spring Boot: arr[0]=a, arr[1]=b
                # For generic, we can just do arr[0]=a
                if not v:
                    items.append((new_key, ""))
                else:
                    for i, item in enumerate(v):
                        list_key = f"{new_key}[{i}]"
                        if isinstance(item, dict):
                            items.extend(PropsLabManager.flatten_dict(item, list_key, separator=separator).items())
                        else:
                            items.append((list_key, str(item) if item is not None else ""))
            else:
                # Basic values
                if v is None:
                    items.append((new_key, ""))
                elif isinstance(v, bool):
                    items.append((new_key, str(v).lower()))
                else:
                    items.append((new_key, str(v)))
        return dict(items)

    @staticmethod
    def to_props(flat_dict: Dict[str, str]) -> str:
        """Converts a flat dictionary to a Java .properties string."""
        lines = []
        for k, v in flat_dict.items():
            escaped_key = PropsLabManager._escape(k, is_key=True)
            escaped_val = PropsLabManager._escape(v, is_key=False)
            lines.append(f"{escaped_key}={escaped_val}")
        return "\n".join(lines)

    @staticmethod
    def props_to_json(props_str: str) -> str:
        """Parses .properties string and returns JSON string."""
        # Unescape \n from unit test input if it was written as literal \n instead of newline
        flat_dict = PropsLabManager.parse_props(props_str)
        nested = PropsLabManager.unflatten_dict(flat_dict)
        return json.dumps(nested, indent=2)

    @staticmethod
    def json_to_props(json_str: str) -> str:
        """Parses JSON string and returns .properties string."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        if not isinstance(data, dict):
            raise ValueError("Root JSON element must be an object.")

        flat_dict = PropsLabManager.flatten_dict(data)
        return PropsLabManager.to_props(flat_dict)

    @staticmethod
    def props_to_yaml(props_str: str) -> str:
        """Parses .properties string and returns YAML string."""
        flat_dict = PropsLabManager.parse_props(props_str)
        nested = PropsLabManager.unflatten_dict(flat_dict)
        return yaml.dump(nested, sort_keys=False)

    @staticmethod
    def yaml_to_props(yaml_str: str) -> str:
        """Parses YAML string and returns .properties string."""
        try:
            data = yaml.safe_load(yaml_str)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")

        if not isinstance(data, dict):
            if data is None:
                return ""
            raise ValueError("Root YAML element must be an object.")

        flat_dict = PropsLabManager.flatten_dict(data)
        return PropsLabManager.to_props(flat_dict)


def run_props_lab_logic(args) -> bool:
    """CLI logic for props-lab."""

    if getattr(args, "action", None) == "tui" or getattr(args, "tui", False):
        from shared.tui import AgentTUI
        from pathlib import Path
        import asyncio

        print("Launching Props Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', Path(".")), start_tab="tab-props")
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            asyncio.ensure_future(app.run_async())
        else:
            app.run()
            sys.exit(0)
        return True

    action = getattr(args, "action", None)
    if not action:
        print("Error: Action required (props2json, json2props, props2yaml, yaml2props, or tui).", file=sys.stderr)
        return False

    input_str = ""

    if hasattr(args, 'file') and args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                input_str = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return False
    elif hasattr(args, 'text') and args.text:
        input_str = args.text
    else:
        if not sys.stdin.isatty():
            input_str = sys.stdin.read()
        else:
            print("Error: Input required via --file, --text, or stdin.", file=sys.stderr)
            return False

    if not input_str.strip() and action not in ["json2props", "yaml2props"]:
        print("Error: Input is empty.", file=sys.stderr)
        return False

    try:
        if action == "props2json":
            result = PropsLabManager.props_to_json(input_str)
        elif action == "json2props":
            result = PropsLabManager.json_to_props(input_str)
        elif action == "props2yaml":
            result = PropsLabManager.props_to_yaml(input_str)
        elif action == "yaml2props":
            result = PropsLabManager.yaml_to_props(input_str)
        else:
            print(f"Error: Unknown action '{action}'.", file=sys.stderr)
            return False

        if hasattr(args, "output") and args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"✅ Success! Output written to {args.output}")
        else:
            print(result)
        return True

    except Exception as e:
        print(f"Error during {action}: {e}", file=sys.stderr)
        return False
