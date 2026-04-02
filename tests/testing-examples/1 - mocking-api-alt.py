from unittest.mock import patch, Mock
import unittest

def get_user_data():
    import requests
    response = requests.get("https://api.example.com/user")
    return response.json()

class TestAPI(unittest.TestCase):
    
    @patch("requests.get")  # Mock requests.get
    def test_get_user_data(self, mock_get):

        # Set the mock response as the return value of requests.get()
        mock_get.return_value.json.return_value = {"name": "John Doe"}

        # Call the function
        result = get_user_data()

        # Assert the expected result
        self.assertEqual(result, {"name": "John Doe"})
        
if __name__ == "__main__":
    unittest.main()

