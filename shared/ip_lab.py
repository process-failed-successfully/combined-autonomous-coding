"""
IP Lab
======

Provides utilities for IP address parsing, validation, geolocation, and information gathering.
"""

import requests
from ipaddress import ip_address


class IPLabManager:
    """Manages IP operations."""

    @staticmethod
    def get_public_ip():
        """Fetches the public IP address."""
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            response.raise_for_status()
            return response.json()['ip']
        except requests.RequestException:
            return None

    @staticmethod
    def geolocate(ip):
        """Geolocates an IP address."""
        try:
            response = requests.get(f'https://ipapi.co/{ip}/json/', timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None

    @staticmethod
    def is_valid(ip):
        """Checks if a string is a valid IP address."""
        try:
            ip_address(ip)
            return True
        except ValueError:
            return False

    @staticmethod
    def get_info(ip_str):
        """Returns information about an IP address."""
        try:
            ip = ip_address(ip_str)
            info = {
                'version': ip.version,
                'is_private': ip.is_private,
                'is_global': ip.is_global,
                'is_multicast': ip.is_multicast,
                'is_loopback': ip.is_loopback,
                'is_link_local': ip.is_link_local,
            }
            if ip.version == 4:
                info['hex'] = f"0x{int(ip):08X}"
            return info
        except ValueError:
            return None


def run_ip_lab_logic(args):
    """CLI logic for ip-lab."""
    manager = IPLabManager()

    if args.action == 'public':
        ip = manager.get_public_ip()
        if ip:
            print(f"Public IP: {ip}")
        else:
            print("Failed to fetch public IP.")

    elif args.action == 'geo':
        if not args.ip:
            ip = manager.get_public_ip()
            if not ip:
                print("Failed to fetch public IP for geolocation.")
                return False
        else:
            ip = args.ip

        if not manager.is_valid(ip):
            print(f"Invalid IP address: {ip}")
            return False

        print(f"Geolocating {ip}...")
        geo_data = manager.geolocate(ip)
        if geo_data:
            if 'error' in geo_data and geo_data['error']:
                print(f"Error: {geo_data.get('reason', 'Unknown error')}")
                return False

            print(f"City: {geo_data.get('city', 'N/A')}")
            print(f"Region: {geo_data.get('region', 'N/A')}")
            print(f"Country: {geo_data.get('country_name', 'N/A')}")
            lat = geo_data.get('latitude', 'N/A')
            lon = geo_data.get('longitude', 'N/A')
            print(f"Location: {lat}, {lon}")
            print(f"Organization: {geo_data.get('org', 'N/A')}")
        else:
            print("Failed to geolocate IP.")
            return False

    elif args.action == 'info':
        if not args.ip:
            print("IP address required for info action.")
            return False

        info = manager.get_info(args.ip)
        if info:
            print(f"IP: {args.ip}")
            print(f"Version: IPv{info['version']}")
            print(f"Private: {info['is_private']}")
            print(f"Global: {info['is_global']}")
            print(f"Multicast: {info['is_multicast']}")
            print(f"Loopback: {info['is_loopback']}")
            print(f"Link Local: {info['is_link_local']}")
            if 'hex' in info:
                print(f"Hex: {info['hex']}")
        else:
            print(f"Invalid IP address: {args.ip}")
            return False

    return True
