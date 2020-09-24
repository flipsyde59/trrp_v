import sqlite3
import pymysql

conn_sqlite = sqlite3.Connection("sqlite.db")
cursor_sqlite = conn_sqlite.execute('select * from libraries')
names_nonorm = [description[0] for description in cursor_sqlite.description]
conn_mysql = pymysql.connect(
    host='localhost',
    user='root',
    password='1234',
    db='trrp_v',
    charset='utf8mb4',
    autocommit=True
)
cursor_mysql = conn_mysql.cursor()
cursor_mysql.execute("show tables")
table_names_norm = [t[0] for t in cursor_mysql.fetchall()]
names_norm = {}
for table in table_names_norm:
    cursor_mysql.execute(f"describe {table}")
    names_norm[table] = [t[0] for t in cursor_mysql.fetchall()]
rows = []

def clear_tables():
    for table in table_names_norm:
        cursor_mysql.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor_mysql.execute(f"truncate table {table}")
        cursor_mysql.execute("SET FOREIGN_KEY_CHECKS = 1")


#def find_diff(row1, row2):
#    diff=[]
#    for i in range(len(row1)):
#        if row1[i]!=row2[i]:
#            diff.append(i)
#    return diff


def find_table(field):
    for i in names_norm.keys():
        for j in names_norm[i]:
            if field == j:
                return i
    return 0

def find_id(field, cell):
    table = find_table(field[0])
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


def func():
    for row in cursor_sqlite:
        ins_t = find_table(names_nonorm[0]) # table in which do insert
        try:
            cursor_mysql.execute(f"insert into {ins_t} ({','.join(names_norm[ins_t][1:])}) values ('{row[0]}','{row[1]}')")
            #libraries
        except pymysql.err.IntegrityError or pymysql.err.ProgrammingError:
            print('Данные не внесены. Ошибка: Такая библиотека уже есть')
        rel_id_lib = find_id(names_norm[ins_t][1:], row[:2])
        ins_t = find_table(names_nonorm[2])
        try:
            cursor_mysql.execute(f"insert into {ins_t} ({','.join(names_norm[ins_t][1:])}) values ('{row[2]}',{rel_id_lib})")
            #departaments
        except pymysql.err.IntegrityError or pymysql.err.ProgrammingError:
            print('Данные не внесены. Ошибка: Такой отдел уже есть')
        rel_id_dep = find_id(names_norm[ins_t][1:], [row[2], rel_id_lib])
        ins_t = find_table(names_nonorm[3])
        try:
            cursor_mysql.execute(f"insert into {ins_t} ({','.join(names_norm[ins_t][1:])}) values ('{row[3]}','{row[4]}',{rel_id_dep})")
            #books
        except pymysql.err.IntegrityError or pymysql.err.ProgrammingError:
            print('Данные не внесены. Ошибка: Такая книга в этом отделе уже есть')
        ins_t = find_table(names_nonorm[6])
        try:
            cursor_mysql.execute(
                f"insert into {ins_t} ({','.join(names_norm[ins_t][1:])}) values ('{row[6]}','{row[7]}',{rel_id_dep})")
            #staffers
        except pymysql.err.IntegrityError or pymysql.err.ProgrammingError:
            print('Данные не внесены. Ошибка: Такой сотруник уже есть')
        ins_t = find_table(names_nonorm[5])
        try:
            cursor_mysql.execute(f"insert into {ins_t} ({','.join(names_norm[ins_t][1:])}) values ('{row[5]}')")
            #janres
        except pymysql.err.IntegrityError or pymysql.err.ProgrammingError:
            print('Данные не внесены. Ошибка: Такой жанр уже есть')
        rel_id_b = find_id(names_nonorm[3:5], row[3:5])
        rel_id_j = find_id([names_nonorm[5]], [row[5]])
        try:
            cursor_mysql.execute(
                f"insert into janres_book (id_j, id_b) values ({rel_id_j},{rel_id_b})")
            #janres_book
        except pymysql.err.IntegrityError or pymysql.err.ProgrammingError:
            print('Данные не внесены. Ошибка: Такой книга уже с таким жанром')
#8 fields in nonorm 0,1 - lib, 2 - dep, 3,4 - book, 5 - janre, 6,7 - staff

clear_tables()
func()

def exporting():
    import xlsxwriter

    workbook = xlsxwriter.Workbook('demo.xlsx',)

    for table in table_names_norm:
        worksheet = workbook.add_worksheet(table)
        worksheet.write_row(0, 0, names_norm[table], workbook.add_format({'bold': True}))
        cursor_mysql.execute(f"select * from {table}")
        rows_insert = [t for t in cursor_mysql.fetchall()]
        for row in rows_insert:
            worksheet.write_row(rows_insert.index(row)+1, 0, row)


    workbook.close()

exporting()

conn_sqlite.close()
conn_mysql.close()
