"""Single source of truth for the PyDocSync version string.

WHAT IS THIS?
-------------
Holds `__version__` so that both the package root and the baseline writer can read it.

WHY DO WE NEED THIS?
--------------------
`pydocsync/__init__.py` imports the CLI, which imports the baseline manager. If the baseline
manager imported the version from the package root, that would be a circular import. A leaf
module with no imports avoids the cycle and keeps the version defined exactly once.
"""

__version__ = "0.4.0"
