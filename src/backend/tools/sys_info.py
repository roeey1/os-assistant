import platform
import socket
import os
import shutil
import psutil
from typing import Dict, List, Union


class SystemInfo:
    """
    Passive system monitoring tools.
    These tools ONLY read information; they do not modify the system.
    """

    def get_system_specs(self) -> Dict[str, str]:
        """
        Returns static hardware and OS details.
        """
        mem = psutil.virtual_memory()

        return {
            "os_name": platform.system(),  # e.g., "Darwin" (macOS) or "Windows"
            "os_version": platform.release(),  # e.g., "14.4.1"
            "architecture": platform.machine(),  # e.g., "arm64" or "AMD64"
            "processor": platform.processor(),  # CPU Model
            "ram_total_gb": f"{round(mem.total / (1024 ** 3), 2)} GB",
            "ram_available_gb": f"{round(mem.available / (1024 ** 3), 2)} GB"
        }

    def get_disk_usage(self, path: str = "/") -> str:
        """
        Returns storage stats for the drive containing the given path.
        """
        # Handle "root" alias
        if path == "root":
            path = "/"

        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist."

        try:
            total, used, free = shutil.disk_usage(path)

            # Helper to convert bytes to GB
            def to_gb(bytes_val):
                return f"{round(bytes_val / (1024 ** 3), 2)} GB"

            return (
                f"Disk Usage for '{path}':\n"
                f"- Total: {to_gb(total)}\n"
                f"- Used:  {to_gb(used)}\n"
                f"- Free:  {to_gb(free)}"
            )
        except Exception as e:
            return f"Error reading disk usage: {str(e)}"

    def get_user_context(self) -> Dict[str, str]:
        """
        Returns details about the current user environment.
        Useful for resolving paths like '~'.
        """
        return {
            "username": os.getlogin(),
            "home_dir": os.path.expanduser("~"),
            "hostname": socket.gethostname(),
            "current_working_dir": os.getcwd()
        }

    def get_running_processes(self, limit: int = 20) -> str:
        """
        Returns a list of the top N processes consuming the most memory.
        We limit this to avoid crashing the LLM context window with 500+ items.
        """
        procs = []
        try:
            # Iterate over all running processes
            for p in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    # SAFETY CHECK: Verify we actually got memory info back
                    mem_info = p.info.get('memory_info')
                    if mem_info is None:
                        continue

                    mem_mb = mem_info.rss / (1024 * 1024)

                    # Some processes have no name; use "Unknown"
                    name = p.info.get('name') or "Unknown"

                    procs.append({
                        "name": name,
                        "pid": p.info['pid'],
                        "memory_mb": mem_mb
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
                except AttributeError:
                    # Catch the specific error you just saw, just in case
                    pass

            # Sort by memory usage (highest first) and take top N
            sorted_procs = sorted(procs, key=lambda x: x['memory_mb'], reverse=True)[:limit]

            output = [f"Top {limit} Processes by Memory:"]
            for p in sorted_procs:
                output.append(f"- {p['name']} (PID: {p['pid']}) - {round(p['memory_mb'], 1)} MB")

            return "\n".join(output)

        except Exception as e:
            return f"Error fetching process list: {str(e)}"

# --- Manual Test ---
if __name__ == "__main__":
    tool = SystemInfo()
    print("--- System Specs ---")
    print(tool.get_system_specs())

    print("\n--- Disk Usage ---")
    print(tool.get_disk_usage("/"))

    print("\n--- User Context ---")
    print(tool.get_user_context())

    print("\n--- Top Processes ---")
    print(tool.get_running_processes(5))