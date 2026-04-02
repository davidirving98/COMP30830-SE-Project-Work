# test_my_module.py
import unittest
from unittest.mock import patch
from my_module import process_number

class TestMocking(unittest.TestCase):
    
    @patch("my_module.get_number")  # Mocking get_number()
    def test_process_number(self, mock_get_number):
        # Tell the mock to return 100 instead of 42
        mock_get_number.return_value = 100

        # Call process_number()
        result = process_number()

        # The expected result should be 100 * 2 = 200
        self.assertEqual(result, 200)

if __name__ == "__main__":
    unittest.main()
