#!/usr/bin/env bash
# Select docker images that have only one repo:tag for their image ID, i.e. images
# that have not been retagged for the private registry yet.
# Optionally tag them with $DESTINATION_REGISTRY and push them.
set -euo pipefail

usage() {
  cat <<EOF
Usage: ${0##*/} [-h] [-l] [-t] [-p] [-i FILE]

Select images from 'docker images' whose image ID occurs only once
(not yet tagged for the private registry). Images tagged 'latest' are skipped.

Options:
  -h, --help           Show this help
  -l, --list           List the selected images (default)
  -t, --tag            Tag the selected images as \$DESTINATION_REGISTRY/<repo>:<tag>
  -p, --push           Tag (if needed) and push the selected images
  -i, --include FILE   Only consider repo:tag references listed in FILE
                       (one per line, '-' for stdin)

Environment:
  DESTINATION_REGISTRY   Registry host[:port] (required for --tag and --push)
EOF
}

do_list=0 do_tag=0 do_push=0 include_file=""
while [ $# -gt 0 ]; do
  case "$1" in
    -h | --help) usage; exit 0 ;;
    -l | --list) do_list=1 ;;
    -t | --tag) do_tag=1 ;;
    -p | --push) do_push=1 ;;
    -i | --include)
      [ $# -ge 2 ] || { echo "$1 needs a FILE argument" >&2; exit 2; }
      include_file=$2
      shift
      ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done
if [ "$do_tag" -eq 0 ] && [ "$do_push" -eq 0 ]; then
  do_list=1
fi

if [ "$do_tag" -eq 1 ] || [ "$do_push" -eq 1 ]; then
  : "${DESTINATION_REGISTRY:?DESTINATION_REGISTRY must be set for --tag/--push}"
  DESTINATION_REGISTRY="${DESTINATION_REGISTRY%/}"
fi

# Keep only "<id> <repo:tag>" lines whose repo:tag is listed in $include_file.
filter_included() {
  if [ -n "$include_file" ]; then
    awk 'NR == FNR { w[$1]; next } $2 in w' "$include_file" -
  else
    cat
  fi
}

# "<id> <repo:tag>" for tagged images; keep only IDs that occur exactly once
# and are not tagged 'latest'. IDs are counted before dropping 'latest', so an
# image that also carries a 'latest' tag is skipped as a whole.
selected=$(
  docker images --format '{{.ID}} {{.Repository}}:{{.Tag}}' |
    grep -v '<none>' |
    awk '{ count[$1]++; line[$1] = $0 } END { for (id in count) if (count[id] == 1 && line[id] !~ /:latest$/) print line[id] }' |
    sort -k2 |
    filter_included
)

if [ -z "$selected" ]; then
  echo "No images with a unique ID found." >&2
  exit 0
fi

while read -r id ref; do
  target="${DESTINATION_REGISTRY:-}/${ref}"
  if [ "$do_list" -eq 1 ]; then
    printf '%s\t%s\n' "$id" "$ref"
  fi
  if [ "$do_tag" -eq 1 ] || [ "$do_push" -eq 1 ]; then
    echo "tag  $ref -> $target"
    docker tag "$ref" "$target"
  fi
  if [ "$do_push" -eq 1 ]; then
    echo "push $target"
    docker push "$target"
  fi
done <<<"$selected"
