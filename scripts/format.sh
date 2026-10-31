#!/bin/bash

set -euo pipefail

ROOT_DIR=$(git rev-parse --show-toplevel)
readonly ROOT_DIR

# Adapted from https://github.com/Ajatt-Tools/mergenotes/blob/b83f34948238a79e8f7f08c3a1a256c0f51908d6/scripts/format.sh
# Include shared code and playground scripts, but leave Hatch's generated version file alone.
# Forward --check so validation uses the shared script's read-only mode instead of rewriting files.
"$ROOT_DIR/media_converter/ajt_common/format.sh" \
	--include media_converter \
	--include tests \
	--include playground \
	--exclude media_converter/__about__.py \
	"$@"
