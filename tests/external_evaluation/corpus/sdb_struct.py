"""Sample representative module from python-sdb (Apache-2.0).

Source: williballenthin/python-sdb (sdb.py extract)
"""

import struct


class SdbRecordHeader:
    """Header for SDB binary database entry tag."""

    def __init__(self, tag_type: int = 0x1000, tag_id: int = 0x1) -> None:
        """Initialize SdbRecordHeader.

        Args:
            tag_type: SDB tag data type bitmask (default 0x1000).
            tag_id: Unique record identifier tag (default 0x1).
        """
        self.tag_type = tag_type
        self.tag_id = tag_id

    def get_tag(self) -> int:
        """Combine tag type and identifier into 32-bit tag integer."""
        return (self.tag_type & 0xF000) | (self.tag_id & 0x0FFF)

    def unpack_tag(self, raw_bytes: bytes) -> int:
        """Unpack 4-byte little-endian tag value."""
        if len(raw_bytes) < 4:
            raise ValueError("Buffer underflow reading SDB tag header")
        val = struct.unpack("<I", raw_bytes[:4])[0]
        return val


def parse_string_table_entry(buf: bytes, offset: int = 0) -> str:
    """Parse null-terminated UTF-16LE string from binary buffer.

    Args:
        buf: Raw binary buffer containing string table.
        offset: Byte offset where string starts (default 0).

    Returns:
        Decoded unicode string.

    Raises:
        ValueError: If null terminator is missing within buffer bounds.
    """
    if offset >= len(buf):
        raise ValueError("String table offset exceeds buffer size")
    end = buf.find(b"\x00\x00", offset)
    if end == -1:
        raise ValueError("Unterminated UTF-16LE string in SDB table")
    return buf[offset:end].decode("utf-16le", errors="replace")
