"""
Nginx Configuration Lab
=====================

Provides boilerplate Nginx configurations for common use cases.
"""


class NginxLabManager:
    """Manages generation of Nginx configurations."""

    def __init__(self):
        pass

    def generate_proxy(self, server_name: str, backend_url: str, port: int = 80) -> str:
        """Generates a reverse proxy configuration."""
        return f"""server {{
    listen {port};
    server_name {server_name};

    location / {{
        proxy_pass {backend_url};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""

    def generate_static(self, server_name: str, root_path: str, port: int = 80) -> str:
        """Generates a static file server configuration."""
        return f"""server {{
    listen {port};
    server_name {server_name};

    root {root_path};
    index index.html index.htm;

    location / {{
        try_files $uri $uri/ =404;
    }}
}}
"""

    def generate_loadbalancer(self, upstreams: list[str], port: int = 80) -> str:
        """Generates a load balancer configuration."""
        upstream_str = "\n".join([f"    server {u};" for u in upstreams])
        return f"""upstream backend {{
{upstream_str}
}}

server {{
    listen {port};

    location / {{
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
}}
"""


def run_nginx_lab_logic(args) -> bool:
    """CLI logic for Nginx Lab."""
    manager = NginxLabManager()

    if args.action == "proxy":
        if not getattr(args, "backend", None):
            print("Error: --backend is required for proxy.")
            return False
        config = manager.generate_proxy(args.server_name, args.backend, args.port)
        print(config)
        return True

    elif args.action == "static":
        if not getattr(args, "root", None):
            print("Error: --root is required for static.")
            return False
        config = manager.generate_static(args.server_name, args.root, args.port)
        print(config)
        return True

    elif args.action == "loadbalancer":
        if not getattr(args, "upstreams", None):
            print("Error: --upstreams is required for loadbalancer.")
            return False
        config = manager.generate_loadbalancer(args.upstreams, args.port)
        print(config)
        return True

    print(f"Unknown action: {args.action}")
    return False
