import http.server
import socketserver
import json
import yaml
import sys
import webbrowser
from pathlib import Path

# Swagger UI html template. It dynamically injects the spec string.
SWAGGER_UI_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>OpenAPI UI Lab</title>
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" >
  <style>
    html
    {
      box-sizing: border-box;
      overflow: -moz-scrollbars-vertical;
      overflow-y: scroll;
    }
    *,
    *:before,
    *:after
    {
      box-sizing: inherit;
    }
    body
    {
      margin:0;
      background: #fafafa;
    }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"> </script>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js"> </script>
  <script>
    window.onload = function() {
      const specData = REPLACE_ME_SPEC_DATA;

      const ui = SwaggerUIBundle({
        spec: specData,
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        plugins: [
          SwaggerUIBundle.plugins.DownloadUrl
        ],
        layout: "StandaloneLayout"
      });
      window.ui = ui;
    };
  </script>
</body>
</html>"""

def run_openapi_ui_lab_logic(args) -> bool:
    """Serve an interactive Swagger UI for an OpenAPI spec."""
    spec_path = Path(args.spec_file).resolve()

    if not spec_path.exists() or not spec_path.is_file():
        print(f"Error: Specification file not found at {spec_path}", file=sys.stderr)
        return False

    try:
        content = spec_path.read_text(encoding="utf-8")
        if spec_path.suffix.lower() in [".yaml", ".yml"]:
            spec_data = yaml.safe_load(content)
        else:
            spec_data = json.loads(content)
    except Exception as e:
        print(f"Error parsing specification file: {e}", file=sys.stderr)
        return False

    spec_json_str = json.dumps(spec_data).replace("</script>", "<\\/script>")
    html_content = SWAGGER_UI_TEMPLATE.replace("REPLACE_ME_SPEC_DATA", spec_json_str)

    class SwaggerUIHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(html_content.encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()

        # Disable console logging of requests
        def log_message(self, format, *args):
            pass

    port = args.port
    print(f"Starting OpenAPI UI Server on port {port}...")

    try:
        with socketserver.TCPServer(("", port), SwaggerUIHandler) as httpd:
            url = f"http://localhost:{port}"
            print(f"Serving Swagger UI at {url}")
            print("Press Ctrl+C to stop.")

            # Automatically open browser
            try:
                webbrowser.open(url)
            except Exception:
                pass

            httpd.serve_forever()
    except OSError as e:
        if e.errno == 98:
            print(f"Error: Port {port} is already in use.", file=sys.stderr)
        else:
            print(f"Error starting server: {e}", file=sys.stderr)
        return False
    except KeyboardInterrupt:
        print("\nStopping server.")
        return True

    return True
