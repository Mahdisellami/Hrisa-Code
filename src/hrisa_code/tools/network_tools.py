"""Network inspection and testing tools."""

import subprocess
import urllib.request
import socket
from typing import Dict, Any, Optional
import json


class PingTool:
    """Ping a host to check connectivity."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "ping",
                "description": "Ping a host to check network connectivity and measure latency. Sends ICMP packets to test if a host is reachable.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "host": {
                            "type": "string",
                            "description": "Hostname or IP address to ping (e.g., 'google.com', '8.8.8.8')"
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of ping packets to send (default: 4)"
                        }
                    },
                    "required": ["host"]
                }
            }
        }

    @staticmethod
    def execute(host: str, count: int = 4) -> str:
        """Execute ping command."""
        try:
            import platform
            system = platform.system().lower()

            if system == "windows":
                cmd = ["ping", "-n", str(count), host]
            else:
                cmd = ["ping", "-c", str(count), host]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            return f"=== Ping {host} ===\n\n{result.stdout}"

        except subprocess.TimeoutExpired:
            return f"Error: Ping to {host} timed out"
        except Exception as e:
            return f"Error pinging {host}: {str(e)}"


class HttpRequestTool:
    """Make HTTP/HTTPS requests."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "http_request",
                "description": "Make an HTTP/HTTPS request to test API endpoints or check if a web service is responding. Returns status code, headers, and body.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to request (e.g., 'https://api.github.com')"
                        },
                        "method": {
                            "type": "string",
                            "description": "HTTP method (default: GET)",
                            "enum": ["GET", "POST", "PUT", "DELETE", "HEAD"]
                        },
                        "headers_only": {
                            "type": "boolean",
                            "description": "Only show headers, not body (default: false)"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Request timeout in seconds (default: 10)"
                        }
                    },
                    "required": ["url"]
                }
            }
        }

    @staticmethod
    def execute(url: str, method: str = "GET", headers_only: bool = False, timeout: int = 10) -> str:
        """Execute HTTP request."""
        try:
            req = urllib.request.Request(url, method=method)
            req.add_header('User-Agent', 'Hrisa-Code/1.0')

            with urllib.request.urlopen(req, timeout=timeout) as response:
                status = response.status
                headers = dict(response.headers)

                output = [f"=== HTTP {method} {url} ===\n"]
                output.append(f"Status: {status}")
                output.append("\nHeaders:")
                for key, value in headers.items():
                    output.append(f"  {key}: {value}")

                if not headers_only:
                    body = response.read().decode('utf-8', errors='replace')
                    # Truncate very long responses
                    if len(body) > 2000:
                        body = body[:2000] + f"\n\n... (truncated, total {len(body)} chars)"
                    output.append(f"\nBody:\n{body}")

                return "\n".join(output)

        except urllib.error.HTTPError as e:
            return f"HTTP Error {e.code}: {e.reason}\nURL: {url}"
        except urllib.error.URLError as e:
            return f"URL Error: {e.reason}\nURL: {url}"
        except socket.timeout:
            return f"Error: Request to {url} timed out"
        except Exception as e:
            return f"Error making request to {url}: {str(e)}"


class DnsLookupTool:
    """Perform DNS lookup."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "dns_lookup",
                "description": "Perform DNS lookup to resolve hostname to IP address. Useful for debugging DNS issues or checking if a domain is reachable.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hostname": {
                            "type": "string",
                            "description": "Hostname to resolve (e.g., 'google.com')"
                        }
                    },
                    "required": ["hostname"]
                }
            }
        }

    @staticmethod
    def execute(hostname: str) -> str:
        """Execute DNS lookup."""
        try:
            # Get all addresses
            addresses = socket.getaddrinfo(hostname, None)

            # Get unique IPs
            ipv4_addresses = set()
            ipv6_addresses = set()

            for addr in addresses:
                family, socktype, proto, canonname, sockaddr = addr
                ip = sockaddr[0]
                if family == socket.AF_INET:
                    ipv4_addresses.add(ip)
                elif family == socket.AF_INET6:
                    ipv6_addresses.add(ip)

            output = [f"=== DNS Lookup: {hostname} ===\n"]

            if ipv4_addresses:
                output.append("IPv4 addresses:")
                for ip in sorted(ipv4_addresses):
                    output.append(f"  {ip}")

            if ipv6_addresses:
                output.append("\nIPv6 addresses:")
                for ip in sorted(ipv6_addresses):
                    output.append(f"  {ip}")

            if not ipv4_addresses and not ipv6_addresses:
                output.append("No addresses found")

            return "\n".join(output)

        except socket.gaierror as e:
            return f"DNS Error: {e}\nHostname: {hostname}"
        except Exception as e:
            return f"Error looking up {hostname}: {str(e)}"


class NetstatTool:
    """Show network connections."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "netstat",
                "description": "Show active network connections and listening ports. Useful for debugging network issues and checking what's connecting to your machine.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filter_port": {
                            "type": "integer",
                            "description": "Filter by specific port number"
                        },
                        "filter_state": {
                            "type": "string",
                            "description": "Filter by connection state",
                            "enum": ["ESTABLISHED", "LISTEN", "TIME_WAIT", "CLOSE_WAIT"]
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of connections to show (default: 50)"
                        }
                    },
                    "required": []
                }
            }
        }

    @staticmethod
    def execute(filter_port: Optional[int] = None, filter_state: Optional[str] = None, limit: int = 50) -> str:
        """Execute netstat equivalent using psutil."""
        try:
            import psutil

            connections = []
            for conn in psutil.net_connections(kind='inet'):
                # Apply filters
                if filter_port and conn.laddr.port != filter_port and (not conn.raddr or conn.raddr.port != filter_port):
                    continue
                if filter_state and conn.status != filter_state:
                    continue

                connections.append(conn)

            connections = connections[:limit]

            output = ["=== Network Connections ===\n"]
            output.append(f"{'PROTO':<6} {'LOCAL':<25} {'REMOTE':<25} {'STATE':<15} {'PID':<8} {'PROCESS'}")
            output.append("-" * 100)

            for conn in connections:
                proto = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
                local = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "-"
                remote = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "-"
                state = conn.status if hasattr(conn, 'status') else "-"

                try:
                    proc = psutil.Process(conn.pid) if conn.pid else None
                    proc_name = proc.name() if proc else "-"
                except:
                    proc_name = "-"

                output.append(
                    f"{proto:<6} {local:<25} {remote:<25} {state:<15} {conn.pid or '-':<8} {proc_name}"
                )

            if not connections:
                output.append("No connections found matching filters")

            return "\n".join(output)

        except Exception as e:
            return f"Error getting network connections: {str(e)}"


# Collect all network tools
NETWORK_TOOLS = {
    "ping": PingTool,
    "http_request": HttpRequestTool,
    "dns_lookup": DnsLookupTool,
    "netstat": NetstatTool,
}
