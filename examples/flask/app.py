# Note that this file contains some inline comments starting with # --, used to
# generate documentation from this file. You're probably better served reading
# the actual documentation (see Using in Flask in the docs).

import os

from flask import Flask
from flask_restful import Api
from doctor.errors import NotFoundError
from doctor.flask import FlaskRouter

# -- mark-logic

note = {'note_id': 1, 'body': 'Example body', 'done': False}


def get_note(note_id):
    """Get a note by ID."""
    if note_id != 1:
        raise NotFoundError('Note does not exist')
    return note


def get_notes():
    """Get a list of notes."""
    return [note]


def create_note(body, done=False):
    """Create a new note."""
    return {'note_id': 2,
            'body': body,
            'done': done}


def update_note(note_id, body=None, done=None):
    """Update an existing note."""
    if note_id != 1:
        raise NotFoundError('Note does not exist')
    new_note = note.copy()
    if body is not None:
        new_note['body'] = body
    if done is not None:
        new_note['done'] = done
    return new_note


def delete_note(note_id):
    """Delete an existing note."""
    if note_id != 1:
        raise NotFoundError('Note does not exist')


def status():
    return 'Notes API v1.0.0'


# -- mark-app
router = FlaskRouter(os.path.abspath('..'))
routes = router.create_routes('API Status', 'schema.yaml', {
    '/': {
        'get': {
            'logic': status,
        },
    },
})
routes.extend(router.create_routes('Notes (v1)', 'schema.yaml', {
    '/note/': {
        'get': {
            'additional_args': {
                'optional': ['limit', 'offset'],
                'required': ['auth'],
            },
            'logic': get_notes,
            'response': 'notes',
            'title': 'Retrieve List',
        },
        'post': {
            'logic': create_note,
            'response': 'note',
        },
    },
    '/note/<int:note_id>/': {
        'delete': {
            'logic': delete_note,
        },
        'get': {
            'logic': get_note,
            'response': 'note',
        },
        'put': {
            'logic': update_note,
            'response': 'note',
        },
    },
}))

app = Flask('Doctor example')

api = Api(app)
for route, resource in routes:
    api.add_resource(resource, route)

if __name__ == '__main__':
    app.run(debug=True)
