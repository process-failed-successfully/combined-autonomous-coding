# CHANGELOG


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
