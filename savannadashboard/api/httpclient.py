import requests


class HTTPClient(object):
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token

    def get(self, url):
        return requests.get(self.base_url + url,
                            headers={'x-auth-token': self.token})

    def post(self, url, body):
        return requests.post(self.base_url + url, body,
                             headers={'x-auth-token': self.token,
                                      'content-type': 'application/json'})

    def delete(self, url):
        return requests.delete(self.base_url + url,
                               headers={'x-auth-token': self.token})
