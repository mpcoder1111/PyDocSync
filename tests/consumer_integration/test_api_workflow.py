"""Programmatic Python API Workflow Test for External Consumer Projects.

WHAT IS THIS?
-------------
Tests PyDocSync Python API (`from pydocsync import check, init, accept, SyncResult`)
in an isolated external consumer codebase.
"""

from pathlib import Path
from pydocsync import SyncResult, accept, check, init
from .consumer_fixtures import create_data_pipeline_project


def test_api_workflow_lifecycle(tmp_path: Path):
    """Verify programmatic Python API usage in isolated consumer project."""
    proj_dir = create_data_pipeline_project(tmp_path / "pipeline_consumer")

    # Step 1: Programmatic init()
    init_count = init(root_dir=proj_dir)
    assert init_count == 3  # BatchProcessor, __init__, process_records

    # Step 2: Programmatic check() (clean)
    res_clean = check(root_dir=proj_dir)
    assert isinstance(res_clean, SyncResult)
    assert res_clean.is_synchronized is True
    assert res_clean.failure_count == 0
    assert len(res_clean.failures) == 0

    # Step 3: Simulate code modification (added KeyError to exception contract)
    processor_file = proj_dir / "data_pipeline" / "processor.py"
    processor_file.write_text(
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
        for r in records:
            if "id" not in r:
                raise KeyError("Missing required record id")
        return records
''',
        encoding="utf-8",
    )

    # Step 4: Programmatic check() detects failure
    res_drift = check(root_dir=proj_dir)
    assert res_drift.is_synchronized is False
    assert res_drift.failure_count >= 1
    failures_by_name = {f.symbol.name: f for f in res_drift.failures}
    assert "process_records" in failures_by_name
    assert failures_by_name["process_records"].rule_result.rule_id == "RULE_EXCEPTION_BEHAVIOR_CHANGE"

    # Step 5: Programmatic accept()
    accepted = accept(
        symbol_qualname="BatchProcessor.process_records",
        reason="Added schema validation checking for record id key",
        root_dir=proj_dir,
    )
    assert accepted is True
    # Also accept class if class body changed
    if "BatchProcessor" in failures_by_name:
        accept(
            symbol_qualname="BatchProcessor",
            reason="Updated method exception contract in class",
            root_dir=proj_dir,
        )

    # Step 6: Final check() passes
    res_final = check(root_dir=proj_dir)
    assert res_final.is_synchronized is True
    assert res_final.failure_count == 0
