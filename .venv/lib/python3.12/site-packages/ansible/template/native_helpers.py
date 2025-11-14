# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


import ast
from collections.abc import Mapping
from itertools import islice, chain
from types import GeneratorType

from ansible.module_utils.common.collections import is_sequence
from ansible.module_utils.common.text.converters import to_text
from ansible.module_utils.six import string_types
from ansible.parsing.yaml.objects import AnsibleVaultEncryptedUnicode
from ansible.utils.native_jinja import NativeJinjaText
from ansible.utils.unsafe_proxy import wrap_var
import ansible.module_utils.compat.typing as t

from jinja2.runtime import StrictUndefined


_JSON_MAP = {
    "true": True,
    "false": False,
    "null": None,
}


class Json2Python(ast.NodeTransformer):
    def visit_Name(self, node):
        if node.id not in _JSON_MAP:
            return node
        return ast.Constant(value=_JSON_MAP[node.id])


def _is_unsafe(value: t.Any) -> bool:
    """
    Our helper function, which will also recursively check dict and
    list entries due to the fact that they may be repr'd and contain
    a key or value which contains jinja2 syntax and would otherwise
    lose the AnsibleUnsafe value.
    """
    to_check = [value]
    seen = set()

    while True:
        if not to_check:
            break

        val = to_check.pop(0)
        val_id = id(val)

        if val_id in seen:
            continue
        seen.add(val_id)

        if isinstance(val, AnsibleUndefined):
            continue
        if isinstance(val, Mapping):
            to_check.extend(val.keys())
            to_check.extend(val.values())
        elif is_sequence(val):
            to_check.extend(val)
        elif getattr(val, '__UNSAFE__', False):
            return True

    return False


def ansible_eval_concat(nodes):
    """Return a string of concatenated compiled nodes. Throw an undefined error
    if any of the nodes is undefined.

    If the result of concat appears to be a dictionary, list or bool,
    try and convert it to such using literal_eval, the same mechanism as used
    in jinja2_native.

    Used in Templar.template() when jinja2_native=False and convert_data=True.
    """
    head = list(islice(nodes, 2))

    if not head:
        return ''

    unsafe = False

    if len(head) == 1:
        out = head[0]

        if isinstance(out, NativeJinjaText):
            return out

        unsafe = _is_unsafe(out)
        out = to_text(out)
    else:
        if isinstance(nodes, GeneratorType):
            nodes = chain(head, nodes)

        out_values = []
        for v in nodes:
            if not unsafe and _is_unsafe(v):
                unsafe = True

            out_values.append(to_text(v))

        out = ''.join(out_values)

    # if this looks like a dictionary, list or bool, convert it to such
    if out.startswith(('{', '[')) or out in ('True', 'False'):
        try:
            out = ast.literal_eval(
                ast.fix_missing_locations(
                    Json2Python().visit(
                        ast.parse(out, mode='eval')
                    )
                )
            )
        except (TypeError, ValueError, SyntaxError, MemoryError):
            pass

    if unsafe:
        out = wrap_var(out)

    return out


def ansible_concat(nodes):
    """Return a string of concatenated compiled nodes. Throw an undefined error
    if any of the nodes is undefined. Other than that it is equivalent to
    Jinja2's default concat function.

    Used in Templar.template() when jinja2_native=False and convert_data=False.
    """
    unsafe = False
    values = []
    for v in nodes:
        if not unsafe and _is_unsafe(v):
            unsafe = True

        values.append(to_text(v))

    out = ''.join(values)
    if unsafe:
        out = wrap_var(out)

    return out


def ansible_native_concat(nodes):
    """Return a native Python type from the list of compiled nodes. If the
    result is a single node, its value is returned. Otherwise, the nodes are
    concatenated as strings. If the result can be parsed with
    :func:`ast.literal_eval`, the parsed value is returned. Otherwise, the
    string is returned.

    https://github.com/pallets/jinja/blob/master/src/jinja2/nativetypes.py
    """
    head = list(islice(nodes, 2))

    if not head:
        return None

    unsafe = False

    if len(head) == 1:
        out = head[0]

        # TODO send unvaulted data to literal_eval?
        if isinstance(out, AnsibleVaultEncryptedUnicode):
            return out.data

        if isinstance(out, NativeJinjaText):
            # Sometimes (e.g. ``| string``) we need to mark variables
            # in a special way so that they remain strings and are not
            # passed into literal_eval.
            # See:
            # https://github.com/ansible/ansible/issues/70831
            # https://github.com/pallets/jinja/issues/1200
            # https://github.com/ansible/ansible/issues/70831#issuecomment-664190894
            return out

        # short-circuit literal_eval for anything other than strings
        if not isinstance(out, string_types):
            return out

        unsafe = _is_unsafe(out)

    else:
        if isinstance(nodes, GeneratorType):
            nodes = chain(head, nodes)

        out_values = []
        for v in nodes:
            if not unsafe and _is_unsafe(v):
                unsafe = True

            out_values.append(to_text(v))

        out = ''.join(out_values)

    try:
        evaled = ast.literal_eval(
            # In Python 3.10+ ast.literal_eval removes leading spaces/tabs
            # from the given string. For backwards compatibility we need to
            # parse the string ourselves without removing leading spaces/tabs.
            ast.parse(out, mode='eval')
        )
    except (TypeError, ValueError, SyntaxError, MemoryError):
        if unsafe:
            out = wrap_var(out)

        return out

    if isinstance(evaled, string_types):
        quote = out[0]
        evaled = f'{quote}{evaled}{quote}'

    if unsafe:
        evaled = wrap_var(evaled)

    return evaled


class AnsibleUndefined(StrictUndefined):
    """
    A custom Undefined class, which returns further Undefined objects on access,
    rather than throwing an exception.
    """
    def __getattr__(self, name):
        if name == '__UNSAFE__':
            # AnsibleUndefined should never be assumed to be unsafe
            # This prevents ``hasattr(val, '__UNSAFE__')`` from evaluating to ``True``
            raise AttributeError(name)
        # Return original Undefined object to preserve the first failure context
        return self

    def __getitem__(self, key):
        # Return original Undefined object to preserve the first failure context
        return self

    def __repr__(self):
        return 'AnsibleUndefined(hint={0!r}, obj={1!r}, name={2!r})'.format(
            self._undefined_hint,
            self._undefined_obj,
            self._undefined_name
        )

    def __contains__(self, item):
        # Return original Undefined object to preserve the first failure context
        return self
