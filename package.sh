#!/bin/bash

set -euo pipefail

readonly NC='\033[0m'
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'

readonly support_dir=support
readonly package="media_converter"
readonly name="AJT Media Converter"
readonly zip_name=${package,,}.ankiaddon

./ajt_common/package.sh \
	--package "$package" \
	--name "$name" \
	--zip_name "$zip_name" \
	"$@"

if ! [[ -f "$zip_name" ]]; then
	echo -e "${RED}Missing file:${NC} $zip_name"
	exit 1
fi

./libwebp-dl.sh
zip -ur "$zip_name" ./$support_dir/cwebp*
echo -e "${GREEN}Added cwebp binaries.${NC}"
