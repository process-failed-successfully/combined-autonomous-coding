import ipaddress
from typing import Dict, Any, List, Union

class CidrLabManager:
    """Utilities for CIDR and network calculations."""

    def get_info(self, cidr: str) -> Dict[str, Any]:
        """Calculates detailed information about a CIDR block."""
        try:
            network = ipaddress.ip_network(cidr, strict=False)
            return {
                "success": True,
                "network": str(network),
                "netmask": str(network.netmask),
                "broadcast": str(network.broadcast_address),
                "num_hosts": network.num_addresses,
                "usable_hosts": network.num_addresses - 2 if network.num_addresses > 2 else 0,
                "first_ip": str(network.network_address + 1) if network.num_addresses > 2 else str(network.network_address),
                "last_ip": str(network.broadcast_address - 1) if network.num_addresses > 2 else str(network.broadcast_address),
                "version": network.version,
                "is_private": network.is_private,
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}

    def check_contains(self, network_cidr: str, ip_or_cidr: str) -> Dict[str, Any]:
        """Checks if a network contains an IP or another subnet."""
        try:
            net = ipaddress.ip_network(network_cidr, strict=False)
            try:
                 # Try parsing as address first (e.g. 192.168.1.5)
                 # Note: ip_interface could be used but ip_address is stricter for single IPs
                 other = ipaddress.ip_address(ip_or_cidr)
            except ValueError:
                 # If not an address, try as network
                 other = ipaddress.ip_network(ip_or_cidr, strict=False)

            is_contained = other.subnet_of(net) if isinstance(other, ipaddress.IPv4Network) or isinstance(other, ipaddress.IPv6Network) else other in net

            return {
                "success": True,
                "contains": is_contained,
                "container": str(net),
                "item": str(other)
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}

    def check_overlap(self, cidr1: str, cidr2: str) -> Dict[str, Any]:
        """Checks if two subnets overlap."""
        try:
            net1 = ipaddress.ip_network(cidr1, strict=False)
            net2 = ipaddress.ip_network(cidr2, strict=False)

            return {
                "success": True,
                "overlaps": net1.overlaps(net2),
                "net1": str(net1),
                "net2": str(net2)
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}

    def split_subnet(self, cidr: str, new_prefix: int) -> Dict[str, Any]:
        """Splits a subnet into smaller subnets with a new prefix."""
        try:
            net = ipaddress.ip_network(cidr, strict=False)
            if new_prefix <= net.prefixlen:
                 return {
                     "success": False,
                     "error": f"New prefix ({new_prefix}) must be larger than current prefix ({net.prefixlen})."
                 }

            subnets = list(net.subnets(new_prefix=new_prefix))
            return {
                "success": True,
                "original": str(net),
                "new_prefix": new_prefix,
                "count": len(subnets),
                "subnets": [str(s) for s in subnets]
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}

def run_cidr_lab_logic(action: str, **kwargs) -> bool:
    """Logic handler for the cidr-lab command."""
    manager = CidrLabManager()

    if action == "info":
        if not kwargs.get("cidr"):
            print("Error: --cidr argument is required.")
            return False
        result = manager.get_info(kwargs["cidr"])
        if result["success"]:
            print(f"--- CIDR Info: {result['network']} ---")
            print(f"  Netmask:      {result['netmask']}")
            print(f"  Broadcast:    {result['broadcast']}")
            print(f"  Total IPs:    {result['num_hosts']}")
            print(f"  Usable IPs:   {result['usable_hosts']}")
            print(f"  Range:        {result['first_ip']} - {result['last_ip']}")
            print(f"  Private:      {result['is_private']}")
            return True
        else:
            print(f"Error: {result['error']}")
            return False

    elif action == "contains":
        if not kwargs.get("network") or not kwargs.get("ip"):
            print("Error: --network and --ip are required.")
            return False
        result = manager.check_contains(kwargs["network"], kwargs["ip"])
        if result["success"]:
            if result["contains"]:
                print(f"✅ {result['item']} IS in {result['container']}")
            else:
                print(f"❌ {result['item']} is NOT in {result['container']}")
            return True
        else:
            print(f"Error: {result['error']}")
            return False

    elif action == "overlap":
        if not kwargs.get("cidr1") or not kwargs.get("cidr2"):
            print("Error: --cidr1 and --cidr2 are required.")
            return False
        result = manager.check_overlap(kwargs["cidr1"], kwargs["cidr2"])
        if result["success"]:
            if result["overlaps"]:
                print(f"⚠️  OVERLAP DETECTED between {result['net1']} and {result['net2']}")
            else:
                print(f"✅ No overlap between {result['net1']} and {result['net2']}")
            return True
        else:
            print(f"Error: {result['error']}")
            return False

    elif action == "split":
        if not kwargs.get("cidr") or not kwargs.get("new_prefix"):
             print("Error: --cidr and --new-prefix are required.")
             return False
        result = manager.split_subnet(kwargs["cidr"], int(kwargs["new_prefix"]))
        if result["success"]:
            print(f"--- Splitting {result['original']} into /{result['new_prefix']}s ---")
            print(f"Total Subnets: {result['count']}")
            for s in result['subnets']:
                print(f"  - {s}")
            return True
        else:
            print(f"Error: {result['error']}")
            return False

    return True
