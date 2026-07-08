from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Input, Button, Markdown, Label

from shared.ip_lab import IPLabManager


class IpLabTab(Vertical):
    """A tab for IP Lab utilities."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = IPLabManager()

    def compose(self) -> ComposeResult:
        yield Label("IP Lab", id="ip-lab-header", classes="text-bold")

        with Horizontal(id="ip-lab-controls"):
            yield Input(placeholder="Enter IP Address (leave blank for your public IP)", id="ip-input", classes="flex-1")
            yield Button("Get Public IP", id="btn-public-ip", variant="primary")
            yield Button("Info & Geolocation", id="btn-ip-info", variant="success")
            yield Button("Clear", id="btn-clear", variant="warning")

        with Horizontal(id="subnet-controls", classes="mt-2"):
            yield Input(placeholder="Enter CIDR (e.g., 192.168.1.0/24)", id="cidr-input", classes="flex-1")
            yield Button("Subnet Info", id="btn-subnet-info", variant="primary")

        yield Markdown("Results will appear here.", id="ip-lab-results")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        results_view = self.query_one("#ip-lab-results", Markdown)
        ip_input = self.query_one("#ip-input", Input)

        if button_id == "btn-public-ip":
            public_ip = self.manager.get_public_ip()
            if public_ip:
                ip_input.value = public_ip
                results_view.update(f"**Your Public IP:** `{public_ip}`")
            else:
                results_view.update("❌ Failed to fetch public IP.")

        elif button_id == "btn-ip-info":
            ip_address = ip_input.value.strip()

            if not ip_address:
                # Try getting public IP if empty
                ip_address = self.manager.get_public_ip()
                if not ip_address:
                    results_view.update("❌ Failed to fetch public IP for info. Please enter an IP address.")
                    return
                ip_input.value = ip_address  # Populate the input so user knows what is being fetched

            if not self.manager.is_valid(ip_address):
                results_view.update(f"❌ Invalid IP address format: `{ip_address}`")
                return

            md_content = f"### IP Information for `{ip_address}`\n\n"

            # Info
            info = self.manager.get_info(ip_address)
            if info:
                md_content += "#### Network Details\n"
                md_content += f"- **Version:** IPv{info['version']}\n"
                md_content += f"- **Private:** {info['is_private']}\n"
                md_content += f"- **Global:** {info['is_global']}\n"
                md_content += f"- **Multicast:** {info['is_multicast']}\n"
                md_content += f"- **Loopback:** {info['is_loopback']}\n"
                md_content += f"- **Link Local:** {info['is_link_local']}\n"
                if 'hex' in info:
                    md_content += f"- **Hex Representation:** `{info['hex']}`\n"

            # Geo
            md_content += "\n#### Geolocation\n"
            geo_data = self.manager.geolocate(ip_address)
            if geo_data:
                if 'error' in geo_data and geo_data['error']:
                    md_content += f"❌ Error: {geo_data.get('reason', 'Unknown error')}\n"
                else:
                    md_content += f"- **City:** {geo_data.get('city', 'N/A')}\n"
                    md_content += f"- **Region:** {geo_data.get('region', 'N/A')}\n"
                    md_content += f"- **Country:** {geo_data.get('country_name', 'N/A')}\n"

                    lat = geo_data.get('latitude', 'N/A')
                    lon = geo_data.get('longitude', 'N/A')
                    md_content += f"- **Location:** {lat}, {lon}\n"
                    md_content += f"- **Organization:** {geo_data.get('org', 'N/A')}\n"
            else:
                md_content += "❌ Failed to fetch geolocation data.\n"

            results_view.update(md_content)

        elif button_id == "btn-subnet-info":
            cidr_input = self.query_one("#cidr-input", Input)
            cidr = cidr_input.value.strip()

            if not cidr:
                results_view.update("❌ Please enter a CIDR block.")
                return

            info = self.manager.get_subnet_info(cidr)
            if info:
                md_content = f"### Subnet Information for `{cidr}`\n\n"
                md_content += f"- **Version:** IPv{info['version']}\n"
                md_content += f"- **Network Address:** `{info['network_address']}`\n"
                md_content += f"- **Netmask:** `{info['netmask']}`\n"
                md_content += f"- **Hostmask:** `{info['hostmask']}`\n"
                if 'broadcast_address' in info:
                    md_content += f"- **Broadcast Address:** `{info['broadcast_address']}`\n"
                md_content += f"- **Total Addresses:** {info['num_addresses']}\n"
                md_content += f"- **Usable Hosts:** {info['usable_hosts']}\n"
                if 'host_range' in info:
                    md_content += f"- **Host Range:** `{info['host_range']}`\n"

                results_view.update(md_content)
            else:
                results_view.update(f"❌ Invalid CIDR format: `{cidr}`")

        elif button_id == "btn-clear":
            ip_input.value = ""
            if self.query("#cidr-input"):
                self.query_one("#cidr-input", Input).value = ""
            results_view.update("Results cleared.")
