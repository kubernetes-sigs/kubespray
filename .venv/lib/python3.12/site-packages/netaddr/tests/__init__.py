import sys

# Yeah it's a private API; this is only test code though, not much risk there.
from packaging._musllinux import _get_musl_version

IS_MUSL = _get_musl_version(sys.executable) is not None
