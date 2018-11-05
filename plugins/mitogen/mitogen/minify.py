# Copyright 2017, Alex Willmer
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

import sys

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

import mitogen.core

if sys.version_info < (2, 7, 11):
    from mitogen.compat import tokenize
else:
    import tokenize

try:
    from functools import lru_cache
except ImportError:
    from mitogen.compat.functools import lru_cache


@lru_cache()
def minimize_source(source):
    """Remove comments and docstrings from Python `source`, preserving line
    numbers and syntax of empty blocks.

    :param str source:
        The source to minimize.

    :returns str:
        The minimized source.
    """
    source = mitogen.core.to_text(source)
    tokens = tokenize.generate_tokens(StringIO(source).readline)
    tokens = strip_comments(tokens)
    tokens = strip_docstrings(tokens)
    tokens = reindent(tokens)
    return tokenize.untokenize(tokens)


def strip_comments(tokens):
    """Drop comment tokens from a `tokenize` stream.

    Comments on lines 1-2 are kept, to preserve hashbang and encoding.
    Trailing whitespace is remove from all lines.
    """
    prev_typ = None
    prev_end_col = 0
    for typ, tok, (start_row, start_col), (end_row, end_col), line in tokens:
        if typ in (tokenize.NL, tokenize.NEWLINE):
            if prev_typ in (tokenize.NL, tokenize.NEWLINE):
                start_col = 0
            else:
                start_col = prev_end_col
            end_col = start_col + 1
        elif typ == tokenize.COMMENT and start_row > 2:
            continue
        prev_typ = typ
        prev_end_col = end_col
        yield typ, tok, (start_row, start_col), (end_row, end_col), line


def strip_docstrings(tokens):
    """Replace docstring tokens with NL tokens in a `tokenize` stream.

    Any STRING token not part of an expression is deemed a docstring.
    Indented docstrings are not yet recognised.
    """
    stack = []
    state = 'wait_string'
    for t in tokens:
        typ = t[0]
        if state == 'wait_string':
            if typ in (tokenize.NL, tokenize.COMMENT):
                yield t
            elif typ in (tokenize.DEDENT, tokenize.INDENT, tokenize.STRING):
                stack.append(t)
            elif typ == tokenize.NEWLINE:
                stack.append(t)
                start_line, end_line = stack[0][2][0], stack[-1][3][0]+1
                for i in range(start_line, end_line):
                    yield tokenize.NL, '\n', (i, 0), (i,1), '\n'
                for t in stack:
                    if t[0] in (tokenize.DEDENT, tokenize.INDENT):
                        yield t[0], t[1], (i+1, t[2][1]), (i+1, t[3][1]), t[4]
                del stack[:]
            else:
                stack.append(t)
                for t in stack: yield t
                del stack[:]
                state = 'wait_newline'
        elif state == 'wait_newline':
            if typ == tokenize.NEWLINE:
                state = 'wait_string'
            yield t


def reindent(tokens, indent=' '):
    """Replace existing indentation in a token steam, with `indent`.
    """
    old_levels = []
    old_level = 0
    new_level = 0
    for typ, tok, (start_row, start_col), (end_row, end_col), line in tokens:
        if typ == tokenize.INDENT:
            old_levels.append(old_level)
            old_level = len(tok)
            new_level += 1
            tok = indent * new_level
        elif typ == tokenize.DEDENT:
            old_level = old_levels.pop()
            new_level -= 1
        start_col = max(0, start_col - old_level + new_level)
        if start_row == end_row:
            end_col = start_col + len(tok)
        yield typ, tok, (start_row, start_col), (end_row, end_col), line
