## 2026-01-21 - [Sensitive Data Leak in Exception Logging]
**Vulnerability:** Found that `subprocess.CalledProcessError`'s string representation includes the full command arguments, including sensitive tokens. In `configure_git_auth`, this exception was being caught and logged blindly with `logger.error(f"... {e}")`, exposing the git auth token in logs.
**Learning:** Generic exception logging (`except Exception as e: log(e)`) is dangerous when dealing with `subprocess` calls that involve secrets, because the exception object itself can carry the secret payload.
**Prevention:** Always catch `subprocess.CalledProcessError` explicitly when running commands with secrets. Log `e.returncode` and `e.stderr` instead of `e` or `e.cmd`. Ensure `e.cmd` is never logged or printed if it contains secrets.

## 2026-02-04 - [Shell Command Filtering Limitations]
**Vulnerability:** The `execute_bash_block` utility restricts file access by checking arguments against a blocklist, but this is bypassed by shell features like `eval`, variables, and command substitution.
**Learning:** Attempting to sanitize shell commands by banning keywords (like `eval` or `exec`) naively causes regressions by blocking benign string arguments (e.g., `git commit -m "fix eval"`). Static analysis of shell commands is unreliable without a full parser.
**Prevention:** Rely on environment isolation (containers) or OS-level access controls rather than regex/keyword-based command filtering. For specific files (like `.agent_api_collections.json`), adding them to `RESTRICTED_PATHS` is effective for preventing accidental direct access but not malicious evasion.

## 2026-10-26 - [Command Substitution Bypass in Restricted Shell]
**Vulnerability:** The `execute_bash_block` function's static path restriction check was easily bypassed using command substitution (e.g., `cat $(echo .git)/config`). The static check analyzed arguments but failed to account for dynamic shell expansion.
**Learning:** Static analysis of shell commands is inherently flawed because the shell evaluates arguments *after* parsing. Blocking only static paths is insufficient if the shell can generate paths dynamically.
**Prevention:** Block command substitution operators `$(...)`, `` `...` `` and process substitution `<(...)` in arguments when relying on static analysis for path restriction. While not a complete sandbox, it raises the bar significantly against trivial bypasses.

## 2026-10-27 - [Fail-Open Vulnerability in Shell Command Validation]
**Vulnerability:** The `execute_bash_block` function used `shlex.split()` to parse commands for security checks. However, if `shlex` raised a `ValueError` (e.g., due to malformed quotes), the exception was caught and ignored, causing the function to proceed with execution without validation.
**Learning:** Security controls must fail closed. When input cannot be parsed or validated, execution must be blocked, not permitted. Swallowing exceptions in validation logic leads to fail-open vulnerabilities.
**Prevention:** Ensure that exception handlers in security-critical paths explicitly deny access or return errors instead of using `pass` or allowing control flow to continue to the privileged operation.
