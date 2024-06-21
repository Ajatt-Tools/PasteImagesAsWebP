#!/bin/bash

set -euo pipefail

readonly NC='\033[0m'
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'

readonly root_dir=$(git rev-parse --show-toplevel)
readonly package="media_converter"
readonly name="AJT Media Converter"
readonly support_dir=$root_dir/$package/support
readonly zip_name=${package,,}.ankiaddon

"$root_dir/$package/ajt_common/package.sh" \
	--package "$package" \
	--root "$package" \
	--name "$name" \
	--zip_name "$zip_name" \
	"$@"

if ! [[ -f "$zip_name" ]]; then
	echo -e "${RED}Missing file:${NC} $zip_name"
	exit 1
fi

"$root_dir/scripts/libwebp-dl.sh"
zip -ur "$zip_name" "$support_dir/cwebp"*
echo -e "${GREEN}Added cwebp binaries.${NC}"
