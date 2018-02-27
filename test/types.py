"""
This module contains custom types used by tests.
"""
from doctor.types import array, boolean, enum, integer, new_type, string, Object


Age = integer('age', minimum=1, maximum=120, example=34)
Auth = string('auth token', example='testtoken')
Color = enum('Color', enum=['blue', 'green'], example='blue')
Colors = array('colors', items=Color, example=['green'])
ExampleArray = array('ex description e', items=Auth, example=['ex', 'array'])
ExampleObject = new_type(Object, 'ex description f', properties={'str': Auth},
                         additional_properties=False, example={'str': 'ex str'})
ExampleObjects = array(
    'ex objects', items=ExampleObject, example=[{'str': 'e'}])
Foo = string('foo', example='foo')
FooId = integer('foo id', example=1)
Foos = array('foos', items=Foo, example=['foo'])
IsAlive = boolean('Is alive?', example=True)
ItemId = integer('item id', minimum=1, example=1)
Item = new_type(Object, 'item', properties={'item_id': ItemId},
                additional_properties=False, required=['item_id'],
                example={'item_id': 1})
IncludeDeleted = boolean('indicates if deleted items should be included.',
                         example=False)
IsDeleted = boolean('Indicates if the item should be marked as deleted',
                    example=False)
Name = string('name', min_length=1, example='John')
