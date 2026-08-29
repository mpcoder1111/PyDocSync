"""Baseline Lockfile Manager for PyDocSync.

WHAT IS THIS?
-------------
Manages distributed JSON baseline lockfiles in `.project/pydocsync/<package>/<module>.json`
and enforces gated baseline creation (refusing baseline creation for symbols with missing
or invalid documentation).
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydocsync.ast_extract import SymbolRepresentation
from pydocsync.fingerprint import FingerprintSet


@dataclass
class BaselineRecord:
    """Persisted baseline state for a single Python symbol."""

    code: str
    api: str
    types: str
    doc: str
    raise_type: str
    raise_detail: str
    example: str | None
    status: str  # "synchronized", "acknowledged"
    last_reviewed_at: str
    review_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaselineRecord":
        return cls(**data)


class BaselineManager:
    """Handles loading, updating, and validating distributed JSON baselines."""

    def __init__(self, root_dir: Path | str = ".") -> None:
        self.root_dir = Path(root_dir)
        self.baseline_root = self.root_dir / ".project" / "pydocsync"

    def _get_baseline_path(self, module_path: Path | str) -> Path:
        """Derive the modular JSON baseline path for a given Python file."""
        mod_p = Path(module_path)
        if mod_p.is_absolute():
            try:
                mod_p = mod_p.relative_to(self.root_dir)
            except ValueError:
                pass
        # Replace .py with .json under baseline_root
        relative_no_ext = mod_p.with_suffix("")
        return self.baseline_root / f"{relative_no_ext}.json"

    def load_module_baseline(self, module_path: Path | str) -> dict[str, BaselineRecord]:
        """Load baseline records for a module; returns empty dict if not found or corrupted."""
        path = self._get_baseline_path(module_path)
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
        
        # Support schema_version 1 envelope
        if isinstance(raw_data, dict) and "schema_version" in raw_data and "symbols" in raw_data:
            records = raw_data["symbols"]
        elif isinstance(raw_data, dict):
            records = raw_data
        else:
            return {}
            
        return {qualname: BaselineRecord.from_dict(rec) for qualname, rec in records.items() if isinstance(rec, dict)}

    def save_module_baseline(self, module_path: Path | str, records: dict[str, BaselineRecord]) -> None:
        """Persist module baseline records as sorted, formatted JSON."""
        path = self._get_baseline_path(module_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        serializable = {k: v.to_dict() for k, v in sorted(records.items())}
        
        envelope = {
            "schema_version": 1,
            "pydocsync_version": "0.2.0",
            "fingerprint_algorithm": "sha256",
            "symbols": serializable,
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2, sort_keys=True)

    def record_symbol_baseline(
        self,
        module_path: Path | str,
        sym: SymbolRepresentation,
        fp: FingerprintSet,
        reason: str | None = None,
        enforce_gating: bool = True,
    ) -> BaselineRecord:
        """Record or update a symbol baseline with gating checks."""
        if enforce_gating and sym.is_public:
            if not sym.docstring or not sym.docstring.strip():
                raise ValueError(
                    f"Gating violation: Cannot baseline public symbol '{sym.qualname}' without a docstring."
                )

        records = self.load_module_baseline(module_path)
        now_iso = datetime.now(timezone.utc).isoformat()
        rec = BaselineRecord(
            code=fp.code,
            api=fp.api,
            types=fp.types,
            doc=fp.doc,
            raise_type=fp.raise_type,
            raise_detail=fp.raise_detail,
            example=fp.example,
            status="acknowledged" if reason else "synchronized",
            last_reviewed_at=now_iso,
            review_reason=reason,
        )
        records[sym.qualname] = rec
        self.save_module_baseline(module_path, records)
        return rec
