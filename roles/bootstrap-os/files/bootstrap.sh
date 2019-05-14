#!/bin/bash
set -e

BINDIR="/opt/bin"

mkdir -p $BINDIR

cd $BINDIR

if [[ -e $BINDIR/.bootstrapped ]]; then
  exit 0
fi

wget -O - $PYPY_URL | tar -xjf -
mv -n $PYPY_FOLDER pypy3

ln -s ./pypy3/bin/pypy3 python
$BINDIR/python --version

touch $BINDIR/.bootstrapped
