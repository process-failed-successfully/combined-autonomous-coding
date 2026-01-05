# CHANGELOG


## v0.9.0 (2026-01-05)

### Features

- Add 'clean' subcommand to remove agent-generated artifacts
  ([#70](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/70),
  [`439aeff`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/439aeff1f95494c9cca3eb0358f5da81de795886))

This commit introduces a new 'clean' subcommand to the main CLI. This command removes all
  agent-generated files and directories from a project, allowing users to easily reset the project
  state without affecting their source code.

The subcommand: - Deletes a predefined list of artifacts such as state files (e.g.,
  .agent_db.sqlite, COMPLETED), reports, and temporary directories (e.g., worktrees/). - Prompts the
  user for confirmation before deleting to prevent accidental data loss. - Includes a `--yes` flag
  to bypass the confirmation for use in scripts. - Is accompanied by a robust suite of unit tests to
  verify its functionality.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add --dry-run flag to display final configuration
  ([#67](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/67),
  [`1c33163`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/1c33163964e62f7e7198b8d14bbbcc9241bd070d))

This commit introduces a `--dry-run` flag to the main script. When used, the flag will print the
  final, resolved configuration as a JSON object and exit without running the agent. This is useful
  for debugging and verifying configuration settings.

The following changes were made: - Added the `--dry-run` argument to `main.py`. - Implemented a
  custom `EnhancedJSONEncoder` in `shared/utils.py` to handle `pathlib.Path` and dataclass objects.
  - Updated existing tests in `test_main.py` and `test_jira_mode_integration.py` to be compatible
  with the new feature.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add `history` command to CLI
  ([#84](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/84),
  [`794ec04`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/794ec048f67b13796c3b9b675b8d992aee40e8c2))

Adds a new `history` subcommand to the `main.py` CLI.

This command provides a summary of all previous agent runs for the current project by reading a
  history of run IDs from a new `.agent_history` file. For each run, it displays the run ID,
  timestamp, and a summary of the final log entries.

The main execution path is also updated to append the `agent_id` of each new run to the
  `.agent_history` file, ensuring a persistent record.

Strong unit tests are included for the new command, covering success and failure cases, such as
  missing history or log files.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add `show-config` subcommand and deprecate `--dry-run`
  ([#69](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/69),
  [`64cc049`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/64cc049610740a17cd5d246478bf0e384adfc878))

This commit introduces a new `show-config` subcommand to the CLI, providing a more intuitive and
  consistent way to display the final resolved configuration. The existing `--dry-run` flag is now
  deprecated in favor of the new subcommand but remains functional to ensure backward compatibility.

Key changes: - Added a `show-config` subcommand to `main.py`. - Marked the `--dry-run` flag as
  deprecated and added a warning message. - Created a `run_show_config` function to handle the
  configuration display logic. - Added comprehensive unit tests to `tests/test_main.py` to verify
  the functionality of both the new subcommand and the deprecated flag.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add archive command to preserve agent artifacts
  ([#71](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/71),
  [`688c5dc`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/688c5dc1ea8939f6deaee34bd1b642cebe1a80aa))

Adds a new `archive` subcommand to the CLI.

This command moves all agent-generated artifacts (e.g., `COMPLETED`, `feature_list.json`,
  `.agent_db.sqlite`) into a timestamped subdirectory within `.agent_archives/`.

This provides a non-destructive alternative to the `clean` command, allowing users to clear their
  workspace while preserving the results of a run for later analysis or debugging.

The feature is accompanied by a new unit test suite that verifies the archiving logic, including the
  handling of cases where no artifacts are present.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add config validation subcommand
  ([#61](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/61),
  [`e67eea5`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/e67eea5538fd8cf467bd9b24bb5e614f5ce76925))

Adds a new `validate` subcommand to `main.py` to allow users to check the validity of their
  `agent_config.yaml` file without running a full agent task.

This feature improves usability by providing early feedback on configuration errors.

The subcommand checks for: - Existence of the configuration file. - Correct YAML syntax. - Presence
  of required keys for integrations like Jira. - Correct data types for configuration values.

A comprehensive test suite is included to verify the validator's logic and exit codes.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add doctor command for environment health checks
  ([#87](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/87),
  [`633e5e3`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/633e5e347bfbd3a5a9584c5e5f3fa65aae066580))

This commit introduces a new `doctor` subcommand to the CLI.

The `doctor` command runs a series of checks to verify that the user's environment is correctly
  configured for running the agent. This includes: - Validating the `agent_config.yaml` file. -
  Checking for the presence of the `git` executable. - Verifying connectivity to Jira and
  notification webhooks, if configured. - Ensuring the project directory is writable.

This feature improves the user experience by helping to diagnose and resolve common setup issues.

Strong unit tests have been added to verify the functionality of the new command in various success
  and failure scenarios.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add empty-trash subcommand to main.py
  ([#73](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/73),
  [`ca00705`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/ca0070544560f267e0c8313e33e965c73a739978))

This commit introduces a new `empty-trash` subcommand to the `main.py` CLI. This feature provides a
  safe and explicit way for users to permanently delete the contents of the `.agent_trash`
  directory, which is used by the `clean` command to temporarily store agent-generated artifacts.

The command includes a confirmation prompt to prevent accidental data loss, which can be bypassed
  with a `--yes` flag for scripting purposes. It also handles edge cases, such as the trash
  directory not existing or being empty.

Strong unit tests have been added in `tests/test_main_empty_trash.py` to ensure the command's
  functionality, safety, and correct handling of user confirmations.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add interactive configure command
  ([#59](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/59),
  [`32b9021`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/32b902118a15afd44f1ef2ceb5e78ca0e5876a29))

This commit introduces a new `configure` subcommand to the `main.py` script. This feature provides a
  user-friendly, interactive way to generate and update the `agent_config.yaml` file.

Key improvements: - Simplifies the setup process for new users. - Reduces the risk of YAML syntax
  errors. - Guides users through configuring Jira, Slack/Discord webhooks, and other settings. -
  Uses `platformdirs` to store the configuration in the appropriate user-specific directory.

A comprehensive unit test has been added to `tests/test_configure.py` to ensure the command
  functions correctly.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add list-agents subcommand
  ([#66](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/66),
  [`e9410a1`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/e9410a1571ccc649fa127d0dda2249684f6d1175))

Adds a new `list-agents` subcommand to the CLI to display a list of available agents and their
  descriptions.

This change centralizes the agent definitions into a single `AVAILABLE_AGENTS` dictionary, which is
  now used to dynamically populate the choices for the `--agent` argument and the output of the
  `list-agents` subcommand. This improves discoverability for users and simplifies maintenance for
  developers.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add restore subcommand
  ([#74](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/74),
  [`518017a`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/518017a2724a110286fc69d65fc25df27d00debf))

This commit introduces a new `restore` subcommand to the CLI.

The `restore` command provides a safe and easy way for users to recover agent-generated artifacts
  that have been moved to the `.agent_trash` directory by the `clean` command. It finds the most
  recent trash archive, checks for any file conflicts in the project directory, and restores the
  files with user confirmation.

This feature improves the tool's usability by making the `clean` action reversible, reducing the
  risk of accidental data loss.

A comprehensive suite of unit tests has been added in `tests/test_main_restore.py` to ensure the
  reliability of the new subcommand, covering success cases, conflict handling, and user
  cancellation.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add status command to CLI
  ([#81](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/81),
  [`7fd471a`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/7fd471a972c02dcb9c5291c3f32096564b771c48))

This commit introduces a new 'status' command to the CLI, providing users with a convenient way to
  get a snapshot of the agent's progress on a project.

The `status` command displays: - The current workflow stage (e.g., In Progress, Completed, QA
  Passed, Signed Off). - A summary of features from `feature_list.json`. - The ID of the last agent
  run and a snippet from the corresponding log file. - The current Git status of the project
  directory.

A comprehensive unit test suite is included to ensure the command's functionality and correctness
  across different project states.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add support for configuration profiles
  ([#68](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/68),
  [`d4a6e4b`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/d4a6e4b821fc9305940d8a2c771346168cc85ff4))

This commit introduces a new `--profile` CLI argument that allows users to select a configuration
  profile from the `agent_config.yaml` file.

Profiles are defined under a `profiles` key in the configuration file. When a profile is selected,
  its settings are merged on top of the base configuration, with command-line arguments taking the
  highest precedence.

This feature enhances the CLI's flexibility by making it easier to switch between different
  configurations (e.g., for different models, agents, or execution parameters) without modifying the
  configuration file.

Additionally, this commit: - Restores deleted tests in `tests/test_config_loader.py`. - Adds
  comprehensive unit tests for the new profile loading functionality.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add trash subcommand for artifact management
  ([#75](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/75),
  [`d9ac5fb`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/d9ac5fb06cef1ad5700f0da67d0b849b3df97fd7))

This commit introduces a new `trash` subcommand to manage agent-generated artifacts. The new command
  provides a more intuitive and flexible interface for managing trashed files, with support for
  listing, restoring, and clearing trash archives.

The `trash` subcommand includes the following actions: - `list`: Displays all trash archives and
  their contents. - `restore`: Restores a specific, named archive, or the latest one if no name is
  provided. - `clear`: Deletes a specific archive, or all archives if the `--all` flag is used.

The old `restore` and `empty-trash` commands have been deprecated in favor of the new `trash`
  subcommand. Warning messages have been added to the old commands to guide users to the new
  interface.

Unit tests have been added to `tests/test_main_trash.py` to ensure the new `trash` subcommand works
  as expected and to prevent regressions.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- **cli**: Deprecate archive command and enhance clean command
  ([#76](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/76),
  [`f1ea6f5`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/f1ea6f525975b31e94dc6310cbcecf3a585b8975))

This commit deprecates the `archive` command and moves its functionality under the `clean` command
  with an `--archive` flag.

New feature: - The `clean` command now supports an `--archive` flag, which moves artifacts to the
  `.agent_archives` directory. - The `--force` and `--archive` flags are mutually exclusive to
  prevent conflicting actions.

Improvements: - The `archive` command is now deprecated and will be removed in a future version. -
  The `README.md` file has been updated to reflect the new functionality. - A comprehensive test
  suite for the `clean` command has been added, covering all modes of operation (trash, force, and
  archive), interactive prompts, and edge cases.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- **cli**: Enhance clean and trash commands
  ([#83](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/83),
  [`39a0901`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/39a0901e542a5f499827a3643dd3e470d2046228))

Improves the developer experience by making the `clean` and `trash` commands more intuitive and
  useful.

The `clean` command now automatically finds and includes the log file from the last agent run,
  ensuring that all run-related artifacts are managed together.

The `trash list` command is enhanced to display a summary of any log file found within a trashed
  archive. This provides immediate context about a run without needing to restore the files.

Added comprehensive unit tests to verify the new functionality.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- **main**: Make clean command safer by moving files to trash
  ([#72](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/72),
  [`0b3b250`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/0b3b250942c5bccd88c6b9e738598702f2242472))

The `clean` subcommand has been modified to move agent-generated artifacts to a timestamped trash
  directory (`.agent_trash/`) by default instead of permanently deleting them. This provides a
  safety net against accidental data loss.

The original destructive behavior is preserved behind a new `--force` flag. The command's help text
  and output have been updated to reflect this new functionality.

Added comprehensive tests to verify both the default "move to trash" behavior and the `--force`
  deletion behavior.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>


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
