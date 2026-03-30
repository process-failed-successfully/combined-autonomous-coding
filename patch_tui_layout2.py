with open("shared/tui.py", "r") as f:
    text = f.read()

# Fix the messy indentation we just added
text = text.replace("                yield Xml2YamlTab()\n                        yield Xml2TomlTab()", "                yield Xml2YamlTab()\n            with TabPane(\"XML to TOML\", id=\"tab-xml2toml\"):\n                yield Xml2TomlTab()")

with open("shared/tui.py", "w") as f:
    f.write(text)
