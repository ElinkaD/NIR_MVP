"""Generate PNG assets for the research report."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-etl-mvp")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate report charts from ETL metrics.")
    parser.add_argument("--metrics", default="data/output/metrics.json", help="Path to metrics.json.")
    parser.add_argument("--log", default="data/output/processing_log.csv", help="Path to processing_log.csv.")
    parser.add_argument("--output", default="reports/assets", help="Directory for generated PNG files.")
    return parser.parse_args()


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as file_obj:
        return json.load(file_obj)


def load_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as file_obj:
        return list(csv.DictReader(file_obj))


def save_bar_chart(
    data: dict[str, float | int],
    *,
    title: str,
    ylabel: str,
    output_path: Path,
    percent: bool = False,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.8))
    if data:
        labels = list(data.keys())
        values = [float(value) * (100 if percent else 1) for value in data.values()]
        ax.bar(labels, values, color="#2F6F73")
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", alpha=0.25)
    else:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.set_axis_off()
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def save_processing_time_chart(items: list[dict[str, Any]], output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.8))
    if items:
        labels = [str(item.get("file_name") or item.get("document_id")) for item in items]
        values = [float(item.get("processing_time_sec") or 0.0) for item in items]
        ax.plot(range(1, len(values) + 1), values, marker="o", color="#7A4E9D")
        ax.set_xticks(range(1, len(labels) + 1))
        ax.set_xticklabels(labels, rotation=30, ha="right")
        ax.set_ylabel("seconds")
        ax.grid(alpha=0.25)
    else:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.set_axis_off()
    ax.set_title("Processing Time Per Document")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def save_architecture_diagram(output_path: Path) -> None:
    stages = ["User", "Input", "Ingest", "Extract", "Transform", "Validate", "Load", "Output"]
    descriptions = [
        "CLI",
        "data/input",
        "pathlib + hashlib",
        "PDF/DOCX/HTML adapters",
        "clean + enrich",
        "Pydantic checks",
        "JSON/CSV",
        "dataset + metrics",
    ]
    fig, ax = plt.subplots(figsize=(14, 3.2))
    ax.set_axis_off()

    for index, (stage, description) in enumerate(zip(stages, descriptions)):
        x = index / len(stages) + 0.03
        width = 0.105
        rect = plt.Rectangle((x, 0.42), width, 0.28, facecolor="#E8F1F2", edgecolor="#2F6F73", linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + width / 2, 0.59, stage, ha="center", va="center", fontsize=10, weight="bold")
        ax.text(x + width / 2, 0.49, description, ha="center", va="center", fontsize=8)
        if index < len(stages) - 1:
            ax.annotate(
                "",
                xy=(x + width + 0.018, 0.56),
                xytext=(x + width + 0.002, 0.56),
                arrowprops={"arrowstyle": "->", "color": "#444444", "lw": 1.2},
            )

    ax.set_title("MVP ETL Architecture: User -> Input -> Ingest -> Extract -> Transform -> Validate -> Load -> Output")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def generate_assets(metrics_path: str | Path, log_path: str | Path, output_dir: str | Path) -> None:
    metrics = load_json(metrics_path)
    _log_rows = load_csv(log_path)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    save_bar_chart(
        metrics.get("file_format_distribution", {}),
        title="File Formats Distribution",
        ylabel="files",
        output_path=output / "file_formats_distribution.png",
    )
    save_bar_chart(
        metrics.get("success_rate_by_format", {}),
        title="Success Rate By Format",
        ylabel="success rate, %",
        output_path=output / "success_rate_by_format.png",
        percent=True,
    )
    save_bar_chart(
        metrics.get("average_processing_time_by_format", {}),
        title="Average Processing Time By Format",
        ylabel="seconds",
        output_path=output / "average_processing_time_by_format.png",
    )
    save_bar_chart(
        metrics.get("metadata_completeness_by_field", {}),
        title="Metadata Completeness",
        ylabel="completeness, %",
        output_path=output / "metadata_completeness.png",
        percent=True,
    )
    save_processing_time_chart(
        metrics.get("processing_time_by_document", []),
        output_path=output / "processing_time_per_document.png",
    )
    save_architecture_diagram(output / "etl_architecture.png")


def main() -> None:
    args = parse_args()
    generate_assets(args.metrics, args.log, args.output)
    print(f"Report assets written to {args.output}")


if __name__ == "__main__":
    main()
