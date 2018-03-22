# Note that this file contains some inline comments starting with # --, used to
# generate documentation from this file. You're probably better served reading
# the actual documentation (see Using in Flask in the docs).

from flask import Flask
from flask_restful import Api
from doctor.errors import NotFoundError
from doctor.flask import create_routes
from doctor.response import Response
from doctor.routing import Route, get, post, put, delete
# -- mark-types
from doctor import types


# doctor provides helper functions to easily define simple types.
Body = types.string('Note body', example='body')
Done = types.boolean('Marks if a note is done or not.', example=False)
NoteId = types.integer('Note ID', example=1)
Status = types.string('API status')
NoteType = types.enum('The type of note', enum=['quick', 'detailed'],
                      example='quick')
NoteTypes = types.array('An array of note types', items=NoteType)


# You can also inherit from type classes to create more complex types.
class Note(types.Object):
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


Notes = types.array('Array of notes', items=Note, example=[Note.example])

# -- mark-logic

note = {'note_id': 1, 'body': 'Example body', 'done': True}


def example_array_and_object(note_types: NoteTypes, a_note: Note):
    """Example signature that contains an object and an array."""
    return {}


# Note the type annotations on this function definition. This tells Doctor how
# to parse and validate parameters for routes attached to this logic function.
# The return type annotation will validate the response conforms to an
# expected definition in development environments.  In non-development
# environments a warning will be logged.
def get_note(note_id: NoteId, note_type: NoteType) -> Note:
    """Get a note by ID."""
    if note_id != 1:
        raise NotFoundError('Note does not exist')
    return note


def get_notes() -> Notes:
    """Get a list of notes."""
    return [note]


def create_note(body: Body, done: Done=False) -> Response[Note]:
    """Create a new note."""
    return Response({
        'note_id': 2,
        'body': body,
        'done': done,
    }, headers={'X-Foo': 'Bar'})


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


# -- mark-routes

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
    Route('/example/list-obj/', methods=(
        get(example_array_and_object),), heading='Z'
    ),
)

# -- mark-app

app = Flask('Doctor example')

api = Api(app)
for route, resource in create_routes(routes):
    api.add_resource(resource, route)

if __name__ == '__main__':
    app.run(debug=True)

# -- mark-end
