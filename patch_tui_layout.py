import re

with open("shared/tui.py", "r") as f:
    content = f.read()

# Look for TabbedContent( and add Xml2TomlTab to it.
# Usually, in tui.py, there's a big compose() method yielding TabbedContent
# which then yields all the Tabs.

# The safest way is to find a known tab like Xml2YamlTab and insert Xml2TomlTab right after it.

if "yield Xml2TomlTab()" not in content:
    content = content.replace("yield Xml2YamlTab()", "yield Xml2YamlTab()\n                        yield Xml2TomlTab()")
    content = content.replace("yield Xml2YamlTab(id=\"tab-xml2yaml\")", "yield Xml2YamlTab(id=\"tab-xml2yaml\")\n                    yield Xml2TomlTab(id=\"tab-xml2toml\")")
    content = content.replace("yield TabPane(\"Xml2Yaml\", Xml2YamlTab(), id=\"tab-xml2yaml\")", "yield TabPane(\"Xml2Yaml\", Xml2YamlTab(), id=\"tab-xml2yaml\")\n                    yield TabPane(\"Xml2Toml\", Xml2TomlTab(), id=\"tab-xml2toml\")")

with open("shared/tui.py", "w") as f:
    f.write(content)
