"""
This module contains custom types used by tests.
"""
from doctor.types import array, boolean, integer, new_type, string, Object


Age = integer('age', minimum=1, maximum=120)
Auth = string('auth token')
Foo = string('foo')
FooId = integer('foo id')
Foos = array('foos', items=Foo)
IsAlive = boolean('Is alive?')
ItemId = integer('item id', minimum=1)
Item = new_type(Object, 'item', properties={'item_id': ItemId},
                additional_properties=False, required=['item_id'])
IncludeDeleted = boolean('indicates if deleted items should be included.')
IsDeleted = boolean('Indicates if the item should be marked as deleted')
Name = string('name', min_length=1)
