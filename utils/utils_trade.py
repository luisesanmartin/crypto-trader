import json
import hashlib
import hmac
import time
import requests
import uuid
from urllib.parse import urlencode
from email.message import EmailMessage
import smtplib

def bs_credentials():

    '''
    '''

    with open('API/credentials_bs.json') as f:
        login_info = json.load(f)

    api_key = login_info['key']
    secret = login_info['secret']

    return api_key, secret

def email_credentials():

    '''
    '''

    with open('API/email-credentials.json') as f:
        email = json.load(f)

    sender = email['sender']
    to = email['to']
    key = email['password']

    return sender, to, key

def send_email(message, subject, sender, to, key):

    '''
    '''

    # Message content
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to
    msg.set_content(message)

    # Credendials and sending
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(sender, key)
    server.send_message(msg)
    server.quit()

    return True

def bs_sell_limit_order(amount, price, market_symbol, credentials=bs_credentials()):

    '''
    Checks account balance
    '''

    api_key = credentials[0]
    secret = credentials[1]
    secret = secret.encode('utf-8')

    # This part is taken from the online example
    timestamp = str(int(round(time.time() * 1000)))
    nonce = str(uuid.uuid4())
    content_type = 'application/x-www-form-urlencoded'
    payload = {
        'amount': amount,
        'price': price
    }
    url_path_query = '/api/v2/sell/{}/'.format(market_symbol)

    payload_string = urlencode(payload)

    message = 'BITSTAMP ' + api_key + \
        'POST' + \
        'www.bitstamp.net' + \
        url_path_query + \
        content_type + \
        nonce + \
        timestamp + \
        'v2' + \
        payload_string
    message = message.encode('utf-8')
    signature = hmac.new(secret, msg=message, digestmod=hashlib.sha256).hexdigest()
    headers = {
        'X-Auth': 'BITSTAMP ' + api_key,
        'X-Auth-Signature': signature,
        'X-Auth-Nonce': nonce,
        'X-Auth-Timestamp': timestamp,
        'X-Auth-Version': 'v2',
        'Content-Type': content_type
    }
    r = requests.post(
        f'https://www.bitstamp.net{url_path_query}',
        headers=headers,
        data=payload_string
    )

    return r

def bs_buy_limit_order(amount, price, market_symbol, credentials=bs_credentials()):

    '''
    Checks account balance
    '''

    api_key = credentials[0]
    secret = credentials[1]
    secret = secret.encode('utf-8')

    # This part is taken from the online example
    timestamp = str(int(round(time.time() * 1000)))
    nonce = str(uuid.uuid4())
    content_type = 'application/x-www-form-urlencoded'
    payload = {
        'amount': amount,
        'price': price
    }
    url_path_query = '/api/v2/buy/{}/'.format(market_symbol)

    payload_string = urlencode(payload)

    message = 'BITSTAMP ' + api_key + \
        'POST' + \
        'www.bitstamp.net' + \
        url_path_query + \
        content_type + \
        nonce + \
        timestamp + \
        'v2' + \
        payload_string
    message = message.encode('utf-8')
    signature = hmac.new(secret, msg=message, digestmod=hashlib.sha256).hexdigest()
    headers = {
        'X-Auth': 'BITSTAMP ' + api_key,
        'X-Auth-Signature': signature,
        'X-Auth-Nonce': nonce,
        'X-Auth-Timestamp': timestamp,
        'X-Auth-Version': 'v2',
        'Content-Type': content_type
    }
    r = requests.post(
        f'https://www.bitstamp.net{url_path_query}',
        headers=headers,
        data=payload_string
    )

    return r