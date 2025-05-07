import unittest

from cora.client.LoginError import LoginError


class TestLoginError(unittest.TestCase):

    def test_login_error_message(self):
        error = LoginError("Login failed")
        self.assertEqual(str(error), "Login failed")

    def test_login_error_with_original_exception(self):
        original = ValueError("Invalid input")
        error = LoginError("Login failed", original)

        self.assertEqual(str(error), "Login failed")
        self.assertIs(error.original_exception, original)
        self.assertEqual(str(error.original_exception), "Invalid input")


if __name__ == "__main__":
    unittest.main()
