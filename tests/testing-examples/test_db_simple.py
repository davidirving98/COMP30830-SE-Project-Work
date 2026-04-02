# test_db_simple.py
import unittest
from db_simple import create_table, insert_user, get_user

class TestDatabase(unittest.TestCase):

    def setUp(self):
        """Set up database before each test"""
        create_table()  # Ensure table exists before tests

    def test_insert_and_retrieve_user(self):
        """Test inserting and retrieving a user"""
        insert_user("Alice")  # Insert user into the database
        user = get_user("Alice")  # Retrieve user

        # Check if the user was retrieved successfully
        self.assertIsNotNone(user)  # Ensure user exists
        self.assertEqual(user[1], "Alice")  # Check if name matches

if __name__ == "__main__":
    unittest.main()
