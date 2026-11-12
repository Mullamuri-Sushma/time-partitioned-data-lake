
from pathlib import Path
import pandas as pd

from src.config import TARGET_FILE_SIZE_MB


def analyze_file_sizes(output_dir: Path) -> dict:
    """
    Analyze Parquet file sizes and identify small files.
    """

    output_dir = Path(output_dir)

    parquet_files = list(output_dir.rglob("*.parquet"))

    if not parquet_files:
        return {
            "file_count": 0,
            "total_size_mb": 0,
            "average_size_mb": 0,
            "small_file_count": 0,
            "target_file_size_mb": TARGET_FILE_SIZE_MB,
        }

    sizes = [
        path.stat().st_size / (1024 * 1024)
        for path in parquet_files
    ]

    total_size = sum(sizes)
    average_size = total_size / len(sizes)

    small_files = [
        size for size in sizes
        if size < TARGET_FILE_SIZE_MB
    ]

    return {
        "file_count": len(parquet_files),
        "total_size_mb": round(total_size, 4),
        "average_size_mb": round(average_size, 4),
        "minimum_size_mb": round(min(sizes), 4),
        "maximum_size_mb": round(max(sizes), 4),
        "small_file_count": len(small_files),
        "target_file_size_mb": TARGET_FILE_SIZE_MB,
    }
