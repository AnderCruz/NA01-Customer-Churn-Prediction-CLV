"""Run the WP-10.9 reference workload against the approved local launcher."""

import asyncio
import json
import os
import platform
import secrets
import socket
import subprocess
import sys
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from importlib.metadata import version
from math import ceil
from pathlib import Path
from statistics import median
from tempfile import TemporaryDirectory
from time import perf_counter, sleep
from typing import Any

from httpx2 import Client, HTTPError
from starlette.requests import HTTPConnection
from test_api_research import configuration, digest, encode, write_fixture

from nowa_customer_intelligence.api.application import create_app
from nowa_customer_intelligence.api.configuration import ApiConfiguration
from nowa_customer_intelligence.api.research import verified_release
from nowa_customer_intelligence.api.security import ResearchBearer

ROUTES = (
    "/health/live",
    "/health/ready",
    "/v1/research/capabilities",
    "/v1/research/models",
    "/v1/research/models/churn",
    "/v1/research/models/clv/evaluation",
    "/v1/research/models/churn/limitations",
    "/v1/research/models/clv/explainability",
    "/v1/research/segmentation/status",
)
REQUESTS, WARMUPS, STARTS = 200, 30, 5


def benchmark_fixture(root: Path) -> tuple[ApiConfiguration, str]:
    _, manifest = write_fixture(root)
    manifest["release_id"] = "reference-isolated-synthetic-forecast-summary-v1"
    manifest["published_at"] = "2026-11-21T12:00:00Z"
    for member in manifest["members"]:
        path = root / member["basename"]
        report = json.loads(path.read_bytes())
        if "limitations" in report["data"]:
            for limitation in report["data"]["limitations"]:
                limitation["description"] = "Synthetic research exercise. " + "a" * 211
        if "methods" in report["data"]:
            for method in report["data"]["methods"]:
                if method["output_scale"] != "class-1-log-odds":
                    method.update(background_rank_median=0.95, bootstrap_rank_median=0.96)
        raw = encode(report)
        path.write_bytes(raw)
        member.update(sha256=digest(raw), size_bytes=len(raw))
    settings = configuration(root, manifest)
    assert settings.release_sha256 is not None
    return settings, settings.release_sha256


def localhost_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reservation:
        reservation.bind(("127.0.0.1", 0))
        return int(reservation.getsockname()[1])


def environment(root: Path, pin: str, port: int, token: str) -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if not key.startswith("NCI_API_")} | {
        "NCI_API_MODE": "loopback",
        "NCI_API_BUNDLE_ROOT": str(root),
        "NCI_API_RELEASE_SHA256": pin,
        "NCI_API_BIND_HOST": "127.0.0.1",
        "NCI_API_BIND_PORT": str(port),
        "NCI_API_BEARER_SECRET": token,
        "NCI_API_BEARER_EXPIRES_AT": (datetime.now(UTC) + timedelta(hours=1))
        .isoformat()
        .replace("+00:00", "Z"),
        "NCI_API_LOG_LEVEL": "WARNING",
    }


@contextmanager
def server(
    root: Path, pin: str
) -> Iterator[tuple[Client, subprocess.Popen[bytes], float, dict[str, str]]]:
    port, token = localhost_port(), secrets.token_urlsafe(32)
    config = environment(root, pin, port, token)
    started = perf_counter()
    with subprocess.Popen(
        [sys.executable, "-m", "nowa_customer_intelligence.api.launcher"],
        env=config,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ) as process:
        try:
            with Client(
                base_url=f"http://127.0.0.1:{port}",
                trust_env=False,
                timeout=4,
                headers={"Authorization": f"Bearer {token}"},
            ) as client:
                while perf_counter() - started < 20 and process.poll() is None:
                    try:
                        ready = client.get("/health/ready").status_code == 200
                    except HTTPError:
                        ready = False
                    if ready:
                        yield client, process, (perf_counter() - started) * 1000, config
                        return
                    sleep(0.01)
                raise RuntimeError("The local process did not publish the pinned fixture.")
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)


def rss_peak_kib(pid: int) -> int | None:
    status = Path(f"/proc/{pid}/status")
    if status.exists():
        for line in status.read_text().splitlines():
            if line.startswith("VmHWM:"):
                return int(line.split()[1])
    return None


def stats(samples: list[float]) -> dict[str, float]:
    return {
        "p50_ms": round(median(samples), 3),
        "p95_ms": round(sorted(samples)[ceil(0.95 * len(samples)) - 1], 3),
    }


def workload(client: Client) -> list[dict[str, Any]]:
    results = []
    for route in ROUTES:
        for _ in range(WARMUPS):
            assert client.get(route).status_code == 200

        def sample(_: int, path: str = route) -> tuple[float, int, int]:
            start = perf_counter()
            response = client.get(path)
            return (perf_counter() - start) * 1000, response.status_code, len(response.content)

        for concurrency in (1, 8):
            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                observations = list(pool.map(sample, range(REQUESTS)))
            errors = sum(status != 200 for _, status, _ in observations)
            results.append(
                {
                    "route": route,
                    "concurrency": concurrency,
                    "requests": REQUESTS,
                    **stats([elapsed for elapsed, _, _ in observations]),
                    "status_errors": errors,
                    "max_payload_bytes": max(size for _, _, size in observations),
                }
            )
    return results


async def component_costs(
    file_settings: ApiConfiguration,
    config: dict[str, str],
) -> dict[str, dict[str, float]]:
    loading = []
    for _ in range(STARTS):
        before = perf_counter()
        async with verified_release(file_settings) as catalogue:
            assert catalogue is not None
            loading.append((perf_counter() - before) * 1000)
    bearer = ResearchBearer(None)
    permission_app = create_app(ApiConfiguration.from_environment(config))
    request = HTTPConnection(
        {
            "type": "http",
            "app": permission_app,
            "headers": [(b"authorization", f"Bearer {config['NCI_API_BEARER_SECRET']}".encode())],
        }
    )
    for _ in range(WARMUPS):
        await bearer(request)
    auth = []
    for _ in range(REQUESTS):
        before = perf_counter()
        await bearer(request)
        auth.append((perf_counter() - before) * 1000)
    return {"evidence_loading": stats(loading), "bearer_only": stats(auth)}


def main() -> None:
    with TemporaryDirectory(prefix="nci-api-benchmark-") as temporary:
        root = Path(temporary)
        settings, pin = benchmark_fixture(root)
        startups = []
        for start in range(STARTS):
            with server(root, pin) as (client, process, startup_ms, config):
                startups.append(startup_ms)
                if start == STARTS - 1:
                    timings = workload(client)
                    peak = rss_peak_kib(process.pid)
                    costs = asyncio.run(component_costs(settings, config))
        cpu = Path("/proc/cpuinfo")
        mem = Path("/proc/meminfo")
        output = {
            "fixture_release_sha256": pin,
            "fixture_total_bytes": sum(path.stat().st_size for path in root.iterdir()),
            "workers": 1,
            "cold_starts": STARTS,
            "warmups_per_route": WARMUPS,
            "platform": platform.platform(),
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "cpu": next(
                (
                    line.split(":", 1)[1].strip()
                    for line in cpu.read_text().splitlines()
                    if line.startswith("model name")
                ),
                "",
            )
            if cpu.exists()
            else platform.processor(),
            "memory": mem.read_text().splitlines()[0] if mem.exists() else None,
            "dependencies": {
                name: version(name)
                for name in ("fastapi", "starlette", "pydantic", "uvicorn", "httpx2")
            },
            "startup": stats(startups),
            "startup_max_ms": round(max(startups), 3),
            "peak_rss_kib": peak,
            "components": costs,
            "measurements": timings,
        }
        print(json.dumps(output, indent=2))
        assert all(item["status_errors"] == 0 for item in timings)


if __name__ == "__main__":
    main()
