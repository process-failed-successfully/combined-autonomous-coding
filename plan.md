1. **Understand the Goal**: Add a high-value feature with strong testing, ensuring not to break existing tests or do simple cleanup/documentation.
2. **Current State**: The `YamlLabManager` lacks a `query` functionality, which is present in the `JsonLabManager`. This `query` feature evaluates a Python expression against the YAML data (similar to JSON). Adding this makes the `yaml-lab` tool more powerful and consistent with the `json-lab` tool.
3. **Proposed Feature**: Add a `query` subcommand to `yaml-lab`. This subcommand will let users evaluate Python expressions on loaded YAML data (e.g. `main.py yaml query --input my.yaml --expression "len(data['items'])"`).
4. **Implementation Steps**:
    * **Add `query` to `YamlLabManager`**: Implement a method that safely evaluates an expression with a restricted scope, passing the parsed YAML as `data` (same as in `JsonLabManager`).
    * **Add `query` to `run_yaml_lab_logic`**: Implement the CLI handling for `args.action == "query"`, passing `args.input` and `args.expression` or `args.path`.
    * **Add CLI arguments**: Modify `main.py` where `yaml-lab` arguments are configured to include the `query` action and the necessary arguments (`input` and `path`).
    * **Add Tests**: Write tests in `tests/test_yaml_lab.py` to cover both `YamlLabManager.query` and `run_yaml_lab_logic(query)`.
5. **Pre-commit**: Follow instructions using the `pre_commit_instructions` tool to ensure tests pass and everything complies with the guidelines.
6. **Submit**: Use the `submit` tool to create the branch, commit with a good message, and push the changes.
