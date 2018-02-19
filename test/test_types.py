import pytest

from doctor.errors import TypeSystemError
from doctor.types import string, SuperType


class TestSuperType(object):

    def test_init_no_description(self):
        class MyType(SuperType):
            pass

        with pytest.raises(ValueError, match='define a description attribute'):
            MyType()

    def test_init_with_description_defined(self):
        class MyType(SuperType):
            description = 'My Type'

        MyType()


class TestString(object):

    def test_trim_whitespace(self):
        S = string('a string', trim_whitespace=True)
        actual = S(' foo ')
        assert 'foo' == actual

    def test_min_length(self):
        S = string('a string', min_length=2)
        # No exception
        S('foo')
        # String too short
        with pytest.raises(TypeSystemError,
                           match='Must have at least 2 characters'):
            S('f')
        # Empty string when min_length is 1
        S = string('empty', min_length=1)
        with pytest.raises(TypeSystemError, match='Must not be blank.'):
            S('')

    def test_max_length(self):
        S = string('a string', max_length=2)
        # No exception
        S('12')
        # String too long
        with pytest.raises(TypeSystemError,
                           match='Must have no more than 2 characters'):
            S('123')

    def test_pattern(self):
        S = string('a regex', pattern=r'^foo*')
        # No exception
        S('foo bar')
        # Does not begin with `foo`
        with pytest.raises(TypeSystemError):
            S('bar')


class TestNumericType(object):
    pass
