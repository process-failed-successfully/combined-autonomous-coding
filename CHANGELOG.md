# CHANGELOG


## v0.8.0 (2026-01-04)

### Bug Fixes

- **workflow**: Add checkout step for local action
  ([`e7fc674`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/e7fc674eb3d45520e709053f879f1ac324ed8e0c))

### Features

- Add real-time logging to the agent dashboard
  ([#51](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/51),
  [`d668da3`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/d668da31756b30c3c78e6fb32e8b8247340cef3c))

This commit introduces a new feature that displays real-time logs from the Python agents in the web
  dashboard.

The implementation includes: - A new `MemoryLogHandler` in the Python agent that captures the last
  50 log messages. - Updates to the `AgentClient` to send the captured logs with each heartbeat. - A
  new API endpoint in the Node.js backend to receive and store the logs. - Frontend modifications to
  display the logs in the agent cards. - New unit tests for the `MemoryLogHandler` and the Node.js
  backend. - Updates to existing tests to ensure compatibility with the new logging setup.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Replace jules-invoke with local action to fix arg list too long
  ([`ed96a07`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/ed96a079ce9eaa3eab79bafab4d23ef5bba99b34))


## v0.7.2 (2026-01-04)

### Performance Improvements

- Optimize file reading in execute_read_block
  ([`1a3229f`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/1a3229f55c260c0bbf6773a7357b000f1560c5b2))

Optimized `execute_read_block` to stream lines from the file object directly instead of reading the
  entire content into memory first. This reduces memory usage for large files and avoids creating
  unnecessary intermediate large strings.

- Replaced `f.read().splitlines()` with iteration over `f` - Used `line.rstrip('\n')` to handle
  newlines


## v0.7.1 (2026-01-04)

### Bug Fixes

- **ci**: Add missing SQLAlchemy dependency
  ([`fbdbaae`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/fbdbaae51f7eda58754b01a65cfc80a43c4c55eb))

- **ci**: Configure git identity for worktree manager tests
  ([`76701c3`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/76701c30c1ced0f08fb8212cf82703e556811b94))


## v0.7.0 (2025-12-27)

### Features

- Add profile support for local ollama service
  ([`76eec68`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/76eec684bbe83a8b55de70b7ce776103fee9fe5e))

- Updated `docker-compose.yml` to put `ollama` under `profiles: ["local"]`. - Updated `safe_run.sh`
  to auto-enable `COMPOSE_PROFILES=local` if `--agent local` is passed. - This ensures `ollama` is
  not started unless specifically requested.

- Introduce local model support via docker (Ollama)
  ([`82993c7`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/82993c700bef05a4185cef5716beb609a1d72ccf))

- Added `ollama` service to `docker-compose.yml`. - Added `DEFAULT_MODEL_LOCAL` and
  `agent_type="local"` support in `shared/config.py`. - Created `agents/local` package with
  `LocalClient` (OpenAI compatible) and `LocalAgent`. - Updated `agents/config_manager.py` to
  support `local` agent type. - Updated `main.py` to dispatch to `LocalAgent`.


## v0.6.0 (2025-12-26)

### Code Style

- Fix linting errors in CLI launcher tests
  ([`6ace356`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/6ace3567f97bd656827aa08ca3237eac019b9482))

### Features

- Verify and complete Agent CLI Launcher features
  ([`e08e3d5`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/e08e3d516d8fa657a1cb857d07d2b3f3a4c10ba7))

- Verified detached mode and config management - Fixed and enabled CLI launcher tests - Confirmed
  Jira integration tests pass - Updated feature_list.json to all passing


## v0.5.0 (2025-12-24)

### Features

- Implement initial CLI structure with Typer, Rich, and Docker check
  ([`ac37eac`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/ac37eac5e9f0441fdd36d40a3e3eca3e2f2ef539))

- Created bin/agent with basic Typer CLI commands (run, list, attach, logs, stop, config). -
  Integrated Rich for terminal UI, including colored output and a progress spinner. - Added Docker
  daemon pre-flight check using docker-py. - Updated feature_list.json to reflect completed
  features: cli_launcher_implementation, interactive_cli, dependency_management, and
  intelligent_pre_flight_checks. - Updated .gitignore to exclude temporary agent files.


## v0.4.0 (2025-12-22)


## v0.3.0 (2025-12-18)

### Features

- Support cursor agent in cleaner to avoid gemini auth errors
  ([`2929d2c`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/2929d2ce948246652fdabcc7adad581c577e5ac8))

- **tests**: Add comprehensive tests for shared modules and sprint logic
  ([`1beccc2`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/1beccc203ee28cbf95de4e794bf84a11257e04a4))

- Added `tests/test_github_client.py` to cover `shared/github_client.py`. - Added
  `tests/test_workflow.py` to cover `shared/workflow.py`. - Added `tests/test_git_wrapper.py` to
  cover `shared/git_wrapper.py`. - Enhanced `tests/test_sprint_extended.py` to cover edge cases in
  `agents/shared/sprint.py`. - Improved overall test coverage from 81% to 86%. - Fixed missing
  coverage in critical shared utilities.


## v0.2.1 (2025-12-18)

### Bug Fixes

- Better handle sprint alignment
  ([`d2de59c`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/d2de59cb8baf8a0304c4a44a16c1a9f93dc68907))

- Sprint complete ends session
  ([`c2e638f`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/c2e638f6ad62a217c8bd6f6e6fb6fb65a6431760))


## v0.2.0 (2025-12-16)

### Chores

- Increase docker awareness
  ([`3ba7fbb`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/3ba7fbbca03e7e2539abd657de3f2ca9367407b4))

### Features

- Notifications
  ([`9fba0a3`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/9fba0a3c5fa53f73ac870c1042d38adc2543db8c))


## v0.1.0 (2025-12-15)

### Bug Fixes

- Add prometheus_client and verification test
  ([`328569c`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/328569c420b7ca91e3608ade42e0f784f3043e05))

- Dependency installation and build config
  ([`75e5d20`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/75e5d209b105e521aa06e9f0347fea22f37bb116))

- Include subpackages in build
  ([`d6e74d3`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/d6e74d3d105fe5b64269cc187d2e0094071aa3ad))

### Chores

- Reduce bandit severity to medium
  ([`810f8ad`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/810f8ad4037ee8cabd54baaa7c2995c7027d40fe))

- Releases
  ([`827cf3f`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/827cf3fb14ec42c3eb877662271239b1e30b0802))

### Features

- **ci**: Implement robust CI pipeline and update local checks
  ([`d29b1c1`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/d29b1c13bcf3e2b96aa917d23dac58e97b830486))
