import unittest

from cora.client.AppTokenClient import AppTokenClient
from unittest.mock import MagicMock
from cora.client.LoginError import LoginError


class TestAppTokenClient(unittest.TestCase):

    def setUp(self):
        self.mock_time = MagicMock()
        self.mock_threading = MagicMock()
        self.mock_requests = MagicMock()

        self.login_url = 'https://cora.epc.ub.uu.se/diva/login/rest/apptoken'
        self.login_id = 'divaAdmin@cora.epc.ub.uu.se'
        self.app_token = '49ce00fb-68b5-4089-a5f7-1c225d3cf156'
        
        self.dependencies = {"requests": self.mock_requests,
                             "time": self.mock_time,
                             "threading": self.mock_threading}
        self.login_spec = {"login_url": self.login_url,
                "login_id": self.login_id,
                "app_token": self.app_token}
        self.client = AppTokenClient(self.dependencies)

    def tearDown(self):
        pass
    
    def test_init(self):
        self.assertIsNotNone(self.client)
    
    def test_login(self):
        self.set_up_response_answer(201, self.get_ok_login_answer()) 
        login_headers = {'Content-Type':'application/vnd.uub.login',
                         'Accept':'application/vnd.uub.authentication+json'}
        
        self.client.login(self.login_spec)
        
        combined_login_id_app_token = self.login_id + '\n' + self.app_token
        self.mock_requests.post.assert_called_once_with(
            self.login_url, data=combined_login_id_app_token, headers=login_headers)
    
    def test_login_schedule_token_refresh(self):
        self.set_up_response_answer(201, self.get_ok_login_answer())
        self.set_up_mock_time_for_ten_minutes_before_renew_until()
        mock_timer = MagicMock()
        self.mock_threading.Timer.return_value = mock_timer
        login_renew_before_expires_time = 20
        
        self.client.login(self.login_spec)
 
        ten_minutes_minus_20_seconds = 10 * 60 - login_renew_before_expires_time
        self.mock_threading.Timer.assert_called_once_with(
            ten_minutes_minus_20_seconds,
            self.client._get_new_token,
            args=[self.get_ok_login_answer()["authentication"]["actionLinks"]["renew"]])
        mock_timer.start.assert_called_once()
    
    def test__get_new_token(self):
        self.set_up_response_answer(200, self.get_ok_login_answer())
        captured = {}

        def fake_handle(captured_response):
            captured["response"] = captured_response

        self.client.get_auth_token = lambda: "fakeToken"
        self.client._handle_login_response = fake_handle
        
        renew = self.get_ok_login_answer()["authentication"]["actionLinks"]["renew"]
        url = renew["url"]
        accept = renew["accept"]
        auth_token = "fakeToken"
        headers = {"Accept": accept, "authToken": auth_token}
        
        self.client._get_new_token(renew)
        
        self.mock_requests.post.assert_called_once_with(url, headers=headers)
        self.assertEqual(captured["response"], self.mock_requests.post.return_value)
    
    def test_get_auth_token_create(self):
        self.set_up_response_answer(201, self.get_ok_login_answer()) 

        self.client.login(self.login_spec)

        self.assertEqual(self.client.get_auth_token(), '5545e11c-7e90-4289-87d0-155bb2078f85')

    def test_get_auth_token_renew(self):
        self.set_up_response_answer(200, self.get_ok_login_answer()) 

        self.client.login(self.login_spec)

        self.assertEqual(self.client.get_auth_token(), '5545e11c-7e90-4289-87d0-155bb2078f85')
    
    def test_get_auth_token_response_code_not_201(self):
        self.set_up_response_answer(401, 'not logged in') 
        
        with self.assertRaises(LoginError) as context:
            self.client.login(self.login_spec)
        
        login_error = context.exception
        self.assertIsInstance(login_error, LoginError)
        self.assertEqual("Login failed", str(login_error))
        
        original_exception = login_error.original_exception
        self.assertIsInstance(original_exception, LoginError)
        self.assertEqual(str(original_exception), "Login failed: Expected 201, got 401")
        self.assertIsInstance(login_error.__cause__, LoginError)
        
    def test_get_auth_token_answer_not_parsable_error(self):
        self.set_up_response_answer(201, 'not ok login') 
        
        with self.assertRaises(LoginError) as context:
            self.client.login(self.login_spec)
        
        login_error = context.exception
        self.assertIsInstance(login_error, LoginError)
        self.assertEqual("Login failed", str(login_error))
        
        original_exception = login_error.original_exception
        self.assertIsInstance(original_exception, TypeError)
        self.assertEqual(str(original_exception), "string indices must be integers, not 'str'")
        self.assertIsInstance(login_error.__cause__, TypeError)
    
    def set_up_response_answer(self, status_code, login_answer):
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = login_answer
        self.mock_requests.post.return_value = mock_response
    
    def set_up_mock_time_for_ten_minutes_before_renew_until(self):
        time_from_valid_until_in_response = 1744703967172
        ten_minutes = 10
        valid_until_minus_ten_minutes = time_from_valid_until_in_response - ten_minutes * 60 * 1000
        valid_until_minus_ten_minutes_sec = valid_until_minus_ten_minutes / 1000
        self.mock_time.time.return_value = valid_until_minus_ten_minutes_sec
       
    def get_ok_login_answer(self):
        return {
            "authentication": {
                "data": {
                    "children": [
                        {
                            "name": "token",
                            "value": "5545e11c-7e90-4289-87d0-155bb2078f85"
                        },
                        {
                            "name": "validUntil",
                            "value": "1744703967172"
                        },
                        {
                            "name": "renewUntil",
                            "value": "1744789767172"
                        },
                        {
                            "name": "userId",
                            "value": "161616"
                        },
                        {
                            "name": "loginId",
                            "value": "divaAdmin@cora.epc.ub.uu.se"
                        },
                        {
                            "name": "firstName",
                            "value": "DiVA"
                        },
                        {
                            "name": "lastName",
                            "value": "Admin"
                        },
                        {
                            "repeatId": "1",
                            "children": [
                                {
                                    "name": "linkedRecordType",
                                    "value": "permissionUnit"
                                },
                                {
                                    "name": "linkedRecordId",
                                    "value": "test1"
                                }
                            ],
                            "name": "permissionUnit"
                        },
                        {
                            "repeatId": "2",
                            "children": [
                                {
                                    "name": "linkedRecordType",
                                    "value": "permissionUnit"
                                },
                                {
                                    "name": "linkedRecordId",
                                    "value": "test2"
                                }
                            ],
                            "name": "permissionUnit"
                        }
                    ],
                    "name": "authToken"
                },
                "actionLinks": {
                    "renew": {
                        "requestMethod": "POST",
                        "rel": "renew",
                        "url": "http://localhost:38182/login/rest/authToken/39d029d1-1262-42a7-82df-a0e64daeb3ec",
                        "accept": "application/vnd.uub.authentication+json"
                    },
                    "delete": {
                        "requestMethod": "DELETE",
                        "rel": "delete",
                        "url": "http://localhost:38182/login/rest/authToken/39d029d1-1262-42a7-82df-a0e64daeb3ec"
                    }
                }
            }
        }


if __name__ == "__main__":
    unittest.main()
