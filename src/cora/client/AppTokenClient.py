from cora.client.LoginError import LoginError


class  AppTokenClient:
    LOGIN_HEADERS = {'Content-Type':'application/vnd.uub.login',
                      'Accept':'application/vnd.uub.authentication+json'}
    LOGIN_RENEW_BEFORE_EXPIRES_TIME = 20
    CREATE = 201
    OK = 200
    
    def __init__(self, dependencies):
        self.time = dependencies["time"]
        self.threading = dependencies["threading"]
        self.requests = dependencies["requests"]

    def login(self, login_spec):
        try:
            self.try_to_login(login_spec)
        except Exception as e:
            raise LoginError("Login failed", e) from e

    def try_to_login(self, login_spec):
        response = self.login_using_spec(login_spec)
        self._handle_login_response(response)

    def _handle_login_response(self, response):
        if response.status_code not in (AppTokenClient.CREATE, AppTokenClient.OK):
            raise LoginError(f"Login failed: Expected 201, got {response.status_code}")
        self.schedule_token_refresh(response)
        self.auth_token = self.get_child_from_response_data(response, "token")
        
    def login_using_spec(self, login_spec):
        combined = self.create_combined_login_id_app_token(login_spec)
        login_url = login_spec["login_url"]
        return self.requests.post(login_url, data=combined, headers=AppTokenClient.LOGIN_HEADERS)

    def create_combined_login_id_app_token(self, login_spec):
        app_token = login_spec["app_token"]
        login_id = login_spec["login_id"]
        return login_id + '\n' + app_token
    
    def schedule_token_refresh(self, response):
        valid_until = int(self.get_child_from_response_data(response, "validUntil"))
        delay = self.calculate_delay_based_on_valid_until(valid_until)
        renew = self.get_renew_from_response(response)
        timer = self.threading.Timer
        self.timer = timer(delay, self._get_new_token, args=[renew])
        self.timer.start()
        
    def calculate_delay_based_on_valid_until(self, valid_until):
        valid_until_sec = valid_until / 1000
        delay = valid_until_sec - self.time.time() - AppTokenClient.LOGIN_RENEW_BEFORE_EXPIRES_TIME
        return delay

    def _get_new_token(self, renew):
        url = renew["url"]
        accept = renew["accept"]
        headers = {"Accept": accept,
                   "authToken": self.get_auth_token()}
        response = self.requests.post(url, headers=headers)
        self._handle_login_response(response)
    
    def get_renew_from_response(self, response):
        response_json = response.json()
        return response_json["authentication"]["actionLinks"]["renew"]
    
    def get_child_from_response_data(self, response, name_in_data):
        response_json = response.json()
        children = response_json["authentication"]["data"]["children"]
        for child in children:
            if child["name"] == name_in_data:
                return child["value"]
        
    def get_auth_token(self):
        return self.auth_token
