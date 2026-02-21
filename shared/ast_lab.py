import ast
from typing import Dict, Any, Union, List

class ASTLabManager:
    """Manages AST operations: parsing and visualization."""

    def parse_code(self, code: str) -> ast.AST:
        """Parses Python code into an AST."""
        try:
            return ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"Syntax Error: {e}")

    def node_to_dict(self, node: Union[ast.AST, List, Any]) -> Any:
        """Recursively converts an AST node to a dictionary."""
        if isinstance(node, list):
            return [self.node_to_dict(item) for item in node]

        if not isinstance(node, ast.AST):
            return node

        fields = {}
        for field, value in ast.iter_fields(node):
            fields[field] = self.node_to_dict(value)

        attrs = {}
        for attr in node._attributes:
            if hasattr(node, attr):
                attrs[attr] = getattr(node, attr)

        return {
            "type": node.__class__.__name__,
            "fields": fields,
            "attributes": attrs
        }

    def dump_tree(self, code: str) -> str:
        """Returns a formatted string dump of the AST."""
        try:
            tree = self.parse_code(code)
            return ast.dump(tree, indent=2)
        except ValueError as e:
            return str(e)

def run_ast_lab_logic(args):
    """CLI Entry point for AST Lab."""
    manager = ASTLabManager()

    if args.action == "parse":
        if args.code:
            code = args.code
        elif args.file:
            try:
                with open(args.file, "r") as f:
                    code = f.read()
            except Exception as e:
                print(f"Error reading file: {e}")
                return
        else:
            print("Error: --code or --file required.")
            return

        print(manager.dump_tree(code))

    elif args.action == "check":
        if args.code:
            code = args.code
        elif args.file:
            try:
                with open(args.file, "r") as f:
                    code = f.read()
            except Exception as e:
                print(f"Error reading file: {e}")
                return
        else:
            print("Error: --code or --file required.")
            return

        try:
            manager.parse_code(code)
            print("✅ Syntax is valid.")
        except ValueError as e:
            print(f"❌ {e}")
