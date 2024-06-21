#!/bin/bash

set -euo pipefail

readonly root_dir=$(git rev-parse --show-toplevel)
readonly package="media_converter"

"$root_dir/$package/ajt_common/format.sh"
