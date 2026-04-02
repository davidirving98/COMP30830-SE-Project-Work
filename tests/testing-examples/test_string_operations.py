import unittest

def capitalize_word(word):
    return word.capitalize()

class TestStringOperations(unittest.TestCase):
    def test_capitalize(self):
        self.assertEqual(capitalize_word("hello"), "Hello")
        self.assertEqual(capitalize_word("world"), "World")
