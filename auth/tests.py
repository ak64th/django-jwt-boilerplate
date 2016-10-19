from __future__ import unicode_literals

import simplejson as json
from django.test import SimpleTestCase
from db import users

JSON_CONTENT = 'application/json'


class AuthenticationTest(SimpleTestCase):
    def test_homepage(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, 'OK')

    def test_jwt_required_decorator_with_valid_request_current_identity(self):
        user = users[0]
        data = {
            'credential': {
                'username': user.username,
                'password': user.password
            },
            'type': 'username'
        }
        resp = self.client.post('/auth/login/', json.dumps(data), content_type=JSON_CONTENT)
        self.assertEqual(resp.status_code, 200)
        resp_data = json.loads(resp.content)
        token = resp_data['access_token']
        self.assertTrue(token)
        resp = self.client.get('/auth/info/', HTTP_AUTHORIZATION='Bearer ' + token)
        self.assertEqual(resp.status_code, 200)
        resp_data = json.loads(resp.content)
        self.assertEqual(resp_data['username'], user.username)
        self.assertEqual(resp_data['id'], user.id)
