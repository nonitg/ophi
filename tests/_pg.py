"""Throwaway Postgres in Docker for outcomes-store tests. Skips when Docker isn't available."""

from __future__ import annotations

import shutil
import subprocess
import time
import uuid

import psycopg
import pytest

IMAGE = "postgres:17-alpine"


def start() -> tuple[str, str]:
    if not shutil.which("docker") or subprocess.run(["docker", "info"], capture_output=True).returncode:
        pytest.skip("docker not available")
    name = f"ophi-test-pg-{uuid.uuid4().hex[:8]}"
    subprocess.run(["docker", "run", "-d", "--rm", "--name", name, "-e", "POSTGRES_PASSWORD=test", "-p", "127.0.0.1::5432", IMAGE],
                   check=True, capture_output=True)
    port = subprocess.run(["docker", "port", name, "5432"], check=True, capture_output=True, text=True).stdout.split(":")[-1].strip()
    url = f"postgresql://postgres:test@127.0.0.1:{port}/postgres"
    for _ in range(60):
        try:
            psycopg.connect(url, connect_timeout=1).close()
            return name, url
        except psycopg.OperationalError:
            time.sleep(0.5)
    stop(name)
    raise RuntimeError("postgres did not start")


def stop(name: str) -> None:
    subprocess.run(["docker", "stop", name], capture_output=True)
