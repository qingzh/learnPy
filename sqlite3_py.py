# -*- coding: utf-8 -*-

import sqlite3

# connect(':memory:') to create a database in RAM
conn = sqlite3.connect('E:/sql/test.db')

c = conn.cursor()

table_name = 'api_cases'
CREATE_TABLE = '''CREATE TABLE IF NOT EXISTS %s (id INTEGER PRIMARY KEY AUTOINCREMENT, casename varchar(32) unique not null, description text, request text not null default '', expect_res text not null default '', exact_res text, status boolean, last_exec_time datetime default current_timestamp)''' % table_name
# Create table
c.execute(CREATE_TABLE)

# Insert a row of data
c.execute(
    "INSERT INTO %s (casename, description, request, expect_res) VALUES ('case001', '测试用例：测试用','{}','{}')" % table_name)

# Save (commit) the changes
conn.commit()

# We can also close the connection if we are done with it.
# Just be sure any changes have been committed or they will be lost.
conn.close()

