with open("tests/test_tui_ksuid.py", "r") as f:
    content = f.read()

import_statement = "import pytest\n"
if "pytest.importorskip" not in content:
    content = content.replace("import pytest\n", "import pytest\npytest.importorskip('textual')\n")
else:
    # replace first line with importorskip immediately
    new_content = "import pytest\npytest.importorskip('textual')\n"
    for line in content.splitlines()[1:]:
        if "pytest.importorskip" not in line:
            new_content += line + "\n"
    content = new_content

with open("tests/test_tui_ksuid.py", "w") as f:
    f.write(content)
