1. **Analyze the Repository:**
   - Evaluated `main.py` which aggregates an immense number of `*-lab` commands (over 100).
   - Identified missing support for Server-Sent Events (SSE). The codebase currently has `ws-lab` for WebSockets, `webhook-lab` for webhooks, and `http-lab` for standard HTTP, but no tool for connecting to SSE streams. This is a highly valuable feature for API developers interacting with LLM APIs, streaming notification services, etc.
2. **Implement `sse-lab` Core Logic:**
   - Created `shared/sse_lab.py` utilizing `aiohttp` for async HTTP streaming.
   - Built an event listener that parses the `data:`, `event:`, `id:`, and `retry:` fields standard in the SSE protocol.
3. **Implement `sse-lab` TUI:**
   - Created `shared/tui_sse.py` based on Textual, providing an interactive UI to stream events, similar to the `ws-lab` UI.
4. **Update `main.py` CLI:**
   - Register the `sse-lab` subcommand in `main.py` with arguments for URL, headers, and TUI.
   - Dispatch to `run_sse_lab_logic` and `run_tui` as appropriate.
5. **Update `shared/tui.py`:**
   - Add the `SseLabTab` to the main Textual App configuration.
6. **Add Unit Tests:**
   - Created `tests/test_sse_lab.py` to test the CLI logic and the async parsing functionality utilizing mocks for `aiohttp`.
7. **Pre-commit Steps:**
   - Execute all pre-commit instructions, linting, type checking, and tests to ensure everything is correct and no existing functionality is broken.
8. **Submit:**
   - Commit the changes and submit the PR.
