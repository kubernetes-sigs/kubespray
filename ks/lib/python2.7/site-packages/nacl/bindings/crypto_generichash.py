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

from six import integer_types

from nacl import exceptions as exc
from nacl._sodium import ffi, lib
from nacl.exceptions import ensure


crypto_generichash_BYTES = lib.crypto_generichash_blake2b_bytes()
crypto_generichash_BYTES_MIN = lib.crypto_generichash_blake2b_bytes_min()
crypto_generichash_BYTES_MAX = lib.crypto_generichash_blake2b_bytes_max()
crypto_generichash_KEYBYTES = lib.crypto_generichash_blake2b_keybytes()
crypto_generichash_KEYBYTES_MIN = lib.crypto_generichash_blake2b_keybytes_min()
crypto_generichash_KEYBYTES_MAX = lib.crypto_generichash_blake2b_keybytes_max()
crypto_generichash_SALTBYTES = lib.crypto_generichash_blake2b_saltbytes()
crypto_generichash_PERSONALBYTES = \
    lib.crypto_generichash_blake2b_personalbytes()
crypto_generichash_STATEBYTES = lib.crypto_generichash_statebytes()

_OVERLONG = '{0} length greater than {1} bytes'
_TOOBIG = '{0} greater than {1}'


def _checkparams(digest_size, key, salt, person):
    """Check hash paramters"""
    ensure(isinstance(key, bytes),
           'Key must be a bytes sequence',
           raising=exc.TypeError)

    ensure(isinstance(salt, bytes),
           'Salt must be a bytes sequence',
           raising=exc.TypeError)

    ensure(isinstance(person, bytes),
           'Person must be a bytes sequence',
           raising=exc.TypeError)

    ensure(isinstance(digest_size, integer_types),
           'Digest size must be an integer number',
           raising=exc.TypeError)

    ensure(digest_size <= crypto_generichash_BYTES_MAX,
           _TOOBIG.format("Digest_size", crypto_generichash_BYTES_MAX),
           raising=exc.ValueError)

    ensure(len(key) <= crypto_generichash_KEYBYTES_MAX,
           _OVERLONG.format("Key", crypto_generichash_KEYBYTES_MAX),
           raising=exc.ValueError)

    ensure(len(salt) <= crypto_generichash_SALTBYTES,
           _OVERLONG.format("Salt", crypto_generichash_SALTBYTES),
           raising=exc.ValueError)

    ensure(len(person) <= crypto_generichash_PERSONALBYTES,
           _OVERLONG.format("Person", crypto_generichash_PERSONALBYTES),
           raising=exc.ValueError)


def generichash_blake2b_salt_personal(data,
                                      digest_size=crypto_generichash_BYTES,
                                      key=b'', salt=b'', person=b''):
    """One shot hash interface

    :param data: the input data to the hash function
    :param digest_size: must be at most
                        :py:data:`.crypto_generichash_BYTES_MAX`;
                        the default digest size is
                        :py:data:`.crypto_generichash_BYTES`
    :type digest_size: int
    :param key: must be at most
                :py:data:`.crypto_generichash_KEYBYTES_MAX` long
    :type key: bytes
    :param salt: must be at most
                 :py:data:`.crypto_generichash_SALTBYTES` long;
                 will be zero-padded if needed
    :type salt: bytes
    :param person: must be at most
                   :py:data:`.crypto_generichash_PERSONALBYTES` long:
                   will be zero-padded if needed
    :type person: bytes
    :return: digest_size long digest
    :rtype: bytes
    """

    _checkparams(digest_size, key, salt, person)

    ensure(isinstance(data, bytes),
           'Input data must be a bytes sequence',
           raising=exc.TypeError)

    digest = ffi.new("unsigned char[]", digest_size)

    # both _salt and _personal must be zero-padded to the correct length
    _salt = ffi.new("unsigned char []", crypto_generichash_SALTBYTES)
    _person = ffi.new("unsigned char []", crypto_generichash_PERSONALBYTES)

    ffi.memmove(_salt, salt, len(salt))
    ffi.memmove(_person, person, len(person))

    rc = lib.crypto_generichash_blake2b_salt_personal(digest, digest_size,
                                                      data, len(data),
                                                      key, len(key),
                                                      _salt, _person)
    ensure(rc == 0, 'Unexpected failure',
           raising=exc.RuntimeError)

    return ffi.buffer(digest, digest_size)[:]


def generichash_blake2b_init(key=b'', salt=b'',
                             person=b'',
                             digest_size=crypto_generichash_BYTES):
    """
    Create a new initialized blake2b hash state

    :param key: must be at most
                :py:data:`.crypto_generichash_KEYBYTES_MAX` long
    :type key: bytes
    :param salt: must be at most
                 :py:data:`.crypto_generichash_SALTBYTES` long;
                 will be zero-padded if needed
    :type salt: bytes
    :param person: must be at most
                   :py:data:`.crypto_generichash_PERSONALBYTES` long:
                   will be zero-padded if needed
    :type person: bytes
    :param digest_size: must be at most
                        :py:data:`.crypto_generichash_BYTES_MAX`;
                        the default digest size is
                        :py:data:`.crypto_generichash_BYTES`
    :type digest_size: int
    :return: an initizialized state buffer
    :rtype: object
    """

    _checkparams(digest_size, key, salt, person)

    statebuf = ffi.new("unsigned char[]", crypto_generichash_STATEBYTES)

    # both _salt and _personal must be zero-padded to the correct length
    _salt = ffi.new("unsigned char []", crypto_generichash_SALTBYTES)
    _person = ffi.new("unsigned char []", crypto_generichash_PERSONALBYTES)

    ffi.memmove(_salt, salt, len(salt))
    ffi.memmove(_person, person, len(person))

    rc = lib.crypto_generichash_blake2b_init_salt_personal(statebuf,
                                                           key, len(key),
                                                           digest_size,
                                                           _salt, _person)
    ensure(rc == 0, 'Unexpected failure',
           raising=exc.RuntimeError)

    return statebuf


def generichash_blake2b_update(statebuf, data):
    """Update the blake2b hash state

    :param statebuf: an initialized blake2b state buffer as returned from
                     :py:func:`.crypto_generichash_blake2b_init`
    :type statebuf: object
    :param data:
    :type data: bytes
    """

    ensure(isinstance(data, bytes),
           'Input data must be a bytes sequence',
           raising=exc.TypeError)

    rc = lib.crypto_generichash_blake2b_update(statebuf, data, len(data))
    ensure(rc == 0, 'Unexpected failure',
           raising=exc.RuntimeError)


def generichash_blake2b_final(statebuf, digest_size):
    """Finalize the blake2b hash state and return the digest.

    :param statebuf:
    :type statebuf: object
    :param digest_size:
    :type digest_size: int
    :return: the blake2 digest of the passed-in data stream
    :rtype: bytes
    """

    _digest = ffi.new("unsigned char[]", crypto_generichash_BYTES_MAX)
    rc = lib.crypto_generichash_blake2b_final(statebuf, _digest, digest_size)

    ensure(rc == 0, 'Unexpected failure',
           raising=exc.RuntimeError)
    return ffi.buffer(_digest, digest_size)[:]


def generichash_blake2b_state_copy(statebuf):
    """Return a copy of the given blake2b hash state"""

    newstate = ffi.new("unsigned char[]", crypto_generichash_STATEBYTES)
    ffi.memmove(newstate, statebuf, crypto_generichash_STATEBYTES)

    return newstate
