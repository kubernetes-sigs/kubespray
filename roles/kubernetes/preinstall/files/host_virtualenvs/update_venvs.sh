#!/bin/sh

for venv in */requirements.in
do
    pip-compile --generate-hashes -o "$(dirname $venv)/requirements.txt" "${venv}"
done
