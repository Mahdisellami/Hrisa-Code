"""System monitoring and inspection tools."""

import subprocess
import platform
import psutil
import json
from typing import Dict, Any, List, Optional
from pathlib import Path


class SystemInfoTool:
    """Get system information (OS, architecture, Python version)."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_system_info",
                "description": "Get system information including OS, architecture, hostname, Python version, and platform details. Useful for understanding the environment.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }

    @staticmethod
    def execute() -> str:
        """Execute system info query."""
        try:
            import sys

            info = {
                "os": platform.system(),
                "os_version": platform.version(),
                "os_release": platform.release(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "hostname": platform.node(),
                "python_version": sys.version.split()[0],
                "python_implementation": platform.python_implementation(),
            }

            # Format as readable output
            output = ["=== System Information ===\n"]
            output.append(f"OS: {info['os']} {info['os_release']}")
            output.append(f"Version: {info['os_version']}")
            output.append(f"Architecture: {info['architecture']}")
            output.append(f"Processor: {info['processor']}")
            output.append(f"Hostname: {info['hostname']}")
            output.append(f"Python: {info['python_version']} ({info['python_implementation']})")

            return "\n".join(output)

        except Exception as e:
            return f"Error getting system info: {str(e)}"


class ResourceUsageTool:
    """Check system resource usage (CPU, memory, disk)."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "check_resources",
                "description": "Check system resource usage including CPU, memory, and disk. Returns percentages and absolute values. Useful for monitoring system health and identifying resource constraints.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "include_disk": {
                            "type": "boolean",
                            "description": "Include disk usage information (default: true)"
                        }
                    },
                    "required": []
                }
            }
        }

    @staticmethod
    def execute(include_disk: bool = True) -> str:
        """Execute resource usage check."""
        try:
            output = ["=== System Resources ===\n"]

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            output.append(f"CPU: {cpu_percent}% ({cpu_count} cores)")

            # Memory usage
            memory = psutil.virtual_memory()
            output.append(f"Memory: {memory.percent}% ({memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB)")

            # Swap usage
            swap = psutil.swap_memory()
            output.append(f"Swap: {swap.percent}% ({swap.used / (1024**3):.1f}GB / {swap.total / (1024**3):.1f}GB)")

            # Disk usage
            if include_disk:
                output.append("\n=== Disk Usage ===")
                for partition in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        output.append(f"{partition.mountpoint}: {usage.percent}% ({usage.used / (1024**3):.1f}GB / {usage.total / (1024**3):.1f}GB)")
                    except PermissionError:
                        continue

            return "\n".join(output)

        except Exception as e:
            return f"Error checking resources: {str(e)}"


class ProcessListTool:
    """List running processes."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "list_processes",
                "description": "List running processes with CPU and memory usage. Can filter by name pattern. Useful for finding specific processes or checking what's running.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filter_name": {
                            "type": "string",
                            "description": "Filter processes by name (case-insensitive substring match)"
                        },
                        "sort_by": {
                            "type": "string",
                            "description": "Sort by 'cpu', 'memory', or 'name' (default: cpu)",
                            "enum": ["cpu", "memory", "name"]
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of processes to return (default: 20)"
                        }
                    },
                    "required": []
                }
            }
        }

    @staticmethod
    def execute(filter_name: Optional[str] = None, sort_by: str = "cpu", limit: int = 20) -> str:
        """Execute process listing."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    if filter_name and filter_name.lower() not in pinfo['name'].lower():
                        continue
                    processes.append(pinfo)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Sort processes
            if sort_by == "cpu":
                processes.sort(key=lambda p: p.get('cpu_percent', 0), reverse=True)
            elif sort_by == "memory":
                processes.sort(key=lambda p: p.get('memory_percent', 0), reverse=True)
            elif sort_by == "name":
                processes.sort(key=lambda p: p.get('name', ''))

            # Limit results
            processes = processes[:limit]

            # Format output
            output = [f"=== Processes (sorted by {sort_by}, top {min(limit, len(processes))}) ===\n"]
            output.append(f"{'PID':<8} {'CPU%':<8} {'MEM%':<8} {'NAME'}")
            output.append("-" * 60)

            for proc in processes:
                output.append(
                    f"{proc['pid']:<8} "
                    f"{proc.get('cpu_percent', 0):<8.1f} "
                    f"{proc.get('memory_percent', 0):<8.1f} "
                    f"{proc['name']}"
                )

            return "\n".join(output)

        except Exception as e:
            return f"Error listing processes: {str(e)}"


class PortCheckTool:
    """Check if a port is open/listening."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "check_port",
                "description": "Check if a port is open and listening. Can also list all listening ports. Useful for debugging network services and checking if servers are running.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "port": {
                            "type": "integer",
                            "description": "Port number to check (e.g., 8080, 3000). If not provided, lists all listening ports."
                        },
                        "host": {
                            "type": "string",
                            "description": "Host to check (default: localhost)"
                        }
                    },
                    "required": []
                }
            }
        }

    @staticmethod
    def execute(port: Optional[int] = None, host: str = "localhost") -> str:
        """Execute port check."""
        try:
            if port is not None:
                # Check specific port
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                sock.close()

                if result == 0:
                    # Try to find process using this port
                    for conn in psutil.net_connections():
                        if conn.laddr.port == port:
                            try:
                                proc = psutil.Process(conn.pid)
                                return f"Port {port} is OPEN on {host}\nProcess: {proc.name()} (PID: {conn.pid})"
                            except:
                                return f"Port {port} is OPEN on {host}"
                    return f"Port {port} is OPEN on {host}"
                else:
                    return f"Port {port} is CLOSED on {host}"
            else:
                # List all listening ports
                output = ["=== Listening Ports ===\n"]
                output.append(f"{'PORT':<8} {'TYPE':<8} {'PID':<8} {'PROCESS'}")
                output.append("-" * 60)

                ports_found = set()
                for conn in psutil.net_connections(kind='inet'):
                    if conn.status == 'LISTEN' and conn.laddr.port not in ports_found:
                        ports_found.add(conn.laddr.port)
                        try:
                            proc = psutil.Process(conn.pid)
                            output.append(
                                f"{conn.laddr.port:<8} "
                                f"{conn.type.name:<8} "
                                f"{conn.pid:<8} "
                                f"{proc.name()}"
                            )
                        except:
                            output.append(f"{conn.laddr.port:<8} {conn.type.name:<8} -        -")

                return "\n".join(output)

        except Exception as e:
            return f"Error checking port: {str(e)}"


class EnvironmentVariablesTool:
    """List or get environment variables."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_env_vars",
                "description": "Get environment variables. Can get a specific variable or list all. Useful for checking configuration and debugging environment issues.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "variable_name": {
                            "type": "string",
                            "description": "Specific environment variable to get (e.g., 'PATH', 'HOME'). If not provided, lists common variables."
                        },
                        "filter_pattern": {
                            "type": "string",
                            "description": "Filter variables by pattern (case-insensitive substring match)"
                        }
                    },
                    "required": []
                }
            }
        }

    @staticmethod
    def execute(variable_name: Optional[str] = None, filter_pattern: Optional[str] = None) -> str:
        """Execute environment variable query."""
        import os

        try:
            if variable_name:
                # Get specific variable
                value = os.environ.get(variable_name)
                if value is None:
                    return f"Environment variable '{variable_name}' is not set"
                return f"{variable_name}={value}"
            else:
                # List variables
                common_vars = ['PATH', 'HOME', 'USER', 'SHELL', 'LANG', 'PWD', 'VIRTUAL_ENV',
                              'NODE_ENV', 'PYTHONPATH', 'JAVA_HOME', 'GOPATH']

                output = ["=== Environment Variables ===\n"]

                if filter_pattern:
                    # Show filtered variables
                    filtered = {k: v for k, v in os.environ.items()
                               if filter_pattern.lower() in k.lower()}
                    if filtered:
                        for key in sorted(filtered.keys()):
                            value = filtered[key]
                            # Truncate long values
                            if len(value) > 100:
                                value = value[:97] + "..."
                            output.append(f"{key}={value}")
                    else:
                        output.append(f"No variables matching '{filter_pattern}'")
                else:
                    # Show common variables
                    for var in common_vars:
                        value = os.environ.get(var, "(not set)")
                        if len(value) > 100:
                            value = value[:97] + "..."
                        output.append(f"{var}={value}")

                    output.append(f"\nTotal variables: {len(os.environ)}")
                    output.append("Use filter_pattern to see more variables")

                return "\n".join(output)

        except Exception as e:
            return f"Error getting environment variables: {str(e)}"


# Collect all system tools
SYSTEM_TOOLS = {
    "get_system_info": SystemInfoTool,
    "check_resources": ResourceUsageTool,
    "list_processes": ProcessListTool,
    "check_port": PortCheckTool,
    "get_env_vars": EnvironmentVariablesTool,
}
