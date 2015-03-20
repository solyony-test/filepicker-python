import json
import base64
import hmac
import hashlib


class FilepickerPolicy(object):

    def __init__(self, policy, app_secret):
        self.policy = policy
        self.app_secret = app_secret

    def signature_params(self):
        policy_enc = base64.urlsafe_b64encode(json.dumps(self.policy).encode('utf-8'))
        signature = hmac.new(self.app_secret.encode('utf-8'),
                             policy_enc,
                             hashlib.sha256).hexdigest()
        return {'signature': signature, 'policy': policy_enc}
