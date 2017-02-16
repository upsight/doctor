import unittest


class TestCase(unittest.TestCase):

    maxDiff = None

    def shortDescription(self):
        # Do not show first line of the docstring as a test description
        return None
