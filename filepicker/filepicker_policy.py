import json
import base64
import hmac
import hashlib


class FilepickerPolicy(object):

    def __init__(self, policy, security_secret):
        self.policy = policy
        self.security_secret = security_secret

    def signature_params(self):
        policy_enc = base64.urlsafe_b64encode(json.dumps(self.policy))
        signature = hmac.new(self.security_secret,
                             policy_enc,
                             hashlib.sha256).hexdigest()
        return {'signature': signature, 'policy': policy_enc}

