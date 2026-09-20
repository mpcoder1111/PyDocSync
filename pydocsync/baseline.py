"""Baseline Lockfile Manager for PyDocSync.

WHAT IS THIS?
-------------
Manages distributed JSON baseline lockfiles in `.project/pydocsync/<package>/<module>.json`
and enforces gated baseline creation (refusing baseline creation for symbols with missing
or invalid documentation).

Reading comes in two flavours. `read_module_baseline` is strict: a missing lockfile is an empty
baseline, but a corrupt, unreadable or unsupported lockfile raises `BaselineProblemError`, so it
can never be mistaken for "no baseline". `load_module_baseline` is the historical lenient reader
(returns `{}` for anything unreadable); it is kept for backward compatibility only and must not
be used on evaluation or write paths.
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydocsync._version import __version__
from pydocsync.ast_extract import SymbolRepresentation
from pydocsync.fingerprint import FingerprintSet
from pydocsync.problems import BaselineProblemError, Problem, ProblemKind

SUPPORTED_SCHEMA_VERSION = 1

_REQUIRED_RECORD_FIELDS = (
    "code",
    "api",
    "types",
    "doc",
    "raise_type",
    "raise_detail",
    "example",
    "status",
    "last_reviewed_at",
)
_OPTIONAL_RECORD_FIELDS = ("review_reason",)
_NULLABLE_RECORD_FIELDS = frozenset({"example", "review_reason"})


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
        """Initialize BaselineManager with project root directory.

        Args:
            root_dir: Root directory of the project (default ".").
        """
        self.root_dir = Path(root_dir).resolve()
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

    def lockfile_relpath(self, module_path: Path | str) -> str:
        """Return the lockfile path for a module as a POSIX string relative to the root."""
        return self._get_baseline_path(module_path).relative_to(self.root_dir).as_posix()

    def _problem(self, path: Path, kind: ProblemKind, reason: str) -> BaselineProblemError:
        rel = path.relative_to(self.root_dir).as_posix()
        return BaselineProblemError(Problem(kind=kind, path=rel, line=None, reason=reason))

    def read_module_baseline(self, module_path: Path | str) -> dict[str, BaselineRecord]:
        """Strictly load baseline records for a module.

        A missing lockfile is an empty baseline (the module was never baselined). Anything else
        that is not a valid lockfile is a problem, never silently treated as "no baseline".

        Args:
            module_path: Python module path (relative to the root, or absolute).

        Returns:
            Records keyed by per-file unique symbol key; `{}` if no lockfile exists.

        Raises:
            BaselineProblemError: If the lockfile is unreadable, empty, not valid JSON, structurally
                invalid, or written by a newer, unsupported schema version.
        """
        path = self._get_baseline_path(module_path)
        if not path.exists():
            return {}
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as err:
            raise self._problem(path, ProblemKind.BASELINE_UNREADABLE, f"cannot read lockfile: {err}") from err
        if not text.strip():
            raise self._problem(path, ProblemKind.BASELINE_CORRUPT, "lockfile is empty")
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as err:
            raise self._problem(
                path, ProblemKind.BASELINE_CORRUPT, f"invalid JSON at line {err.lineno} column {err.colno}: {err.msg}"
            ) from err

        records = self._extract_records(path, raw)
        return {key: BaselineRecord.from_dict(rec) for key, rec in records.items()}

    def _extract_records(self, path: Path, raw: Any) -> dict[str, dict[str, Any]]:
        """Validate the lockfile structure and return raw record dicts."""
        if not isinstance(raw, dict):
            raise self._problem(path, ProblemKind.BASELINE_CORRUPT, "top-level JSON value must be an object")

        if "schema_version" in raw:
            version = raw["schema_version"]
            if isinstance(version, bool) or not isinstance(version, int) or version < 1:
                raise self._problem(path, ProblemKind.BASELINE_CORRUPT, f"invalid schema_version {version!r}")
            if version > SUPPORTED_SCHEMA_VERSION:
                raise self._problem(
                    path,
                    ProblemKind.BASELINE_UNSUPPORTED_VERSION,
                    f"schema_version {version} is newer than the supported version "
                    f"{SUPPORTED_SCHEMA_VERSION}; upgrade pydocsync",
                )
            records = raw.get("symbols")
            if not isinstance(records, dict):
                raise self._problem(path, ProblemKind.BASELINE_CORRUPT, "'symbols' must be a JSON object")
        else:
            # Legacy (pre-envelope) format: the top-level object maps symbol keys to records.
            records = raw

        for key, rec in records.items():
            self._validate_record(path, key, rec)
        return records

    def _validate_record(self, path: Path, key: str, rec: Any) -> None:
        if not isinstance(rec, dict):
            raise self._problem(path, ProblemKind.BASELINE_CORRUPT, f"record '{key}' must be a JSON object")
        missing = [f for f in _REQUIRED_RECORD_FIELDS if f not in rec]
        if missing:
            raise self._problem(
                path, ProblemKind.BASELINE_CORRUPT, f"record '{key}' is missing field(s): {', '.join(missing)}"
            )
        unknown = sorted(set(rec) - set(_REQUIRED_RECORD_FIELDS) - set(_OPTIONAL_RECORD_FIELDS))
        if unknown:
            raise self._problem(
                path, ProblemKind.BASELINE_CORRUPT, f"record '{key}' has unknown field(s): {', '.join(unknown)}"
            )
        for name, value in rec.items():
            if value is None and name in _NULLABLE_RECORD_FIELDS:
                continue
            if not isinstance(value, str):
                raise self._problem(
                    path, ProblemKind.BASELINE_CORRUPT, f"record '{key}' field '{name}' must be a string"
                )

    def load_module_baseline(self, module_path: Path | str) -> dict[str, BaselineRecord]:
        """Load baseline records for a module; returns empty dict if not found or corrupted.

        Historical lenient reader kept for backward compatibility. It cannot tell a corrupt
        lockfile from a missing one, so evaluation and write paths use `read_module_baseline`.
        """
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
            "pydocsync_version": __version__,
            "fingerprint_algorithm": "sha256",
            "symbols": serializable,
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(envelope, f, indent=2, sort_keys=True)

    @staticmethod
    def make_record(fp: FingerprintSet, reason: str | None = None) -> BaselineRecord:
        """Build a baseline record for the given fingerprints.

        Args:
            fp: Current fingerprints of the symbol.
            reason: Audit reason; when given the record is marked `acknowledged`.

        Returns:
            A new BaselineRecord stamped with the current UTC time.
        """
        return BaselineRecord(
            code=fp.code,
            api=fp.api,
            types=fp.types,
            doc=fp.doc,
            raise_type=fp.raise_type,
            raise_detail=fp.raise_detail,
            example=fp.example,
            status="acknowledged" if reason else "synchronized",
            last_reviewed_at=datetime.now(timezone.utc).isoformat(),
            review_reason=reason,
        )

    def record_symbol_baseline(
        self,
        module_path: Path | str,
        sym: SymbolRepresentation,
        fp: FingerprintSet,
        reason: str | None = None,
        enforce_gating: bool = True,
    ) -> BaselineRecord:
        """Record or update a symbol baseline with gating checks.

        The record is stored under the symbol's per-file unique `key`, so same-named definitions
        in one file keep separate records.

        Args:
            module_path: Python module path (relative to the root, or absolute).
            sym: Symbol to record.
            fp: Current fingerprints of the symbol.
            reason: Audit reason; when given the record is marked `acknowledged`.
            enforce_gating: Refuse to baseline a public symbol that has no docstring.

        Returns:
            The record that was written.

        Raises:
            ValueError: If gating is enforced and a public symbol has no docstring.
            BaselineProblemError: If the module's existing lockfile is corrupt, unreadable or
                unsupported; it is never overwritten.
        """
        if enforce_gating and sym.is_public:
            if not sym.docstring or not sym.docstring.strip():
                raise ValueError(
                    f"Gating violation: Cannot baseline public symbol '{sym.qualname}' without a docstring."
                )

        records = self.read_module_baseline(module_path)
        rec = self.make_record(fp, reason)
        records[sym.key] = rec
        self.save_module_baseline(module_path, records)
        return rec
