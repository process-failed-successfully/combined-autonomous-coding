import argparse
import sys
import yaml

class Compose2K8sManager:
    """
    Parses a docker-compose.yml file and outputs equivalent Kubernetes manifests.
    """

    def generate_k8s_manifests(self, compose_content: str) -> str:
        """
        Takes docker-compose YAML as input and returns Kubernetes YAML.
        """
        try:
            compose_data = yaml.safe_load(compose_content)
        except yaml.YAMLError as e:
            return f"Error parsing Compose YAML: {e}"

        if not compose_data or not isinstance(compose_data, dict):
            return "Invalid docker-compose format."

        services = compose_data.get('services', {})
        if not services:
            return "No services found in docker-compose.yml."

        k8s_manifests = []

        for service_name, service_def in services.items():
            # 1. Generate Deployment
            deployment = self._generate_deployment(service_name, service_def)
            k8s_manifests.append(yaml.dump(deployment, sort_keys=False))

            # 2. Generate Service (if ports are defined)
            ports = service_def.get('ports', [])
            if ports:
                service = self._generate_service(service_name, ports)
                if service:
                    k8s_manifests.append(yaml.dump(service, sort_keys=False))

        return "\n---\n".join(k8s_manifests)

    def _generate_deployment(self, name: str, service_def: dict) -> dict:
        image = service_def.get('image', f"{name}:latest")
        replicas = service_def.get('deploy', {}).get('replicas', 1)

        # Handle environment variables
        env = []
        env_vars = service_def.get('environment', [])
        if isinstance(env_vars, dict):
            for k, v in env_vars.items():
                env.append({"name": k, "value": str(v)})
        elif isinstance(env_vars, list):
            for e in env_vars:
                if '=' in e:
                    k, v = e.split('=', 1)
                    env.append({"name": k, "value": v})
                else:
                    env.append({"name": e, "value": ""})

        # Handle command
        command = service_def.get('command', None)
        if isinstance(command, str):
            import shlex
            command = shlex.split(command)

        # Handle ports for container containerPort
        container_ports = []
        ports = service_def.get('ports', [])
        for p in ports:
            if isinstance(p, str) and ':' in p:
                # Basic mapping e.g., "8080:80"
                parts = p.split(':')
                if len(parts) == 2:
                    container_ports.append({"containerPort": int(parts[1])})
            elif isinstance(p, int):
                container_ports.append({"containerPort": p})
            elif isinstance(p, dict) and 'target' in p:
                container_ports.append({"containerPort": int(p['target'])})

        container = {
            "name": name,
            "image": image,
        }
        if env:
            container["env"] = env
        if command:
            container["command"] = command
        if container_ports:
            # Deduplicate container ports
            unique_ports = []
            seen = set()
            for cp in container_ports:
                if cp['containerPort'] not in seen:
                    unique_ports.append(cp)
                    seen.add(cp['containerPort'])
            container["ports"] = unique_ports

        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": name,
                "labels": {
                    "app": name
                }
            },
            "spec": {
                "replicas": replicas,
                "selector": {
                    "matchLabels": {
                        "app": name
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": name
                        }
                    },
                    "spec": {
                        "containers": [container]
                    }
                }
            }
        }

        return deployment

    def _generate_service(self, name: str, ports: list) -> dict:
        svc_ports = []
        for p in ports:
            if isinstance(p, str) and ':' in p:
                parts = p.split(':')
                if len(parts) == 2:
                    svc_ports.append({
                        "name": f"port-{parts[0]}",
                        "port": int(parts[0]),
                        "targetPort": int(parts[1])
                    })
            elif isinstance(p, int):
                svc_ports.append({
                    "name": f"port-{p}",
                    "port": p,
                    "targetPort": p
                })
            elif isinstance(p, dict):
                port = p.get('published', p.get('target'))
                target = p.get('target', port)
                if port and target:
                    svc_ports.append({
                        "name": f"port-{port}",
                        "port": int(port),
                        "targetPort": int(target)
                    })

        if not svc_ports:
            return None

        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": name,
                "labels": {
                    "app": name
                }
            },
            "spec": {
                "selector": {
                    "app": name
                },
                "ports": svc_ports
            }
        }
        return service


def run_compose2k8s_lab_logic(args: argparse.Namespace) -> bool:
    """
    CLI logic for the compose2k8s-lab command.
    """
    manager = Compose2K8sManager()

    content = ""
    if getattr(args, "file", None):
        try:
            with open(args.file, "r") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return False
    elif getattr(args, "text", None):
        content = args.text
    else:
        if not sys.stdin.isatty():
            content = sys.stdin.read()
        else:
            print("Error: must provide docker-compose content via --file, --text, or stdin", file=sys.stderr)
            return False

    if not content.strip():
        print("No content provided.", file=sys.stderr)
        return False

    result = manager.generate_k8s_manifests(content)

    if getattr(args, "output", None):
        try:
            with open(args.output, "w") as f:
                f.write(result)
            print(f"✅ Generated Kubernetes manifests saved to {args.output}")
        except Exception as e:
            print(f"Error writing to output file: {e}", file=sys.stderr)
            return False
    else:
        print(result)

    return True
