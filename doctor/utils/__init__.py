import os
import re
import sys

try:
    from sphinx.util.docstrings import prepare_docstring
except ImportError:
    prepare_docstring = None


#: Used to identify the end of the description block, and the beginning of the
#: parameters. This assumes that the parameters and such will always occur at
#: the end of the docstring.
DESCRIPTION_END_RE = re.compile(':(arg|param|returns|throws)', re.I)


def nested_set(data, keys, value):
    """Set a nested key value in a dict based on key list.

    :param data dict: the dict to set nested key in.
    :param keys list: the nested list of keys.
    :param value object: the final value to set.
    """
    for key in keys[:-1]:
        data = data.setdefault(key, {})
    data[keys[-1]] = value


def exec_params(call, *args, **kwargs):
    """Execute a callable with only the defined parameters
    and not just *args, **kwargs.

    :param callable call: The callable to exec with the given params as
        defined by itself. call should have an inspect.ArgSpec attached
        as an attribute _argspec
    :returns anything:
    :raises TypeError:
    """
    arg_spec = getattr(call, '_argspec', None)
    if arg_spec and not arg_spec.keywords:
        kwargs = {key: value for key, value in kwargs.iteritems()
                  if key in arg_spec.args}
    return call(*args, **kwargs)


def get_module_attr(module_filename, module_attr, namespace=None):
    """Get an attribute from a module.

    This uses execfile to load the module with a private namespace, and then
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
        execfile(module_filename, namespace)
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

    if not isinstance(docstring, basestring):
        return []
    lines = []
    for line in prepare_docstring(docstring):
        if DESCRIPTION_END_RE.match(line):
            break
        lines.append(line)
    if lines and lines[-1] != '':
        lines.append('')
    return lines
