import ipaddress
import sys
from typing import Dict, Any, List, Union

class CidrLabManager:
    """
    Manages CIDR and IP operations.
    """

    def get_info(self, cidr: str) -> Dict[str, Any]:
        """
        Returns detailed information about a CIDR block.
        """
        try:
            network = ipaddress.ip_network(cidr, strict=False)
        except ValueError as e:
            return {"error": str(e)}

        info = {
            "cidr": str(network),
            "version": network.version,
            "netmask": str(network.netmask),
            "hostmask": str(network.hostmask),
            "num_addresses": network.num_addresses,
            "prefixlen": network.prefixlen,
            "is_private": network.is_private,
            "is_global": network.is_global,
        }

        if network.version == 4:
            info["network_address"] = str(network.network_address)
            info["broadcast_address"] = str(network.broadcast_address)
            if network.num_addresses > 2:
                info["first_host"] = str(network.network_address + 1)
                info["last_host"] = str(network.broadcast_address - 1)
                info["usable_hosts"] = network.num_addresses - 2
            else:
                info["first_host"] = "N/A"
                info["last_host"] = "N/A"
                info["usable_hosts"] = 0
        else:
            # IPv6
            info["network_address"] = str(network.network_address)
            # IPv6 usually doesn't have broadcast
            info["first_host"] = str(network.network_address + 1)
            info["last_host"] = str(network.network_address + network.num_addresses - 1)
            info["usable_hosts"] = network.num_addresses

        return info

    def contains(self, cidr: str, ip_or_cidr: str) -> Dict[str, Any]:
        """
        Checks if the CIDR contains the given IP or CIDR.
        """
        try:
            network = ipaddress.ip_network(cidr, strict=False)
        except ValueError as e:
            return {"error": f"Invalid CIDR: {e}"}

        try:
            # Try as address first
            target = ipaddress.ip_address(ip_or_cidr)
            is_contained = target in network
            return {
                "container": str(network),
                "target": str(target),
                "contains": is_contained,
                "type": "address"
            }
        except ValueError:
            pass

        try:
            # Try as network
            target = ipaddress.ip_network(ip_or_cidr, strict=False)
            is_contained = target.subnet_of(network)
            return {
                "container": str(network),
                "target": str(target),
                "contains": is_contained,
                "type": "network"
            }
        except ValueError as e:
            return {"error": f"Invalid Target IP/CIDR: {e}"}

    def overlaps(self, cidr1: str, cidr2: str) -> Dict[str, Any]:
        """
        Checks if two subnets overlap.
        """
        try:
            net1 = ipaddress.ip_network(cidr1, strict=False)
            net2 = ipaddress.ip_network(cidr2, strict=False)
        except ValueError as e:
            return {"error": f"Invalid CIDR: {e}"}

        return {
            "cidr1": str(net1),
            "cidr2": str(net2),
            "overlaps": net1.overlaps(net2)
        }

    def subnet(self, cidr: str, new_prefix: int) -> Dict[str, Any]:
        """
        Splits a network into smaller subnets.
        """
        try:
            network = ipaddress.ip_network(cidr, strict=False)
        except ValueError as e:
            return {"error": f"Invalid CIDR: {e}"}

        try:
            subnets = list(network.subnets(new_prefix=new_prefix))
            return {
                "cidr": str(network),
                "new_prefix": new_prefix,
                "count": len(subnets),
                "subnets": [str(s) for s in subnets]
            }
        except ValueError as e:
            return {"error": str(e)}

def run_cidr_lab_logic(args):
    """
    CLI entry point for CIDR Lab.
    """
    manager = CidrLabManager()

    if args.action == "info":
        info = manager.get_info(args.cidr)
        if "error" in info:
            print(f"❌ {info['error']}", file=sys.stderr)
            sys.exit(1)

        print(f"--- Network Info: {info['cidr']} ---")
        for k, v in info.items():
            if k == "cidr": continue
            key_display = k.replace("_", " ").title()
            print(f"  {key_display:<20}: {v}")

    elif args.action == "contains":
        result = manager.contains(args.cidr, args.target)
        if "error" in result:
            print(f"❌ {result['error']}", file=sys.stderr)
            sys.exit(1)

        emoji = "✅" if result["contains"] else "❌"
        msg = "contains" if result["contains"] else "does NOT contain"
        print(f"{emoji} Network {result['container']} {msg} {result['type']} {result['target']}")
        sys.exit(0 if result["contains"] else 1)

    elif args.action == "overlaps":
        result = manager.overlaps(args.cidr1, args.cidr2)
        if "error" in result:
             print(f"❌ {result['error']}", file=sys.stderr)
             sys.exit(1)

        emoji = "⚠️ " if result["overlaps"] else "✅"
        msg = "OVERLAP" if result["overlaps"] else "do not overlap"
        print(f"{emoji} {result['cidr1']} and {result['cidr2']} {msg}.")

    elif args.action == "subnet":
        result = manager.subnet(args.cidr, args.new_prefix)
        if "error" in result:
             print(f"❌ {result['error']}", file=sys.stderr)
             sys.exit(1)

        print(f"--- Subnetting {result['cidr']} to /{result['new_prefix']} ---")
        print(f"Total Subnets: {result['count']}")
        print("Subnets:")
        for s in result["subnets"]:
            print(f"  - {s}")

    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
