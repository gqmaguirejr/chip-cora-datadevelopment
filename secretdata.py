import requests
class  SecretData:
    authToken = None
    @staticmethod
    def get_authToken(system):
        if SecretData.authToken != None:
#            print("returning old token")
            return SecretData.authToken
        try:
            getAuthTokenUrl = SecretData.token_url[system]+'login/rest/apptoken'
            appToken = 'divaAdmin@cora.epc.ub.uu.se\n49ce00fb-68b5-4089-a5f7-1c225d3cf156'
            json_headers = {'Content-Type':'application/vnd.uub.login', 'Accept':'application/vnd.uub.authentication+json'}
            response = requests.post(getAuthTokenUrl, data=appToken, headers=json_headers)
            response_json = response.json()
            authToken = response_json['authentication']['data']['children'][0]['value']
            SecretData.authToken = authToken
            return(authToken)
        except requests.exceptions.JSONDecodeError:
            print("Could not decode JSON response. Raw response:")
            print(response.text)
#            raise
            return SecretData.get_authToken(system)
        except Exception as e:
            print("Error getting authToken:", e)
            raise
    token_url = {
    'local': 'http://localhost:8182/',
    'preview': 'https://cora.epc.ub.uu.se/diva/',
    'mig': 'https://mig.diva-portal.org/',
    'pre': 'https://pre.diva-portal.org/',
}