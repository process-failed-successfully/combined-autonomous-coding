1. Add an `XPathLab` utility
   - Similar to `jsonpath-lab` or `jq-lab`, this will allow evaluating XPath queries against XML data.
   - It will use `defusedxml.ElementTree` to securely parse XML (as mandated by previous knowledge context) and evaluate XPath expressions using standard `xml.etree.ElementTree` functionality or `lxml` if available. Since the repository avoids extra dependencies when possible and uses `defusedxml.ElementTree`, we'll implement simple XPath support with the built-in `.findall()` or `.find()`.
   - Command aliases: `xpath-lab`, `xpath`
   - Operations: `evaluate`, `tui`

2. Create `shared/xpath_lab.py`
   - Contains `XpathLabManager` and `run_xpath_lab_logic()`.
   - Supports `evaluate` action taking `--input` and `--expression`.

3. Create `shared/tui_xpath.py`
   - Contains `XpathLabTab` for the interactive Textual TUI.

4. Update `main.py`
   - Add aliases to `KNOWN_COMMANDS`.
   - Add `run_xpath_lab` wrapper function.
   - Add subparsers setup.
   - Add dispatch block for `xpath-lab`.

5. Update `shared/tui.py`
   - Import `XpathLabTab` and yield it in `AgentTUI.compose()`.

6. Add unit tests
   - Create `tests/test_xpath_lab.py`
   - Create `tests/test_tui_xpath.py`
   - Ensure 100% code coverage.

7. Run all tests to verify.
   - `python3 -m pytest tests/test_xpath_lab.py tests/test_tui_xpath.py --cov=shared.xpath_lab --cov=shared.tui_xpath --cov-report=term-missing`

8. Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
9. Submit changes.
