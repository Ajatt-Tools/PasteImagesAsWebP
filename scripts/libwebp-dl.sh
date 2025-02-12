#!/usr/bin/bash

# https://developers.google.com/speed/webp/download

set -euo pipefail

readonly NC='\033[0m'
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'

readonly version=1.5.0
readonly webp_windows="https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-${version}-windows-x64.zip"
readonly webp_linux="https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-${version}-linux-x86-64.tar.gz"
readonly webp_mac="https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-${version}-mac-x86-64.tar.gz"

readonly root_dir=$(git rev-parse --show-toplevel)
readonly package="media_converter"
readonly support_dir=$root_dir/$package/support
readonly tmp_dir=/tmp/ajt__download_temp

get_libwebp() {
	local -r url=${1:?} file_path=$tmp_dir/${1##*/}
	if ! [[ -f $file_path ]]; then
		curl -s --output "$file_path" -- "$url"
	fi
	atool -f -X "$tmp_dir/" -- "$file_path"
}

check_dependencies() {
	if ! command -v atool >/dev/null; then
		echo -e "${RED}atool is not installed!${NC}"
		exit 1
	fi
}

main() {
	if ! [[ -d $support_dir ]]; then
		echo "can't find support dir"
		exit 1
	fi

	check_dependencies

	if [[ -f $support_dir/cwebp.lin && -f $support_dir/cwebp.exe && -f $support_dir/cwebp.mac ]]; then
		echo "cwebp is already downloaded."
		exit
	fi

	rm -rf -- "$tmp_dir" || true
	mkdir -p -- "$tmp_dir"

	echo "downloading cwebp..."
	for url in "$webp_windows" "$webp_linux" "$webp_mac"; do
		get_libwebp "$url" &
	done
	wait

	find "$tmp_dir"/*windows* -type f -name 'cwebp.exe' -exec mv -- {} "$support_dir/cwebp.exe" \;
	find "$tmp_dir"/*linux* -type f -name 'cwebp' -exec mv -- {} "$support_dir/cwebp.lin" \;
	find "$tmp_dir"/*mac* -type f -name 'cwebp' -exec mv -- {} "$support_dir/cwebp.mac" \;

	rm -rf -- "$tmp_dir"
	echo -e "${GREEN}downloaded cwebp.${NC}"
}

main "$@"
