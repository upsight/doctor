import inspect
import os
import re
import sys
from copy import copy
from inspect import Parameter, Signature
from typing import Callable, List

try:
    from sphinx.util.docstrings import prepare_docstring
except ImportError:
    prepare_docstring = None

from doctor.types import SuperType

#: Used to identify the end of the description block, and the beginning of the
#: parameters. This assumes that the parameters and such will always occur at
#: the end of the docstring.
DESCRIPTION_END_RE = re.compile(':(arg|param|returns|throws)', re.I)


class RequestParamAnnotation(object):
    """Represents a new request parameter annotation.

    :param name: The name of the parameter.
    :param annotation: The annotation type of the parameter.
    :type annotation: A doctor type that should subclass
        :class:`~doctor.types.SuperType`.
    :param required: Indicates if the parameter is required or not.
    """
    def __init__(self, name: str, annotation, required: bool=False):
        self.annotation = annotation
        self.name = name
        self.required = required


class Params(object):
    """Represents parameters for a request.

    :param all: A list of all paramter names for a request.
    :param required: A list of all required parameter names for a request.
    :param optional: A list of all optional parameter names for a request.
    :param logic: A list of all parameter names that are part ofthe logic
        function signature.
    """
    def __init__(self, all: List[str], required: List[str],
                 optional: List[str], logic: List[str]):
        self.all = all
        self.optional = optional
        self.required = required
        self.logic = logic

    def __repr__(self):
        return str({
            'all': self.all,
            'logic': self.logic,
            'optional': self.optional,
            'required': self.required
        })

    def __eq__(self, other):
        for attr in ('all', 'logic', 'optional', 'required'):
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)


def get_params_from_func(func: Callable, signature: Signature=None) -> Params:
    """Gets all parameters from a function signature.

    :param func: The function to inspect.
    :param signature: An inspect.Signature instance.
    :returns: A named tuple containing information about all, optional,
        required and logic function parameters.
    """
    if signature is None:
        # Check if the function already parsed the signature
        signature = getattr(func, '_doctor_signature', None)
        # Otherwise parse the signature
        if signature is None:
            signature = inspect.signature(func)

    # Required is a positional argument with no defualt value and it's
    # annotation must sub class SuperType.  This is so we don't try to
    # require parameters passed to a logic function by a decorator that are
    # not part of a request.
    required = [key for key, p in signature.parameters.items()
                if p.default == p.empty and issubclass(p.annotation, SuperType)]
    optional = [key for key, p in signature.parameters.items()
                if p.default != p.empty]
    all_params = [key for key in signature.parameters.keys()]
    # Logic params are all parameters that are part of the logic signature.
    logic_params = copy(all_params)
    return Params(all_params, required, optional, logic_params)


def add_param_annotations(
        logic: Callable, params: List[RequestParamAnnotation]) -> Callable:
    """Adds parameter annotations to a logic function.

    This adds additional required and/or optional parameters to the logic
    function that are not part of it's signature.  It's intended to be used
    by decorators decorating logic functions or middleware.

    :param logic: The logic function to add the parameter annotations to.
    :param params: The list of RequestParamAnnotations to add to the logic func.
    :returns: The logic func with updated parameter annotations.
    """
    sig = inspect.signature(logic)
    doctor_params = get_params_from_func(logic, sig)

    new_params = []
    for param in params:
        doctor_params.all.append(param.name)
        default = None
        if param.required:
            default = Parameter.empty
            doctor_params.required.append(param.name)
        else:
            doctor_params.optional.append(param.name)
        new_params.append(
                Parameter(param.name, Parameter.KEYWORD_ONLY, default=default,
                          annotation=param.annotation))

    prev_parameters = [p for _, p in sig.parameters.items()]
    new_sig = sig.replace(parameters=prev_parameters + new_params)
    logic._doctor_signature = new_sig
    logic._doctor_params = doctor_params
    return logic


def get_module_attr(module_filename, module_attr, namespace=None):
    """Get an attribute from a module.

    This uses exec to load the module with a private namespace, and then
    plucks and returns the given attribute from that module's namespace.

    Note that, while this method doesn't have any explicit unit tests, it is
    tested implicitly by the doctor's own documentation. The Sphinx
    build process will fail to generate docs if this does not work.

    :param str module_filename: Path to the module to execute (e.g.
        "../src/app.py").
    :param str module_attr: Attribute to pluck from the module's namespace.
        (e.g. "app").
    :param dict namespace: Optional namespace. If one is not passed, an empty
        dict will be used instead. Note that this function mutates the passed
        namespace, so you can inspect a passed dict after calling this method
        to see how the module changed it.
    :returns: The attribute from the module.
    :raises KeyError: if the module doesn't have the given attribute.
    """
    if namespace is None:
        namespace = {}
    module_filename = os.path.abspath(module_filename)
    namespace['__file__'] = module_filename
    module_dir = os.path.dirname(module_filename)
    old_cwd = os.getcwd()
    old_sys_path = sys.path[:]
    try:
        os.chdir(module_dir)
        sys.path.append(module_dir)
        with open(module_filename, 'r') as mf:
            exec(compile(mf.read(), module_filename, 'exec'), namespace)
        return namespace[module_attr]
    finally:
        os.chdir(old_cwd)
        sys.path = old_sys_path


def get_description_lines(docstring):
    """Extract the description from the given docstring.

    This grabs everything up to the first occurrence of something that looks
    like a parameter description. The docstring will be dedented and cleaned
    up using the standard Sphinx methods.

    :param str docstring: The source docstring.
    :returns: list
    """
    if prepare_docstring is None:
        raise ImportError('sphinx must be installed to use this function.')

    if not isinstance(docstring, str):
        return []
    lines = []
    for line in prepare_docstring(docstring):
        if DESCRIPTION_END_RE.match(line):
            break
        lines.append(line)
    if lines and lines[-1] != '':
        lines.append('')
    return lines


def get_valid_class_name(s: str) -> str:
    """Return the given string converted so that it can be used for a class name

    Remove leading and trailing spaces; removes spaces and capitalizes each
    word; and remove anything that is not alphanumeric.  Returns a pep8
    compatible class name.

    :param s: The string to convert.
    :returns: The updated string.
    """
    s = str(s).strip()
    s = ''.join([w.title() for w in re.split('\W+|_', s)])
    return re.sub(r'[^\w|_]', '', s)
