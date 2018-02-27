#: HTTP methods that are allowed to have a JSON body.  Technically all HTTP
#: methods are allowed to have a body, but some like GET/DELETE have no
#: contextual meaning server side, so should not be used.
HTTP_METHODS_WITH_JSON_BODY = ('PATCH', 'POST', 'PUT')
