"""
Misc utility functions and constants
"""

import functools
import inspect
import warnings
from textwrap import dedent

from hvac import exceptions


def raise_for_error(status_code, message=None, errors=None):
    """Helper method to raise exceptions based on the status code of a response received back from Vault.

    :param status_code: Status code received in a response from Vault.
    :type status_code: int
    :param message: Optional message to include in a resulting exception.
    :type message: str
    :param errors: Optional errors to include in a resulting exception.
    :type errors: list | str

    :raises: hvac.exceptions.InvalidRequest | hvac.exceptions.Unauthorized | hvac.exceptions.Forbidden |
        hvac.exceptions.InvalidPath | hvac.exceptions.RateLimitExceeded | hvac.exceptions.InternalServerError |
        hvac.exceptions.VaultNotInitialized | hvac.exceptions.VaultDown | hvac.exceptions.UnexpectedError

    """
    if status_code == 400:
        raise exceptions.InvalidRequest(message, errors=errors)
    elif status_code == 401:
        raise exceptions.Unauthorized(message, errors=errors)
    elif status_code == 403:
        raise exceptions.Forbidden(message, errors=errors)
    elif status_code == 404:
        raise exceptions.InvalidPath(message, errors=errors)
    elif status_code == 429:
        raise exceptions.RateLimitExceeded(message, errors=errors)
    elif status_code == 500:
        raise exceptions.InternalServerError(message, errors=errors)
    elif status_code == 501:
        raise exceptions.VaultNotInitialized(message, errors=errors)
    elif status_code == 503:
        raise exceptions.VaultDown(message, errors=errors)
    else:
        raise exceptions.UnexpectedError(message)


def generate_method_deprecation_message(to_be_removed_in_version, old_method_name, method_name=None, module_name=None):
    """Generate a message to be used when warning about the use of deprecated methods.

    :param to_be_removed_in_version: Version of this module the deprecated method will be removed in.
    :type to_be_removed_in_version: str
    :param old_method_name: Deprecated method name.
    :type old_method_name:  str
    :param method_name:  Method intended to replace the deprecated method indicated. This method's docstrings are
        included in the decorated method's docstring.
    :type method_name: str
    :param module_name: Name of the module containing the new method to use.
    :type module_name: str
    :return: Full deprecation warning message for the indicated method.
    :rtype: str
    """
    message = "Call to deprecated function '{old_method_name}'. This method will be removed in version '{version}'".format(
        old_method_name=old_method_name,
        version=to_be_removed_in_version,
    )
    if method_name is not None and module_name is not None:
        message += " Please use the '{method_name}' method on the '{module_name}' class moving forward.".format(
            method_name=method_name,
            module_name=module_name,
        )
    return message


def generate_property_deprecation_message(to_be_removed_in_version, old_name, new_name, new_attribute,
                                          module_name='Client'):
    """Generate a message to be used when warning about the use of deprecated properties.

    :param to_be_removed_in_version: Version of this module the deprecated property will be removed in.
    :type to_be_removed_in_version: str
    :param old_name: Deprecated property name.
    :type old_name: str
    :param new_name: Name of the new property name to use.
    :type new_name: str
    :param new_attribute: The new attribute where the new property can be found.
    :type new_attribute: str
    :param module_name: Name of the module containing the new method to use.
    :type module_name: str
    :return: Full deprecation warning message for the indicated property.
    :rtype: str
    """
    message = "Call to deprecated property '{name}'. This property will be removed in version '{version}'".format(
        name=old_name,
        version=to_be_removed_in_version,
    )
    message += " Please use the '{new_name}' property on the '{module_name}.{new_attribute}' attribute moving forward.".format(
        new_name=new_name,
        module_name=module_name,
        new_attribute=new_attribute,
    )
    return message


def getattr_with_deprecated_properties(obj, item, deprecated_properties):
    """Helper method to use in the getattr method of a class with deprecated properties.

    :param obj: Instance of the Class containing the deprecated properties in question.
    :type obj: object
    :param item: Name of the attribute being requested.
    :type item: str
    :param deprecated_properties: List of deprecated properties. Each item in the list is a dict with at least a
        "to_be_removed_in_version" and "client_property" key to be used in the displayed deprecation warning.
    :type deprecated_properties: List[dict]
    :return: The new property indicated where available.
    :rtype: object
    """
    if item in deprecated_properties:
        deprecation_message = generate_property_deprecation_message(
            to_be_removed_in_version=deprecated_properties[item]['to_be_removed_in_version'],
            old_name=item,
            new_name=deprecated_properties[item].get('new_property', item),
            new_attribute=deprecated_properties[item]['client_property'],
        )
        warnings.simplefilter('always', DeprecationWarning)
        warnings.warn(
            message=deprecation_message,
            category=DeprecationWarning,
            stacklevel=2,
        )
        warnings.simplefilter('default', DeprecationWarning)
        client_property = getattr(obj, deprecated_properties[item]['client_property'])
        return getattr(client_property, deprecated_properties[item].get('new_property', item))

    raise AttributeError("'{class_name}' has no attribute '{item}'".format(
        class_name=obj.__class__.__name__,
        item=item,
    ))


def deprecated_method(to_be_removed_in_version, new_method=None):
    """This is a decorator which can be used to mark methods as deprecated. It will result in a warning being emitted
    when the function is used.

    :param to_be_removed_in_version: Version of this module the decorated method will be removed in.
    :type to_be_removed_in_version: str
    :param new_method: Method intended to replace the decorated method. This method's docstrings are included in the
        decorated method's docstring.
    :type new_method: function
    :return: Wrapped function that includes a deprecation warning and update docstrings from the replacement method.
    :rtype: types.FunctionType
    """
    def decorator(method):
        deprecation_message = generate_method_deprecation_message(
            to_be_removed_in_version=to_be_removed_in_version,
            old_method_name=method.__name__,
            method_name=new_method.__name__,
            module_name=inspect.getmodule(new_method).__name__,
        )

        @functools.wraps(method)
        def new_func(*args, **kwargs):
            warnings.simplefilter('always', DeprecationWarning)  # turn off filter
            warnings.warn(
                message=deprecation_message,
                category=DeprecationWarning,
                stacklevel=2,
            )
            warnings.simplefilter('default', DeprecationWarning)  # reset filter
            return method(*args, **kwargs)

        if new_method:
            new_func.__doc__ = """\
                {message}
                Docstring content from this method's replacement copied below:
                {new_docstring}
                """.format(
                    message=deprecation_message,
                    new_docstring=dedent(new_method.__doc__),
                )

        else:
            new_func.__doc__ = deprecation_message
        return new_func
    return decorator


def validate_list_of_strings_param(param_name, param_argument):
    """Validate that an argument is a list of strings.

    :param param_name: The name of the parameter being validated. Used in any resulting exception messages.
    :type param_name: str | unicode
    :param param_argument: The argument to validate.
    :type param_argument: list
    :return: True if the argument is validated, False otherwise.
    :rtype: bool
    """
    if param_argument is None:
        param_argument = []
    if not isinstance(param_argument, list) or not all([isinstance(p, str) for p in param_argument]):
        error_msg = 'unsupported {param} argument provided "{arg}" ({arg_type}), required type: List[str]"'
        raise exceptions.ParamValidationError(error_msg.format(
            param=param_name,
            arg=param_argument,
            arg_type=type(param_argument),
        ))


def list_to_comma_delimited(list_param):
    """Convert a list of strings into a comma-delimited list / string.

    :param list_param: A list of strings.
    :type list_param: list
    :return: Comma-delimited string.
    :rtype: str
    """
    if list_param is None:
        list_param = []
    return ','.join(list_param)
