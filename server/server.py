from flask import Flask, request, abort, jsonify
import pymysql
from base64 import b64decode
from Crypto.PublicKey import RSA
import json

app = Flask(__name__)
with open("server_config.ini", "r") as read_file:
    config = json.load(read_file)
conn_mysql = pymysql.connect(host=config["host"], user=config["user"], password=config["password"], db=config["db"], charset='utf8mb4', autocommit=True)


@app.route('/get-public-key', methods=['GET'])
def get_public_key():
    from Crypto.PublicKey import RSA
    private_key = RSA.generate(2048)
    export_key = private_key.export_key()
    file_out = open(f"rsa_key.pem", "wb")
    file_out.write(export_key)
    file_out.close()
    public_key = private_key.publickey().export_key()
    return public_key, 200


def rsa_decrypt_message(msg):
    from Crypto.Cipher import PKCS1_OAEP
    private_key = RSA.import_key(open(f"rsa_key.pem").read())
    cipher = PKCS1_OAEP.new(private_key)
    return cipher.decrypt(b64decode(msg))


def des_decrypt_message(encrypted_message, iv, verbose=False):
    from Crypto.Cipher import DES
    file_in = open("des_key.bin", "rb")
    key = file_in.read()
    file_in.close()
    cipher = DES.new(key, DES.MODE_OFB, iv=iv)
    decrypted_message = cipher.decrypt(b64decode(encrypted_message))
    if verbose:
        print(f'Message: {encrypted_message}\n was decrypted to\n{decrypted_message}')
    return decrypted_message


@app.route('/post-symetric-key', methods=['POST'])
def post_symetric_key():
    if not request.json or not 'key' in request.json:
        abort(400)
    encrypted_key = request.json.get('key')
    decrypted_key = rsa_decrypt_message(encrypted_key)
    file_out = open(f"des_key.bin", "wb")
    file_out.write(decrypted_key)
    file_out.close()
    return 'success get key', 200


@app.route('/del-keys-files', methods=['GET'])
def del_keys_files():
    import os
    file = f"rsa_key.pem"
    if os.path.isfile(file):
        os.remove(file)
    file = f"des_key.bin"
    if os.path.isfile(file):
        os.remove(file)
    return "files deleted", 200


def tables(cursor_mysql):
    cursor_mysql.execute("show tables")
    table_names_norm = [t[0] for t in cursor_mysql.fetchall()]
    names_norm = {}
    for table in table_names_norm:
        cursor_mysql.execute(f"describe {table}")
        names_norm[table] = [t[0] for t in cursor_mysql.fetchall()]
    return names_norm


@app.route('/get-tables', methods=['GET'])
def get_tables():
    cursor_mysql=conn_mysql.cursor()
    names_tables=tables(cursor_mysql)
    return names_tables, 200


@app.route('/clear-tables', methods=['GET'])
def clear_tables():
    cursor_mysql = conn_mysql.cursor()
    cursor_mysql.execute("show tables")
    table_names_norm = [t[0] for t in cursor_mysql.fetchall()]
    for table in table_names_norm:
        cursor_mysql.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor_mysql.execute(f"truncate table {table}")
        cursor_mysql.execute("SET FOREIGN_KEY_CHECKS = 1")
    return "data clearned", 200


def find_table(field, names_norm):
    for i in names_norm.keys():
        for j in names_norm[i]:
            if field == j:
                return i
    return 0

def find_id(field, cell, cursor_mysql, names_norm):
    table = find_table(field[0], names_norm)
    if table!=0:
        if len(cell)>1:
            if type(cell[1])==int:
                cursor_mysql.execute(f"select id from {table} where {field[0]}='{cell[0]}' and {field[1]}={cell[1]}")
            else:
                cursor_mysql.execute(
                    f"select id from {table} where {field[0]}='{cell[0]}' and {field[1]}='{cell[1]}'")
        else:
            if type(cell[0])==int:
                cursor_mysql.execute(f"select id from {table} where {field[0]}={cell[0]}")
            else:
                cursor_mysql.execute(f"select id from {table} where {field[0]}='{cell[0]}'")
    tmp = cursor_mysql.fetchall()[0][0]
    result = tmp if tmp else 0
    return result


@app.route('/post-data', methods=['POST'])
def post_data():
    if not request.json or not 'key' in request.json or not 'msg' in request.json:
        abort(400)
    enc_key = request.json.get('key')
    dec_key = rsa_decrypt_message(enc_key)
    enc_msg = request.json.get('msg')
    import json
    tmp = des_decrypt_message(enc_msg, dec_key)
    dec_msg = json.loads(tmp)
    names_nonorm = dec_msg.get('names_nonorm')
    row = dec_msg.get('row')
    cursor_mysql = conn_mysql.cursor()
    names_norm = tables(cursor_mysql)
    ins_t = find_table(names_nonorm[0], names_norm)  # table in which do insert
    try:
        cursor_mysql.execute(f"insert into {ins_t} ({','.join(names_norm[ins_t][1:])}) values ('{row[0]}','{row[1]}')")
        # libraries
    except pymysql.err.IntegrityError or pymysql.err.ProgrammingError:
        pass
        #print('Данные не внесены. Ошибка: Такая библиотека уже есть')
    rel_id_lib = find_id(names_norm[ins_t][1:], row[:2], cursor_mysql, names_norm)
    ins_t = find_table(names_nonorm[2], names_norm)
    try:
        cursor_mysql.execute(
            f"insert into {ins_t} ({','.join(names_norm[ins_t][1:])}) values ('{row[2]}',{rel_id_lib})")
        # departaments
    except pymysql.err.IntegrityError or pymysql.err.ProgrammingError:
        pass
        #print('Данные не внесены. Ошибка: Такой отдел уже есть')
    rel_id_dep = find_id(names_norm[ins_t][1:], [row[2], rel_id_lib], cursor_mysql, names_norm)
    ins_t = find_table(names_nonorm[3], names_norm)
    try:
        cursor_mysql.execute(
            f"insert into {ins_t} ({','.join(names_norm[ins_t][1:])}) values ('{row[3]}','{row[4]}',{rel_id_dep})")
        # books
    except pymysql.err.IntegrityError or pymysql.err.ProgrammingError:
        pass
        #print('Данные не внесены. Ошибка: Такая книга в этом отделе уже есть')
    ins_t = find_table(names_nonorm[6], names_norm)
    try:
        cursor_mysql.execute(
            f"insert into {ins_t} ({','.join(names_norm[ins_t][1:])}) values ('{row[6]}','{row[7]}',{rel_id_dep})")
        # staffers
    except pymysql.err.IntegrityError or pymysql.err.ProgrammingError:
        pass
        #print('Данные не внесены. Ошибка: Такой сотруник уже есть')
    ins_t = find_table(names_nonorm[5], names_norm)
    try:
        cursor_mysql.execute(f"insert into {ins_t} ({','.join(names_norm[ins_t][1:])}) values ('{row[5]}')")
        # janres
    except pymysql.err.IntegrityError or pymysql.err.ProgrammingError:
        pass
        #print('Данные не внесены. Ошибка: Такой жанр уже есть')
    rel_id_b = find_id(names_nonorm[3:5], row[3:5], cursor_mysql, names_norm)
    rel_id_j = find_id([names_nonorm[5]], [row[5]], cursor_mysql, names_norm)
    try:
        cursor_mysql.execute(
            f"insert into janres_book (id_j, id_b) values ({rel_id_j},{rel_id_b})")
        # janres_book
    except pymysql.err.IntegrityError or pymysql.err.ProgrammingError:
        pass
        #print('Данные не внесены. Ошибка: Такая книга уже с таким жанром')
    return 'insert success', 200



if __name__ == '__main__':
    app.run(debug=True, port=5000)