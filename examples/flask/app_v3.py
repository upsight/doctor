# Note that this file contains some inline comments starting with # --, used to
# generate documentation from this file. You're probably better served reading
# the actual documentation (see Using in Flask in the docs).

from flask import Flask
from flask_restful import Api
from doctor.errors import NotFoundError
from doctor.router_v3 import create_routes, get, post, put, delete
from doctor.types import array, boolean, integer, string, Object

# -- mark-types

Body = string('Note body')
Done = boolean('Marks if a note is done or not.')
NoteId = integer('Note ID')
Status = string('API status')


class Note(Object):
    description = 'A note object'
    properties = {
        'note_id': NoteId,
        'body': Body,
        'done': Done,
    }


Notes = array('Array of notes', items=Note)

# -- mark-logic

note = {'note_id': 1, 'body': 'Example body', 'done': False}


def get_note(note_id: NoteId) -> Note:
    """Get a note by ID."""
    if note_id != 1:
        raise NotFoundError('Note does not exist')
    return note


def get_notes() -> Notes:
    """Get a list of notes."""
    return [note]


def create_note(body: Body, done: Done=False) -> Note:
    """Create a new note."""
    return {'note_id': 2,
            'body': body,
            'done': done}


def update_note(note_id: NoteId, body: Body=None, done: Done=None) -> Note:
    """Update an existing note."""
    if note_id != 1:
        raise NotFoundError('Note does not exist')
    new_note = note.copy()
    if body is not None:
        new_note['body'] = body
    if done is not None:
        new_note['done'] = done
    return new_note


def delete_note(note_id: NoteId):
    """Delete an existing note."""
    if note_id != 1:
        raise NotFoundError('Note does not exist')


def status() -> Status:
    return 'Notes API v1.0.0'


# -- mark-app

routes = (
    ('/', (
        get(status),)),
    ('/note/', (
        get(get_notes),
        post(create_note))),
    ('/note/<int:note_id>/', (
        delete(delete_note),
        get(get_note),
        put(update_note))),
)

app = Flask('Doctor example')

api = Api(app)
for route, resource in create_routes(routes):
    api.add_resource(resource, route)

if __name__ == '__main__':
    app.run(debug=True)

# -- mark-end
