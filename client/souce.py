import sqlite3
import requests
import json


conn_sqlite = sqlite3.Connection("client/sqlite.db")
cursor_sqlite = conn_sqlite.execute('select * from libraries')
names_nonorm = [description[0] for description in cursor_sqlite.description]


def rsa_encrypt_message(message, key, verbose=False):
    from Crypto.Cipher import PKCS1_OAEP
    from Crypto.PublicKey import RSA
    public_key = RSA.import_key(key)
    cipher = PKCS1_OAEP.new(public_key)
    encrypted_message = cipher.encrypt(message)
    if verbose:
        print(f'Message: {message}\n was encrypted to\n{encrypted_message}')
    return encrypted_message


def des_encrypt_message(message, key, verbose=False):
    from Crypto.Cipher import DES
    cipher = DES.new(key, DES.MODE_OFB)
    encrypted_message = cipher.encrypt(message.encode('utf-8'))
    if verbose:
        print(f'Message: {message}\n was encrypted to\n{encrypted_message}')
    return encrypted_message, cipher.iv


def func():
    response = requests.get('http://127.0.0.1:5000/get-public-key')
    public_key = response.content
    from Crypto.Random import get_random_bytes
    key = get_random_bytes(8)
    enc_key = rsa_encrypt_message(key, public_key)
    headers = {'Content-type': 'application/json'}
    from base64 import b64encode
    print(requests.post('http://127.0.0.1:5000/post-symetric-key', headers=headers,
                             data=json.dumps({'key': b64encode(enc_key).decode('utf-8')})).text)
    print(requests.get('http://127.0.0.1:5000/clear-tables').text)
    for row in cursor_sqlite:
        msg = json.dumps({'names_nonorm': names_nonorm, 'row': row })
        encrypt_msg, iv = des_encrypt_message(msg, key)
        encrypt_iv = rsa_encrypt_message(iv, public_key)
        response = requests.post('http://127.0.0.1:5000/post-data', headers=headers, data=json.dumps({'key':b64encode(encrypt_iv).decode('utf-8'), 'msg':b64encode(encrypt_msg).decode('utf-8')}))
    print(requests.get('http://127.0.0.1:5000/del-keys-files').text)


func()


conn_sqlite.close()
