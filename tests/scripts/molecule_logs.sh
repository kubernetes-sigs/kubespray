#!/bin/bash

# Ensure a clean environent
rm -fr molecule_logs
mkdir -p molecule_logs

# Collect and archive the logs
find ~/.cache/molecule/ -name \*.out -o -name \*.err -type f | xargs tar -uf molecule_logs/molecule.tar
gzip molecule_logs/molecule.tar
