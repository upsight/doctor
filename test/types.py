"""
This module contains custom types used by tests.
"""
from doctor.types import array, boolean, integer, string


Name = string('name', min_length=1)
Age = integer('age', minimum=1, maximum=120)
IsAlive = boolean('Is alive?')
FooId = integer('foo id')
Foo = string('foo')
Foos = array('foos', items=Foo)
