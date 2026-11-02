"""Runtime hook (macOS only): provide safe sys.stdout/sys.stderr stand-ins
for Finder-launched .app bundles where no terminal is attached."""
import sys


class _SafeStream:
    encoding = "utf-8"
    errors = "replace"

    def write(self, *_a, **_k):
        return 0

    def writelines(self, *_a, **_k):
        pass

    def flush(self):
        pass

    def close(self):
        pass

    def isatty(self):
        return False

    def reconfigure(self, **_k):
        pass

    def fileno(self):
        raise OSError("no fileno")


if sys.stdout is None:
    sys.stdout = _SafeStream()
if sys.stderr is None:
    sys.stderr = _SafeStream()