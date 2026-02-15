from pathlib import Path
from textual.app import ComposeResult
from textual.widgets import Button, Label, RichLog, DataTable, TabbedContent, TabPane
from textual.containers import Container, Horizontal, Vertical
from textual import on
import asyncio

from shared.k8s_manager import K8sManager

class K8sTab(Container):
    """Tab for managing Kubernetes resources."""

    def __init__(self, project_dir: Path, **kwargs) -> None:
        super().__init__(**kwargs)
        self.project_dir = project_dir
        self.manager = K8sManager()
        self.selected_resource = None  # (type, name, namespace)
        self.timer = None
        self.is_k8s_available = self.manager.check_kubectl_installed()

    def compose(self) -> ComposeResult:
        if not self.is_k8s_available:
            yield Label("[bold red]kubectl not found. Please install it to use this tab.[/bold red]", classes="welcome-text")
            return

        with Horizontal():
            # Left Pane: Resources Lists
            with Vertical(id="k8s-list-container", classes="stat-box"):
                with TabbedContent(id="k8s-resource-tabs"):
                    with TabPane("Pods", id="tab-pods"):
                        yield DataTable(id="k8s-pods-table")
                    with TabPane("Deployments", id="tab-deploy"):
                        yield DataTable(id="k8s-deploy-table")
                    with TabPane("Services", id="tab-svc"):
                        yield DataTable(id="k8s-svc-table")
                    with TabPane("Contexts", id="tab-ctx"):
                        yield DataTable(id="k8s-ctx-table")

                yield Button("Refresh", id="btn-k8s-refresh", variant="default")

            # Right Pane: Details & Actions
            with Vertical(id="k8s-details-container"):
                yield Label("[bold]Resource Details[/bold]", id="k8s-header")
                yield RichLog(id="k8s-log", wrap=True, highlight=True, markup=True)

                with Horizontal(id="k8s-actions"):
                    yield Button("Get Logs", id="btn-k8s-logs", variant="primary", disabled=True)
                    yield Button("Describe", id="btn-k8s-describe", variant="default", disabled=True)
                    yield Button("Delete", id="btn-k8s-delete", variant="error", disabled=True)
                    yield Button("Use Context", id="btn-k8s-use-ctx", variant="warning", disabled=True)

    def on_mount(self) -> None:
        if not self.is_k8s_available:
            return

        # Setup Tables
        pods_table = self.query_one("#k8s-pods-table", DataTable)
        pods_table.cursor_type = "row"
        pods_table.add_column("Namespace", key="ns")
        pods_table.add_column("Name", key="name")
        pods_table.add_column("Status", key="status")
        pods_table.add_column("Restarts", key="restarts")
        pods_table.add_column("Age", key="age")

        deploy_table = self.query_one("#k8s-deploy-table", DataTable)
        deploy_table.cursor_type = "row"
        deploy_table.add_column("Namespace", key="ns")
        deploy_table.add_column("Name", key="name")
        deploy_table.add_column("Ready", key="ready")
        deploy_table.add_column("Up-to-date", key="up-to-date")
        deploy_table.add_column("Available", key="available")

        svc_table = self.query_one("#k8s-svc-table", DataTable)
        svc_table.cursor_type = "row"
        svc_table.add_column("Namespace", key="ns")
        svc_table.add_column("Name", key="name")
        svc_table.add_column("Type", key="type")
        svc_table.add_column("Cluster-IP", key="cluster-ip")
        svc_table.add_column("External-IP", key="external-ip")
        svc_table.add_column("Ports", key="ports")

        ctx_table = self.query_one("#k8s-ctx-table", DataTable)
        ctx_table.cursor_type = "row"
        ctx_table.add_column("Current", key="current")
        ctx_table.add_column("Name", key="name")
        ctx_table.add_column("Cluster", key="cluster")
        ctx_table.add_column("User", key="user")

        # Initial Load
        self.refresh_ui()

    def refresh_ui(self) -> None:
        if not self.is_k8s_available:
            return

        # Run in background
        asyncio.create_task(self._async_refresh())

    async def _async_refresh(self) -> None:
        # Fetch data in threads
        pods = await asyncio.to_thread(self.manager.list_pods)
        deploys = await asyncio.to_thread(self.manager.list_deployments)
        svcs = await asyncio.to_thread(self.manager.list_services)
        ctxs = await asyncio.to_thread(self.manager.list_contexts)

        # Update Pods
        try:
            table = self.query_one("#k8s-pods-table", DataTable)
            table.clear()
            for p in pods:
                meta = p.get("metadata", {})
                status = p.get("status", {})

                # Check container statuses for restarts
                restarts = 0
                for c in status.get("containerStatuses", []):
                    restarts += c.get("restartCount", 0)

                # Calculate age (rough)
                # startTime = status.get("startTime", "")

                phase = status.get("phase", "Unknown")
                color = "green" if phase == "Running" else "red" if phase in ["Failed", "Unknown"] else "yellow"

                ns = meta.get("namespace", "default")
                name = meta.get("name", "")

                table.add_row(
                    ns,
                    name,
                    f"[{color}]{phase}[/{color}]",
                    str(restarts),
                    "N/A", # Too complex to calc relative time easily without datetime parsing
                    key=f"pod:{ns}:{name}"
                )
        except Exception:
            pass

        # Update Deployments
        try:
            table = self.query_one("#k8s-deploy-table", DataTable)
            table.clear()
            for d in deploys:
                meta = d.get("metadata", {})
                status = d.get("status", {})
                spec = d.get("spec", {})

                ns = meta.get("namespace", "default")
                name = meta.get("name", "")

                ready = f"{status.get('readyReplicas', 0)}/{spec.get('replicas', 0)}"
                uptodate = str(status.get("updatedReplicas", 0))
                available = str(status.get("availableReplicas", 0))

                table.add_row(ns, name, ready, uptodate, available, key=f"deploy:{ns}:{name}")
        except Exception:
            pass

        # Update Services
        try:
            table = self.query_one("#k8s-svc-table", DataTable)
            table.clear()
            for s in svcs:
                meta = s.get("metadata", {})
                spec = s.get("spec", {})

                ns = meta.get("namespace", "default")
                name = meta.get("name", "")

                ports = ", ".join([f"{p.get('port')}/{p.get('protocol')}" for p in spec.get("ports", [])])
                external_ips = ", ".join(spec.get("externalIPs", [])) or "none"
                if spec.get("type") == "LoadBalancer":
                    ingress = s.get("status", {}).get("loadBalancer", {}).get("ingress", [])
                    if ingress:
                        ip = ingress[0].get("ip") or ingress[0].get("hostname")
                        if ip:
                            external_ips = ip

                table.add_row(
                    ns,
                    name,
                    spec.get("type", ""),
                    spec.get("clusterIP", ""),
                    external_ips,
                    ports,
                    key=f"svc:{ns}:{name}"
                )
        except Exception:
            pass

        # Update Contexts
        try:
            table = self.query_one("#k8s-ctx-table", DataTable)
            table.clear()
            for c in ctxs:
                name = c.get("name", "")
                context = c.get("context", {})
                is_current = c.get("current", False)

                marker = "[green]*[/green]" if is_current else ""

                table.add_row(
                    marker,
                    name,
                    context.get("cluster", ""),
                    context.get("user", ""),
                    key=f"ctx::{name}"
                )
        except Exception:
            pass

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        if not event.row_key.value:
            return

        key_parts = event.row_key.value.split(":")
        # Format: type:namespace:name or ctx::name
        rtype = key_parts[0]
        ns = key_parts[1]
        name = key_parts[2]

        self.selected_resource = (rtype, name, ns)

        header = self.query_one("#k8s-header", Label)
        header.update(f"[bold]{rtype.capitalize()}: {name}[/bold] ({ns or 'N/A'})")

        # Update buttons
        self.query_one("#btn-k8s-logs").disabled = (rtype != "pod")
        self.query_one("#btn-k8s-describe").disabled = (rtype == "ctx")
        self.query_one("#btn-k8s-delete").disabled = (rtype == "ctx")
        self.query_one("#btn-k8s-use-ctx").disabled = (rtype != "ctx")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-k8s-refresh":
            self.refresh_ui()
            self.notify("Refreshing K8s resources...")
            return

        if not self.selected_resource:
            return

        rtype, name, ns = self.selected_resource

        if event.button.id == "btn-k8s-logs":
            await self.fetch_logs(name, ns)
        elif event.button.id == "btn-k8s-describe":
            await self.describe_resource(rtype, name, ns)
        elif event.button.id == "btn-k8s-delete":
            await self.delete_resource(rtype, name, ns)
        elif event.button.id == "btn-k8s-use-ctx":
            await self.use_context(name)

    async def fetch_logs(self, name: str, ns: str) -> None:
        self.notify(f"Fetching logs for {name}...")
        log_view = self.query_one("#k8s-log", RichLog)
        log_view.clear()
        log_view.write("Loading...")

        logs = await asyncio.to_thread(self.manager.get_logs, name, ns, tail=500)
        log_view.clear()
        log_view.write(logs)

    async def describe_resource(self, rtype: str, name: str, ns: str) -> None:
        self.notify(f"Describing {rtype} {name}...")
        log_view = self.query_one("#k8s-log", RichLog)
        log_view.clear()
        log_view.write("Loading...")

        desc = await asyncio.to_thread(self.manager.describe_resource, rtype, name, ns)
        log_view.clear()
        log_view.write(desc)

    async def delete_resource(self, rtype: str, name: str, ns: str) -> None:
        # No confirmation dialog in TUI yet, so be careful?
        # Or just notify. Ideally we'd have a confirmation modal.
        # For now, let's just do it and notify.
        self.notify(f"Deleting {rtype} {name}...", severity="warning")

        res = await asyncio.to_thread(self.manager.delete_resource, rtype, name, ns)

        log_view = self.query_one("#k8s-log", RichLog)
        log_view.clear()
        log_view.write(res)

        self.refresh_ui()

    async def use_context(self, name: str) -> None:
        self.notify(f"Switching context to {name}...")
        success = await asyncio.to_thread(self.manager.use_context, name)

        if success:
            self.notify("Context switched.")
            self.refresh_ui()
        else:
            self.notify("Failed to switch context.", severity="error")
