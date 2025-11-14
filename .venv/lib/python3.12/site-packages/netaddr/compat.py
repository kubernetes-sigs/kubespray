# -----------------------------------------------------------------------------
#   Copyright (c) 2008 by David P. D. Moss. All rights reserved.
#
#   Released under the BSD license. See the LICENSE file for details.
# -----------------------------------------------------------------------------


import importlib.resources

if hasattr(importlib.resources, 'files'):

    def _open_binary(pkg, res):
        return importlib.resources.files(pkg).joinpath(res).open('rb')
else:
    _open_binary = importlib.resources.open_binary
