import unittest
from flask import Flask
from app import app  # Assuming the Flask app is in app.py

class FlaskTestCase(unittest.TestCase):
    
    def setUp(self):
        # Set up the test client
        self.app = app.test_client()
        self.app.testing = True

    def test_hello(self):
        # Simulate a GET request to the '/hello' route
        response = self.app.get('/hello')
        # Assert the HTTP status code and response data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Hello, World!')

if __name__ == '__main__':
    unittest.main()
