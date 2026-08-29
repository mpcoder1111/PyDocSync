"""External project fixture generators for consumer integration testing.

WHAT IS THIS?
-------------
Creates realistic, standalone external Python projects in isolated temporary
directories to simulate third-party developers using PyDocSync as an installed package.
"""

from pathlib import Path


def create_cli_app_project(dest_dir: Path) -> Path:
    """Create a multi-module CLI utility application in dest_dir."""
    src_dir = dest_dir / "my_cli_app"
    src_dir.mkdir(parents=True, exist_ok=True)

    # 1. parser.py
    (src_dir / "parser.py").write_text(
        '''"""CLI argument and payload parser."""

def parse_config(raw_path: str, max_retries: int = 3) -> dict:
    """Parse configuration file into structured dictionary.

    Args:
        raw_path: Path to configuration file.
        max_retries: Retry attempts on transient read error (default 3).

    Returns:
        Parsed configuration dictionary.
    """
    return {"path": raw_path, "retries": max_retries}
''',
        encoding="utf-8",
    )

    # 2. formatter.py
    (src_dir / "formatter.py").write_text(
        '''"""Output formatter for CLI tool."""

def format_output(data: dict, indent: int = 2) -> str:
    """Format dictionary as indented text string.

    Args:
        data: Dictionary data to format.
        indent: Space indentation count (default 2).

    Returns:
        Formatted multi-line text string.
    """
    return str(data)
''',
        encoding="utf-8",
    )

    return dest_dir


def create_data_pipeline_project(dest_dir: Path) -> Path:
    """Create a class-based data pipeline engine in dest_dir."""
    src_dir = dest_dir / "data_pipeline"
    src_dir.mkdir(parents=True, exist_ok=True)

    (src_dir / "processor.py").write_text(
        '''"""Batch stream processor module."""

class BatchProcessor:
    """Processes chunks of data records."""

    def __init__(self, batch_size: int = 100, strict_mode: bool = True) -> None:
        """Initialize BatchProcessor.

        Args:
            batch_size: Number of records per chunk (default 100).
            strict_mode: If True, raise on invalid record (default True).
        """
        self.batch_size = batch_size
        self.strict_mode = strict_mode

    def process_records(self, records: list[dict]) -> list[dict]:
        """Transform batch of records.

        Args:
            records: List of raw input dictionaries.

        Returns:
            List of processed records.

        Raises:
            ValueError: If records list is empty.
        """
        if not records:
            raise ValueError("Records list cannot be empty")
        return [r for r in records if r]
''',
        encoding="utf-8",
    )

    return dest_dir
