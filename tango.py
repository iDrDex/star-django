import os
import json
import requests

from funcy import retry


# API_URL = 'https://integration-api.tangocard.com/raas/v1/'
API_URL = 'https://sandbox.tangocard.com/raas/v1/'
PLATFORM_NAME, PLATFORM_KEY = os.environ.get('TANGO_AUTH').split(':')
CUSTOMER = 'stargeo'
IDENTIFIER = 'stargeo'
EMAIL = 'suor.web@gmail.com'

MAX_AMOUNT = 500000

# Sandbox cc_token
CC_TOKEN = '30032544'


@retry(2, requests.ConnectionError)
def make_request(method, url, data=None, silent=False):
    request_func = getattr(requests, method)
    r = request_func(API_URL + url, data=json.dumps(data), auth=(PLATFORM_NAME, PLATFORM_KEY))
    return r.json()


def create_account():
    data = {
        "customer": CUSTOMER,
        "identifier": IDENTIFIER,
        "email": EMAIL,
    }
    return make_request('post', 'accounts', data)

def account_info():
    return make_request('get', 'accounts/stargeo/stargeo')


def cc_register():
    # NOTE: this is test info
    data = {
        "customer": CUSTOMER,
        "account_identifier": IDENTIFIER,
        "client_ip": "55.44.33.22",
        "credit_card": {
            "number": "4111111111111111",
            "security_code": "123",
            "expiration": "2016-11",
            "billing_address": {
                "f_name": "John",
                "l_name": "Doe",
                "address": "1234 Fake St",
                "city": "Springfield",
                "state": "WA",
                "zip": "99196",
                "country": "USA",
                "email": "test@example.com"
            }
        }
    }
    return make_request('post', 'cc_register', data)

def cc_fund(amount):
    # NOTE: this is test info
    data = {
        "customer": CUSTOMER,
        "account_identifier": IDENTIFIER,
        "amount": amount,
        "client_ip": "127.0.0.1",
        "cc_token": CC_TOKEN,
        "security_code": "123"
    }
    return make_request('post', 'cc_fund', data)


def place_order(name=None, email=None, amount=None):
    """
    This call orders a card for somebody
    """
    data = {
        "customer": CUSTOMER,
        "account_identifier": IDENTIFIER,
        "recipient": {
            "name": name,
            "email": email,
        },
        "sku": "TNGO-E-V-STD",
        "amount": amount * 100,  # in cents
        "reward_message": "Thank you for annotating stargeo data.",
        "reward_subject": "Stargeo reward",
        "reward_from": "Stargeo"
    }
    return make_request('post', 'orders', data=data)
