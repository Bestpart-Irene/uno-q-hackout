#!/bin/sh
set -eu
arcade_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$(uname -s)" != Linux ]; then
    echo "Run this on UNO Q Linux, not on the development computer." >&2
    exit 1
fi
for command in xvfb-run Xvfb xauth retroarch; do
    command -v "$command" >/dev/null || { echo "Missing host dependency: $command" >&2; exit 1; }
done
if [ ! -x "$arcade_dir/.venv/bin/python" ]; then
    echo "Create retroarch/.venv and install requirements.txt; see README.md." >&2
    exit 1
fi
export LIBGL_ALWAYS_SOFTWARE=true GALLIUM_DRIVER=llvmpipe
unset WAYLAND_DISPLAY
exec xvfb-run -a -s '-screen 0 160x120x24 -nolisten tcp -noreset' \
    "$arcade_dir/.venv/bin/python" "$arcade_dir/run.py" "$@"
