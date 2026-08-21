import ast
import sys

def verify_tests():
    with open("tests/test_main.py", "r") as f:
        content = f.read()

    tree = ast.parse(content)
    found = False

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name == "test_parse_args_ulid_extract":
                found = True

    if not found:
        print("Test test_parse_args_ulid_extract not found")
        sys.exit(1)

    print("Tests found and syntactically valid!")

verify_tests()
