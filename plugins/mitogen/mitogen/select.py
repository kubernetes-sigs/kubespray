# Copyright 2017, David Wilson
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import mitogen.core


class Error(mitogen.core.Error):
    pass


class Select(object):
    notify = None

    @classmethod
    def all(cls, receivers):
        return list(msg.unpickle() for msg in cls(receivers))

    def __init__(self, receivers=(), oneshot=True):
        self._receivers = []
        self._oneshot = oneshot
        self._latch = mitogen.core.Latch()
        for recv in receivers:
            self.add(recv)

    def _put(self, value):
        self._latch.put(value)
        if self.notify:
            self.notify(self)

    def __bool__(self):
        return bool(self._receivers)

    def __enter__(self):
        return self

    def __exit__(self, e_type, e_val, e_tb):
        self.close()

    def __iter__(self):
        while self._receivers:
            yield self.get()

    loop_msg = 'Adding this Select instance would create a Select cycle'

    def _check_no_loop(self, recv):
        if recv is self:
            raise Error(self.loop_msg)

        for recv_ in self._receivers:
            if recv_ == recv:
                raise Error(self.loop_msg)
            if isinstance(recv_, Select):
                recv_._check_no_loop(recv)

    owned_msg = 'Cannot add: Receiver is already owned by another Select'

    def add(self, recv):
        if isinstance(recv, Select):
            recv._check_no_loop(self)

        self._receivers.append(recv)
        if recv.notify is not None:
            raise Error(self.owned_msg)

        recv.notify = self._put
        # Avoid race by polling once after installation.
        if not recv.empty():
            self._put(recv)

    not_present_msg = 'Instance is not a member of this Select'

    def remove(self, recv):
        try:
            if recv.notify != self._put:
                raise ValueError
            self._receivers.remove(recv)
            recv.notify = None
        except (IndexError, ValueError):
            raise Error(self.not_present_msg)

    def close(self):
        for recv in self._receivers[:]:
            self.remove(recv)
        self._latch.close()

    def empty(self):
        return self._latch.empty()

    empty_msg = 'Cannot get(), Select instance is empty'

    def get(self, timeout=None, block=True):
        if not self._receivers:
            raise Error(self.empty_msg)

        while True:
            recv = self._latch.get(timeout=timeout, block=block)
            try:
                msg = recv.get(block=False)
                if self._oneshot:
                    self.remove(recv)
                msg.receiver = recv
                return msg
            except mitogen.core.TimeoutError:
                # A receiver may have been queued with no result if another
                # thread drained it before we woke up, or because another
                # thread drained it between add() calling recv.empty() and
                # self._put(). In this case just sleep again.
                continue
