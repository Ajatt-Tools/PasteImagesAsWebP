#!/bin/bash

set -euo pipefail

readonly NC='\033[0m'
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'

readonly support_dir=support
package=PasteImagesAsWebP

./ajt_common/package.sh \
	--package "$package" \
	--name "AJT Paste Images As WebP" \
	"$@"

./libwebp-dl.sh
zip -ur "${package,,}.ankiaddon" ./$support_dir/cwebp*
echo -e "${GREEN}Added cwebp binaries.${NC}"
