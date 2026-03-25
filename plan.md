1. **Goal**: Add a new `yaml2json-lab` feature to easily convert YAML to JSON format and vice versa.
2. **Components**:
   - `shared/yaml2json_lab.py`: Core logic for converting yaml string to json string, and vice versa.
   - `shared/tui_yaml2json.py`: Textual UI tab for interacting with conversions graphically.
   - `main.py` modifications to register the `yaml2json-lab` command (and its aliases `yaml2json`, `y2j`).
   - `tests/test_yaml2json_lab.py`: Unit tests for the CLI logic and manager.
   - `tests/test_tui_yaml2json.py`: Tests for the new TUI tab.
3. **Execution Steps**:
   - Write the `Yaml2JsonLabManager` logic.
   - Integrate it into the main CLI commands.
   - Create the TUI tab.
   - Write integration and unit tests.
   - Run existing CI tests to ensure nothing breaks.
