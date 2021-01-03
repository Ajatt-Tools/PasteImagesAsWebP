#!/usr/bin/env bash

readonly target=${1:?Please provide build target: \"ankiweb\" or \"github\"}
readonly package_name="PasteImagesAsWebP.ankiaddon"
readonly support_dir="support"
readonly manifest=manifest.json

rm -- $package_name 2>/dev/null

if [[ "$target" != 'ankiweb' ]]; then
    # https://addon-docs.ankiweb.net/#/sharing?id=sharing-outside-ankiweb
    # If you wish to distribute .ankiaddon files outside of AnkiWeb,
    # your add-on folder needs to contain a ‘manifest.json’ file.
    {
        echo '{'
        echo -e "\t\"package\": \"${package_name%.*}\","
        echo -e '\t"name": "Paste Images As WebP",'
        echo -e "\t\"mod\": $(date -u '+%s')"
        echo '}'
    } > $manifest
fi

zip -r "$package_name" \
	./*.py \
	./utils/*.py \
	./$manifest \
	./config.* \
	./*icon.png \
	./$support_dir \

rm -- $manifest 2>/dev/null
