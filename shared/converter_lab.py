import json
import yaml
import tomlkit
import defusedxml.ElementTree as DetusedET
import xml.etree.ElementTree as ET
from typing import Any, Dict
import shlex


class ConverterManager:
    """
    Manages code and format conversions.
    """

    def parse_curl(self, curl_cmd: str) -> Dict[str, Any]:
        """
        Parses a curl command string into a dictionary.
        Best-effort parsing for standard flags.
        """
        if not curl_cmd.strip().lower().startswith("curl"):
            raise ValueError("Not a curl command")

        try:
            tokens = shlex.split(curl_cmd)
        except ValueError as e:
            raise ValueError(f"Invalid shell syntax: {e}")

        # Remove 'curl'
        if tokens and tokens[0] == "curl":
            tokens = tokens[1:]

        result = {
            "method": "GET",
            "url": "",
            "headers": {},
            "data": None,
            "auth": None
        }

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token in ("-X", "--request"):
                if i + 1 < len(tokens):
                    result["method"] = tokens[i+1].upper()
                    i += 2
                    continue

            elif token in ("-H", "--header"):
                if i + 1 < len(tokens):
                    header = tokens[i+1]
                    if ":" in header:
                        key, val = header.split(":", 1)
                        result["headers"][key.strip()] = val.strip()
                    i += 2
                    continue

            elif token in ("-d", "--data", "--data-raw", "--data-binary", "--data-ascii"):
                if i + 1 < len(tokens):
                    # If multiple data flags, curl concatenates them with '&'
                    # But for simplicity, we'll just take the last one or try to merge if it looks like form data
                    # Here we overwrite for simplicity unless we detect it's JSON
                    result["data"] = tokens[i+1]
                    # Implicit POST if data is present and method not specified
                    if result["method"] == "GET":
                        result["method"] = "POST"
                    i += 2
                    continue

            elif token in ("-u", "--user"):
                if i + 1 < len(tokens):
                    result["auth"] = tokens[i+1]
                    i += 2
                    continue

            elif token.startswith("-"):
                # Ignore other flags
                i += 1
                if i < len(tokens) and not tokens[i].startswith("-"):
                    # Skip value if it looks like an argument (heuristic)
                    i += 1
                continue

            else:
                # Positional argument = URL
                if not result["url"]:
                    result["url"] = token
                i += 1

        if not result["url"]:
            raise ValueError("No URL found")

        return result

    def curl_to_python(self, curl_cmd: str) -> str:
        """Generates Python requests code from curl."""
        try:
            req = self.parse_curl(curl_cmd)
        except ValueError as e:
            return f"# Error parsing curl: {e}"

        code = "import requests\n\n"

        url = req["url"]
        method = req["method"]
        headers = req["headers"]
        data = req["data"]
        auth = req["auth"]

        args = [f'"{url}"']

        if headers:
            code += "headers = {\n"
            for k, v in headers.items():
                code += f'    "{k}": "{v}",\n'
            code += "}\n\n"
            args.append("headers=headers")

        if data:
            # Check if JSON
            try:
                json.loads(data)
                # It's JSON
                # Escape quotes properly for python string
                # or use triple quotes
                code += f"data = '''{data}'''\n\n"
                # If content-type is json, requests can take json= parameter if we parse it,
                # or data= string. `requests` usually prefers data=string for exact raw body or json=dict.
                # Let's use data=string to be safe with raw curl data.
                args.append("data=data")
            except Exception:
                code += f"data = {repr(data)}\n\n"
                args.append("data=data")

        if auth:
            if ":" in auth:
                user, pw = auth.split(":", 1)
                args.append(f'auth=("{user}", "{pw}")')
            else:
                args.append(f'auth=("{auth}", "")')

        args_str = ", ".join(args)
        code += f"response = requests.{method.lower()}({args_str})\n"
        code += "print(response.status_code)\n"
        code += "print(response.text)\n"

        return code

    def curl_to_node(self, curl_cmd: str) -> str:
        """Generates Node.js fetch code from curl."""
        try:
            req = self.parse_curl(curl_cmd)
        except ValueError as e:
            return f"// Error parsing curl: {e}"

        code = "const fetch = require('node-fetch'); // npm install node-fetch\n\n"

        url = req["url"]
        method = req["method"]
        headers = req["headers"]
        data = req["data"]
        auth = req["auth"]

        # Basic Auth header handling
        if auth:
            import base64
            b64 = base64.b64encode(auth.encode()).decode()
            headers["Authorization"] = f"Basic {b64}"

        code += f'const url = "{url}";\n\n'

        options = {
            "method": method
        }
        if headers:
            options["headers"] = headers

        if data:
            options["body"] = data

        # Format options as JS object
        opts_str = "{\n"
        opts_str += f'  method: "{method}",\n'

        if headers:
            opts_str += "  headers: {\n"
            for k, v in headers.items():
                opts_str += f'    "{k}": "{v}",\n'
            opts_str += "  },\n"

        if data:
            # If looks like JSON, maybe pretty print?
            # For now, just raw string
            opts_str += f'  body: {json.dumps(data)},\n'

        opts_str += "}"

        code += f"const options = {opts_str};\n\n"
        code += "fetch(url, options)\n"
        code += "  .then(res => res.text())\n"
        code += "  .then(text => console.log(text))\n"
        code += "  .catch(err => console.error('error:' + err));\n"

        return code

    def json_to_pydantic(self, json_str: str, model_name: str = "Root") -> str:
        """Generates Pydantic models from JSON."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return f"# Error parsing JSON: {e}"

        models = {}  # name -> code

        def get_type_name(val: Any) -> str:
            if isinstance(val, str):
                return "str"
            if isinstance(val, bool):
                return "bool"
            if isinstance(val, int):
                return "int"
            if isinstance(val, float):
                return "float"
            if val is None:
                return "Optional[Any]"
            if isinstance(val, list):
                return "List[Any]"  # refined later
            if isinstance(val, dict):
                return "Dict[str, Any]"  # refined later
            return "Any"

        def generate_model(name: str, obj: Dict[str, Any]) -> str:
            # Check if model already exists with same structure?
            # For simplicity, if name exists, verify keys match, else rename
            original_name = name
            counter = 1
            while name in models:
                # Check collision - naive check
                name = f"{original_name}{counter}"
                counter += 1

            lines = [f"class {name}(BaseModel):"]
            if not obj:
                lines.append("    pass")

            for k, v in obj.items():
                field_name = k
                # Handle invalid python identifiers? naive replace
                if not field_name.isidentifier():
                    # Pydantic alias handling is complex, skip for MVP or use Alias
                    pass

                type_str = "Any"
                if isinstance(v, dict):
                    # Nested model
                    sub_name = f"{name}{k.capitalize()}"
                    type_str = generate_model(sub_name, v)
                elif isinstance(v, list):
                    if v:
                        item = v[0]
                        if isinstance(item, dict):
                            sub_name = f"{name}{k.capitalize()}Item"
                            item_type = generate_model(sub_name, item)
                            type_str = f"List[{item_type}]"
                        else:
                            type_str = f"List[{get_type_name(item)}]"
                    else:
                        type_str = "List[Any]"
                else:
                    type_str = get_type_name(v)

                lines.append(f"    {field_name}: {type_str}")

            models[name] = "\n".join(lines)
            return name

        if isinstance(data, dict):
            generate_model(model_name, data)
        elif isinstance(data, list):
            if data and isinstance(data[0], dict):
                _ = generate_model(f"{model_name}Item", data[0])
                # We need a root container or just return the item model?
                # User usually expects the object model.
                # If root is list, we can't make a Pydantic model representing a list directly as a class.
                # We return `List[ItemModel]`.
                # But to display code, we need the item model definition.
                pass
            else:
                return "# Root is a list of primitives, no model needed."
        else:
            return "# Root is a primitive, no model needed."

        code = "from typing import List, Optional, Any, Dict\nfrom pydantic import BaseModel\n\n"
        # Output models in reverse order (dependencies first) is hard without DAG.
        # But Python requires defined before use.
        # Dict preserves insertion order since 3.7.
        # Recursive calls happen *inside* generate_model loop.
        # Wait, my recursion `type_str = generate_model(...)` executes immediately.
        # So child models are added to `models` *before* parent model finishes.
        # So iterating `models` values should be in correct order (children first).

        for name, model_code in models.items():
            code += model_code + "\n\n"

        return code

    def json_to_typescript(self, json_str: str, interface_name: str = "Root") -> str:
        """Generates TypeScript interfaces from JSON."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return f"// Error parsing JSON: {e}"

        interfaces = {}

        def get_ts_type(val: Any) -> str:
            if isinstance(val, str):
                return "string"
            if isinstance(val, bool):
                return "boolean"
            if isinstance(val, (int, float)):
                return "number"
            if val is None:
                return "null"
            return "any"

        def generate_interface(name: str, obj: Dict[str, Any]) -> str:
            original_name = name
            counter = 1
            while name in interfaces:
                name = f"{original_name}{counter}"
                counter += 1

            lines = [f"interface {name} {{"]
            for k, v in obj.items():
                type_str = "any"
                if isinstance(v, dict):
                    sub_name = f"{name}{k.capitalize()}"
                    type_str = generate_interface(sub_name, v)
                elif isinstance(v, list):
                    if v:
                        item = v[0]
                        if isinstance(item, dict):
                            sub_name = f"{name}{k.capitalize()}Item"
                            item_type = generate_interface(sub_name, item)
                            type_str = f"{item_type}[]"
                        else:
                            type_str = f"{get_ts_type(item)}[]"
                    else:
                        type_str = "any[]"
                else:
                    type_str = get_ts_type(v)

                lines.append(f"  {k}: {type_str};")
            lines.append("}")

            interfaces[name] = "\n".join(lines)
            return name

        if isinstance(data, dict):
            generate_interface(interface_name, data)
        elif isinstance(data, list):
            if data and isinstance(data[0], dict):
                generate_interface(f"{interface_name}Item", data[0])
            else:
                return "// Root is list of primitives"
        else:
            return "// Root is primitive"

        code = ""
        for name, iface_code in interfaces.items():
            code += iface_code + "\n\n"

        return code

    def json_to_go(self, json_str: str, struct_name: str = "Root") -> str:
        """Generates Go structs from JSON."""
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return f"// Error parsing JSON: {e}"

        structs = {}

        def get_go_type(val: Any) -> str:
            if isinstance(val, str):
                return "string"
            if isinstance(val, bool):
                return "bool"
            if isinstance(val, int):
                return "int"
            if isinstance(val, float):
                return "float64"
            if val is None:
                return "interface{}"
            return "interface{}"

        def generate_struct(name: str, obj: Dict[str, Any]) -> str:
            original_name = name
            counter = 1
            while name in structs:
                name = f"{original_name}{counter}"
                counter += 1

            lines = [f"type {name} struct {{"]
            for k, v in obj.items():
                field_name = "".join(word.capitalize() for word in k.split("_"))
                type_str = "interface{}"

                if isinstance(v, dict):
                    sub_name = f"{name}{field_name}"
                    type_str = generate_struct(sub_name, v)
                elif isinstance(v, list):
                    if v:
                        item = v[0]
                        if isinstance(item, dict):
                            sub_name = f"{name}{field_name}Item"
                            item_type = generate_struct(sub_name, item)
                            type_str = f"[]{item_type}"
                        else:
                            type_str = f"[]{get_go_type(item)}"
                    else:
                        type_str = "[]interface{}"
                else:
                    type_str = get_go_type(v)

                lines.append(f'\t{field_name} {type_str} `json:"{k}"`')
            lines.append("}")

            structs[name] = "\n".join(lines)
            return name

        if isinstance(data, dict):
            generate_struct(struct_name, data)
        elif isinstance(data, list):
            if data and isinstance(data[0], dict):
                generate_struct(f"{struct_name}Item", data[0])
            else:
                return "// Root is list of primitives"
        else:
            return "// Root is primitive"

        code = ""
        for name, struct_code in structs.items():
            code += struct_code + "\n\n"

        return code

    def convert_format(self, content: str, from_fmt: str, to_fmt: str) -> str:
        """
        Converts content between formats: json, yaml, toml, xml.
        """
        if not content.strip():
            return ""

        from_fmt = from_fmt.lower()
        to_fmt = to_fmt.lower()

        if from_fmt == to_fmt:
            return content

        # Parse to dict
        data = self._parse(content, from_fmt)

        # Serialize to string
        return self._serialize(data, to_fmt)

    def _parse(self, content: str, fmt: str) -> Any:
        if fmt == "json":
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
        elif fmt == "yaml":
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML: {e}")
        elif fmt == "toml":
            try:
                return tomlkit.parse(content)
            except tomlkit.exceptions.ParseError as e:
                raise ValueError(f"Invalid TOML: {e}")
        elif fmt == "xml":
            try:
                root = DetusedET.fromstring(content)
                return self._xml_to_dict(root)
            except DetusedET.ParseError as e:
                raise ValueError(f"Invalid XML: {e}")
        else:
            raise ValueError(f"Unsupported input format: {fmt}")

    def _serialize(self, data: Any, fmt: str) -> str:
        if fmt == "json":
            return json.dumps(data, indent=2)
        elif fmt == "yaml":
            # PyYAML dump doesn't handle tomlkit objects well sometimes, convert to dict first
            if hasattr(data, "unwrap"):
                data = data.unwrap()
            return yaml.dump(data, sort_keys=False)
        elif fmt == "toml":
            if not isinstance(data, dict):
                # TOML requires root to be a table (dict)
                data = {"value": data}
            return tomlkit.dumps(data)
        elif fmt == "xml":
            root = self._dict_to_xml("root", data)
            if hasattr(ET, "indent"):
                ET.indent(root, space="  ", level=0)
            return ET.tostring(root, encoding="unicode", method="xml")
        else:
            raise ValueError(f"Unsupported output format: {fmt}")

    def _xml_to_dict(self, element: ET.Element) -> Any:
        """Naive XML to Dict conversion."""
        result = {}
        # Attributes
        if element.attrib:
            result["@attributes"] = element.attrib

        # Text content
        text = element.text and element.text.strip()
        if text:
            result["#text"] = text

        # Children
        for child in element:
            child_data = self._xml_to_dict(child)
            tag = child.tag

            if tag in result:
                if isinstance(result[tag], list):
                    result[tag].append(child_data)
                else:
                    result[tag] = [result[tag], child_data]
            else:
                result[tag] = child_data

        # Simplify: if no attributes and no children, return text directly
        if not result.get("@attributes") and len(element) == 0:
            return text or ""

        # If we have text but no children/attributes (already handled above)
        # If we have children but text is empty, remove #text key
        if "#text" in result and not result["#text"]:
            del result["#text"]

        return result

    def _dict_to_xml(self, tag: str, data: Any) -> ET.Element:
        """Naive Dict to XML conversion."""
        elem = ET.Element(tag)

        if isinstance(data, dict):
            for key, value in data.items():
                if key == "@attributes":
                    if isinstance(value, dict):
                        # Ensure string values for attributes
                        elem.attrib.update({k: str(v) for k, v in value.items()})
                elif key == "#text":
                    elem.text = str(value)
                elif isinstance(value, list):
                    for item in value:
                        child = self._dict_to_xml(key, item)
                        elem.append(child)
                else:
                    child = self._dict_to_xml(key, value)
                    elem.append(child)
        elif isinstance(data, list):
            # Should not happen if called correctly (list is handled by parent)
            # But if root is list, we wrap in 'item'
            for item in data:
                child = self._dict_to_xml("item", item)
                elem.append(child)
        else:
            elem.text = str(data)

        return elem


def run_converter_lab_logic(args) -> bool:
    """CLI handler for Converter Lab."""
    manager = ConverterManager()

    import sys

    def get_input(arg_val):
        if arg_val:
            return arg_val
        if not sys.stdin.isatty():
            try:
                return sys.stdin.read()
            except Exception:
                pass
        return None

    try:
        action = getattr(args, "action", None)
        if not action:
            print("Error: No action specified.")
            return False

        if action == "format":
            content = get_input(getattr(args, "input", None))
            if not content:
                print("Error: Input content required via arg or stdin.")
                return False

            from_fmt = getattr(args, "from_fmt", "json")
            to_fmt = getattr(args, "to_fmt", "yaml")

            result = manager.convert_format(content, from_fmt, to_fmt)
            print(result)
            return True

        elif action == "curl":
            content = get_input(getattr(args, "input", None))
            if not content:
                print("Error: Input CURL command required via arg or stdin.")
                return False

            target = getattr(args, "target", "python").lower()
            if target == "python":
                result = manager.curl_to_python(content)
            elif target == "node":
                result = manager.curl_to_node(content)
            else:
                print(f"Error: Unknown target {target}")
                return False

            print(result)
            return True

        elif action == "types":
            content = get_input(getattr(args, "input", None))
            if not content:
                print("Error: Input JSON required via arg or stdin.")
                return False

            target = getattr(args, "target", "pydantic").lower()
            name = getattr(args, "name", "Root")

            if target == "pydantic":
                result = manager.json_to_pydantic(content, name)
            elif target == "typescript" or target == "ts":
                result = manager.json_to_typescript(content, name)
            elif target == "go":
                result = manager.json_to_go(content, name)
            else:
                print(f"Error: Unknown target {target}")
                return False

            print(result)
            return True

        else:
            print(f"Error: Unknown action {action}")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False
