"""Realistic AI modification scenarios across 3 external Apache-2.0 repositories.

WHAT IS THIS?
-------------
Contains 20 realistic AI development modification scenarios across:
1. Dulwich (7 scenarios)
2. Janome (7 scenarios)
3. python-sdb (6 scenarios)

Spanning 6 categories (SAFE_REFACTOR, BUG_FIX_THRESHOLD, API_DEFAULT_CHANGE,
EXCEPTION_ADDITION, TYPE_REFINEMENT, DOC_UPDATE).
"""

from dataclasses import dataclass


@dataclass
class ExternalScenario:
    scenario_id: str
    repository: str  # "Dulwich", "Janome", "python-sdb"
    target_symbol: str
    category: str
    description: str
    initial_code: str
    modified_code: str
    ai_intended_action: str  # "PASS", "DOC_UPDATE", "CLI_ACCEPT"


EXTERNAL_SCENARIOS: list[ExternalScenario] = [
    # -------------------------------------------------------------------------
    # DULWICH SCENARIOS (7 cases)
    # -------------------------------------------------------------------------
    ExternalScenario(
        scenario_id="EXT_DULWICH_01_REFACTOR",
        repository="Dulwich",
        target_symbol="PackFileHeader.pack",
        category="SAFE_REFACTOR",
        description="Local variable caching before struct.pack call",
        initial_code='''def pack(self) -> bytes:
    """Serialize header into 12-byte binary format."""
    return struct.pack("!4sII", b"PACK", self.version, self.num_objects)
''',
        modified_code='''def pack(self) -> bytes:
    """Serialize header into 12-byte binary format."""
    fmt = "!4sII"
    return struct.pack(fmt, b"PACK", self.version, self.num_objects)
''',
        ai_intended_action="PASS",
    ),
    ExternalScenario(
        scenario_id="EXT_DULWICH_02_DEFAULT_VERSION",
        repository="Dulwich",
        target_symbol="PackFileHeader.__init__",
        category="API_DEFAULT_CHANGE",
        description="Changed default packfile version from 2 to 3",
        initial_code='''def __init__(self, version: int = 2, num_objects: int = 0) -> None:
    """Initialize PackFileHeader.

    Args:
        version: Pack format version (default 2).
        num_objects: Total count of objects contained in the pack.
    """
    self.version = version
    self.num_objects = num_objects
''',
        modified_code='''def __init__(self, version: int = 3, num_objects: int = 0) -> None:
    """Initialize PackFileHeader.

    Args:
        version: Pack format version (default 2).
        num_objects: Total count of objects contained in the pack.
    """
    self.version = version
    self.num_objects = num_objects
''',
        ai_intended_action="DOC_UPDATE",
    ),
    ExternalScenario(
        scenario_id="EXT_DULWICH_03_VARINT_THRESHOLD",
        repository="Dulwich",
        target_symbol="unpack_object_header",
        category="BUG_FIX_THRESHOLD",
        description="Increased bitmask threshold shift from 4 to 7 for extended varint",
        initial_code='''def unpack_object_header(stream: BinaryIO) -> tuple[int, int]:
    """Unpack variable-length Git object type and uncompressed size."""
    max_shift = 28
    return (1, 100)
''',
        modified_code='''def unpack_object_header(stream: BinaryIO) -> tuple[int, int]:
    """Unpack variable-length Git object type and uncompressed size."""
    max_shift = 56
    return (1, 100)
''',
        ai_intended_action="CLI_ACCEPT",
    ),
    ExternalScenario(
        scenario_id="EXT_DULWICH_04_RAISE_CHECKSUM_ERROR",
        repository="Dulwich",
        target_symbol="PackFileHeader.parse_checksum",
        category="EXCEPTION_ADDITION",
        description="Added ChecksumMismatchError when trailer is corrupted",
        initial_code='''def parse_checksum(self, raw_bytes: bytes, offset: int = 0) -> bytes:
    """Extract 20-byte SHA-1 trailer checksum."""
    if len(raw_bytes) < offset + 20:
        raise ValueError("Buffer too small for pack trailer SHA-1")
    return raw_bytes[offset : offset + 20]
''',
        modified_code='''def parse_checksum(self, raw_bytes: bytes, offset: int = 0) -> bytes:
    """Extract 20-byte SHA-1 trailer checksum."""
    if len(raw_bytes) < offset + 20:
        raise ValueError("Buffer too small for pack trailer SHA-1")
    sha = raw_bytes[offset : offset + 20]
    if sha == b"\\x00" * 20:
        raise RuntimeError("Null SHA trailer detected")
    return sha
''',
        ai_intended_action="DOC_UPDATE",
    ),
    ExternalScenario(
        scenario_id="EXT_DULWICH_05_CRC32_DOC",
        repository="Dulwich",
        target_symbol="compute_pack_crc32",
        category="DOC_UPDATE",
        description="Added docstring Google style parameters",
        initial_code='''def compute_pack_crc32(data: bytes, initial_crc: int = 0) -> int:
    """Compute 32-bit CRC checksum for delta chunk."""
    import zlib
    return zlib.crc32(data, initial_crc) & 0xFFFFFFFF
''',
        modified_code='''def compute_pack_crc32(data: bytes, initial_crc: int = 0) -> int:
    """Compute 32-bit CRC checksum for delta chunk.

    Args:
        data: Chunk bytes to compute CRC32 for.
        initial_crc: Initial CRC seed (default 0).

    Returns:
        Unsigned 32-bit integer checksum.
    """
    import zlib
    return zlib.crc32(data, initial_crc) & 0xFFFFFFFF
''',
        ai_intended_action="DOC_UPDATE",
    ),
    ExternalScenario(
        scenario_id="EXT_DULWICH_06_RENAME_VAR",
        repository="Dulwich",
        target_symbol="unpack_object_header",
        category="SAFE_REFACTOR",
        description="Renamed local shift variable to bit_shift",
        initial_code='''def unpack_object_header(stream: BinaryIO) -> tuple[int, int]:
    """Unpack variable-length Git object type and uncompressed size."""
    shift = 4
    return (1, shift)
''',
        modified_code='''def unpack_object_header(stream: BinaryIO) -> tuple[int, int]:
    """Unpack variable-length Git object type and uncompressed size."""
    bit_shift = 4
    return (1, bit_shift)
''',
        ai_intended_action="PASS",
    ),
    ExternalScenario(
        scenario_id="EXT_DULWICH_07_OPTIONAL_RETURN",
        repository="Dulwich",
        target_symbol="PackFileHeader.parse_checksum",
        category="TYPE_REFINEMENT",
        description="Refined return type to bytes | None",
        initial_code='''def parse_checksum(self, raw_bytes: bytes, offset: int = 0) -> bytes:
    """Extract 20-byte SHA-1 trailer checksum."""
    return raw_bytes[offset : offset + 20]
''',
        modified_code='''def parse_checksum(self, raw_bytes: bytes, offset: int = 0) -> bytes | None:
    """Extract 20-byte SHA-1 trailer checksum."""
    if not raw_bytes:
        return None
    return raw_bytes[offset : offset + 20]
''',
        ai_intended_action="DOC_UPDATE",
    ),

    # -------------------------------------------------------------------------
    # JANOME SCENARIOS (7 cases)
    # -------------------------------------------------------------------------
    ExternalScenario(
        scenario_id="EXT_JANOME_01_DEFAULT_READING",
        repository="Janome",
        target_symbol="Token.__init__",
        category="API_DEFAULT_CHANGE",
        description="Changed default reading from '*' to 'UNK'",
        initial_code='''def __init__(self, surface: str, pos: str, base_form: str, reading: str = "*") -> None:
    """Initialize token.

    Args:
        surface: Surface string form.
        pos: Part of speech tag.
        base_form: Base dictionary form.
        reading: Phonetic reading or pronunciation (default '*').
    """
    self.surface = surface
''',
        modified_code='''def __init__(self, surface: str, pos: str, base_form: str, reading: str = "UNK") -> None:
    """Initialize token.

    Args:
        surface: Surface string form.
        pos: Part of speech tag.
        base_form: Base dictionary form.
        reading: Phonetic reading or pronunciation (default '*').
    """
    self.surface = surface
''',
        ai_intended_action="DOC_UPDATE",
    ),
    ExternalScenario(
        scenario_id="EXT_JANOME_02_PUNCT_CHECK_REFACTOR",
        repository="Janome",
        target_symbol="Token.is_punct",
        category="SAFE_REFACTOR",
        description="Consolidated tuple prefix check in is_punct",
        initial_code='''def is_punct(self) -> bool:
    """Check if token is punctuation."""
    return self.pos.startswith("記号") or self.pos.startswith("Punctuation")
''',
        modified_code='''def is_punct(self) -> bool:
    """Check if token is punctuation."""
    return self.pos.startswith(("記号", "Punctuation"))
''',
        ai_intended_action="PASS",
    ),
    ExternalScenario(
        scenario_id="EXT_JANOME_03_MAX_LEN_THRESHOLD",
        repository="Janome",
        target_symbol="SimpleTokenizer.__init__",
        category="BUG_FIX_THRESHOLD",
        description="Increased default max input length limit from 1024 to 4096",
        initial_code='''def __init__(self, max_len: int = 1024, wakati: bool = False) -> None:
    """Initialize tokenizer.

    Args:
        max_len: Max allowed input string length (default 1024).
        wakati: If True, yield only surface strings.
    """
    self.max_len = max_len
''',
        modified_code='''def __init__(self, max_len: int = 4096, wakati: bool = False) -> None:
    """Initialize tokenizer.

    Args:
        max_len: Max allowed input string length (default 1024).
        wakati: If True, yield only surface strings.
    """
    self.max_len = max_len
''',
        ai_intended_action="DOC_UPDATE",
    ),
    ExternalScenario(
        scenario_id="EXT_JANOME_04_RAISE_EMPTY_TEXT",
        repository="Janome",
        target_symbol="SimpleTokenizer.tokenize",
        category="EXCEPTION_ADDITION",
        description="Added ValueError when text input is empty string",
        initial_code='''def tokenize(self, text: str) -> list[Token]:
    """Tokenize text into list of Tokens."""
    return []
''',
        modified_code='''def tokenize(self, text: str) -> list[Token]:
    """Tokenize text into list of Tokens."""
    if not text.strip():
        raise ValueError("Cannot tokenize empty string")
    return []
''',
        ai_intended_action="DOC_UPDATE",
    ),
    ExternalScenario(
        scenario_id="EXT_JANOME_05_TOKEN_FORMAT_FSTRING",
        repository="Janome",
        target_symbol="Token.format_node",
        category="SAFE_REFACTOR",
        description="F-string formatting restructure",
        initial_code='''def format_node(self, sep: str = "\\t") -> str:
    """Format token as tab-separated surface and features."""
    return f"{self.surface}{sep}{self.pos},{self.base_form},{self.reading}"
''',
        modified_code='''def format_node(self, sep: str = "\\t") -> str:
    """Format token as tab-separated surface and features."""
    feats = f"{self.pos},{self.base_form},{self.reading}"
    return f"{self.surface}{sep}{feats}"
''',
        ai_intended_action="PASS",
    ),
    ExternalScenario(
        scenario_id="EXT_JANOME_06_DOC_CLARIFICATION",
        repository="Janome",
        target_symbol="Token.is_punct",
        category="DOC_UPDATE",
        description="Updated docstring to specify both Japanese and English punctuation tags",
        initial_code='''def is_punct(self) -> bool:
    """Check if token is punctuation."""
    return True
''',
        modified_code='''def is_punct(self) -> bool:
    """Check if token is punctuation matching Japanese or English POS categories."""
    return True
''',
        ai_intended_action="DOC_UPDATE",
    ),
    ExternalScenario(
        scenario_id="EXT_JANOME_07_TOKEN_COMPREHENSION",
        repository="Janome",
        target_symbol="SimpleTokenizer.tokenize",
        category="SAFE_REFACTOR",
        description="Loop replaced with list comprehension",
        initial_code='''def tokenize(self, text: str) -> list[Token]:
    """Tokenize text into list of Tokens."""
    tokens = []
    for word in text.split():
        tokens.append(Token(surface=word, pos="名詞", base_form=word))
    return tokens
''',
        modified_code='''def tokenize(self, text: str) -> list[Token]:
    """Tokenize text into list of Tokens."""
    return [Token(surface=w, pos="名詞", base_form=w) for w in text.split()]
''',
        ai_intended_action="PASS",
    ),

    # -------------------------------------------------------------------------
    # PYTHON-SDB SCENARIOS (6 cases)
    # -------------------------------------------------------------------------
    ExternalScenario(
        scenario_id="EXT_SDB_01_DEFAULT_TAG_TYPE",
        repository="python-sdb",
        target_symbol="SdbRecordHeader.__init__",
        category="API_DEFAULT_CHANGE",
        description="Changed default tag_type bitmask from 0x1000 to 0x2000",
        initial_code='''def __init__(self, tag_type: int = 0x1000, tag_id: int = 0x1) -> None:
    """Initialize SdbRecordHeader.

    Args:
        tag_type: SDB tag data type bitmask (default 0x1000).
        tag_id: Unique record identifier tag (default 0x1).
    """
    self.tag_type = tag_type
''',
        modified_code='''def __init__(self, tag_type: int = 0x2000, tag_id: int = 0x1) -> None:
    """Initialize SdbRecordHeader.

    Args:
        tag_type: SDB tag data type bitmask (default 0x1000).
        tag_id: Unique record identifier tag (default 0x1).
    """
    self.tag_type = tag_type
''',
        ai_intended_action="DOC_UPDATE",
    ),
    ExternalScenario(
        scenario_id="EXT_SDB_02_BITWISE_MASK_REFACTOR",
        repository="python-sdb",
        target_symbol="SdbRecordHeader.get_tag",
        category="SAFE_REFACTOR",
        description="Extracted bitwise mask constants into local variables",
        initial_code='''def get_tag(self) -> int:
    """Combine tag type and identifier into 32-bit tag integer."""
    return (self.tag_type & 0xF000) | (self.tag_id & 0x0FFF)
''',
        modified_code='''def get_tag(self) -> int:
    """Combine tag type and identifier into 32-bit tag integer."""
    t_mask = 0xF000
    i_mask = 0x0FFF
    return (self.tag_type & t_mask) | (self.tag_id & i_mask)
''',
        ai_intended_action="PASS",
    ),
    ExternalScenario(
        scenario_id="EXT_SDB_03_STRUCT_MIN_SIZE",
        repository="python-sdb",
        target_symbol="SdbRecordHeader.unpack_tag",
        category="BUG_FIX_THRESHOLD",
        description="Increased minimum header buffer size check from 4 to 8 bytes for 64-bit tags",
        initial_code='''def unpack_tag(self, raw_bytes: bytes) -> int:
    """Unpack 4-byte little-endian tag value."""
    if len(raw_bytes) < 4:
        raise ValueError("Buffer underflow reading SDB tag header")
    return 0
''',
        modified_code='''def unpack_tag(self, raw_bytes: bytes) -> int:
    """Unpack 4-byte little-endian tag value."""
    if len(raw_bytes) < 8:
        raise ValueError("Buffer underflow reading SDB tag header")
    return 0
''',
        ai_intended_action="CLI_ACCEPT",
    ),
    ExternalScenario(
        scenario_id="EXT_SDB_04_RAISE_ENCODING_ERROR",
        repository="python-sdb",
        target_symbol="parse_string_table_entry",
        category="EXCEPTION_ADDITION",
        description="Added UnicodeDecodeError propagation when decoding invalid UTF-16",
        initial_code='''def parse_string_table_entry(buf: bytes, offset: int = 0) -> str:
    """Parse null-terminated UTF-16LE string from binary buffer."""
    return buf.decode("utf-16le", errors="replace")
''',
        modified_code='''def parse_string_table_entry(buf: bytes, offset: int = 0) -> str:
    """Parse null-terminated UTF-16LE string from binary buffer."""
    try:
        return buf.decode("utf-16le", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Corrupted UTF-16 string: {exc}") from exc
''',
        ai_intended_action="DOC_UPDATE",
    ),
    ExternalScenario(
        scenario_id="EXT_SDB_05_OFFSET_NAME_REFACTOR",
        repository="python-sdb",
        target_symbol="parse_string_table_entry",
        category="SAFE_REFACTOR",
        description="Renamed local end position to null_pos",
        initial_code='''def parse_string_table_entry(buf: bytes, offset: int = 0) -> str:
    """Parse null-terminated UTF-16LE string from binary buffer."""
    end = buf.find(b"\\x00\\x00", offset)
    return str(end)
''',
        modified_code='''def parse_string_table_entry(buf: bytes, offset: int = 0) -> str:
    """Parse null-terminated UTF-16LE string from binary buffer."""
    null_pos = buf.find(b"\\x00\\x00", offset)
    return str(null_pos)
''',
        ai_intended_action="PASS",
    ),
    ExternalScenario(
        scenario_id="EXT_SDB_06_DOCSTRING_HEADER",
        repository="python-sdb",
        target_symbol="SdbRecordHeader.unpack_tag",
        category="DOC_UPDATE",
        description="Added Raises: section to unpack_tag docstring",
        initial_code='''def unpack_tag(self, raw_bytes: bytes) -> int:
    """Unpack 4-byte little-endian tag value."""
    return 0
''',
        modified_code='''def unpack_tag(self, raw_bytes: bytes) -> int:
    """Unpack 4-byte little-endian tag value.

    Args:
        raw_bytes: Binary buffer containing at least 4 bytes.

    Raises:
        ValueError: If buffer contains fewer than 4 bytes.
    """
    return 0
''',
        ai_intended_action="DOC_UPDATE",
    ),
]
