#!/bin/bash
set -e

BINDIR="/opt/bin"
PYPY_VERSION=7.3.1
PYPI_URL="https://bitbucket.org/pypy/pypy/downloads/pypy3.6-v${PYPY_VERSION}-linux64.tar.bz2"
PYPI_HASH=f67cf1664a336a3e939b58b3cabfe47d893356bdc01f2e17bc912aaa6605db12

mkdir -p $BINDIR

cd $BINDIR

if [[ -e $BINDIR/.bootstrapped ]]; then
  exit 0
fi

TAR_FILE=pyp.tar.bz2
wget -O "${TAR_FILE}" "${PYPI_URL}"
echo "${PYPI_HASH} ${TAR_FILE}" | sha256sum -c -
tar -xjf "${TAR_FILE}" && rm "${TAR_FILE}"
mv -n "pypy3.6-v${PYPY_VERSION}-linux64" pypy3

ln -s ./pypy3/bin/pypy3 python
$BINDIR/python --version

touch $BINDIR/.bootstrapped
