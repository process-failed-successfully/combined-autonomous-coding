import sys
import json
from typing import Optional, List, Dict, Any
from shared.k8s_manager import K8sManager

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

class K8sLabManager:
    def __init__(self):
        self.manager = K8sManager()
        if HAS_RICH:
            self.console = Console()
        else:
            self.console = None

    def check_kubectl(self) -> bool:
        if not self.manager.check_kubectl_installed():
            print("❌ kubectl not found. Please install it and ensure it is in your PATH.", file=sys.stderr)
            return False
        return True

    def list_pods(self, namespace: Optional[str] = None):
        pods = self.manager.list_pods(namespace)
        if not pods:
            print("No pods found.")
            return

        if HAS_RICH:
            table = Table(title=f"Pods ({namespace or 'All Namespaces'})")
            if not namespace:
                table.add_column("Namespace", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Ready", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Restarts", style="blue")
            table.add_column("Age", style="white")

            for pod in pods:
                metadata = pod.get("metadata", {})
                status = pod.get("status", {})
                spec = pod.get("spec", {})

                name = metadata.get("name", "")
                ns = metadata.get("namespace", "")
                phase = status.get("phase", "")

                # Calculate ready containers
                container_statuses = status.get("containerStatuses", [])
                ready_count = sum(1 for c in container_statuses if c.get("ready"))
                total_count = len(spec.get("containers", []))
                ready_str = f"{ready_count}/{total_count}"

                # Calculate restarts
                restarts = sum(c.get("restartCount", 0) for c in container_statuses)

                # Format status color
                status_style = "green" if phase == "Running" else "red" if phase in ["Failed", "Unknown"] else "yellow"

                row = []
                if not namespace:
                    row.append(ns)
                row.extend([name, ready_str, Text(phase, style=status_style), str(restarts), metadata.get("creationTimestamp", "")])
                table.add_row(*row)

            self.console.print(table)
        else:
            print(f"{'Namespace':<15} | {'Name':<30} | {'Ready':<10} | {'Status':<10} | {'Restarts'}")
            print("-" * 80)
            for pod in pods:
                metadata = pod.get("metadata", {})
                status = pod.get("status", {})
                spec = pod.get("spec", {})

                name = metadata.get("name", "")
                ns = metadata.get("namespace", "")
                phase = status.get("phase", "")

                container_statuses = status.get("containerStatuses", [])
                ready_count = sum(1 for c in container_statuses if c.get("ready"))
                total_count = len(spec.get("containers", []))
                ready_str = f"{ready_count}/{total_count}"
                restarts = sum(c.get("restartCount", 0) for c in container_statuses)

                print(f"{ns:<15} | {name:<30} | {ready_str:<10} | {phase:<10} | {restarts}")

    def list_namespaces(self):
        namespaces = self.manager.list_namespaces()
        if not namespaces:
            print("No namespaces found.")
            return

        if HAS_RICH:
            table = Table(title="Namespaces")
            table.add_column("Name", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Age", style="white")

            for ns in namespaces:
                metadata = ns.get("metadata", {})
                status = ns.get("status", {})
                table.add_row(
                    metadata.get("name", ""),
                    status.get("phase", ""),
                    metadata.get("creationTimestamp", "")
                )
            self.console.print(table)
        else:
            print(f"{'Name':<20} | {'Status':<10}")
            print("-" * 35)
            for ns in namespaces:
                metadata = ns.get("metadata", {})
                status = ns.get("status", {})
                print(f"{metadata.get('name', ''):<20} | {status.get('phase', ''):<10}")

    def list_deployments(self, namespace: Optional[str] = None):
        deps = self.manager.list_deployments(namespace)
        if not deps:
            print("No deployments found.")
            return

        if HAS_RICH:
            table = Table(title=f"Deployments ({namespace or 'All Namespaces'})")
            if not namespace:
                table.add_column("Namespace", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Ready", style="green")
            table.add_column("Up-to-date", style="blue")
            table.add_column("Available", style="yellow")
            table.add_column("Age", style="white")

            for dep in deps:
                metadata = dep.get("metadata", {})
                status = dep.get("status", {})

                row = []
                if not namespace:
                    row.append(metadata.get("namespace", ""))

                ready = f"{status.get('readyReplicas', 0)}/{status.get('replicas', 0)}"

                row.extend([
                    metadata.get("name", ""),
                    ready,
                    str(status.get("updatedReplicas", 0)),
                    str(status.get("availableReplicas", 0)),
                    metadata.get("creationTimestamp", "")
                ])
                table.add_row(*row)
            self.console.print(table)
        else:
             print("Use --json or install rich for better output.")
             print(json.dumps(deps, indent=2))

    def list_services(self, namespace: Optional[str] = None):
        svcs = self.manager.list_services(namespace)
        if not svcs:
            print("No services found.")
            return

        if HAS_RICH:
            table = Table(title=f"Services ({namespace or 'All Namespaces'})")
            if not namespace:
                table.add_column("Namespace", style="cyan")
            table.add_column("Name", style="magenta")
            table.add_column("Type", style="green")
            table.add_column("Cluster-IP", style="blue")
            table.add_column("External-IP", style="yellow")
            table.add_column("Ports", style="white")

            for svc in svcs:
                metadata = svc.get("metadata", {})
                spec = svc.get("spec", {})
                status = svc.get("status", {})

                ports = ", ".join([f"{p.get('port')}/{p.get('protocol')}" for p in spec.get("ports", [])])
                external_ips = status.get("loadBalancer", {}).get("ingress", [])
                ext_ip_str = ", ".join([i.get("ip", "") or i.get("hostname", "") for i in external_ips])

                row = []
                if not namespace:
                    row.append(metadata.get("namespace", ""))

                row.extend([
                    metadata.get("name", ""),
                    spec.get("type", ""),
                    spec.get("clusterIP", ""),
                    ext_ip_str or "<none>",
                    ports
                ])
                table.add_row(*row)
            self.console.print(table)
        else:
             print(json.dumps(svcs, indent=2))

    def list_contexts(self):
        contexts = self.manager.list_contexts()
        if not contexts:
            print("No contexts found.")
            return

        if HAS_RICH:
            table = Table(title="Contexts")
            table.add_column("Current", style="bold green", justify="center")
            table.add_column("Name", style="cyan")
            table.add_column("Cluster", style="magenta")
            table.add_column("User", style="blue")
            table.add_column("Namespace", style="yellow")

            for ctx in contexts:
                is_current = "*" if ctx.get("current") else ""
                details = ctx.get("context", {})
                table.add_row(
                    is_current,
                    ctx.get("name", ""),
                    details.get("cluster", ""),
                    details.get("user", ""),
                    details.get("namespace", "")
                )
            self.console.print(table)
        else:
            print(f"{' ':1} | {'Name':<20} | {'Cluster':<20} | {'User':<20}")
            print("-" * 70)
            for ctx in contexts:
                marker = "*" if ctx.get("current") else " "
                details = ctx.get("context", {})
                print(f"{marker} | {ctx.get('name', ''):<20} | {details.get('cluster', ''):<20} | {details.get('user', ''):<20}")

    def run_logs(self, pod: str, namespace: Optional[str], tail: int):
        logs = self.manager.get_logs(pod, namespace, tail)
        print(f"--- Logs: {pod} (ns: {namespace or 'default'}) ---")
        print(logs)

    def run_describe(self, resource_type: str, name: str, namespace: Optional[str]):
        desc = self.manager.describe_resource(resource_type, name, namespace)
        print(f"--- Describe: {resource_type}/{name} ---")
        print(desc)

def run_k8s_lab_logic(args):
    """
    CLI Entry point for Kubernetes Lab.
    """
    lab = K8sLabManager()
    if not lab.check_kubectl():
        sys.exit(1)

    if args.action == "pods":
        lab.list_pods(args.namespace)

    elif args.action == "ns":
        lab.list_namespaces()

    elif args.action == "deploy":
        lab.list_deployments(args.namespace)

    elif args.action == "svc":
        lab.list_services(args.namespace)

    elif args.action == "ctx":
        if getattr(args, 'use_context', None):
            if lab.manager.use_context(args.use_context):
                print(f"✅ Switched to context '{args.use_context}'")
            else:
                print(f"❌ Failed to switch to context '{args.use_context}'", file=sys.stderr)
                sys.exit(1)
        else:
            lab.list_contexts()

    elif args.action == "logs":
        if not args.pod:
            print("Error: --pod required for logs.")
            sys.exit(1)
        lab.run_logs(args.pod, args.namespace, args.tail)

    elif args.action == "describe":
        if not args.resource_type or not args.name:
            print("Error: resource type and name required for describe. (e.g., describe pod my-pod)")
            sys.exit(1)
        lab.run_describe(args.resource_type, args.name, args.namespace)

    elif args.action == "apply":
        if not args.file:
            print("Error: --file required for apply.")
            sys.exit(1)
        print(lab.manager.apply_file(args.file))

    elif args.action == "delete":
        if not args.resource_type or not args.name:
            print("Error: resource type and name required for delete.")
            sys.exit(1)
        print(lab.manager.delete_resource(args.resource_type, args.name, args.namespace))

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
