## 2025-01-13 - Unsanitized HTML Injection in Dashboard
**Vulnerability:** The dashboard used `innerHTML` to render agent state and logs without sanitization, allowing XSS via malicious payloads in agent logs or file paths.
**Learning:** Frontend rendering logic must never trust backend data, even from 'internal' agents, as they process untrusted input (logs, filenames) which can contain malicious HTML/JS.
**Prevention:** Always use `textContent` or an HTML escaping helper (like `escapeHtml`) when interpolating variables into HTML strings.
