#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Kill all servers started by this project.

This script finds and terminates all uvicorn processes running main:app
for the learn_fastapi_auth project.

Usage:
    python scripts/kill_all_servers.py

    # Or make it executable and run directly
    chmod +x scripts/kill_all_servers.py
    ./scripts/kill_all_servers.py
"""

import subprocess
import sys


def find_server_processes():
    """Find all uvicorn processes running main:app."""
    try:
        # Use pgrep to find uvicorn processes
        result = subprocess.run(
            ["pgrep", "-f", "uvicorn.*main:app"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            return [int(pid) for pid in pids if pid]
        return []
    except Exception as e:
        print(f"Error finding processes: {e}")
        return []


def get_process_info(pid: int) -> str:
    """Get process command line info."""
    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "command="],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return "Unknown"


def kill_process(pid: int) -> bool:
    """Kill a process by PID."""
    try:
        subprocess.run(["kill", str(pid)], check=True)
        return True
    except subprocess.CalledProcessError:
        # Try force kill
        try:
            subprocess.run(["kill", "-9", str(pid)], check=True)
            return True
        except subprocess.CalledProcessError:
            return False


def find_processes_on_port(port: int = 8000):
    """Find processes listening on a specific port."""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            return [int(pid) for pid in pids if pid]
        return []
    except Exception as e:
        print(f"Error finding processes on port {port}: {e}")
        return []


def main():
    """Main function to kill all server processes."""
    print("=" * 50)
    print("Kill All Servers - learn_fastapi_auth")
    print("=" * 50)

    # Find uvicorn processes
    uvicorn_pids = find_server_processes()

    # Also find any process on port 8000
    port_pids = find_processes_on_port(8000)

    # Combine and deduplicate
    all_pids = list(set(uvicorn_pids + port_pids))

    if not all_pids:
        print("\nNo running servers found.")
        print("  - No uvicorn main:app processes")
        print("  - No processes on port 8000")
        return 0

    print(f"\nFound {len(all_pids)} server process(es):\n")

    for pid in all_pids:
        info = get_process_info(pid)
        print(f"  PID {pid}: {info[:60]}...")

    print("\nKilling processes...")

    killed = 0
    failed = 0

    for pid in all_pids:
        if kill_process(pid):
            print(f"  [OK] Killed PID {pid}")
            killed += 1
        else:
            print(f"  [FAILED] Could not kill PID {pid}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"Summary: {killed} killed, {failed} failed")
    print("=" * 50)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
