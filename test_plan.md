I have noticed there is a UUID lab and other ID generator labs (NanoID, Snowflake, ULID), but no KSUID lab.

K-Sortable Globally Unique IDs (KSUIDs) are highly valuable in distributed systems since they are sortable by timestamp, providing an excellent alternative to standard UUIDs.

I propose to implement a `ksuid-lab` tool with the following features:
1. Generate KSUIDs.
2. Inspect KSUIDs (decoding and parsing out the timestamp and payload).
3. A TUI tab for an interactive KSUID lab.

Plan:
1. Create `shared/ksuid_lab.py` containing a `KsuidLabManager` (generation and inspection logic) and the CLI handler `run_ksuid_lab_logic`.
2. Create `shared/tui_ksuid.py` containing a `KsuidLabTab` widget for the TUI.
3. Update `main.py` to register the `ksuid-lab` parser, aliases, subcommands (`generate`, `inspect`, `tui`), and `run_ksuid_lab` dispatch. Also add it to `KNOWN_COMMANDS`.
4. Update `shared/tui.py` to import and mount the `KsuidLabTab` into the main TUI app.
5. Create tests in `tests/test_ksuid_lab.py` and `tests/test_tui_ksuid.py` to ensure high test coverage.
6. Run `run_tests.sh` to ensure nothing is broken and my tests pass.
