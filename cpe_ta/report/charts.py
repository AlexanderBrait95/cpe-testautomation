"""Chart generators — headless matplotlib (Agg backend)."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # Must be set before importing pyplot

import matplotlib.pyplot as plt  # noqa: E402


def generate_throughput_chart(data: list[dict[str, object]], output_path: str) -> None:
    """Generate a bar chart of throughput_mbps per firmware_version.

    Parameters
    ----------
    data:
        List of dicts with keys ``firmware_version`` (str) and
        ``throughput_mbps`` (float).
    output_path:
        Destination PNG file path.
    """
    labels = [str(d["firmware_version"]) for d in data]
    values = [float(d["throughput_mbps"]) for d in data]  # type: ignore[arg-type]

    fig, ax = plt.subplots()
    ax.bar(labels, values, color="steelblue")
    ax.set_xlabel("Firmware Version")
    ax.set_ylabel("Throughput (Mbit/s)")
    ax.set_title("Throughput by Firmware Version")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def generate_latency_chart(data: list[dict[str, object]], output_path: str) -> None:
    """Generate a bar chart of latency_ms per firmware_version.

    Parameters
    ----------
    data:
        List of dicts with keys ``firmware_version`` (str) and
        ``latency_ms`` (float).
    output_path:
        Destination PNG file path.
    """
    labels = [str(d["firmware_version"]) for d in data]
    values = [float(d["latency_ms"]) for d in data]  # type: ignore[arg-type]

    fig, ax = plt.subplots()
    ax.bar(labels, values, color="tomato")
    ax.set_xlabel("Firmware Version")
    ax.set_ylabel("Latency (ms)")
    ax.set_title("Latency by Firmware Version")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
