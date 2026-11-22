"""Explicit launcher for approved authenticated loopback demonstrations."""

import os
from collections.abc import Mapping
from copy import deepcopy

from uvicorn import run
from uvicorn.config import LOGGING_CONFIG

from .application import create_app
from .audit import LOGGER_NAME
from .configuration import ApiConfiguration, ConfigurationError


def run_loopback(environment: Mapping[str, str]) -> None:
    settings = ApiConfiguration.from_environment(environment)
    if settings.mode != "loopback" or settings.bind_host is None or settings.bind_port is None:
        raise ConfigurationError("The HTTP launcher requires authenticated loopback mode.")
    logs = deepcopy(LOGGING_CONFIG)
    logs["formatters"]["nci_audit"] = {"format": "%(message)s"}
    logs["handlers"]["nci_audit"] = {
        "class": "logging.StreamHandler",
        "formatter": "nci_audit",
        "stream": "ext://sys.stderr",
    }
    logs["loggers"][LOGGER_NAME] = {
        "handlers": ["nci_audit"],
        "level": "INFO",
        "propagate": False,
    }
    run(
        create_app(settings),
        host=settings.bind_host,
        port=settings.bind_port,
        proxy_headers=False,
        access_log=False,
        server_header=False,
        lifespan="on",
        log_config=logs,
        log_level=settings.log_level.lower(),
        timeout_keep_alive=5,
    )


if __name__ == "__main__":
    run_loopback(os.environ)
