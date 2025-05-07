import unittest

def load_tests(loader, tests, pattern):
    all_tests = unittest.TestSuite()
    all_tests.addTests(load_test(loader, 'cora'))
    all_tests.addTests(load_test(loader, 'common'))

    return all_tests

def load_test(loader, package_name):
    return loader.discover(package_name, pattern='*Test*.py')

if __name__ == "__main__":
    unittest.main()
    



