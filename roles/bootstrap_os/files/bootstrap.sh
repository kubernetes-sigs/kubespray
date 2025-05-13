#!/bin/bash
set -e

BINDIR="/opt/bin"
if [[ -e $BINDIR/.bootstrapped ]]; then
  exit 0
fi

ARCH=$(uname -m)
case $ARCH in
  "x86_64")
    PYPY_ARCH=linux64
    PYPI_HASH=46818cb3d74b96b34787548343d266e2562b531ddbaf330383ba930ff1930ed5
    ;;
  "aarch64")
    PYPY_ARCH=aarch64
    PYPI_HASH=2e1ae193d98bc51439642a7618d521ea019f45b8fb226940f7e334c548d2b4b9
    ;;
  *)
    echo "Unsupported Architecture: ${ARCH}"
    exit 1
esac

PYTHON_VERSION=3.9
PYPY_VERSION=7.3.9
PYPY_FILENAME="pypy${PYTHON_VERSION}-v${PYPY_VERSION}-${PYPY_ARCH}"
PYPI_URL="https://downloads.python.org/pypy/${PYPY_FILENAME}.tar.bz2"

mkdir -p $BINDIR

cd $BINDIR

TAR_FILE=pyp.tar.bz2
wget -O "${TAR_FILE}" "${PYPI_URL}"
echo "${PYPI_HASH} ${TAR_FILE}" | sha256sum -c -
tar -xjf "${TAR_FILE}" && rm "${TAR_FILE}"
mv -n "${PYPY_FILENAME}" pypy3

ln -s ./pypy3/bin/pypy3 python
$BINDIR/python --version

# install PyYAML
./python -m ensurepip
./python -m pip install pyyaml

touch $BINDIR/.bootstrapped
