"""
This is a collection of functions used to convert untyped param strings into
their appropriate JSON schema types.
"""

import inspect
import logging
from typing import List

import simplejson as json

from doctor.errors import ParseError, TypeSystemError


_bracket_strings = ('[', ord('['))
_brace_strings = ('{', ord('{'))
_false_strings = ('false', b'false')
_true_strings = ('true', b'true')


def _parse_array(value):
    """Coerce value into an list.

    :param str value: Value to parse.
    :returns: list or None if the value is not a JSON array
    :raises: TypeError or ValueError if value appears to be an array but can't
        be parsed as JSON.
    """
    value = value.lstrip()
    if not value or value[0] not in _bracket_strings:
        return None
    return json.loads(value)


def _parse_boolean(value):
    """Coerce value into an bool.

    :param str value: Value to parse.
    :returns: bool or None if the value is not a boolean string.
    """
    value = value.lower()
    if value in _true_strings:
        return True
    elif value in _false_strings:
        return False
    else:
        return None


def _parse_object(value):
    """Coerce value into a dict.

    :param str value: Value to parse.
    :returns: dict or None if the value is not a JSON object
    :raises: TypeError or ValueError if value appears to be an object but can't
        be parsed as JSON.
    """
    value = value.lstrip()
    if not value or value[0] not in _brace_strings:
        return None
    return json.loads(value)


def _parse_string(value):
    """Coerce value into a string.

    This is usually a no-op, but if value is a unicode string, it will be
    encoded as UTF-8 before returning.

    :param str value: Value to parse.
    :returns: str
    """
    if not isinstance(value, str):
        return value.decode('utf-8')
    return value


_parser_funcs = (('boolean', _parse_boolean),
                 ('integer', int),
                 ('number', float),
                 ('array', _parse_array),
                 ('object', _parse_object),
                 ('string', _parse_string))


def parse_value(value, allowed_types, name='value'):
    """Parse a value into one of a number of types.

    This function is used to coerce untyped HTTP parameter strings into an
    appropriate type. It tries to coerce the value into each of the allowed
    types, and uses the first that evaluates properly.

    Because this is coercing a string into multiple, potentially ambiguous,
    types, it tests things in the order of least ambiguous to most ambiguous:

    - The "null" type is checked first. If allowed, and the value is blank
      (""), None will be returned.
    - The "boolean" type is checked next. Values of "true" (case insensitive)
      are True, and values of "false" are False.
    - Numeric types are checked next -- first "integer", then "number".
    - The "array" type is checked next. A value is only considered a valid
      array if it begins with a "[" and can be parsed as JSON.
    - The "object" type is checked next. A value is only considered a valid
      object if it begins with a "{" and can be parsed as JSON.
    - The "string" type is checked last, since any value is a valid string.
      Unicode strings are encoded as UTF-8.

    :param str value: Parameter value. Example: "1"
    :param list allowed_types: Types that should be attempted. Example:
        ["integer", "null"]
    :param str name: Parameter name. If not specified, "value" is used.
        Example: "campaign_id"
    :returns: a tuple of a type string and coerced value
    :raises: ParseError if the value cannot be coerced to any of the types
    """
    if not isinstance(value, str):
        raise ValueError('value for %r must be a string' % name)
    if isinstance(allowed_types, str):
        allowed_types = [allowed_types]

    # Note that the order of these type considerations is important. Because we
    # have an untyped value that may be one of any given number of types, we
    # need a consistent order of evaluation in cases when there is ambiguity
    # between types.

    if 'null' in allowed_types and value == '':
        return 'null', None

    # For all of these types, we'll pass the value to the function and it will
    # raise a TypeError or ValueError or return None if it can't be parsed as
    # the given type.

    for allowed_type, parser in _parser_funcs:
        if allowed_type in allowed_types:
            try:
                parsed_value = parser(value)
                if parsed_value is not None:
                    return allowed_type, parsed_value
            except (TypeError, ValueError):
                # Ignore any errors, and continue trying other types
                pass

    raise ParseError('%s must be a valid type (%s)' %
                     (name, ', '.join(allowed_types)))


def parse_json(value: str, sig_params: List[inspect.Parameter] = None) -> dict:
    """Parse a value as JSON.

    This is just a wrapper around json.loads which re-raises any errors as a
    ParseError instead.

    :param str value: JSON string.
    :param dict sig_params: The logic function's signature parameters.
    :returns: the parsed JSON value
    """
    try:
        loaded = json.loads(value)
    except Exception as e:
        message = 'Error parsing JSON: %s' % e
        logging.debug(message, exc_info=e)
        raise ParseError(message)

    if sig_params is not None:
        return map_param_names(loaded, sig_params)
    return loaded


_native_type_to_json = {
    list: 'array',
    bool: 'boolean',
    int: 'integer',
    dict: 'object',
    float: 'number',
    str: 'string'
}


def map_param_names(
        req_params: dict, sig_params: List[inspect.Parameter]) -> dict:
    """Maps request param names to match logic function param names.

    If a doctor type defined a `param_name` attribute for the name of the
    parameter in the request, we should use that as the key when looking up
    the value for the request parameter.

    When we declare a type we can specify what the parameter name
    should be in the request that the annotated type should get mapped to.

    >>> from doctor.types import number
    >>> Latitude = number('The latitude', param_name='location.lat')
    >>> def my_logic(lat: Latitude): pass
    >>> request_params = {'location.lat': 45.2342343}

    In the above example doctor knows to pass the value at key `location.lat`
    to the logic function variable named `lat` since it's annotated by the
    `Latitude` type which specifies what the param_name is on the request.

    :param dict req_params: The parameters specified in the request.
    :param dict sig_params: The logic function's signature parameters.
    :returns: A dict of re-mapped params.
    """
    new_request_params = {}
    for k, param in sig_params.items():
        param_name = getattr(param.annotation, 'param_name', None)
        key = k if param_name is None else param_name
        if key in req_params:
            new_request_params[k] = req_params[key]
    return new_request_params


def parse_form_and_query_params(req_params, sig_params):
    """Uses the parameter annotations to coerce string params.

    This is used for HTTP requests, in which the form parameters are all
    strings, but need to be converted to the appropriate types before
    validating them.

    :param dict req_params: The parameters specified in the request.
    :param dict sig_params: The logic function's signature parameters.
    :returns: a dict of params parsed from the input dict.
    :raises TypeSystemError: If there are errors parsing values.
    """
    errors = {}
    parsed_params = {}
    for param, value in req_params.items():
        if param not in sig_params:
            continue
        native_type = sig_params[param].annotation.native_type
        json_type = [_native_type_to_json[native_type]]
        # If the type is nullable, also add null as an allowed type.
        if sig_params[param].annotation.nullable:
            json_type.append('null')
        try:
            _, parsed_params[param] = parse_value(value, json_type)
        except ParseError as e:
            errors[param] = str(e)

    if errors:
        raise TypeSystemError(errors, errors=errors)

    return parsed_params
