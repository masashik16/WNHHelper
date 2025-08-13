"""OpenID 2.0 - Requesting Authentication

Ref: https://openid.net/specs/openid-authentication-2_0.html#requesting_authentication
"""
from datetime import datetime
from urllib.parse import urlencode
from uuid import uuid4
from zoneinfo import ZoneInfo

from requests import get

from .utils import create_return_to


class Authentication:
    """Authentication initialization

    Note:
        Based on OpenID specification
        https://openid.net/specs/openid-authentication-2_0.html

    Args:
        mode
        ns
        identity
        claimed_id
        return_to
        request_id

    Attributes:
        mode
        ns
        identity
        claimed_id
        return_to
        request_id
    """

    def __init__(self, mode=None, ns=None, identity=None,
                 claimed_id=None, return_to=None, request_id=None):
        self.mode = mode or 'checkid_setup'
        self.ns = ns or 'http://specs.openid.net/auth/2.0'
        self.identity = identity or 'http://specs.openid.net/auth/2.0/' \
                                    'identifier_select'
        self.claimed_id = claimed_id or 'http://specs.openid.net/auth/2.0/' \
                                        'identifier_select'

        self.request_id = request_id or uuid4().hex
        self.return_to = return_to or create_return_to(self.request_id)

    async def authenticate(self, where, request_id=None):
        """Process to authenticate a request based on few data

        On this step, the most important information is the request_id.
        This parameter will allow us to recover this transaction on
        return url.
        """
        request = get(await self.destination(where), allow_redirects=False)
        location = request.headers['Location']
        query = location.split("?")[1]
        location = "/id/accountchoice/?" + query
        return location

    @property
    async def payload(self):
        """Prepare the OpenID payload to authenticate this request"""
        return {
            'openid.mode': self.mode,
            'openid.ns': self.ns,
            'openid.identity': self.identity,
            'openid.claimed_id': self.claimed_id,
            'openid.return_to': self.return_to,
        }

    async def convert(self, payload):
        """Convert the OpenID payload on QueryString format"""
        return urlencode(payload)

    async def destination(self, base):
        """Full destination URL to send the payload"""
        return base + '?' + await self.convert(await self.payload)

    @property
    async def evidence(self):
        """This function could be used to get an evidence about what requests
        were sent.

        Example:
        {
         'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
         'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
         'openid.mode': 'checkid_setup',
         'openid.ns': 'http://specs.openid.net/auth/2.0',
         'openid.return_to': 'https://requestb.in/1e7ing31?request_id=07c52d8bb36c4412a4f7e133be9b08ee',
         'request_id': '07c52d8bb36c4412a4f7e133be9b08ee',
         'timestamp': datetime.datetime(2017, 8, 9, 12, 12, 36, 735736, tzinfo=datetime.timezone.utc)
         }
        """
        evidence = {}
        evidence.update(await self.payload)
        evidence.update({'request_id': await self.request_id})
        evidence.update({'timestamp': datetime.now(ZoneInfo("Asia/Tokyo"))})
        return evidence
