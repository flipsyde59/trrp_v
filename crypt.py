from Crypto.Cipher import PKCS1_OAEP, DES
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes


# https://www.pycryptodome.org/en/latest/index.html

def generate_keys(bits=2048):
    private_key = RSA.generate(bits)
    public_key = private_key.publickey()
    return private_key, public_key


# region rsa
def rsa_encrypt_message(message, public_key, verbose=False):
    cipher = PKCS1_OAEP.new(public_key)
    encrypted_message = cipher.encrypt(message.encode('utf-8'))
    if verbose:
        print(f'Message: {message}\n was encrypted to\n{encrypted_message}')
    return encrypted_message


def rsa_decrypt_message(encrypted_message, private_key, verbose=False):
    cipher = PKCS1_OAEP.new(private_key)
    decrypted_message = cipher.decrypt(encrypted_message).decode('utf-8')
    if verbose:
        print(f'Message: {encrypted_message}\n was decrypted to\n{decrypted_message}')
    return decrypted_message


# endregion

#region des
def des_encrypt_message(message, key, verbose=False):
    cipher = DES.new(key, DES.MODE_OFB)
    encrypted_message = cipher.encrypt(message.encode('utf-8'))
    if verbose:
        print(f'Message: {message}\n was encrypted to\n{encrypted_message}')
    return encrypted_message, cipher.iv


def des_decrypt_message(encrypted_message, key, iv, verbose=False):
    cipher = DES.new(key, DES.MODE_OFB, iv=iv)
    decrypted_message = cipher.decrypt(encrypted_message).decode('utf-8')
    if verbose:
        print(f'Message: {encrypted_message}\n was decrypted to\n{decrypted_message}')
    return decrypted_message
#endregion

msg = 'Ололо, привет мир'
pr_k, pu_k = generate_keys()
e_m = rsa_encrypt_message(msg, pu_k, True)
d_m = rsa_decrypt_message(e_m, pr_k, True)

key = get_random_bytes(8)
e_m, iv = des_encrypt_message(msg, key, True)
d_m = des_decrypt_message(e_m, key, iv, True)
