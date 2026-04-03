import unittest
from test_math_operations import TestMathOperations
from test_string_operations import TestStringOperations

# Create a test suite
def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestMathOperations))
    suite.addTest(unittest.makeSuite(TestStringOperations))
    return suite
    
if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(suite())
