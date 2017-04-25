"""
This module defines a custom field type named `ObjectTypedField`.  This class
will document object properties.

The DoctorHTTPResource class is necessary in order to override the
`doc_field_types` to set json request/response fields as `ObjectTypedField`.

The `HTTP<method>` classes needed to be redefined to extend from the new
`DoctorHTTPResource` class.  Likewise, the `DoctorHTTPDomain` class was
required to set the directives to use the `HTTP<method>` classes.

Finally, a new `setup` method was created to use the `DoctorHTTPDomain` class.
"""

try:
    from docutils import nodes
    from pygments.lexers import get_lexer_by_name
    from pygments.util import ClassNotFound
    from sphinx import addnodes
    from sphinx.util.docfields import GroupedField, TypedField
    from sphinxcontrib.httpdomain import HTTPDomain, HTTPLexer, HTTPResource
except ImportError:  # pragma: no cover
    raise ImportError('You must install sphinx and sphinxcontrib-httpdomain to '
                      'use the doctor.docs module.')


class ObjectTypedField(TypedField):
    """
    A doc field that is grouped and has type information for the arguments.  It
    always has an argument.  The argument can be linked using the given
    *rolename*, the type using the given *typerolename*.
    Two uses are possible: either parameter and type description are given
    separately, using a field from *names* and one from *typenames*,
    respectively, or both are given using a field from *names*, see the example.

    This class will also document object properties as sub-lists of the object.

    Example::
       :param foo: description of parameter foo
       :type foo:  SomeClass
       -- or --
       :param SomeClass foo: description of parameter foo
    """

    def make_field(self, types, domain, items, env=None, **kwargs):
        def handle_item(fieldarg, content):
            """Handles translating an item into a node.

            :param str fieldarg: The name of the field.  This is either in the
                format of 'some_field', 'some_field|object', or
                'some_field|objectproperty'.  If there is a `|` character in
                the fieldarg it is treated differently in order to generate
                a sub-list for objects.
            :param list(docutils.nodes.node) content: The content field which
                contains a list of node types to render.
            :returns: A tuple containing the item as a node paragraph and
                a list node if the item is an object, otherwise None.
            """
            # store a copy of the original value for looking up types within
            # this function.
            orig_fieldarg = fieldarg
            # Determine if the field is an object or not.
            is_object = False
            fieldargs = fieldarg.split('|')
            fieldarg = fieldargs[0]
            if len(fieldargs) == 2 and fieldargs[1] == 'object':
                is_object = True

            par = nodes.paragraph()
            par += self.make_xref(self.rolename, domain, fieldarg,
                                  addnodes.literal_strong)
            if orig_fieldarg in types:
                par += nodes.Text(' (')
                # NOTE: using .pop() here to prevent a single type node to be
                # inserted twice into the doctree, which leads to
                # inconsistencies later when references are resolved
                fieldtype = types.pop(orig_fieldarg)
                if len(fieldtype) == 1 and isinstance(fieldtype[0], nodes.Text):
                    typename = u''.join(n.astext() for n in fieldtype)
                    par += self.make_xref(self.typerolename, domain, typename,
                                          addnodes.literal_emphasis)
                else:
                    par += fieldtype
                par += nodes.Text(')')
            par += nodes.Text(' -- ')
            # We need to add each child node individually.  If we don't and
            # just do `par += content` the order of the rendered nodes sometimes
            # is generated in an unexpected order.
            for item in content:
                for node in item.children:
                    par += node

            # If the item is an object we need to create a sub-list to show
            # all of the object's properties.
            ul = None
            if is_object:
                ul = self.list_type()
                obj_pos = items.index((orig_fieldarg, content))
                # Loop over all items after the current item and add them to
                # the sub list until we reach the end of the item's properties.
                for obj_prop, content in items[obj_pos + 1:]:
                    fieldargs = obj_prop.split('|')
                    if len(fieldargs) == 2 and fieldargs[1] == 'objectproperty':
                        # Remove the object property from items so we don't
                        # document it again as we iterate over items outside
                        # of this function.
                        items.remove((obj_prop, content))
                        li, _ = handle_item(obj_prop, content)
                        ul += nodes.list_item('', li)
                    else:
                        break
            return (par, ul)

        fieldname = nodes.field_name('', self.label)
        if len(items) == 1 and self.can_collapse:
            fieldarg, content = items[0]
            bodynode, _ = handle_item(fieldarg, content)
        else:
            bodynode = self.list_type()
            for fieldarg, content in items:
                li, ul = handle_item(fieldarg, content)
                # If the item was an object we will have a sub-list returned
                # that we should add to the list item.
                if ul:
                    li += ul
                bodynode += nodes.list_item('', li)
        fieldbody = nodes.field_body('', bodynode)
        return nodes.field('', fieldname, fieldbody)


class DoctorHTTPResource(HTTPResource):

    doc_field_types = [
        TypedField('parameter', label='Parameters',
                   names=('param', 'parameter', 'arg', 'argument'),
                   typerolename='obj', typenames=('paramtype', 'type')),
        TypedField('jsonparameter', label='JSON Parameters',
                   names=('jsonparameter', 'jsonparam', 'json'),
                   typerolename='obj', typenames=('jsonparamtype', 'jsontype')),
        ObjectTypedField(
            'requestjsonobject', label='Request JSON Object',
            names=('reqjsonobj', 'reqjson', '<jsonobj', '<json'),
            typerolename='obj', typenames=('reqjsonobj', '<jsonobj')),
        ObjectTypedField('requestjsonarray',
                         label='Request JSON Array of Objects',
                         names=('reqjsonarr', '<jsonarr'),
                         typerolename='obj',
                         typenames=('reqjsonarrtype', '<jsonarrtype')),
        ObjectTypedField(
            'responsejsonobject', label='Response JSON Object',
            names=('resjsonobj', 'resjson', '>jsonobj', '>json'),
            typerolename='obj', typenames=('resjsonobj', '>jsonobj')),
        ObjectTypedField('responsejsonarray',
                         label='Response JSON Array of Objects',
                         names=('resjsonarr', '>jsonarr'),
                         typerolename='obj',
                         typenames=('resjsonarrtype', '>jsonarrtype')),
        TypedField('queryparameter', label='Query Parameters',
                   names=('queryparameter', 'queryparam', 'qparam', 'query'),
                   typerolename='obj',
                   typenames=('queryparamtype', 'querytype', 'qtype')),
        GroupedField('formparameter', label='Form Parameters',
                     names=('formparameter', 'formparam', 'fparam', 'form')),
        GroupedField('requestheader', label='Request Headers',
                     rolename='header',
                     names=('<header', 'reqheader', 'requestheader')),
        GroupedField('responseheader', label='Response Headers',
                     rolename='header',
                     names=('>header', 'resheader', 'responseheader')),
        GroupedField('statuscode', label='Status Codes',
                     rolename='statuscode',
                     names=('statuscode', 'status', 'code'))
    ]


class HTTPOptions(DoctorHTTPResource):

    method = 'options'


class HTTPHead(DoctorHTTPResource):

    method = 'head'


class HTTPPatch(DoctorHTTPResource):

    method = 'patch'


class HTTPPost(DoctorHTTPResource):

    method = 'post'


class HTTPGet(DoctorHTTPResource):

    method = 'get'


class HTTPPut(DoctorHTTPResource):

    method = 'put'


class HTTPDelete(DoctorHTTPResource):

    method = 'delete'


class HTTPTrace(DoctorHTTPResource):

    method = 'trace'


class HTTPConnect(DoctorHTTPResource):

    method = 'connect'


class HTTPCopy(DoctorHTTPResource):

    method = 'copy'


class HTTPAny(DoctorHTTPResource):

    method = 'any'


class DoctorHTTPDomain(HTTPDomain):

    directives = {
        'options': HTTPOptions,
        'head': HTTPHead,
        'post': HTTPPost,
        'get': HTTPGet,
        'put': HTTPPut,
        'patch': HTTPPatch,
        'delete': HTTPDelete,
        'trace': HTTPTrace,
        'connect': HTTPConnect,
        'copy': HTTPCopy,
        'any': HTTPAny
    }


def setup(app):
    app.add_domain(DoctorHTTPDomain)
    try:
        get_lexer_by_name('http')
    except ClassNotFound:
        app.add_lexer('http', HTTPLexer())
    app.add_config_value('http_index_ignore_prefixes', [], None)
    app.add_config_value('http_index_shortname', 'routing table', True)
    app.add_config_value('http_index_localname', 'HTTP Routing Table', True)
    app.add_config_value('http_strict_mode', True, None)
    app.add_config_value('http_headers_ignore_prefixes', ['X-'], None)
