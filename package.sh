#!/usr/bin/env sh
readonly package_name="PasteImagesAsWebP"
readonly support_dir="support"
zip -r "$package_name" \
	./*.py \
	./config.* \
	./*icon.png \
	./$support_dir \
