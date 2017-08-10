class Response(object):
    """Represents a response.

    This object contains the response itsetlf along with any additional headers
    that should be added and returned with the response data.  It contains all
    of the common response headers.

    :param content: The data to be returned with the response.
    :param str access_control_allow_origin: Indicates whether a resource can be
        shared based by returning the value of the Origin request header
    :param bool access_control_allow_credentials: Indicates whether the response
        to request can be exposed when the omit credentials flag is unset. When
        part of the response to a preflight request it indicates that the actual
        request can include user credentials.
    :param str access_control_expose_headers: Indicates which headers are safe
        to expose to the API of a CORS API specification.
    :param str access_control_max_age: Indicates how long the results of a
        preflight request can be cached in a preflight result cache.
    :param str access_control_allow_methods: Indicates, as part of the response
        to a preflight request, which methods can be used during the actual
        request.
    :param str access_control_allow_headers: Indicates, as part of the response
        to a preflight request, which header field names can be used during the
        actual request.
    :param str accept_patch: Specifies which patch document formats this
        server supports.
    :param str accept_ranges: What partial content range types this server
        supports via byte serving.
    :param int age: The age the object has been in a proxy cache in seconds.
    :param str allow: Valid methods for a specified resource. To be used for a
        405 Method not allowed.
    :param str alt_svc: A server uses "Alt-Svc" header (meaning Alternative
        Services) to indicate that its resources can also be accessed at a
        different network location (host or port) or using a different protocol.
    :param str cache_control: Tells all caching mechanisms from server to client
        whether they may cache this object. It is measured in seconds.
    :param str content_disposition: An opportunity to raise a "File Download"
        dialogue box for a known MIME type with binary format or suggest a
        filename for dynamic content. Quotes are necessary with special
        characters.
    :param str content_encoding: The type of encoding used on the data.
    :param str content_language: The natural language or languages of the
        intended audience for the enclosed content.
    :param int content_length: The length of the response body in octets
        (8-bit bytes).
    :param str content_location: An alternate location for the returned data.
    :param str content_range: Where in a full body message this partial message
        belongs.
    :param str content_type: The MIME type of this content.
    :param str date: The date and time that the message was sent (in "HTTP-date"
        format as defined by RFC 7231).
    :param str etag: An identifier for a specific version of a resource, often
        a message digest.
    :param str expires: Gives the date/time after which the response is
        considered stale (in "HTTP-date" format as defined by RFC 7231).
    :param str last_modified: The last modified date for the requested object
        (in "HTTP-date" format as defined by RFC 7231).
    :param str link: Used to express a typed relationship with another resource,
        where the relation type is defined by RFC 5988.
    :param str location: Used in redirection, or when a new resource has been
        created.
    :param str pragma: Implementation-specific fields that may have various
        effects anywhere along the request-response chain.
    :param str proxy_authenticate: Request authentication to access the proxy.
    :param str public_key_pins: HTTP Public Key Pinning, announces hash of
        website's authentic TLS certificate.
    :param str retry_after: If an entity is temporarily unavailable, this
        instructs the client to try again later. Value could be a specified
        period of time (in seconds) or a HTTP-date.
    :param str server: A name for the server.
    :param str set_cookie: A HTTP cookie.
    :param strict_transport_security: A HSTS Policy informing the HTTP client
        how long to cache the HTTPS only policy and whether this applies to
        subdomains.
    :param str trailer: The Trailer general field value indicates that the
        given set of header fields is present in the trailer of a message
        encoded with chunked transfer coding.
    :param str tk: Tracking Status header, value suggested to be sent in
        response to a DNT(do-not-track).
    :prarm str upgrade: Ask the client to upgrade to another protocol.
    :pram str vary: Tells downstream proxies how to match future request
        headers to decide whether the cached response can be used rather than
        requesting a fresh one from the origin server.
    :param str via: Informs the client of proxies through which the response
        was sent.
    :param str warning: A general warning about possible problems with the
        entity body.
    :param str www_authenticate: Indicates the authentication scheme that
        should be used to access the requested entity.
    """

    def __init__(self, content, access_control_allow_origin=None,
                 access_control_allow_credentials=None,
                 access_control_expose_headers=None,
                 access_control_max_age=None, access_control_allow_methods=None,
                 access_control_allow_headers=None, accept_patch=None,
                 accept_ranges=None, age=None, allow=None, alt_svc=None,
                 cache_control=None, content_disposition=None,
                 content_encoding=None, content_language=None,
                 content_length=None, content_location=None, content_range=None,
                 content_type=None, date=None, etag=None, expires=None,
                 last_modified=None, link=None, location=None, pragma=None,
                 proxy_authenticate=None, public_key_pins=None,
                 retry_after=None, server=None, set_cookie=None,
                 strict_transport_security=None, trailer=None,
                 transfer_encoding=None, tk=None, upgrade=None, vary=None,
                 via=None, warning=None, www_authenticate=None):
        self.content = content
        self.access_control_allow_origin = access_control_allow_origin
        self.access_control_allow_credentials = access_control_allow_credentials
        self.access_control_expose_headers = access_control_expose_headers
        self.access_control_max_age = access_control_max_age
        self.access_control_allow_methods = access_control_allow_methods
        self.access_control_allow_headers = access_control_allow_headers
        self.accept_patch = accept_patch
        self.accept_ranges = accept_ranges
        self.age = age
        self.allow = allow
        self.alt_svc = alt_svc
        self.cache_control = cache_control
        self.content_disposition = content_disposition
        self.content_encoding = content_encoding
        self.content_language = content_language
        self.content_length = content_length
        self.content_location = content_location
        self.content_range = content_range
        self.content_type = content_type
        self.date = date
        self.etag = etag
        self.expires = expires
        self.last_modified = last_modified
        self.link = link
        self.location = location
        self.pragma = pragma
        self.proxy_authenticate = proxy_authenticate
        self.public_key_pins = public_key_pins
        self.retry_after = retry_after
        self.server = server
        self.set_cookie = set_cookie
        self.strict_transport_security = strict_transport_security
        self.trailer = trailer
        self.transfer_encoding = transfer_encoding
        self.tk = tk
        self.upgrade = upgrade
        self.vary = vary
        self.via = via
        self.warning = warning
        self.www_authenticate = www_authenticate

    def get_headers(self):
        """Gets all the headers for the response.

        :returns: A dict of response headers.
        """
        raise NotImplemented(
            'This class must be subclassed and get_headers must be implemented '
            'to return a dict of response headers.')
