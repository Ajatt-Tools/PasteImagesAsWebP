#!/bin/bash

readonly NC='\033[0m'
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'

for exe in git zip zipmerge; do
	if ! command -v "$exe" >/dev/null; then
		echo -e "${RED}Missing dependency:${NC} $exe"
		exit 1
	fi
done

readonly root_dir=$(git rev-parse --show-toplevel)
readonly target=${1:?Please provide build target: \"ankiweb\" or \"github\"}
readonly branch=${2:-$(git branch --show-current)}
readonly addon_name="Paste Images As WebP"
readonly package_filename="${addon_name// /}_${branch}.ankiaddon"
readonly support_dir=support
readonly manifest=manifest.json

cd -- "$root_dir" || exit 1
rm -- "$package_filename" 2>/dev/null
export root_dir branch

if [[ $target != ankiweb ]]; then
	# https://addon-docs.ankiweb.net/sharing.html
	# If you wish to distribute .ankiaddon files outside of AnkiWeb,
	# your add-on folder needs to contain a ‘manifest.json’ file.
	cat <<- EOF > $manifest
	{
		"package": "${package_filename%.*}",
		"name": "$addon_name",
		"mod": $(date -u '+%s')
	}
	EOF
fi

bash ./libwebp-dl.sh

git archive "$branch" --format=zip --output "$package_filename"
zip -ur "$package_filename" ./"$manifest" ./$support_dir/cwebp*

# shellcheck disable=SC2016
git submodule foreach 'git archive HEAD --prefix=$path/ --format=zip --output "$root_dir/${path}_${branch}.zip"'

zipmerge "$package_filename" ./*.zip

rm -- $manifest 2>/dev/null
rm -- ./*.zip
echo -e "${GREEN}Done.${NC}"
