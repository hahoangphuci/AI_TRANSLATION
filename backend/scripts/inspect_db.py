import sqlite3
p = r'D:\LuanVanToNghiep\instance\translation.db'
print('exists', __import__('os').path.exists(p))
try:
    c = sqlite3.connect(p)
    cur = c.cursor()
    cur.execute("PRAGMA table_info('translation')")
    print(cur.fetchall())
    c.close()
except Exception as e:
    print('err', e)
