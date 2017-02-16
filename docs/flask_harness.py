from doctor.docs.flask import AutoFlaskHarness


class CustomFlaskHarness(AutoFlaskHarness):

    def setup_app(self, sphinx_app):
        super(CustomFlaskHarness, self).setup_app(sphinx_app)
        self.headers = {'Authorization': 'testtoken'}
        self.header_definitions = {
            'Authorization': 'The auth token for the authenticated user.',
            'X-GeoIp-Country': 'An ISO 3166-1 alpha-2 country code.'
        }
        self.define_header_values('GET', '/note/', {'X-GeoIp-Country': 'US'},
                                  update=True)
