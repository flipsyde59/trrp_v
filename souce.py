import sqlite3
import requests
import json


conn_sqlite = sqlite3.Connection("sqlite.db")
cursor_sqlite = conn_sqlite.execute('select * from libraries')
names_nonorm = [description[0] for description in cursor_sqlite.description]


def func():
    print(requests.get('http://127.0.0.1:5000/clear-tables').text)
    for row in cursor_sqlite:
        headers = {'Content-type': 'application/json'}
        param_dict = {'names_nonorm': names_nonorm, 'row': row }
        response = requests.post('http://127.0.0.1:5000/post-data', headers=headers, data=json.dumps(param_dict))
        print(response.text)
func()

conn_sqlite.close()
