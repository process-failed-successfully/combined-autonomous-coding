import shlex
import argparse
import sys
import json
from typing import Dict, Any


class CurlLabManager:
    """
    Manages parsing of cURL commands and converting them to various languages/frameworks.
    """

    def parse_curl(self, curl_cmd: str) -> Dict[str, Any]:
        """
        Parses a cURL command string into a structured dictionary.
        """
        # Clean up multiline escapes
        cmd = curl_cmd.replace('\\\n', ' ').strip()

        try:
            tokens = shlex.split(cmd)
        except ValueError as e:
            raise ValueError(f"Error parsing command string: {e}")

        if not tokens or tokens[0] != 'curl':
            raise ValueError("Input is not a valid curl command")

        class NoExitArgumentParser(argparse.ArgumentParser):

            def error(self, message):
                raise ValueError(message)

            def exit(self, status=0, message=None):
                if message:
                    raise ValueError(message)
                raise ValueError("Exited")

        parser = NoExitArgumentParser(add_help=False)
        parser.add_argument('url', nargs='?', default=None)
        parser.add_argument('-X', '--request', default=None)
        parser.add_argument('-H', '--header', action='append', default=[])
        parser.add_argument('-d', '--data', '--data-raw', '--data-binary', '--data-ascii', default=None)
        parser.add_argument('-u', '--user', default=None)
        parser.add_argument('-A', '--user-agent', default=None)
        parser.add_argument('-I', '--head', action='store_true')
        parser.add_argument('-b', '--cookie', default=None)
        parser.add_argument('--url', dest='kw_url', default=None)

        # Ignore unknown arguments like --compressed, -s, etc.
        args, unknown = parser.parse_known_args(tokens[1:])

        url = args.url or args.kw_url
        if not url:
            for token in unknown:
                if token.startswith('http://') or token.startswith('https://'):
                    url = token
                    break

        if not url:
            raise ValueError("URL not found in curl command")

        method = args.request
        if not method:
            if args.head:
                method = 'HEAD'
            elif args.data is not None:
                method = 'POST'
            else:
                method = 'GET'

        method = method.upper()

        headers = {}
        for h in args.header:
            if ':' in h:
                k, v = h.split(':', 1)
                headers[k.strip()] = v.strip()

        if args.user_agent:
            headers['User-Agent'] = args.user_agent

        if args.cookie:
            headers['Cookie'] = args.cookie

        auth = None
        if args.user:
            if ':' in args.user:
                auth = tuple(args.user.split(':', 1))
            else:
                auth = (args.user, '')

        return {
            'url': url,
            'method': method,
            'headers': headers,
            'data': args.data,
            'auth': auth
        }

    def to_python_requests(self, parsed: Dict[str, Any]) -> str:
        """
        Converts parsed cURL data into Python requests code.
        """
        lines = ["import requests"]

        has_json_data = False
        data_str = "None"

        if parsed['data'] is not None:
            # Try to format as JSON if possible
            if parsed['headers'].get('Content-Type', '').lower() == 'application/json':
                try:
                    json_data = json.loads(parsed['data'])
                    # Generate a valid Python dictionary string by pretty printing the json representation
                    # but properly replacing booleans/null.
                    # Simplest robust way is to just use standard repr on the dict, or use json and parse it back via json module
                    data_str = "json.loads(" + repr(json.dumps(json_data)) + ")"
                    has_json_data = True
                    lines.append("import json")
                except json.JSONDecodeError:
                    data_str = repr(parsed['data'])
            else:
                data_str = repr(parsed['data'])

        lines.append("\nurl = " + repr(parsed['url']))

        if parsed['headers']:
            lines.append("headers = {")
            for k, v in parsed['headers'].items():
                lines.append(f"    {repr(k)}: {repr(v)},")
            lines.append("}")

        if parsed['data'] is not None:
            if has_json_data:
                lines.append(f"json_data = {data_str}")
            else:
                lines.append(f"data = {data_str}")

        if parsed['auth']:
            lines.append(f"auth = {repr(parsed['auth'])}")

        # Build the request call
        req_call = f"response = requests.{parsed['method'].lower()}(url"
        if parsed['headers']:
            req_call += ", headers=headers"
        if parsed['data'] is not None:
            if has_json_data:
                req_call += ", json=json_data"
            else:
                req_call += ", data=data"
        if parsed['auth']:
            req_call += ", auth=auth"
        req_call += ")"

        lines.append("\n" + req_call)
        lines.append("print(response.status_code)")
        lines.append("print(response.text)")

        return "\n".join(lines)

    def to_js_fetch(self, parsed: Dict[str, Any]) -> str:
        """
        Converts parsed cURL data into JavaScript fetch code.
        """
        lines = [f"fetch({repr(parsed['url'])}, {{"]
        lines.append(f"  method: {repr(parsed['method'])},")

        if parsed['headers'] or parsed['auth']:
            lines.append("  headers: {")
            for k, v in parsed['headers'].items():
                lines.append(f"    {repr(k)}: {repr(v)},")
            if parsed['auth']:
                # Need to manually construct basic auth header for fetch
                import base64
                auth_str = f"{parsed['auth'][0]}:{parsed['auth'][1]}"
                b64_auth = base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')
                lines.append(f"    'Authorization': 'Basic {b64_auth}',")
            lines.append("  },")

        if parsed['data'] is not None:
            # Try to format as JS object if JSON
            if parsed['headers'].get('Content-Type', '').lower() == 'application/json':
                try:
                    json_data = json.loads(parsed['data'])
                    # For JS, we just send it as stringified JSON
                    lines.append(f"  body: JSON.stringify({json.dumps(json_data, indent=2)}),")
                except json.JSONDecodeError:
                    lines.append(f"  body: {repr(parsed['data'])},")
            else:
                lines.append(f"  body: {repr(parsed['data'])},")

        lines.append("})")
        lines.append(".then(response => response.text())")
        lines.append(".then(text => console.log(text))")
        lines.append(".catch(err => console.error(err));")

        return "\n".join(lines)

    def to_go_http(self, parsed: Dict[str, Any]) -> str:
        """
        Converts parsed cURL data into Go net/http code.
        """
        lines = [
            "package main",
            "",
            "import (",
            '\t"fmt"',
            '\t"io/ioutil"',
            '\t"net/http"',
        ]

        if parsed['data'] is not None:
            lines.append('\t"strings"')

        lines.append(")")
        lines.append("")
        lines.append("func main() {")

        if parsed['data'] is not None:
            # Go string formatting
            lines.append(f"\tpayload := strings.NewReader({json.dumps(parsed['data'])})")
            lines.append(f"\treq, _ := http.NewRequest(\"{parsed['method']}\", {json.dumps(parsed['url'])}, payload)")
        else:
            lines.append(f"\treq, _ := http.NewRequest(\"{parsed['method']}\", {json.dumps(parsed['url'])}, nil)")

        if parsed['headers']:
            for k, v in parsed['headers'].items():
                lines.append(f"\treq.Header.Add({json.dumps(k)}, {json.dumps(v)})")

        if parsed['auth']:
            lines.append(f"\treq.SetBasicAuth({json.dumps(parsed['auth'][0])}, {json.dumps(parsed['auth'][1])})")

        lines.append("")
        lines.append("\tres, _ := http.DefaultClient.Do(req)")
        lines.append("\tdefer res.Body.Close()")
        lines.append("\tbody, _ := ioutil.ReadAll(res.Body)")
        lines.append("")
        lines.append("\tfmt.Println(res.StatusCode)")
        lines.append("\tfmt.Println(string(body))")
        lines.append("}")

        return "\n".join(lines)

    def to_rust_reqwest(self, parsed: Dict[str, Any]) -> str:
        """
        Converts parsed cURL data into Rust reqwest code.
        """
        lines = [
            "use reqwest::Client;",
            "use std::error::Error;",
            "",
            "#[tokio::main]",
            "async fn main() -> Result<(), Box<dyn Error>> {",
            "    let client = Client::new();",
        ]

        if parsed['headers']:
            lines.append("    let mut headers = reqwest::header::HeaderMap::new();")
            for k, v in parsed['headers'].items():
                lines.append(f"    headers.insert({json.dumps(k)}, {json.dumps(v)}.parse()?);")

        req_method = parsed['method'].lower()
        # rust reqwest method syntax e.g. client.get, client.post
        lines.append(f"    let mut request = client.{req_method}({json.dumps(parsed['url'])});")

        if parsed['headers']:
            lines.append("    request = request.headers(headers);")

        if parsed['auth']:
            user, pwd = parsed['auth']
            # basic_auth(username, Some(password))
            lines.append(f"    request = request.basic_auth({json.dumps(user)}, Some({json.dumps(pwd)}));")

        if parsed['data'] is not None:
            # Check if json
            is_json = parsed['headers'].get('Content-Type', '').lower() == 'application/json'
            if is_json:
                try:
                    # formatting json object string in Rust isn't strictly necessary but helpful to pass a raw string
                    # or serde_json macro
                    json_data = json.loads(parsed['data'])
                    json_str = json.dumps(json_data, indent=4)
                    # use raw string literal for json
                    lines.append(f"    let body = r#\"{json_str}\"#;")
                    # We can use .body or since we know it's json, reqwest has .body() taking anything impl Into<Body>
                    lines.append("    request = request.body(body.to_owned());")
                except json.JSONDecodeError:
                    lines.append(f"    request = request.body(r#\"{parsed['data']}\"#.to_owned());")
            else:
                lines.append(f"    request = request.body(r#\"{parsed['data']}\"#.to_owned());")

        lines.append("")
        lines.append("    let response = request.send().await?;")
        lines.append("    println!(\"Status: {}\", response.status());")
        lines.append("    println!(\"Body:\\n{}\", response.text().await?);")
        lines.append("")
        lines.append("    Ok(())")
        lines.append("}")
        return "\n".join(lines)

    def to_powershell_iwr(self, parsed: Dict[str, Any]) -> str:
        """
        Converts parsed cURL data into PowerShell Invoke-WebRequest code.
        """
        lines = []
        method = parsed['method']
        url = parsed['url']

        cmd_parts = ["Invoke-WebRequest", f"-Uri '{url}'", f"-Method {method}"]

        if parsed['headers']:
            lines.append("$headers = @{")
            for k, v in parsed['headers'].items():
                lines.append(f"  '{k}' = '{v}'")
            lines.append("}")
            cmd_parts.append("-Headers $headers")

        if parsed['auth']:
            user, pwd = parsed['auth']
            # Creating credentials in PS
            lines.append(f"$user = '{user}'")
            lines.append(f"$pass = '{pwd}' | ConvertTo-SecureString -AsPlainText -Force")
            lines.append("$cred = New-Object System.Management.Automation.PSCredential ($user, $pass)")
            cmd_parts.append("-Credential $cred")

        if parsed['data'] is not None:
            # Check if json
            is_json = parsed['headers'].get('Content-Type', '').lower() == 'application/json'
            if is_json:
                try:
                    json_data = json.loads(parsed['data'])
                    # Let powershell format it
                    lines.append(f"$body = @'")
                    lines.append(json.dumps(json_data, indent=2))
                    lines.append("'@")
                except json.JSONDecodeError:
                    lines.append(f"$body = '{parsed['data']}'")
            else:
                lines.append(f"$body = '{parsed['data']}'")
            cmd_parts.append("-Body $body")

        lines.append(" ".join(cmd_parts))
        return "\n".join(lines)

    def to_json(self, parsed: Dict[str, Any]) -> str:
        """
        Converts parsed cURL data into a formatted JSON string.
        """
        return json.dumps(parsed, indent=2)


def run_curl_lab_logic(args):
    """
    CLI handler for cURL Lab.
    """
    manager = CurlLabManager()

    if getattr(args, "tui", False):
        from shared.tui import AgentTUI
        print("Launching cURL Lab TUI...")
        app = AgentTUI(project_dir=getattr(args, 'project_dir', None), start_tab="tab-curl")
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            asyncio.ensure_future(app.run_async())
        else:
            app.run()
            sys.exit(0)
        return

    # Check for CLI usage
    if not hasattr(args, 'command_str') or not args.command_str:
        print("Error: A cURL command string is required. Use --command_str or launch the TUI with --tui.", file=sys.stderr)
        sys.exit(1)

    try:
        parsed = manager.parse_curl(args.command_str)
        target = getattr(args, 'target', 'python').lower()

        if target == 'python':
            print(manager.to_python_requests(parsed))
        elif target == 'js':
            print(manager.to_js_fetch(parsed))
        elif target == 'go':
            print(manager.to_go_http(parsed))
        elif target == 'powershell':
            print(manager.to_powershell_iwr(parsed))
        elif target == 'rust':
            print(manager.to_rust_reqwest(parsed))
        elif target == 'json':
            print(manager.to_json(parsed))
        else:
            print(f"Error: Unknown target language '{target}'. Valid options: python, js, go, powershell, rust, json.", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error processing cURL command: {e}", file=sys.stderr)
        sys.exit(1)
