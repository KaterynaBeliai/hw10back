import db

with open("schema.sql", encoding="utf-8") as f:
    sql = f.read()

db.execute(sql)
