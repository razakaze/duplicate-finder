"""Report generation — CSV and JSON export of duplicate analysis results."""

import csv
import json
from pathlib import Path
from datetime import datetime

from models import ScanResult, DuplicateGroup
from utils.formatting import format_size


def write_csv_report(result: ScanResult, output_dir: Path) -> Path:
    """Write a detailed CSV report of all duplicate groups."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_dir / f"duplicate_report_{timestamp}.csv"

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "Group ID",
                "Match Type",
                "Filename",
                "Full Path",
                "Directory Root",
                "Size (bytes)",
                "Size (human)",
                "Last Modified",
                "SHA-256",
            ]
        )

        group_id = 1
        for group in result.binary_duplicates + result.diverged_files:
            for file in group.files:
                writer.writerow(
                    [
                        group_id,
                        group.match_type.value,
                        file.filename,
                        str(file.path),
                        str(file.directory_root),
                        file.size,
                        format_size(file.size),
                        file.modified.isoformat(),
                        file.sha256 or "",
                    ]
                )
            group_id += 1

    return filepath


def write_json_summary(result: ScanResult, output_dir: Path) -> Path:
    """Write a JSON summary report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_dir / f"duplicate_summary_{timestamp}.json"

    summary = {
        "scan_date": datetime.now().isoformat(),
        "directories": [str(d) for d in result.directories],
        "total_files": result.total_files,
        "files_per_directory": {
            str(k): v for k, v in result.files_per_directory.items()
        },
        "binary_duplicate_groups": len(result.binary_duplicates),
        "binary_duplicate_files": result.total_binary_duplicate_count,
        "diverged_groups": len(result.diverged_files),
        "reclaimable_bytes": result.total_reclaimable_bytes,
        "reclaimable_human": format_size(result.total_reclaimable_bytes),
        "scan_duration_seconds": round(result.scan_duration, 2),
        "hash_duration_seconds": round(result.hash_duration, 2),
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return filepath
