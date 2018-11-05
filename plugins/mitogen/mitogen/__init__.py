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

"""
On the Mitogen master, this is imported from ``mitogen/__init__.py`` as would
be expected. On the slave, it is built dynamically during startup.
"""


#: Library version as a tuple.
__version__ = (0, 2, 3)


#: This is :data:`False` in slave contexts. Previously it was used to prevent
#: re-execution of :mod:`__main__` in single file programs, however that now
#: happens automatically.
is_master = True


#: This is `0` in a master, otherwise it is the master-assigned ID unique to
#: the slave context used for message routing.
context_id = 0


#: This is :data:`None` in a master, otherwise it is the master-assigned ID
#: unique to the slave's parent context.
parent_id = None


#: This is an empty list in a master, otherwise it is a list of parent context
#: IDs ordered from most direct to least direct.
parent_ids = []


def main(log_level='INFO', profiling=False):
    """
    Convenience decorator primarily useful for writing discardable test
    scripts.

    In the master process, when `func` is defined in the :mod:`__main__`
    module, arranges for `func(router)` to be invoked immediately, with
    :py:class:`mitogen.master.Router` construction and destruction handled just
    as in :py:func:`mitogen.utils.run_with_router`. In slaves, this function
    does nothing.

    :param str log_level:
        Logging package level to configure via
        :py:func:`mitogen.utils.log_to_file`.

    :param bool profiling:
        If :py:data:`True`, equivalent to setting
        :py:attr:`mitogen.master.Router.profiling` prior to router
        construction. This causes ``/tmp`` files to be created everywhere at
        the end of a successful run with :py:mod:`cProfile` output for every
        thread.

    Example:

    ::

        import mitogen
        import requests

        def get_url(url):
            return requests.get(url).text

        @mitogen.main()
        def main(router):
            z = router.ssh(hostname='k3')
            print(z.call(get_url, 'https://example.org/')))))

    """

    def wrapper(func):
        if func.__module__ != '__main__':
            return func
        import mitogen.parent
        import mitogen.utils
        if profiling:
            mitogen.core.enable_profiling()
            mitogen.master.Router.profiling = profiling
        utils.log_to_file(level=log_level)
        return mitogen.core._profile_hook(
            'main',
            utils.run_with_router,
            func,
        )
    return wrapper
