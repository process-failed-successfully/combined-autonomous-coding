# CHANGELOG


## v0.13.0 (2026-01-18)

### Features

- Add 'todos' command to scan codebase for tasks
  ([#516](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/516),
  [`b08b9b9`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/b08b9b9740bcd070bbc6e430db69485be00650f5))

- Implemented `shared/todos.py` to scan for TODO, FIXME, etc. - Added `todos` subcommand to
  `main.py` with CLI options. - Supports `--blame` to fetch author/date info. - Supports `--json`
  for structured output. - Uses git search capabilities for performance with a Python fallback. -
  Added comprehensive unit and integration tests.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>


## v0.12.0 (2026-01-18)

### Features

- Add 'benchmark' command for performance analysis
  ([#126](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/126),
  [`17b3af2`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/17b3af2162e84b831a2c8a8a72fd7c57cec0b4f2))

This commit introduces a new `benchmark` subcommand to the CLI, providing tools to analyze and
  compare agent performance metrics.

The `benchmark` command includes three actions: - `show [RUN_ID]`: Displays a formatted summary of
  performance metrics from `final_metrics.txt`. It can find the metric file in the project root,
  `.agent_archives`, or `.agent_trash`. If no RUN_ID is provided, it defaults to the latest run in
  the current project. - `compare [RUN_ID_1] [RUN_ID_2]`: Shows a side-by-side comparison of two
  runs, highlighting differences in key numerical metrics and indicating whether the change is an
  improvement or a regression. - `summary`: Displays a table summarizing the key performance
  indicators for the last 10 agent runs, allowing users to track performance trends over time.

A comprehensive suite of unit tests has been added in `tests/test_main_benchmark.py` to ensure the
  new functionality is robust and correct.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add 'commit' subcommand with pre-commit test execution
  ([#172](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/172),
  [`fe0f655`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/fe0f655b517667016cf8eeb3ef957d8ec8e9ba91))

Introduces a new `commit` subcommand to the main CLI. This command provides a safe and convenient
  wrapper for creating git commits.

Key features: - Stages all unstaged changes before committing using `git add -A`, correctly handling
  new, modified, and deleted files. - Includes a `--run-tests` flag to execute project-specific
  tests. If the tests fail, the commit is automatically aborted, preventing broken code from being
  committed. - Provides clear feedback to the user throughout the process.

This feature enhances the CLI's capabilities as a developer tool by streamlining a common workflow
  and integrating a quality gate directly into the commit process.

A new test file, `tests/test_main_commit_command.py`, has been added with a comprehensive suite of
  unit tests to verify the functionality, including the pre-commit test execution and the correct
  handling of file deletions.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add 'config' subcommand for managing settings
  ([#186](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/186),
  [`dc26a02`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/dc26a02b9e197590f34ab28af618edb1c6ad2e7b))

Introduces a new `config` subcommand to the CLI to dynamically manage settings in
  `agent_config.yaml`.

This command provides three actions: - `list`: Displays all current configurations. - `get [KEY]`:
  Retrieves the value of a specific key, supporting nested keys (e.g., 'jira.url'). - `set [KEY]
  [VALUE]`: Sets the value for a specific key. It automatically parses string inputs into boolean,
  integer, or float types.

This feature improves usability by allowing users to manage their configuration without manually
  editing YAML files.

Includes a new test suite (`tests/test_main_config_command.py`) with comprehensive unit tests for
  all actions, ensuring the new functionality is robust and correct.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add 'feature' command for guided workflow
  ([#177](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/177),
  [`cff59c0`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/cff59c0efdd0eabbfcbd4ec5e1b867f7967e116f))

Introduces a new 'feature' subcommand to streamline the development workflow.

This command provides an interactive, guided process for: 1. Creating a new feature branch. 2.
  Committing all current changes. 3. Pushing the branch to the remote repository. 4. Creating a pull
  request on GitHub.

This composes existing commands (`branch`, `commit`, `push`, `pr`) into a single, user-friendly
  workflow, reducing friction and enforcing a consistent process.

Includes a comprehensive test suite that covers the successful "golden path" as well as user-aborted
  paths and various failure scenarios to ensure robustness.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add 'models' subcommand to CLI
  ([#131](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/131),
  [`508eb00`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/508eb004e0f540d41f03e560f53eb2e031fb9658))

This commit introduces a new 'models' subcommand to the CLI. This feature allows users to easily
  view the recommended models for each agent, improving discoverability and making it easier to
  configure the right model for their needs.

The subcommand can be filtered by agent using the `--agent` flag.

A new unit test file, `tests/test_main_models.py`, has been added to ensure the new command works as
  expected.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add 'plan' subcommand to generate a feature plan
  ([#115](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/115),
  [`eabf9ed`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/eabf9ed5e6dab650fd2718a19ff2e0d26d281fb4))

This commit introduces a new 'plan' subcommand to the main CLI.

This command allows users to perform a dry run of the agent's planning phase. It reads a spec file,
  generates a `feature_list.json` with the proposed plan, and prints it to the console without
  executing any code.

This feature enhances usability by allowing users to review and validate the agent's plan before
  committing to a full execution run.

- Adds a `plan` subparser and `run_plan` function to `main.py`. - Implements a
  `run_planning_session` method in `BaseAgent` to encapsulate the planning-only logic. - Includes a
  new test file `tests/test_main_plan.py` with unit tests for the new subcommand, covering both
  success and failure cases. - Updates `__init__.py` files to correctly export agent classes. - Adds
  `console_output` parameter to `setup_logger` to facilitate testing.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add 'pr' subcommand to create GitHub pull requests
  ([#169](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/169),
  [`dc8d4ae`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/dc8d4ae1302faab49f9ad04c02ce139885c7acb3))

This commit introduces a new `pr` subcommand to the CLI, allowing users to create GitHub pull
  requests directly from the command line.

The `pr create` command includes the following features: - Creates a pull request with a specified
  title and body. - Automatically detects the current feature branch and sets it as the head branch.
  - Performs pre-flight checks to ensure the branch has been pushed to the remote repository. -
  Supports both public GitHub and GitHub Enterprise instances.

To support this new feature, the following changes were made: - A new `shared/github_client.py`
  module was created to handle all interactions with the GitHub API. - The `configure` command was
  updated to include prompts for a GitHub token and host, which are stored in `agent_config.yaml`. -
  Comprehensive unit tests were added in `tests/test_main_pr.py` and `tests/test_github_client.py`
  to ensure the new functionality is well-tested.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add 'push' subcommand with safety checks
  ([#158](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/158),
  [`6de318d`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/6de318d5a0e41fc473433669fc60d363133ae6dd))

This commit introduces a new 'push' subcommand to the CLI.

This command provides a "smart" push that: - Automatically detects the current feature branch. -
  Pushes the branch to the 'origin' remote. - Includes a critical safety check to prevent direct
  pushes to protected branches ('main', 'master').

This feature improves the developer experience by simplifying the push process and adds a layer of
  protection against common Git mistakes.

The implementation includes: - A new `push` subcommand in `main.py`. - A `get_current_branch` helper
  function in `shared/git.py`. - A comprehensive suite of unit tests in `tests/test_main_push.py` to
  ensure the command is robust and reliable.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add 'test' subcommand for automated test execution
  ([#139](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/139),
  [`ed7b284`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/ed7b284d00b80bc7354139686fb862428f10cb2e))

Adds a new 'test' subcommand to the main CLI.

This feature enhances the CLI by providing a unified command to run tests in the agent's project
  directory. It automatically detects the project type (Node.js, Python, Go) and executes the
  appropriate test runner.

Key features: - Detects Node.js projects (npm, yarn, pnpm), Python projects (pytest, unittest), and
  Go projects. - Supports passing through additional arguments to the underlying test runner. -
  Includes a comprehensive suite of unit tests to verify functionality.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add 'why' subcommand and refactor commands
  ([#201](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/201),
  [`6dea8b1`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/6dea8b1c3faaac169003a48907454280072ea6c8))

Adds a new 'why' subcommand to the CLI. This command provides a user-friendly explanation of what
  other commands do, improving the discoverability and usability of the tool.

- Implemented the `why` command with descriptions for all major subcommands. - Added comprehensive
  unit tests for the `why` command. - Refactored `main.py` by moving several command implementations
  into a new `shared/commands.py` module to improve code organization and maintainability.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add `diff` subcommand to view changes
  ([#188](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/188),
  [`30a45cd`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/30a45cd1524bfbbf5fee9e275cc37cc06bee2845))

This commit introduces a new `diff` subcommand to the CLI.

The `diff` command provides a way for users to easily view code changes directly from the command
  line. It supports three modes: - `diff`: Shows all uncommitted changes in the current project,
  equivalent to `git diff HEAD`. - `diff <run_id>`: Shows the complete diff of the commit associated
  with a specific agent Run ID. - `diff <commit_hash>`: Shows the complete diff for a given git
  commit hash.

This feature enhances observability and makes it easier to debug and track the agent's work. The
  implementation reuses existing logic for finding commits by Run ID and leverages `git` to provide
  colorized output.

Strong unit tests have been added to verify all modes of the `diff` command.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add `last` command to summarize the last run
  ([#168](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/168),
  [`21dda9e`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/21dda9e2c08b9a6d51c18740dc498d67a27bab92))

This commit introduces a new `last` subcommand to the CLI.

The `last` command provides a concise summary of the most recent agent run by displaying: - Key
  performance metrics from `final_metrics.txt`. - The contents of `qa_summary.txt`. - The last 10
  lines of the corresponding log file.

This provides a convenient way for users to quickly check the outcome of an agent run without
  manually inspecting multiple files.

A new unit test file, `tests/test_main_last.py`, has been added to ensure the functionality of the
  `last` command is working correctly and handles missing files gracefully.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add `lint` subcommand to CLI
  ([#157](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/157),
  [`bf1003f`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/bf1003fd24843acc9ee0b844e89870d26e4e2c86))

This introduces a new `lint` subcommand to the main CLI, providing a convenient way to run
  project-appropriate linters.

The command automatically detects the project type (Python or Node.js) based on the presence of
  common marker files like `pyproject.toml` or `package.json`. It then executes a suitable linter:

- For Python, it prefers `ruff`, falling back to `flake8` and then `pylint`. - For Node.js, it runs
  the `lint` script defined in `package.json`.

A `--fix` option is included to allow for automatic fixing of linting errors. The implementation is
  smart enough to check for a dedicated `lint:fix` script in Node.js projects and warns users when a
  linter (like `flake8`) does not support the fix flag.

This feature improves developer experience and helps maintain code quality by integrating linting
  directly into the agent's toolkit. Comprehensive unit tests have been added to ensure the command
  functions correctly across different scenarios.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add `log` subcommand for git history
  ([#136](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/136),
  [`4be16ac`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/4be16aca9448c5853cce3ac911f9e6a9a4bafa6e))

Adds a new `log` subcommand to the CLI.

This command provides a formatted and colorized view of the `git log`, allowing users to quickly
  inspect the commit history of the project directly from the tool.

The subcommand includes: - A `--count` (`-n`) argument to limit the number of commits shown. -
  Robust checks to ensure `git` is installed and the command is run within a valid git repository. -
  Comprehensive unit and integration tests for the new functionality.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add blame command to trace agent changes
  ([#192](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/192),
  [`b8ec8a0`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/b8ec8a0c5fb8fbb81aa4ad1ba3406f966402c4c2))

Adds a new 'blame' subcommand to the CLI.

This command functions like 'git blame' but is tailored for the agentic workflow. It inspects the
  git history for a given file and displays the agent 'Run ID' responsible for each line's last
  modification.

If a commit was not made by an agent (i.e., it lacks a 'Run ID:' trailer in the commit message), the
  command falls back to showing the author's name.

This feature provides a powerful tool for debugging and understanding the agent's behavior by
  creating a direct, line-level link between the code and the specific agent run that produced it.

Includes comprehensive unit tests to validate the new functionality.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add branch subcommand for feature branch management
  ([#137](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/137),
  [`6fcc7e5`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/6fcc7e52b9feaef888ec640ffe603c8f6fb00e58))

This commit introduces a new `branch` subcommand to the CLI, allowing users to manage a dedicated
  feature branch for the agent's work.

The `branch` subcommand supports the following actions: - `create`: Creates and checks out a new
  branch, setting it as the agent's active branch. - `checkout`: Checks out an existing branch and
  sets it as the agent's active branch. - `status`: Shows the currently configured agent branch. -
  `merge`: Merges the agent's branch into the main branch. - `list`: Lists all branches and
  indicates the active agent branch.

The agent's core logic has been updated to recognize and use the configured branch, falling back to
  the previous behavior if no branch is set.

This feature improves the agent's workflow by allowing for better organization and isolation of
  changes, aligning it with standard development practices.

Comprehensive unit tests have been added to ensure the reliability of the new subcommand.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add cherry-pick command to CLI
  ([#319](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/319),
  [`5657461`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/5657461717136b15311615906ce01dcd5de4a597))

This commit introduces a new `cherry-pick` command to the CLI, allowing users to apply the changes
  from a specific commit onto the current branch.

The command accepts a `target` argument, which can be either a standard git commit hash or an
  agent-generated Run ID. The implementation resolves the Run ID by searching the git log for the
  corresponding commit.

To ensure safety and allow for user review, the command uses the `--no-commit` flag, staging the
  changes instead of committing them immediately. The command also provides clear user feedback,
  especially in the case of merge conflicts, guiding the user on how to resolve them.

Comprehensive unit tests have been added in `tests/test_cherry_pick.py` to verify the functionality,
  including success cases, conflict handling, and Run ID resolution.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add completion subcommand and tests
  ([#154](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/154),
  [`4c18ca2`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/4c18ca240189a9de255c3f28aa7d4f61bce2a6b7))

Adds a `completion` subcommand to the CLI to provide shell completion for users.

This feature improves the usability of the CLI by allowing users to auto-complete commands and
  arguments.

The implementation includes: - A `run_completion` function to generate the completion script. - A
  new test file `tests/test_main_completion.py` with tests for the subcommand. - Refactoring of
  `main.py` to make the completion logic testable.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add context command for analyzing agent file context
  ([#310](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/310),
  [`c47d1a7`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/c47d1a7a4b346545cb903c98e96c79abbb323be5))

This commit introduces a new `context` subcommand to provide users with tools to inspect and analyze
  the file context that will be used by the AI agent.

This command helps users understand the scope of the files the agent will see, identify large files,
  and analyze the composition of the project context by file type. This is crucial for managing
  token count, reducing costs, and improving agent focus.

The new command has two actions: - `context show`: Displays a git-aware file tree with file sizes
  and a summary of the total context size. - `context analyze`: Provides a summary table of the
  project context, categorized by file extension.

The implementation includes: - Logic in `shared/cli_utils.py` to handle file traversal, gitignore
  checks, and output formatting. - Integration into `main.py` with a new subparser and command
  dispatcher. - A new test suite in `tests/test_main_context.py` to ensure the command functions
  correctly and respects `.gitignore` rules.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add dashboard command
  ([#185](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/185),
  [`133ac97`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/133ac977665254cac99ed508b2b38af49c5dc9b3))

This commit introduces a new `dashboard` command to the CLI.

The `dashboard` command provides a comprehensive, scannable summary of the project's current state,
  including: - Workflow status - Git status - A summary of the last agent run - Suggested next
  commands

This feature improves the user experience by consolidating key information from multiple commands
  into a single, easy-to-use command.

This commit also includes comprehensive unit tests for the new command's logic, ensuring its
  correctness and robustness.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add discard subcommand
  ([#147](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/147),
  [`7be8fcf`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/7be8fcfa28544033c55a3aad1570fdffc329da69))

Adds a new `discard` subcommand to the CLI.

This command provides a safe and user-friendly way to discard uncommitted changes in the current git
  repository.

Features: - `discard`: Discards all uncommitted changes (both staged and unstaged) and removes all
  untracked files. - `discard <file1> <file2> ...`: Discards changes only for the specified files. -
  `discard --interactive`: Presents a list of all changed files and allows the user to interactively
  select which ones to discard.

The command includes safety prompts for all destructive operations, which can be bypassed with the
  `--yes` flag.

This feature was named `discard` to avoid ambiguity with the `git revert` command.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add format subcommand
  ([#159](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/159),
  [`08856b2`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/08856b28b80e00535fbbb88ae9e7345275be98e4))

Adds a new `format` subcommand to the CLI.

This command automatically detects the project type (Python or Node.js) and runs the appropriate
  code formatter (`black` for Python, `prettier` for Node.js).

It includes a `--check` flag to run in a dry-run mode, which is useful for CI checks.

This feature improves developer productivity and ensures code consistency across the project.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add git proxy subcommand for worktrees
  ([#146](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/146),
  [`6986698`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/69866989740dfe9c232686dd661dc4aadd515e97))

This commit introduces a new `git` subcommand to the CLI.

This command acts as a proxy, allowing users to run any Git command directly on a specific task's
  worktree by providing a task ID. This significantly improves the developer experience and
  streamlines the workflow when interacting with agent-managed worktrees.

For example: `./main.py git --task <task_id> status`

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add glance command for a high-level project overview
  ([#138](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/138),
  [`3ff6b01`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/3ff6b01d1f349c63ab85228588432c940c21cce8))

This commit introduces a new `glance` command to the CLI.

The `glance` command provides a quick, high-level terminal dashboard that displays the most critical
  project information in a single screen: - The project's current workflow stage - A summary of the
  git status, including counts of staged, unstaged, and untracked files - A suggestion for the next
  logical command to run

This feature reuses existing logic from the `status` and `suggest` commands to ensure consistency
  and minimize new code.

The implementation includes: - A `run_glance` function in `main.py` to orchestrate the data
  gathering and formatting. - The addition of the `glance` subcommand to the `argparse`
  configuration. - A new test file, `tests/test_main_glance.py`, with unit tests that verify the
  command's output in various scenarios, including clean, modified, and mixed git states, as well as
  in a non-git repository. - A non-breaking update to `shared/cli_utils.py` to allow the
  `get_suggestions` function to be limited to a single suggestion.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add interactive `init` command
  ([#144](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/144),
  [`68ca99d`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/68ca99db4ff3a054986fe6f820d1519ff6e9b76e))

This commit introduces a new `init` subcommand to the CLI. This command provides an interactive
  setup wizard for new projects, guiding the user through the following steps:

- **Git Initialization:** Checks for an existing Git repository and offers to initialize one if it's
  missing. - **.gitignore Creation:** Prompts the user to create a standard Python `.gitignore`
  file. - **Spec File Generation:** Interactively prompts the user to create the initial
  `app_spec.txt` file. - **Next Steps:** Provides guidance on what commands to run next.

This feature improves the user onboarding experience by simplifying the initial project setup
  process into a single, user-friendly command.

A comprehensive suite of unit tests has been added in `tests/test_main_init.py` to ensure the
  command's functionality is robust and handles various scenarios, including user input,
  non-interactive mode, and pre-existing files.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add interactive mode CLI command
  ([#191](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/191),
  [`2fbc6ea`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/2fbc6ea35b61c9fb0134f96defd129446df878d8))

Adds a new `interact` subcommand to the `main.py` CLI.

This command provides a user-friendly, menu-driven interface for running common project commands,
  such as `status`, `test`, `lint`, and `commit`.

The implementation reuses the existing command functions (`run_status`, `run_test`, etc.) by
  programmatically constructing `argparse.Namespace` objects and calling them, ensuring consistency
  and maximizing code reuse.

A new test file, `tests/test_main_interact.py`, is added with unit tests that mock user input and
  verify that the correct functions are called.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add interactive review command
  ([#311](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/311),
  [`1c5c1c4`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/1c5c1c435c9916353803dc82ede7fc4cbe645d17))

This commit introduces a new `review` command to the CLI. This command provides a guided,
  interactive workflow for a human to conduct a QA review of the agent's completed work.

The `review` command: - Verifies that the agent has marked its work as 'COMPLETED'. - Automatically
  runs the project's test suite. - Displays a git diff of the changes. - Prompts the user to approve
  or reject the work. - On approval, creates a `QA_PASSED` file to advance the workflow. - On
  rejection, removes the `COMPLETED` file to signal the agent to continue.

This feature enhances the human-in-the-loop aspect of the agent's workflow, making the QA process
  more robust and user-friendly.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add interactive shell for CLI
  ([#117](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/117),
  [`d752a72`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/d752a72c6fb74c1ba02f5eba71494e0191f22be0))

This commit introduces a new `shell` subcommand that launches an interactive session for the agent
  CLI.

The interactive shell provides a persistent environment for running multiple commands without
  restarting the script, improving workflow and discoverability.

Key changes: - Created `shared/shell.py` with the `InteractiveShell` class based on `cmd.Cmd`. -
  Integrated the shell into `main.py` with a new `shell` subcommand. - Refactored existing `run_*`
  command functions to be shell-compatible by separating logic from argument parsing. - Implemented
  `do_*` command handlers in `InteractiveShell` for existing subcommands. - Added comprehensive unit
  tests for the interactive shell in `tests/test_shell.py`.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add interactive TUI dashboard
  ([#128](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/128),
  [`d80fa72`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/d80fa72462b4d1b96a7e6216deb365008dab9055))

This commit introduces a new `tui` subcommand that launches an interactive terminal user interface
  for the autonomous coding agent.

The TUI is built using the `textual` library and provides a dashboard view with: - A project summary
  widget that displays key information about the project's state. - A live log viewer that tails the
  latest agent log file.

To support this new feature, the following changes were made: - The `textual` dependency was added
  to `requirements-dev.txt`. - Project summary logic was refactored from `main.py` into a new
  `shared/cli_utils.py` module to allow for code reuse between the CLI and the TUI. - Unit tests for
  the TUI were added in `tests/test_tui.py`. - The `run_tests.sh` script was updated to install both
  `requirements.txt` and `requirements-dev.txt` to ensure a consistent testing environment.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add last-run-id command
  ([#180](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/180),
  [`a8d279b`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/a8d279b52fc60d619238e6528ce7b68c3ed526fd))

Adds a new 'last-run-id' subcommand to the CLI to print the ID of the most recent agent run. This is
  useful for scripting and chaining commands. Includes unit tests and adds .agent_history to
  .gitignore.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add next command for guided workflow
  ([#306](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/306),
  [`fea8641`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/fea86415e255884cd2e4a25e8741e3f9cd1a15c7))

Adds a new `next` command to the CLI.

This command acts as a workflow copilot by: 1. Analyzing the current project state to determine the
  most logical next action. 2. Presenting the suggested command and its reasoning to the user. 3.
  Executing the command upon user confirmation.

This feature improves usability by guiding users through the development lifecycle, making the tool
  more interactive and accessible.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add patch subcommand
  ([#315](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/315),
  [`da7ddea`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/da7ddeab9ce4c17753e67560610e8eb223eaa448))

This commit introduces a new `patch` subcommand to the CLI.

The `patch` command allows applying a standard `git diff` patch to the current project. It can read
  the patch from a specified file or directly from standard input, providing flexibility for various
  workflows.

Key features: - Apply a patch from a file: `main.py patch <path/to/patch.file>` - Apply a patch from
  stdin: `cat my.patch | main.py patch` - Reverse a patch (unpatch): `main.py patch --reverse
  <path/to/patch.file>`

The implementation uses `git apply` for robust patch handling.

Added comprehensive unit tests in `tests/test_main_patch.py` to cover: - Patching from a file -
  Patching from stdin - Reversing a patch - Handling invalid patch content

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add profile subcommand for configuration management
  ([#190](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/190),
  [`ac9b435`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/ac9b435fb57d741e3011a2ccea5631bae1acb4a2))

This commit introduces a new `profile` subcommand to the CLI, allowing users to manage configuration
  profiles directly from the command line.

The `profile` subcommand supports the following actions: - `list`: Lists all available configuration
  profiles. - `create`: Interactively creates a new profile and saves it to the `agent_config.yaml`
  file. - `show`: Displays the configuration for a specified profile. - `delete`: Removes a
  specified profile after a confirmation prompt.

This feature improves usability by providing a streamlined way to handle multiple project
  configurations without needing to manually edit the YAML file.

Key implementation details: - Adds a new subparser and a `run_profile` handler function in
  `main.py`. - Implements robust logic for each action, including error handling for missing files
  or profiles. - Ensures security by setting file permissions to `0o600` on the configuration file
  after any modification. - Includes a comprehensive suite of unit tests in
  `tests/test_main_profile_command.py` to validate all aspects of the new functionality.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add pull subcommand
  ([#167](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/167),
  [`f253f18`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/f253f1820e997c62cfd86eb7a2939d360c42e062))

This commit introduces a new `pull` subcommand to the CLI.

This command provides a safe way to pull the latest changes from the remote repository. It includes
  pre-flight checks to ensure the working directory is clean, preventing accidental merges or
  conflicts with uncommitted changes.

The implementation mirrors the existing `push` command's structure for consistency. Comprehensive
  unit tests have been added in `tests/test_main_pull.py` to cover various scenarios, including
  success, uncommitted changes, and non-Git directories.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add push command with safety checks
  ([#160](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/160),
  [`6039dc9`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/6039dc98592a43ee1a521607a1076ea53be3a49b))

Adds a new `push` subcommand to the CLI.

This command acts as a safe wrapper around `git push`, providing the following features:

- Prevents pushing directly to protected branches (`main`, `master`). - Checks for uncommitted
  changes before pushing and aborts if any are found. - Pushes the current feature branch to the
  `origin` remote.

Includes a comprehensive suite of unit tests to verify the new functionality and its error handling.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add report command to generate run summaries
  ([#150](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/150),
  [`c9dfb97`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/c9dfb971e9854ed23a20be8ba69c9ef57ce8a289))

This commit introduces a new `report` subcommand to the CLI.

The `report` command generates a Markdown summary for a specific agent run, identified by its
  `run_id`. The report includes: - A summary table with key performance metrics from
  `final_metrics.txt`. - A code changes section with the git commit summary associated with the run.
  - A list of notable events extracted from the agent's log file.

This feature improves the user experience by providing a quick and easy way to assess the outcome of
  an agent's run without manually inspecting multiple files.

The implementation includes: - A new `report` subcommand in `main.py`. - Core report generation
  logic in `shared/cli_utils.py`. - Unit tests for the new command.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add rewind command for project state time travel
  ([#148](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/148),
  [`a3a610a`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/a3a610a320c093046cce5c979310da7d5eee43cd))

This commit introduces a new `rewind` subcommand to the CLI, providing a powerful and safe mechanism
  for developers to revert the project to a previous state.

The `rewind` command acts as a user-friendly wrapper around `git reset --hard`, with several key
  features:

- **Targeted Rewind:** Allows rewinding to a specific git commit hash or a relative reference (e.g.,
  `HEAD~2`). - **Interactive Mode:** If no target is specified, it launches an interactive mode that
  displays a list of the 15 most recent commits, allowing the user to easily select a target. -
  **Safety First:** - It performs a pre-flight check to ensure the repository has no uncommitted
  changes, preventing accidental data loss. - It requires user confirmation for the destructive `git
  reset` operation, unless the `--yes` flag is provided. - **Thoroughly Tested:** The command is
  accompanied by a new test suite (`tests/test_main_rewind.py`) that covers its core functionality,
  safety checks, and interactive mode.

This feature enhances the developer experience by providing a safe and intuitive way to navigate the
  project's history, which is invaluable for debugging agent behavior, experimenting with different
  approaches, or recovering from undesired changes.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add safer discard with undo functionality
  ([#151](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/151),
  [`1e7849c`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/1e7849c67ac912294bd8c6fd1bcd104a63cb27b6))

Introduces a safer `discard` command that stashes changes before deleting them, preventing
  accidental data loss. A corresponding `undo` command is added to allow users to easily restore
  these stashed changes.

Key changes: - The `discard` command now uses `git stash` to save uncommitted changes with a unique
  message (`agent-discard-stash-<timestamp>`) before cleaning the working directory. - A new `undo`
  command is implemented to list these specific stashes and interactively restore a selected one. -
  Added a new test file, `tests/test_main_undo.py`, with integration tests to verify the
  stash-and-restore functionality. - Moved the `datetime` import to the top of the file to adhere to
  PEP 8.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add shell completion to CLI
  ([#129](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/129),
  [`95383fe`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/95383fec0f349d5d55bc8fa76838eb0d8f90b15e))

This commit introduces shell autocompletion for the CLI, significantly improving usability and
  discoverability of commands and options.

The `argcomplete` library is used to provide tab completion for `argparse`. A new `completion`
  subcommand has been added to generate the necessary shell script for activation.

The implementation includes: - The `argcomplete` library as an optional dependency. - A new
  `completion` subcommand to generate the shell completion script. - A unit test to verify the
  functionality of the `completion` subcommand.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add sprint subcommand for better observability
  ([#127](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/127),
  [`b62f7a0`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/b62f7a0a68ad609bbf82fe10f2a08a8ba50f25d1))

This commit introduces a new `sprint` subcommand to the CLI. This command provides a dedicated
  interface for observing and managing sprint progress, which was previously only possible through a
  combination of more generic commands like `worktrees` and `logs`.

The `sprint` subcommand includes the following actions: - `status`: Displays a summary of all tasks
  in the current sprint, including their ID, title, and status (Pending, In Progress, or Merged). -
  `diff [task_id]`: Shows the git diff for a specific task's worktree. - `merge [task_id]`: Merges a
  completed task's branch into the main branch.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add stash command
  ([#307](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/307),
  [`124a685`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/124a685d2e08ace6129ecaebafaf5a83872252c6))

This commit introduces a new `stash` command to the CLI, providing a user-friendly interface for
  `git stash`.

The `stash` command includes the following actions: - `push`: Stashes all uncommitted changes,
  including untracked files, with an optional message. - `list`: Displays all stashes in the
  repository. - `pop`: Interactively prompts the user to select a stash to apply and remove. -
  `drop`: Interactively prompts the user to select a stash to delete.

This feature improves the CLI's usability for developers by providing a non-destructive way to
  temporarily save work-in-progress.

The implementation includes comprehensive unit tests that run in an isolated, temporary Git
  repository to ensure robustness. The `help` command has also been updated to include the new
  `stash` functionality.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add suggest command to CLI
  ([#132](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/132),
  [`2bff6bd`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/2bff6bd783e672c883b12bafe2b07b9d486a6abe))

Implements a new `suggest` subcommand that analyzes the current project state and provides
  context-aware recommendations for the next most logical commands to run.

This feature improves CLI usability and discoverability by guiding the user through the agent's
  workflow. The suggestions are based on: - Git status (e.g., uncommitted changes) - Workflow stage
  (e.g., `COMPLETED`, `QA_PASSED`) - Presence of artifacts (e.g., items in the trash)

The implementation includes the CLI plumbing in `main.py`, the suggestion logic in
  `shared/cli_utils.py`, and a comprehensive suite of unit tests.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add summary command for high-level overview
  ([#116](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/116),
  [`1598fcb`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/1598fcb8a91a35ed825a86fa90b1c4ec7e015233))

Adds a new `summary` subcommand to the CLI.

This command provides a quick, high-level overview of the project's status by consolidating key
  information into a single view: - Current workflow stage (e.g., In Progress, QA Passed) - Presence
  of key artifacts (e.g., Feature Plan, QA Summary) - Current Git branch and status (e.g., Clean, 2
  uncommitted changes) - Last agent run ID

This improves CLI usability by giving users a simple way to quickly assess the state of the agent's
  work without needing to run multiple, more detailed commands.

Includes a comprehensive new unit test suite for the `summary` command, ensuring its correctness and
  stability.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add tree command to display project structure
  ([#143](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/143),
  [`f015e5f`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/f015e5fb6df00550b3628c75b72ce0375381de65))

This commit introduces a new `tree` subcommand to the CLI, providing a convenient way to visualize
  the project's file and directory structure.

The `tree` command includes the following features: - A `--depth` option to limit the recursion
  depth of the tree. - A `--full` option to include all files, even those ignored by `.gitignore`.

The implementation is separated into a new `_run_tree_logic` function in `shared/cli_utils.py` and
  is integrated into `main.py` with its own subparser and command handler.

Comprehensive unit tests have been added in `tests/test_main_tree.py` to ensure the correctness of
  the command's output, options, and edge case handling.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add watch command to CLI
  ([#189](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/189),
  [`6720556`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/6720556ff7d5ca38c524f3e1fd5dbe9ab703e749))

This commit introduces a new `watch` command to the CLI.

The `watch` command monitors the project directory for file changes and runs a specified command in
  response to a modification. This is useful for automatically running tests or linters during
  development.

This change includes: - The `watch` subcommand implementation in `main.py`. - The `watchdog` library
  added to `requirements.txt` and `requirements-dev.txt`. - Unit tests for the `watch` command in
  `tests/test_main_watch.py`.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add workflow subcommand for manual state management
  ([#114](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/114),
  [`d72a1ec`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/d72a1ec3e915ecb7bca722d171a47ab73724f2be))

Adds a new `workflow` subcommand to the `main.py` CLI to provide users with manual control over the
  agent's high-level workflow state.

The agent's workflow is tracked by the presence of marker files (`COMPLETED`, `QA_PASSED`,
  `PROJECT_SIGNED_OFF`). Previously, users had no direct way to influence this state without
  manually creating or deleting these files.

This change introduces three actions: - `workflow status`: Displays the current workflow stage
  (e.g., In Progress, Completed). - `workflow advance`: Moves the project to the next stage by
  creating the appropriate marker file. - `workflow revert`: Moves the project to the previous stage
  by deleting the current marker file.

This feature enhances usability by giving users a safe and intuitive way to manage the project's
  lifecycle, especially in cases where manual intervention is desired.

Comprehensive unit tests have been added in `tests/test_main_workflow.py` to ensure the new
  functionality is robust and correct.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Implement `worktrees` subcommand
  ([#145](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/145),
  [`3fa6fd1`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/3fa6fd104ebd74c0e64c488a54ece0e0bfd99712))

This commit introduces a new `worktrees` subcommand to provide a comprehensive and user-friendly
  interface for managing agent-created git worktrees.

The subcommand includes the following actions: - `create`: Creates a new worktree with a specified
  name and branch. - `list`: Lists all agent-created worktrees. - `show`: Displays a dashboard for a
  specific worktree, including its path, branch, associated sprint task, git status, and a diff
  summary. - `clean`: Removes a specific worktree or all worktrees. - `revert`: Discards uncommitted
  changes in a specific worktree. - `merge`: Merges a worktree branch back into the main branch. -
  `diff`: Shows the git diff for a specific worktree. - `manage`: Provides an interactive interface
  for managing worktrees.

This feature enhances the developer's ability to interact with, debug, and finalize agent-driven
  tasks by providing a high-level abstraction over the underlying git commands.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Optimize agent dashboard rendering
  ([#155](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/155),
  [`b64080c`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/b64080cabe201c1c5c3cdd04a02ffe779a5d2832))

Optimized the `renderAgents` function in `ui/public/script.js` to use a differential update
  strategy. Instead of clearing and rebuilding the entire DOM tree every 2 seconds, it now: -
  Updates existing agent cards in place if their content changes. - Adds new cards only when
  necessary. - Removes stale cards.

This reduces DOM layout thrashing and improves performance, especially with larger lists of agents.

Tests: - Verified `ui/server.test.js` passes. - Verified manual correctness of the logic.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- **cli**: Add comprehensive `worktrees show` dashboard
  ([#135](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/135),
  [`747584c`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/747584cc6fc3793ea6879cfd769654604796843d))

This commit enhances the `worktrees show` command, transforming it from a basic status check into a
  comprehensive dashboard for a specific worktree.

The new "dashboard" view provides a wealth of information in a single, easy-to-read format,
  including:

- The worktree's absolute path and its associated Git branch. - The corresponding sprint task's
  title and description from `sprint_plan.json` (if applicable). - A summary of any uncommitted
  changes within the worktree. - A high-level `git diff --stat` to show the overall scope of the
  changes compared to the main branch.

This feature streamlines the development workflow by providing a single, intuitive command to get a
  complete picture of any ongoing task.

To support this new feature, this commit also:

- Adds a new `_worktree_show` helper function to `main.py` to encapsulate the logic for the new
  dashboard. - Adds a comprehensive suite of unit tests to `tests/test_main_worktrees.py` to ensure
  the new feature is working correctly and to prevent future regressions.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- **cli**: Add setup command for dependency installation
  ([#314](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/314),
  [`c265a64`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/c265a6437628f40bc456f9ec672744b2f70918cb))

Adds a new `setup` subcommand to the CLI that automatically detects the project type and installs
  its dependencies.

This command streamlines the project setup process by providing a unified way to install
  dependencies for different project types: - Python: Installs dependencies from `requirements.txt`
  and `requirements-dev.txt`. - Node.js: Intelligently selects `pnpm`, `yarn`, or `npm` based on the
  presence of lock files. - Go: Runs `go mod tidy` to ensure module consistency.

The new command is accompanied by a comprehensive suite of unit tests to ensure its correctness and
  reliability.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- **cli**: Add structured help command
  ([#204](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/204),
  [`cda4919`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/cda491984630d7e97da07d72b220510ff9476f3f))

Adds a new `help` command to the CLI.

This command provides a structured, user-friendly, and color-coded overview of all available
  commands, grouped by functionality. This improves discoverability and makes the CLI easier to
  navigate for both new and experienced users.

The implementation includes: - A `run_help` function to generate the formatted help text. -
  Integration into `argparse` as a dedicated subcommand. - A new unit test
  (`tests/test_main_help.py`) to verify the command's output and ensure its correctness.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- **cli**: Add worktrees subcommand
  ([#130](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/130),
  [`6aa9cff`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/6aa9cffff87122318338a3d88de8f05fc07dc9fd))

This commit adds a new `worktrees` subcommand to the CLI to manage Git worktrees.

The `worktrees` subcommand provides the following actions: - `list`: Lists all active agent-created
  worktrees. - `show <worktree_name>`: Shows the status of a specific worktree. - `clean [--force]
  [<worktree_name>]`: Removes a specific worktree or all worktrees. - `revert <worktree_name>`:
  Reverts all uncommitted changes in a specific worktree. - `create <worktree_name> [--branch
  <branch_name>]`: Creates a new worktree. - `merge [--clean] <worktree_name>`: Merges a worktree's
  branch into the main branch. - `diff <worktree_name>`: Shows the diff of a worktree against the
  main repo's HEAD. - `manage`: An interactive mode to manage worktrees.

This feature improves the usability of the CLI by providing better visibility and control over the
  Git worktrees used by agents for concurrent tasks.

I have also added a new test file, `tests/test_main_worktrees.py`, with comprehensive integration
  tests for all the actions of the `worktrees` subcommand. The tests use temporary directories and
  `subprocess` to create and manipulate test-specific Git repositories, ensuring that the feature is
  robust and reliable.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- **cli**: Enable rewind by run id
  ([#175](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/175),
  [`a9e01b2`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/a9e01b26eeff0a1a7504a82e80e362a642be4ea4))

This change enhances the `rewind` command to accept an agent Run ID as a target, in addition to a
  git commit hash or reference.

This improves the user experience by allowing users to easily revert to the state of a specific
  agent run without needing to manually find the corresponding commit.

The implementation includes: - A new function `_find_commit_by_run_id` that searches the git log for
  a commit message containing the specified Run ID. - Updated logic in the `run_rewind` function to
  first check if the target is a git reference, and if not, to search for it as a Run ID. - A new
  unit test `test_rewind_by_run_id` to verify the functionality. - An update to the agent's coding
  prompt to include the `Run ID: {run_id}` in the commit message template. - An update to the
  `BaseAgent` to inject the `run_id` into the prompt.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- **cli**: Enhance `status` command and deprecate `summary`
  ([#133](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/133),
  [`5554b44`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/5554b4455bc57d9eb1d85143a1466ab8c6d03ade))

This commit introduces a new, enhanced `status` command that acts as a comprehensive terminal
  dashboard for the project.

The new `status` command provides: - The current workflow stage - A summary of features from
  `feature_list.json` - A timeline of recent agent activity from `.agent_history` - A list of recent
  file changes from `git status` - Actionable next steps based on the project's state

The old `summary` command is now deprecated in favor of the new `status` command. A warning is
  printed when `summary` is used.

This change also includes: - Unit tests for the new `_run_enhanced_status_logic` function. - Updates
  to existing tests for the `status` command to reflect the new output. - Restoration of previously
  removed tests for the `get_suggestions` function.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- **cli**: Enhance doctor command validation
  ([#125](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/125),
  [`591ebf7`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/591ebf74c2e487a61f8be76d68a06c3aec7d5d71))

Improves the `doctor` command by adding more robust validation for the `agent_config.yaml` file.

- Adds a specific check for malformed YAML, providing a clearer error message to the user. -
  Enhances the Jira configuration check to ensure that `url`, `email`, and `token` not only exist
  but also have non-empty values. - Adds validation for the format of Slack and Discord webhook
  URLs.

Includes comprehensive unit tests for the new validation logic, covering malformed files, invalid
  configurations, and multiple simultaneous failures.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- **cli**: Enhance logs command with advanced features
  ([#118](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/118),
  [`47629c9`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/47629c97f15f77344874f611bb8b4101f6a1316a))

This commit enhances the `logs` subcommand to provide a more powerful and interactive log viewing
  experience.

The following features have been added: - **Real-time Tailing (`-f`, `--follow`):** Allows users to
  stream log output in real-time, which is crucial for monitoring active agent sessions. - **Line
  Limiting (`-n`, `--lines`):** Enables users to specify the number of recent log lines to display,
  preventing overwhelmingly large outputs. When no run ID is provided, this applies to the latest
  log file. - **Content Filtering (`-g`, `--grep`):** Provides a way to filter log lines, showing
  only those that contain a specific string, which is useful for quickly finding errors or specific
  events.

A comprehensive test suite has been added to verify the new functionality, including tests for line
  limiting, content filtering, real-time following, and various combinations of the new flags.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- **cli**: Enhance status command with run metrics
  ([#149](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/149),
  [`a6a3af7`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/a6a3af787ea8e29ad5b9cdc2f63697738b8b0b0d))

Adds a "Latest Run Metrics" section to the `status` command's output.

This provides users with an immediate, at-a-glance summary of the most recent agent run's
  performance, including execution time, iteration count, errors, and token usage.

The implementation reads from `final_metrics.txt` and gracefully handles cases where the file is
  missing or contains non-numeric data.

Includes unit tests to verify both the successful display of metrics and the graceful handling of
  the missing metrics file scenario.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- **cli**: Implement interactive commit command
  ([#193](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/193),
  [`643ee42`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/643ee426b53362898ab73c7cca18deb033a1af4b))

Adds an interactive mode to the `commit` subcommand, triggered when the `-m` flag is not provided.

This feature guides the user through creating a Conventional Commit message by prompting for: -
  Commit type (e.g., feat, fix, chore) - Scope - Short description - Optional body - Breaking change
  information

This encourages a more structured and consistent commit history, which is especially valuable in an
  agent-driven development workflow.

The original functionality of providing a commit message directly with the `-m` flag is preserved.
  Added unit tests to verify both the interactive and non-interactive modes.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- **revert**: Add interactive mode for reverting changes
  ([#119](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/119),
  [`22989c0`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/22989c07282e85f4b5f920792c0ba7f225cdd00e))

This commit introduces an interactive mode to the `revert` subcommand.

Users can now run `revert --interactive` to get a numbered list of all uncommitted (modified and
  untracked) files. They can then select which files to revert, providing a safer and more
  user-friendly way to discard specific changes without having to manually list them or revert
  everything at once.

This new feature is accompanied by a comprehensive suite of unit tests to ensure its functionality,
  including tests for selecting modified files, untracked files, a mix of both, and handling user
  cancellation or invalid input.

The existing non-interactive modes (reverting all files or a specified list of files) are preserved
  and are also now covered by the new test suite.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

### Performance Improvements

- Optimize `has_recent_activity` file traversal
  ([#181](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/181),
  [`058f4da`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/058f4da11cd27eeaa2701ff8ba02dfd7a4996a1f))

Replaced `pathlib.Path.rglob` with `os.walk` and implemented explicit pruning of common ignored
  directories (`.git`, `node_modules`, etc.). This significantly improves performance in large
  repositories by avoiding unnecessary recursion into build artifacts and hidden directories.

Optimization details: - Used `os.walk` instead of `rglob` for manual control over traversal. -
  Pruned `IGNORED_DIRS` in-place to skip entire subtrees. - Reduced object creation overhead by
  using strings instead of `Path` objects in the loop. - Moved `ignored_dirs` to a module-level
  constant for efficiency.

Benchmark results showed a reduction from ~0.3s to ~0.06s in a test environment with simulated large
  directories.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>


## v0.11.0 (2026-01-06)

### Bug Fixes

- **tests**: Refactor artifacts tests to fix CI failures
  ([#112](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/112),
  [`2f89780`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/2f897803f69f9a531ab5c18a98a69bd8e81e9805))

This commit addresses a CI failure by refactoring the tests for the deprecated 'archives' and
  'trash' commands.

The root cause of the failure was that the old test files (`tests/test_main_archives.py`,
  `tests/test_main_trash_diff.py`, `tests/test_main_trash_interactive.py`) were still testing the
  deprecated command structure and using brittle `sys.argv` patching.

The following changes were made: - Consolidated all relevant test logic into a single, robust test
  file: `tests/test_main_artifacts.py`. - Refactored all tests to call the `run_artifacts` function
  directly with a mock `argparse.Namespace` object, making them more resilient to future changes. -
  Deleted the old, redundant test files. - Corrected assertion errors in the new test suite to align
  with the actual command output.

This resolves the CI failures and improves the overall quality and stability of the test suite.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

### Features

- Add diff-summary subcommand
  ([#111](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/111),
  [`21e90d5`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/21e90d5646a69c996dd915e43431caa16f0dd8cf))

Adds a new `diff-summary` subcommand to the CLI.

This command provides a concise, high-level summary of uncommitted git changes by running `git diff
  --stat`. It is designed to give developers a quick overview of their work-in-progress without
  leaving the context of the agent CLI.

The feature includes: - A new `run_diff_summary` function to handle the logic. - An `argparse`
  subparser to expose the command. - Robust error handling for cases where `git` is not installed or
  the directory is not a git repository. - A new test file `tests/test_main_diff_summary.py` with
  unit tests covering success, no-changes, and error scenarios.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add interactive worktree management
  ([#107](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/107),
  [`15c8e8a`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/15c8e8aa9009973e26a10f49ac747668d5eed5c7))

This commit introduces a new `manage` action to the `worktrees` subcommand, providing an interactive
  TUI for managing worktrees.

The new interactive mode streamlines the workflow for managing concurrent agent tasks by allowing
  users to select a worktree from a list and then choose an action to perform (e.g., show status,
  diff, merge, clean, revert) from a menu. This is a significant usability improvement over the
  previous manual process, which required users to copy and paste worktree names.

The implementation reuses existing helper functions by constructing a mock `argparse.Namespace`
  object, and it includes comprehensive unit tests for the new functionality.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Unify artifact management with `artifacts` command
  ([`1e464bb`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/1e464bb8c421c5104c4a0937eecc14aaf1c8b662))

This commit introduces a new `artifacts` subcommand to provide a single, unified interface for
  managing agent-generated artifacts. The `trash` and `archives` commands have been refactored into
  this new structure, eliminating duplicated code and improving maintainability.

Key changes: - A new `artifacts` command with `trash` and `archive` subcommands. - Generic helper
  functions (`_artifacts_*`) to handle listing, restoring, clearing, inspecting, and diffing
  artifacts. - Deprecation warnings for the old `trash` and `archives` commands, which now act as
  wrappers for the new `artifacts` command to ensure backward compatibility. - Comprehensive unit
  tests for the new `artifacts` command, covering all actions and modes.

- Unify artifact management with `artifacts` command
  ([`056a5cf`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/056a5cf5b3d58d35bb477e195ee1fbc005b45203))

This commit introduces a new `artifacts` subcommand to provide a single, unified interface for
  managing agent-generated artifacts. The `trash` and `archives` commands have been refactored into
  this new structure, eliminating duplicated code and improving maintainability.

Key changes: - A new `artifacts` command with `trash` and `archive` subcommands. - Generic helper
  functions (`_artifacts_*`) to handle listing, restoring, clearing, inspecting, and diffing
  artifacts. - Deprecation warnings for the old `trash` and `archives` commands, which now act as
  wrappers for the new `artifacts` command to ensure backward compatibility. - Comprehensive unit
  tests for the new `artifacts` command, covering all actions and modes.

- **cli**: Add snapshot diff command
  ([#105](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/105),
  [`056020d`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/056020d0986dc1976ca7894c7b7937169fdd2ad3))

Implements a new `snapshot diff` command to compare the current project state against a previously
  created snapshot.

This enhances the CLI by providing a powerful tool for reviewing changes made by the agent over
  time.

The `snapshot` command has been refactored to use sub-actions: - `snapshot create [name]`: Creates a
  new snapshot. - `snapshot diff <name>`: Diffs the project against a named snapshot.

Existing tests have been updated to reflect this new structure, and new tests have been added to
  cover the `diff` functionality.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>


## v0.10.0 (2026-01-05)

### Features

- Add 'trash inspect' subcommand
  ([#91](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/91),
  [`e86d0f4`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/e86d0f40e09452d0b211ecd2e0e87581ea1946c6))

This commit introduces a new 'inspect' action to the 'trash' subcommand. This feature allows users
  to view the contents of files within a specified trash archive directly from the CLI, which helps
  in deciding whether to restore or permanently delete artifacts.

The 'inspect' action supports two modes: - `trash inspect <archive_name>`: Shows a summary of all
  files in the archive, with a preview of the first 10 lines for each text file. - `trash inspect
  <archive_name> <file_name>`: Displays the full content of a specific file within the archive.

Additionally, this commit introduces a new, comprehensive test suite for the `trash` subcommand in
  `tests/test_main_trash.py`. This suite verifies the functionality of the new `inspect` action and
  also provides full test coverage for the existing `list`, `restore`, and `clear` actions to
  prevent regressions.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add --list option to clean subcommand
  ([#98](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/98),
  [`a3b3c87`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/a3b3c87cc2e5b73d618ca1d37718041cbe215d0e))

This commit introduces a `--list` option to the `clean` subcommand, providing a non-destructive "dry
  run" mode.

When `clean --list` is used, the command will print a list of all agent-generated artifacts that
  would be removed or archived without actually modifying any files. This enhances safety by
  allowing users to preview the impact of the clean operation before committing to it.

The implementation includes: - A new `--list` argument in an exclusive group within the `clean`
  subcommand's parser. - Updated logic in the `run_clean` function to handle the `--list` argument.
  - A new unit test to verify that `--list` correctly prints the targeted files and does not delete
  them. - Patches to existing tests to ensure they are compatible with the new argument, preventing
  regressions.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add `create` action to `worktrees` subcommand
  ([#99](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/99),
  [`1059f92`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/1059f92959450aa31fdef571aba4af1310aa4b4e))

Adds a new `create` action to the `worktrees` subcommand in `main.py`.

This feature allows users to manually create new git worktrees for isolated development and testing
  environments.

Key changes: - Extended the `argparse` configuration to include the `create` action and an optional
  `--branch` argument. - Implemented the logic to call `git worktree add` with appropriate
  arguments. - Added comprehensive unit tests for the new functionality, covering success and
  failure cases. - Refactored `main.py` to move `subprocess` and `shutil` imports to the top level,
  enabling proper mocking in tests.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add `logs` subcommand to view agent logs
  ([#90](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/90),
  [`fbe6b44`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/fbe6b44e46a4d5ccf1044ac6a02b51f81d20c07c))

This commit introduces a new `logs` subcommand to the CLI, allowing users to easily view and manage
  agent log files.

The `logs` subcommand supports two modes of operation: - `logs`: Lists the 10 most recent log files
  from the `agents/logs/` directory. - `logs <run_id>`: Displays the full content of the specified
  log file.

This feature improves the usability of the CLI for debugging and monitoring agent runs.

A comprehensive suite of unit tests has been added in `tests/test_main_logs.py` to ensure the new
  functionality is robust and reliable.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add `worktrees` subcommand for git worktree management
  ([#95](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/95),
  [`98e1844`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/98e1844eeacff94c13150b93cfecf3dbfcfe7c69))

Adds a new `worktrees` subcommand to the main CLI to provide better visibility and control over the
  git worktrees used by the agent for concurrent tasks.

This command helps users debug and manage the repository state when agents are running in sprint
  mode or if a worktree is left in an inconsistent state after an error.

The subcommand supports three actions: - `list`: Displays all active worktrees created by the agent
  within the `worktrees/` directory. - `show`: Provides the `git status` for a specific worktree to
  inspect uncommitted changes. - `clean`: Safely removes a specific worktree or all agent-created
  worktrees, with an interactive confirmation prompt to prevent accidental data loss.

Includes comprehensive unit tests for the new subcommand, mocking filesystem and git subprocess
  interactions to validate all actions and edge cases.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add diff action to trash subcommand
  ([#96](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/96),
  [`47c6ba4`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/47c6ba47cd438744e2b6e588f5f0a12a59efc086))

Adds a `diff` action to the `trash` subcommand to compare a trashed file with its counterpart in the
  project directory.

This feature enhances the usability of the trash utility by allowing users to see the changes
  between a trashed file and the current version before deciding to restore it.

The implementation includes: - A new `diff` action in the `trash` subcommand's argument parser. - A
  `_trash_diff` helper function that uses `difflib` to generate and print a unified diff. - Robust
  error handling for cases where the archive or file does not exist. - A new test file
  `tests/test_main_trash_diff.py` with comprehensive unit tests for the new functionality.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add non-destructive `snapshot` command to CLI
  ([#101](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/101),
  [`9006943`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/90069437c60156da0a111be2471390b43a5fef04))

This commit introduces a new `snapshot` subcommand to the `main.py` CLI.

The `snapshot` command provides a non-destructive way to save a copy of key agent-generated
  artifacts to a timestamped or custom-named directory in `.agent_archives/`. This is useful for
  capturing the agent's state at a specific moment for debugging, comparison, or milestone tracking
  without interrupting its workflow by cleaning the directory.

The command copies: - `feature_list.json` - `qa_summary.txt` - `reviewer_report.txt` -
  `final_metrics.txt` - The log file from the last agent run

A comprehensive suite of unit tests has been added in `tests/test_main_snapshot.py` to ensure the
  command functions correctly, handles edge cases, and provides a good user experience.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add revert command to discard uncommitted changes
  ([#92](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/92),
  [`bcff62c`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/bcff62c228aaf13ab2e9652570402aee855c15e7))

This commit introduces a new `revert` command to the CLI.

The `revert` command provides a safe and convenient way for users to discard all uncommitted changes
  in the project directory, including modifications, new files, and deletions.

Key features: - Shows a list of changes that will be discarded. - Prompts the user for confirmation
  before proceeding. - Includes a `--yes` flag to bypass the confirmation prompt for scripting. -
  Dynamically locates the `git` executable for improved portability.

A comprehensive test suite is included to ensure the command functions correctly and safely.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Add worktrees merge subcommand
  ([#102](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/102),
  [`549e3f3`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/549e3f38e7a351332c3bf000bf9daef36e2d0aa2))

Adds a new 'merge' subcommand to the 'worktrees' command group.

This feature streamlines the development workflow by allowing a completed agent's work from a git
  worktree to be merged back into the main branch.

Key features: - Automatically commits uncommitted changes in the worktree before merging. - Merges
  the worktree branch into the main branch using a no-fast-forward merge. - Provides an optional
  '--clean' flag to remove the worktree and its associated branch after a successful merge. -
  Includes unit tests to verify the functionality of the new subcommand.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Enhance `revert` command to support specific files
  ([#93](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/93),
  [`0ee497a`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/0ee497abfcb5788b65d1b119fb79ad1115389182))

The `revert` subcommand has been enhanced to allow users to revert specific files instead of the
  entire repository.

This change modifies the `revert` command in `main.py` to accept an optional list of file paths. If
  no paths are provided, the command maintains its original behavior, reverting all uncommitted
  changes. If paths are provided, only those specific files are reverted.

The implementation correctly distinguishes between tracked and untracked files, using `git checkout`
  for the former and `git clean` for the latter.

A new test suite in `tests/test_main_revert.py` has been added to verify the new functionality,
  including tests for reverting all files, specific files, and handling repositories with no
  changes.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- Implement interactive trash restore
  ([#94](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/94),
  [`10a8157`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/10a815753b5824d399f89a77e8918d6a021bebb9))

Improves the `trash restore` command by making it interactive.

Previously, running `trash restore` without specifying an archive would only restore the most recent
  item.

This change introduces an interactive prompt that displays a numbered list of available archives,
  allowing the user to select which one to restore. This makes the command more user-friendly and
  flexible.

- Modified `_trash_restore` in `main.py` to present an interactive list. - Added a new test file
  `tests/test_main_trash_interactive.py` to verify the new functionality. - Updated
  `tests/test_main_trash.py` to align with the new interactive behavior.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- **cli**: Add --dry-run to trash subcommand
  ([#100](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/100),
  [`4d6a10d`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/4d6a10d4be02217566b5181fc40089f8331422c9))

Adds a `--dry-run` flag to the `trash` subcommand for the `restore` and `clear` actions. This allows
  users to preview the changes without modifying the filesystem.

- Adds `--dry-run` argument to the `trash` subparser in `main.py`. - Updates `_trash_restore` and
  `_trash_clear` to show intended actions when `--dry-run` is used. - Adds comprehensive unit tests
  for the `--dry-run` functionality in `tests/test_main_trash.py`. - Fixes a bug in
  `tests/test_main_trash_interactive.py` where the mock `argparse.Namespace` was missing attributes.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- **cli**: Add archives subcommand for managing snapshots
  ([#104](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/104),
  [`c743621`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/c74362163d17aee20a4276d1df5d0cd6dd8cc2a6))

Adds a new 'archives' subcommand to the CLI to manage agent-generated archives and snapshots in the
  .agent_archives/ directory.

This feature mirrors the functionality of the existing 'trash' subcommand, providing a consistent
  user experience for artifact management.

The new command includes the following actions: - list: Lists all available archives. - inspect:
  Shows the contents of a specific archive or a file within it. - diff: Compares a file in an
  archive with the version in the project directory. - restore: Copies artifacts from an archive
  back to the project directory, with conflict detection. - clear: Permanently deletes a specific
  archive or all archives.

Comprehensive unit tests have been added in tests/test_main_archives.py to ensure the correctness
  and safety of all actions.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- **cli**: Add revert action to worktrees subcommand
  ([#97](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/97),
  [`12692bc`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/12692bc65bba90c1408a151165bf8c4e03f3a240))

This commit introduces a `revert` action to the `worktrees` subcommand.

The new `worktrees revert` action provides a safe and convenient way to discard all uncommitted
  changes in a specified worktree, resetting it to the last committed state. This is particularly
  useful for developers who need to quickly reset an agent's progress in a worktree without having
  to manually delete and recreate it.

Key features of this implementation include: - A confirmation prompt to prevent accidental data
  loss, which can be bypassed with the `--yes` flag. - Robust error handling that checks for the
  existence of the worktree and catches potential errors from the underlying git commands. - A
  comprehensive unit test that verifies the core logic of the `revert` action, ensuring that the
  correct `git` commands are executed in the right sequence.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>

- **cli**: Add worktrees diff command
  ([#103](https://github.com/process-failed-successfully/combined-autonomous-coding/pull/103),
  [`0081463`](https://github.com/process-failed-successfully/combined-autonomous-coding/commit/00814638ec2e6913406a73a76251c322c4f15362))

Adds a new `diff` action to the `worktrees` subcommand.

This command allows users to quickly view the changes within a specific worktree by running `git
  diff HEAD` from the worktree's directory. This is a useful usability improvement for monitoring
  the agent's progress in Sprint Mode.

The implementation includes: - A new `diff` choice in the `worktrees` subparser. - A
  `_worktree_diff` helper function to execute the diff and handle output. - A new test file,
  `tests/test_main_worktrees_diff.py`, with comprehensive unit tests covering success, no-change,
  and error cases.

Co-authored-by: google-labs-jules[bot] <161369871+google-labs-jules[bot]@users.noreply.github.com>


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
