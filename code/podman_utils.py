"""
Podman Utility - Remote container operations over SSH.
"""

import subprocess
from typing import List, Optional


class PodmanRemote:
    """
    A utility class to manage Podman containers on a remote server via SSH.
    """

    def __init__(self, user: str, host: str, password: Optional[str] = None):
        """
        Initialize the PodmanRemote instance with connection details.

        Args:
            user (str): SSH username.
            host (str): Remote host address.
            password (Optional[str]): SSH password (if needed).
        """
        self.user = user
        self.host = host
        self.password = password

    def _run_command(self, command: List[str]) -> str:
        """
        Run a command on the remote server via SSH.

        Args:
            command (List[str]): The command and arguments to run.

        Returns:
            str: The standard output from the command.
        """
        ssh_command = ["ssh", f"{self.user}@{self.host}"] + command

        if self.password:
            ssh_command = ["sshpass", "-p", self.password] + ssh_command

        result = subprocess.run(
            ssh_command,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    def list_running_containers(self) -> List[str]:
        """
        List all running containers on the remote host.

        Returns:
            List[str]: A list of container names.
        """
        output = self._run_command(
            ["podman", "ps", "--format", "{{.Names}}"]
        )
        return [name for name in output.splitlines() if name]

    def start_container(self, container_name: str) -> str:
        """
        Start a specified container on the remote host.

        Args:
            container_name (str): The name of the container to start.

        Returns:
            str: The output of the start command.
        """
        return self._run_command(["podman", "start", container_name])

    def stop_container(self, container_name: str) -> str:
        """
        Stop a specified container on the remote host.

        Args:
            container_name (str): The name of the container to stop.

        Returns:
            str: The output of the stop command.
        """
        return self._run_command(["podman", "stop", container_name])

    def remove_container(self, container_name: str) -> str:
        """
        Remove a specified container from the remote host.

        Args:
            container_name (str): The name of the container to remove.

        Returns:
            str: The output of the remove command.
        """
        return self._run_command(["podman", "rm", "-f", container_name])

    def get_container_logs(self, container_name: str) -> str:
        """
        Retrieve logs from a specified container on the remote host.

        Args:
            container_name (str): The name of the container.

        Returns:
            str: The logs from the container.
        """
        return self._run_command(["podman", "logs", container_name])
