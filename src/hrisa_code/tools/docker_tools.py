"""Docker management and inspection tools."""

import subprocess
import json
from typing import Dict, Any, Optional


class DockerPsTool:
    """List Docker containers."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "docker_ps",
                "description": "List Docker containers. Can show all containers or just running ones. Displays container ID, image, status, ports, and names.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "all": {
                            "type": "boolean",
                            "description": "Show all containers including stopped ones (default: false, only running)"
                        },
                        "filter": {
                            "type": "string",
                            "description": "Filter containers by name (substring match)"
                        }
                    },
                    "required": []
                }
            }
        }

    @staticmethod
    def execute(all: bool = False, filter: Optional[str] = None) -> str:
        """Execute docker ps command."""
        try:
            cmd = ["docker", "ps", "--format", "{{json .}}"]
            if all:
                cmd.append("-a")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                if "Cannot connect to the Docker daemon" in result.stderr:
                    return "Error: Docker daemon is not running"
                return f"Error: {result.stderr}"

            if not result.stdout.strip():
                return "No containers found" if not all else "No containers found (including stopped)"

            # Parse JSON lines
            containers = []
            for line in result.stdout.strip().split('\n'):
                try:
                    container = json.loads(line)
                    if filter and filter.lower() not in container.get('Names', '').lower():
                        continue
                    containers.append(container)
                except json.JSONDecodeError:
                    continue

            if not containers:
                return f"No containers matching filter '{filter}'"

            # Format output
            output = [f"=== Docker Containers ({'all' if all else 'running'}) ===\n"]
            for c in containers:
                output.append(f"ID: {c.get('ID', 'N/A')[:12]}")
                output.append(f"  Name: {c.get('Names', 'N/A')}")
                output.append(f"  Image: {c.get('Image', 'N/A')}")
                output.append(f"  Status: {c.get('Status', 'N/A')}")
                if c.get('Ports'):
                    output.append(f"  Ports: {c['Ports']}")
                output.append("")

            return "\n".join(output)

        except FileNotFoundError:
            return "Error: Docker is not installed or not in PATH"
        except subprocess.TimeoutExpired:
            return "Error: Docker command timed out"
        except Exception as e:
            return f"Error listing containers: {str(e)}"


class DockerInspectTool:
    """Inspect Docker container or image."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "docker_inspect",
                "description": "Inspect a Docker container or image to get detailed information including configuration, networking, mounts, and environment variables.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "Container ID/name or image name to inspect"
                        },
                        "format": {
                            "type": "string",
                            "description": "Output format: 'summary' (default) or 'full' (complete JSON)"
                        }
                    },
                    "required": ["target"]
                }
            }
        }

    @staticmethod
    def execute(target: str, format: str = "summary") -> str:
        """Execute docker inspect command."""
        try:
            result = subprocess.run(
                ["docker", "inspect", target],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return f"Error: {result.stderr}"

            data = json.loads(result.stdout)
            if not data:
                return f"No information found for '{target}'"

            info = data[0]

            if format == "full":
                return json.dumps(info, indent=2)

            # Summary format
            output = [f"=== Docker Inspect: {target} ===\n"]

            # Basic info
            output.append(f"ID: {info.get('Id', 'N/A')[:12]}")
            output.append(f"Created: {info.get('Created', 'N/A')}")

            # Container-specific
            if 'State' in info:
                state = info['State']
                output.append(f"Status: {state.get('Status', 'N/A')}")
                output.append(f"Running: {state.get('Running', False)}")
                if state.get('ExitCode') is not None:
                    output.append(f"Exit Code: {state['ExitCode']}")

            # Config
            if 'Config' in info:
                config = info['Config']
                output.append(f"\nImage: {config.get('Image', 'N/A')}")
                if config.get('Cmd'):
                    output.append(f"Command: {' '.join(config['Cmd'])}")
                if config.get('Env'):
                    output.append(f"\nEnvironment:")
                    for env in config['Env'][:10]:  # Limit to 10
                        output.append(f"  {env}")
                    if len(config['Env']) > 10:
                        output.append(f"  ... and {len(config['Env']) - 10} more")

            # Network
            if 'NetworkSettings' in info:
                networks = info['NetworkSettings'].get('Networks', {})
                if networks:
                    output.append(f"\nNetworks:")
                    for net_name, net_info in networks.items():
                        output.append(f"  {net_name}: {net_info.get('IPAddress', 'N/A')}")

            # Ports
            if 'NetworkSettings' in info and 'Ports' in info['NetworkSettings']:
                ports = info['NetworkSettings']['Ports']
                if ports:
                    output.append(f"\nPorts:")
                    for port, bindings in ports.items():
                        if bindings:
                            for binding in bindings:
                                output.append(f"  {port} -> {binding.get('HostIp', '0.0.0.0')}:{binding.get('HostPort', 'N/A')}")

            # Mounts
            if 'Mounts' in info and info['Mounts']:
                output.append(f"\nMounts:")
                for mount in info['Mounts']:
                    output.append(f"  {mount.get('Source', 'N/A')} -> {mount.get('Destination', 'N/A')} ({mount.get('Mode', 'N/A')})")

            return "\n".join(output)

        except FileNotFoundError:
            return "Error: Docker is not installed"
        except json.JSONDecodeError:
            return "Error: Could not parse docker inspect output"
        except Exception as e:
            return f"Error inspecting {target}: {str(e)}"


class DockerLogsTool:
    """Get Docker container logs."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "docker_logs",
                "description": "Get logs from a Docker container. Can show recent logs or follow logs in real-time.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "container": {
                            "type": "string",
                            "description": "Container ID or name"
                        },
                        "tail": {
                            "type": "integer",
                            "description": "Number of lines to show from the end (default: 100)"
                        },
                        "since": {
                            "type": "string",
                            "description": "Show logs since timestamp (e.g., '1h', '30m', '2023-01-01')"
                        }
                    },
                    "required": ["container"]
                }
            }
        }

    @staticmethod
    def execute(container: str, tail: int = 100, since: Optional[str] = None) -> str:
        """Execute docker logs command."""
        try:
            cmd = ["docker", "logs", "--tail", str(tail)]
            if since:
                cmd.extend(["--since", since])
            cmd.append(container)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return f"Error: {result.stderr}"

            logs = result.stdout
            if not logs:
                logs = result.stderr  # Some logs go to stderr

            if not logs.strip():
                return f"No logs found for container '{container}'"

            return f"=== Logs for {container} (last {tail} lines) ===\n\n{logs}"

        except FileNotFoundError:
            return "Error: Docker is not installed"
        except subprocess.TimeoutExpired:
            return "Error: Docker logs command timed out"
        except Exception as e:
            return f"Error getting logs: {str(e)}"


class DockerExecTool:
    """Execute command in Docker container."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "docker_exec",
                "description": "Execute a command inside a running Docker container. Useful for debugging or running one-off commands.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "container": {
                            "type": "string",
                            "description": "Container ID or name"
                        },
                        "command": {
                            "type": "string",
                            "description": "Command to execute (e.g., 'ls -la', 'cat /etc/hosts')"
                        }
                    },
                    "required": ["container", "command"]
                }
            }
        }

    @staticmethod
    def execute(container: str, command: str) -> str:
        """Execute docker exec command."""
        try:
            # Split command for subprocess
            import shlex
            cmd_parts = shlex.split(command)

            result = subprocess.run(
                ["docker", "exec", container] + cmd_parts,
                capture_output=True,
                text=True,
                timeout=30
            )

            output = result.stdout
            if result.returncode != 0:
                output += f"\n[Exit code: {result.returncode}]\n{result.stderr}"

            return f"=== docker exec {container}: {command} ===\n\n{output}"

        except FileNotFoundError:
            return "Error: Docker is not installed"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out"
        except Exception as e:
            return f"Error executing command: {str(e)}"


class DockerImagesTool:
    """List Docker images."""

    @staticmethod
    def get_definition() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "docker_images",
                "description": "List Docker images with details including repository, tag, size, and creation time.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filter": {
                            "type": "string",
                            "description": "Filter images by name (substring match)"
                        }
                    },
                    "required": []
                }
            }
        }

    @staticmethod
    def execute(filter: Optional[str] = None) -> str:
        """Execute docker images command."""
        try:
            result = subprocess.run(
                ["docker", "images", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return f"Error: {result.stderr}"

            if not result.stdout.strip():
                return "No images found"

            # Parse JSON lines
            images = []
            for line in result.stdout.strip().split('\n'):
                try:
                    image = json.loads(line)
                    if filter and filter.lower() not in image.get('Repository', '').lower():
                        continue
                    images.append(image)
                except json.JSONDecodeError:
                    continue

            if not images:
                return f"No images matching filter '{filter}'"

            # Format output
            output = ["=== Docker Images ===\n"]
            output.append(f"{'REPOSITORY':<30} {'TAG':<15} {'SIZE':<12} {'CREATED'}")
            output.append("-" * 80)

            for img in images:
                output.append(
                    f"{img.get('Repository', 'N/A'):<30} "
                    f"{img.get('Tag', 'N/A'):<15} "
                    f"{img.get('Size', 'N/A'):<12} "
                    f"{img.get('CreatedSince', 'N/A')}"
                )

            return "\n".join(output)

        except FileNotFoundError:
            return "Error: Docker is not installed"
        except Exception as e:
            return f"Error listing images: {str(e)}"


# Collect all Docker tools
DOCKER_TOOLS = {
    "docker_ps": DockerPsTool,
    "docker_inspect": DockerInspectTool,
    "docker_logs": DockerLogsTool,
    "docker_exec": DockerExecTool,
    "docker_images": DockerImagesTool,
}
