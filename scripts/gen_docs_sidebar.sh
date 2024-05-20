#!/usr/bin/env bash

# Generate documentation
# This script generates a list of all the markdown files in the docs folder
# and prints them in a markdown list format.
# The script will print the name of the folder and the files inside it.
# The script will also convert the folder and file names to a more human-readable format.
# The script will ignore any files that are not markdown files.
# Usage: bash scripts/gen_docs_sidebar.sh > docs/_sidebar.md

export LANG=C
{
echo "* [Readme](/)"

for folder in $(find docs/*/ | sort -f); do
  # Check if it is a directory
  if [ -d "$folder" ]; then
    subdir=$(basename "$folder")
    subdir=${subdir//_/ }  # Replace "_" with empty string
    subdir=$(echo "$subdir" | awk '{for(i=1;i<=NF;i++)sub(/./,toupper(substr($i,1,1)),$i)}1')  # Convert first letter of each word to uppercase
    if [ -n "$(find "$folder" -name '*.md' -type f)" ]; then
      echo "* $subdir"
    fi
    for file in $(find docs/"$(basename "$folder")"/*.md | sort -f); do
      if [ -f "$file" ]; then
        FILE=$(basename "$file" .md)
        FILE=${FILE//_/ }  # Replace "_" with empty string
        FILE=$(echo "$FILE" | awk '{for(i=1;i<=NF;i++)sub(/./,toupper(substr($i,1,1)),$i)}1')  # Convert first letter of each word to uppercase
        echo "  * [$FILE](/$file)"
      fi
    done
  fi
done
} > docs/_sidebar.md
