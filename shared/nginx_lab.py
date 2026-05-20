import sys
from typing import Dict, Any

class NginxLabManager:
    """Manages Nginx Lab operations to generate standard configs."""

    def generate_proxy(self, domain: str, port: int) -> str:
        """Generates a reverse proxy config."""
        return f"""server {{
    listen 80;
    server_name {domain};

    location / {{
        proxy_pass http://localhost:{port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}"""

    def generate_static(self, domain: str, path: str) -> str:
        """Generates a static site config."""
        return f"""server {{
    listen 80;
    server_name {domain};

    root {path};
    index index.html index.htm;

    location / {{
        try_files $uri $uri/ =404;
    }}
}}"""

    def generate_loadbalancer(self, domain: str, upstreams: list[str]) -> str:
        """Generates a load balancer config."""
        upstream_blocks = "\n    ".join([f"server {u};" for u in upstreams])

        return f"""upstream backend_servers {{
    {upstream_blocks}
}}

server {{
    listen 80;
    server_name {domain};

    location / {{
        proxy_pass http://backend_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}"""

def run_nginx_lab_logic(args) -> bool:
    """CLI handler for Nginx Lab."""
    manager = NginxLabManager()

    if args.action == "proxy":
        if not getattr(args, 'domain', None) or getattr(args, 'port', None) is None:
            print("Error: --domain and --port are required for 'proxy' action.", file=sys.stderr)
            return False
        print(manager.generate_proxy(args.domain, args.port))
        return True

    elif args.action == "static":
        if not getattr(args, 'domain', None) or not getattr(args, 'path', None):
            print("Error: --domain and --path are required for 'static' action.", file=sys.stderr)
            return False
        print(manager.generate_static(args.domain, args.path))
        return True

    elif args.action == "loadbalancer":
        if not getattr(args, 'domain', None) or not getattr(args, 'upstreams', None):
            print("Error: --domain and --upstreams are required for 'loadbalancer' action.", file=sys.stderr)
            return False
        upstreams_list = [u.strip() for u in args.upstreams.split(",")]
        print(manager.generate_loadbalancer(args.domain, upstreams_list))
        return True

    return False
