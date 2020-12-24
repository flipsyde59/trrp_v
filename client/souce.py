import sqlite3
import requests
import json
from base64 import b64encode


conn_sqlite = sqlite3.Connection("sqlite.db")
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


def monobit(bin_data: str):
    import math
    count = 0
    for char in bin_data:
        if char == '0':
            count -= 1
        else:
            count += 1
    sobs = count / math.sqrt(len(bin_data))
    p_val = math.erfc(math.fabs(sobs) / math.sqrt(2))
    return p_val

def bin_str(s):
    return  ''.join(format(ord(i), 'b') for i in s)


def func():
    response = requests.get(f'http://{config["host"]}:{config["port"]}/get-public-key')
    public_key = response.content
    from Crypto.Random import get_random_bytes
    key = get_random_bytes(8)
    enc_key = rsa_encrypt_message(key, public_key)
    headers = {'Content-type': 'application/json'}
    print(requests.post(f'http://{config["host"]}:{config["port"]}/post-symetric-key', headers=headers,
                             data=json.dumps({'key': b64encode(enc_key).decode('utf-8')})).text)
    print(requests.get(f'http://{config["host"]}:{config["port"]}/clear-tables').text)
    for row in cursor_sqlite:
        msg = json.dumps({'names_nonorm': names_nonorm, 'row': row })
        encrypt_msg, iv = des_encrypt_message(msg, key)
        encrypt_iv = rsa_encrypt_message(iv, public_key)
        print('сообщение до шифрования: ', monobit(bin_str(msg)))
        print('сообщение после шифрования: ', monobit(bin_str(b64encode(encrypt_msg).decode('utf-8'))))
        print('ключ до шифрования: ', monobit(bin_str(b64encode(iv).decode('utf-8'))))
        print('ключ после шифрования: ', monobit(bin_str(b64encode(encrypt_iv).decode('utf-8'))))
        response = requests.post(f'http://{config["host"]}:{config["port"]}/post-data', headers=headers, data=json.dumps({'key':b64encode(encrypt_iv).decode('utf-8'), 'msg':b64encode(encrypt_msg).decode('utf-8')}))
        print(response.text)
    print(requests.get(f'http://{config["host"]}:{config["port"]}/del-keys-files').text)


def soc_func():
    import socket

    sock = socket.socket()
    sock.connect((config["host"], config["port"]))
    sock.send(b'get-public-key')
    public_key = sock.recv(1024)
    sock.send(b'post-symetric-key')
    from Crypto.Random import get_random_bytes
    key = get_random_bytes(8)
    enc_key = rsa_encrypt_message(key, public_key)
    sock.send(b64encode(enc_key))
    resp = sock.recv(1024)
    print(resp.decode('utf-8'))
    sock.send(b'clear-tables')
    resp = sock.recv(1024)
    print(resp.decode('utf-8'))
    for row in cursor_sqlite:
        sock.send(b'post-data')
        msg = json.dumps({'names_nonorm': names_nonorm, 'row': row})
        encrypt_msg, iv = des_encrypt_message(msg, key)
        encrypt_iv = rsa_encrypt_message(iv, public_key)
        sock.send(b64encode(encrypt_iv))
        sock.send(b64encode(encrypt_msg))
        resp = sock.recv(1024)
        print(resp.decode('utf-8'))
    sock.send(b'del-keys-files')
    resp = sock.recv(1024)
    print(resp.decode('utf-8'))

    sock.close()

with open("config.ini", "r") as read_file:
    config = json.load(read_file)
func()
#soc_func()

conn_sqlite.close()
