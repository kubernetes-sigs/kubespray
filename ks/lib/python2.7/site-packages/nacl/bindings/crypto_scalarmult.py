# Copyright 2013 Donald Stufft and individual contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import, division, print_function

from nacl import exceptions as exc
from nacl._sodium import ffi, lib
from nacl.exceptions import ensure


crypto_scalarmult_BYTES = lib.crypto_scalarmult_bytes()
crypto_scalarmult_SCALARBYTES = lib.crypto_scalarmult_scalarbytes()


def crypto_scalarmult_base(n):
    """
    Computes and returns the scalar product of a standard group element and an
    integer ``n``.

    :param n: bytes
    :rtype: bytes
    """
    q = ffi.new("unsigned char[]", crypto_scalarmult_BYTES)

    rc = lib.crypto_scalarmult_base(q, n)
    ensure(rc == 0,
           'Unexpected library error',
           raising=exc.RuntimeError)

    return ffi.buffer(q, crypto_scalarmult_SCALARBYTES)[:]


def crypto_scalarmult(n, p):
    """
    Computes and returns the scalar product of the given group element and an
    integer ``n``.

    :param p: bytes
    :param n: bytes
    :rtype: bytes
    """
    q = ffi.new("unsigned char[]", crypto_scalarmult_BYTES)

    rc = lib.crypto_scalarmult(q, n, p)
    ensure(rc == 0,
           'Unexpected library error',
           raising=exc.RuntimeError)

    return ffi.buffer(q, crypto_scalarmult_SCALARBYTES)[:]
