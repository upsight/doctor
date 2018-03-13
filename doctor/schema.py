import logging
import os

import jsonschema
import yaml
from jsonschema.compat import urldefrag

from .errors import (
    SchemaError, SchemaLoadingError, SchematicError, SchemaValidationError)
from .parsers import parse_json


DEFAULT = object()


class SchemaRefResolver(jsonschema.RefResolver):

    """Subclass in order to provide support for loading YAML files."""

    def _format_stack(self, stack, current=None):
        """Prettifies a scope stack for use in error messages.

        :param list(str) stack: List of scopes.
        :param str current: The current scope. If specified, will be appended
            onto the stack before formatting.
        :returns: str
        """
        if current is not None:
            stack = stack + [current]
        if len(stack) > 1:
            prefix = os.path.commonprefix(stack)
            if prefix.endswith('/'):
                prefix = prefix[:-1]
            stack = [scope[len(prefix):] for scope in stack]
        return ' => '.join(stack)

    def resolve(self, ref, document=None):
        """Resolve a fragment within the schema.

        If the resolved value contains a $ref, it will attempt to resolve that
        as well, until it gets something that is not a reference. Circular
        references will raise a SchemaError.

        :param str ref: URI to resolve.
        :param dict document: Optional schema in which to resolve the URI.
        :returns: a tuple of the final, resolved URI (after any recursion) and
            resolved value in the schema that the URI references.
        :raises SchemaError:
        """
        try:
            # This logic is basically the RefResolver's resolve function, but
            # updated to support fragments of dynamic documents. The jsonschema
            # module supports passing documents when resolving fragments, but
            # it doesn't expose that capability in the resolve function.
            url = self._urljoin_cache(self.resolution_scope, ref)
            if document is None:
                # No document passed, so just resolve it as we normally would.
                resolved = self._remote_cache(url)
            else:
                # Document passed, so assume it's a fragment.
                _, fragment = urldefrag(url)
                resolved = self.resolve_fragment(document, fragment)
        except jsonschema.RefResolutionError as e:
            # Failed to find a ref. Make the error a bit prettier so we can
            # figure out where it came from.
            message = e.args[0]
            if self._scopes_stack:
                message = '{} (from {})'.format(
                    message, self._format_stack(self._scopes_stack))
            raise SchemaError(message)

        if isinstance(resolved, dict) and '$ref' in resolved:
            # Try to resolve the reference, so we can get the actual value we
            # want, instead of a useless dict with a $ref in it.
            if url in self._scopes_stack:
                # We've already tried to look up this URL, so this must
                # be a circular reference in the schema.
                raise SchemaError(
                    'Circular reference in schema: {}'.format(
                        self._format_stack(self._scopes_stack + [url])))
            try:
                self.push_scope(url)
                return self.resolve(resolved['$ref'])
            finally:
                self.pop_scope()
        else:
            return url, resolved

    def resolve_remote(self, uri):
        """Add support to load YAML files.

        This will attempt to load a YAML file first, and then go back to the
        default behavior.

        :param str uri: the URI to resolve
        :returns: the retrieved document
        """
        if uri.startswith('file://'):
            try:
                path = uri[7:]
                with open(path, 'r') as schema_file:
                    result = yaml.load(schema_file)
                if self.cache_remote:
                    self.store[uri] = result
                return result
            except yaml.parser.ParserError as e:
                logging.debug('Error parsing {!r} as YAML: {}'.format(
                    uri, e))
        return super(SchemaRefResolver, self).resolve_remote(uri)


class Schema(object):

    """
    This class is used to manipulate JSON schemas and validate values against
    the schema.

    :param dict schema: The loaded schema.
    :param str schema_path: The absolute path to the directory of local schemas.
    """

    def __init__(self, schema, schema_path=None):
        self.schema = schema
        self._resolver = None
        self._schema_path = schema_path

    def get_validator(self, schema=None):
        """Get a jsonschema validator.

        :param dict schema: A custom schema to validate against.
        :returns: an instance of jsonschema Draft4Validator.
        """
        schema = schema if schema is not None else self.schema
        return jsonschema.Draft4Validator(
            schema, resolver=self.resolver,
            format_checker=jsonschema.draft4_format_checker)

    def resolve(self, ref, document=None):
        """Resolve a ref within the schema.

        This is just a convenience method, since RefResolver returns both a URI
        and the resolved value, and we usually just need the resolved value.

        :param str ref: URI to resolve.
        :param dict document: Optional schema in which to resolve the URI.
        :returns: the portion of the schema that the URI references.
        :see: :meth:`SchemaRefResolver.resolve`
        """
        _, resolved = self.resolver.resolve(ref, document=document)
        return resolved

    @property
    def resolver(self):
        """jsonschema RefResolver object for the base schema."""
        if self._resolver is not None:
            return self._resolver
        if self._schema_path is not None:
            # the documentation for ref resolving
            # https://github.com/Julian/jsonschema/issues/98
            # https://python-jsonschema.readthedocs.org/en/latest/references/
            self._resolver = SchemaRefResolver(
                'file://' + self._schema_path + '/', self.schema)
        else:
            self._resolver = SchemaRefResolver.from_schema(self.schema)
        return self._resolver

    def validate(self, value, validator):
        """Validates and returns the value.

        If the value does not validate against the schema, SchemaValidationError
        will be raised.

        :param value: A value to validate (usually a dict).
        :param validator: An instance of a jsonschema validator class, as
            created by Schema.get_validator().
        :returns: the passed value.
        :raises SchemaValidationError:
        :raises Exception:
        """
        try:
            validator.validate(value)
        except Exception as e:
            logging.debug(e, exc_info=e)
            if isinstance(e, SchematicError):
                raise
            else:
                # Gather all the validation errors
                validation_errors = sorted(
                    validator.iter_errors(value), key=lambda e: e.path)
                errors = {}
                for error in validation_errors:
                    try:
                        key = error.path[0]
                    except IndexError:
                        key = '_other'
                    errors[key] = error.args[0]
                raise SchemaValidationError(e.args[0], errors=errors)
        return value

    def validate_json(self, json_value, validator):
        """Validates and returns the parsed JSON string.

        If the value is not valid JSON, ParseError will be raised. If it is
        valid JSON, but does not validate against the schema,
        SchemaValidationError will be raised.

        :param str json_value: JSON value.
        :param validator: An instance of a jsonschema validator class, as
            created by Schema.get_validator().
        :returns: the parsed JSON value.
        """
        value = parse_json(json_value)
        return self.validate(value, validator)

    @classmethod
    def from_file(cls, schema_filepath, *args, **kwargs):
        """Create an instance from a YAML or JSON schema file.

        Any additional args or kwargs will be passed on when constructing the
        new schema instance (useful for subclasses).

        :param str schema_filepath: Path to the schema file.
        :returns: an instance of the class.
        :raises SchemaLoadingError: for invalid input files.
        """
        schema_filepath = os.path.abspath(schema_filepath)
        try:
            with open(schema_filepath, 'r') as schema_file:
                schema = yaml.load(schema_file.read())
        except Exception:
            msg = 'Error loading schema file {}'.format(schema_filepath)
            logging.exception(msg)
            raise SchemaLoadingError(msg)
        return cls(schema, *args, schema_path=os.path.dirname(schema_filepath),
                   **kwargs)
