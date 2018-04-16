#!/bin/bash
set -e

BINDIR="/opt/bin"

mkdir -p $BINDIR

cd $BINDIR

if [[ -e $BINDIR/.bootstrapped ]]; then
  exit 0
fi

PYPY_VERSION=5.1.0

wget -O - https://bitbucket.org/pypy/pypy/downloads/pypy-$PYPY_VERSION-linux64.tar.bz2 |tar -xjf -
mv -n pypy-$PYPY_VERSION-linux64 pypy

## library fixup
mkdir -p pypy/lib
ln -snf /lib64/libncurses.so.5.9 $BINDIR/pypy/lib/libtinfo.so.5

cat > $BINDIR/python <<EOF
#!/bin/bash
LD_LIBRARY_PATH=$BINDIR/pypy/lib:$LD_LIBRARY_PATH exec $BINDIR/pypy/bin/pypy "\$@"
EOF

chmod +x $BINDIR/python
$BINDIR/python --version

touch $BINDIR/.bootstrapped
