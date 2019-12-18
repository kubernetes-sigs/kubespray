#!/bin/sh
set -euxo pipefail

echo "Install requirements..."
pip install -r ./tests/scripts/md-table/requirements.txt

echo "Generate current file..."
./tests/scripts/md-table/main.py > tmp.md

echo "Compare docs/ci.md with actual tests in tests/files/*.yml ..."
cmp docs/ci.md tmp.md