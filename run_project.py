import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883
BACKEND_URL = "http://127.0.0.1:5000"
DASHBOARD_URL = f"{BACKEND_URL}/dashboard"


def port_is_open(host, port):
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def find_mosquitto():
    executable = shutil.which("mosquitto")
    if executable:
        return executable

    for program_files in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if program_files:
            candidate = Path(program_files) / "mosquitto" / "mosquitto.exe"
            if candidate.is_file():
                return str(candidate)
    return None


def wait_for_port(host, port, process, description, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if port_is_open(host, port):
            return
        if process and process.poll() is not None:
            raise RuntimeError(f"{description} exited before becoming ready.")
        time.sleep(0.25)
    raise RuntimeError(f"Timed out waiting for {description} on {host}:{port}.")


def backend_is_ready():
    try:
        with urllib.request.urlopen(f"{BACKEND_URL}/health", timeout=1) as response:
            return response.status == 200
    except (OSError, urllib.error.URLError):
        return False


def start_console(arguments):
    return subprocess.Popen(
        arguments,
        cwd=PROJECT_ROOT,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )


def main():
    if os.name != "nt":
        raise RuntimeError("This one-command launcher is intended for Windows.")

    processes = []
    try:
        backend_already_running = backend_is_ready()
        if port_is_open("127.0.0.1", 5000) and not backend_already_running:
            raise RuntimeError(
                "Port 5000 is in use by another application. Stop that application, "
                "then run this launcher again."
            )

        if not port_is_open(BROKER_HOST, BROKER_PORT):
            mosquitto = find_mosquitto()
            if not mosquitto:
                raise RuntimeError(
                    "Mosquitto is not running and its executable was not found. "
                    "Install Mosquitto or start its service, then run this launcher again."
                )
            broker_process = start_console([mosquitto, "-v"])
            processes.append(broker_process)
            wait_for_port(BROKER_HOST, BROKER_PORT, broker_process, "Mosquitto")
            print("Started Mosquitto.")
        else:
            print("Mosquitto is already running.")

        if backend_already_running:
            print("Using the backend already running on port 5000.")
        else:
            backend_process = start_console([sys.executable, "-u", "-m", "backend.app"])
            processes.append(backend_process)
            wait_for_port("127.0.0.1", 5000, backend_process, "Flask backend")
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline and not backend_is_ready():
                time.sleep(0.25)
            if not backend_is_ready():
                raise RuntimeError("Flask started but its /health endpoint did not respond.")
            print("Started the backend.")

        subscriber = start_console([sys.executable, "-u", "-m", "mqtt.subscriber"])
        processes.append(subscriber)
        time.sleep(1)

        publisher = start_console([sys.executable, "-u", "-m", "mqtt.publisher"])
        processes.append(publisher)

        webbrowser.open(DASHBOARD_URL)
        print(f"Started backend, subscriber, and publisher in separate windows: {DASHBOARD_URL}")
        print("Leave the windows open. Press Ctrl+C in each window to stop its service.")
    except Exception:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        raise


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError) as error:
        print(f"Could not start the project: {error}", file=sys.stderr)
        raise SystemExit(1)