# Note that this file contains some inline comments starting with # --, used to
# generate documentation from this file. You're probably better served reading
# the actual documentation (see Using in Flask in the docs).

from flask import Flask
from flask_restful import Api
from doctor.errors import NotFoundError
from doctor.routing import Route, create_routes, get, post, put, delete
from doctor.types import array, boolean, enum, integer, string, Object

# -- mark-types

Body = string('Note body', example='body')
Done = boolean('Marks if a note is done or not.', example=False)
NoteId = integer('Note ID', example=1)
Status = string('API status')
NoteType = enum('The type of note', enum=['quick', 'detailed'], example='quick')


class Note(Object):
    description = 'A note object'
    additional_properties = False
    properties = {
        'note_id': NoteId,
        'body': Body,
        'done': Done,
    }
    required = ['body', 'done', 'note_id']
    example = {
        'body': 'Example Body',
        'done': True,
        'note_id': 1,
    }


Notes = array('Array of notes', items=Note, example=[Note.example])

# -- mark-logic

note = {'note_id': 1, 'body': 'Example body', 'done': True}


def get_note(note_id: NoteId, note_type: NoteType) -> Note:
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
    Route('/', methods=(
        get(status),), heading='API Status'),
    Route('/note/', methods=(
        get(get_notes, title='Retrieve List'),
        post(create_note)), handler_name='NoteListHandler', heading='Notes (v1)'
    ),
    Route('/note/<int:note_id>/', methods=(
        delete(delete_note),
        get(get_note),
        put(update_note)), heading='Notes (v1)'
    ),
)

app = Flask('Doctor example')

api = Api(app)
for route, resource in create_routes(routes):
    api.add_resource(resource, route)

if __name__ == '__main__':
    app.run(debug=True)

# -- mark-end
