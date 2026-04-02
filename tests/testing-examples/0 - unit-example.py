import unittest

# Function to be tested
def add(a, b):
    return a + b

# Test case class
class TestMathFunctions(unittest.TestCase):
    
    def test_add(self):
        # Test that addition works
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(add(-1, 1), 0)
        self.assertEqual(add(0, 0), 0)

if __name__ == '__main__':
    unittest.main()
