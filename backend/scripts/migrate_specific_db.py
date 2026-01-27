import sqlite3
p = r'D:\LuanVanToNghiep\instance\translation.db'
print('DB path:', p)
if not __import__('os').path.exists(p):
    print('not found')
    raise SystemExit(1)
con = sqlite3.connect(p)
try:
    cur = con.cursor()
    cur.execute('PRAGMA foreign_keys=OFF;')
    cur.execute('BEGIN TRANSACTION;')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS translation_new (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        original_text TEXT,
        translated_text TEXT,
        source_lang VARCHAR(10),
        target_lang VARCHAR(10),
        file_path VARCHAR(500),
        created_at DATETIME
    );
    ''')
    cur.execute('''
    INSERT INTO translation_new (id, user_id, original_text, translated_text, source_lang, target_lang, file_path, created_at)
    SELECT id, user_id, original_text, translated_text, source_lang, target_lang, file_path, created_at FROM translation;
    ''')
    cur.execute('DROP TABLE translation;')
    cur.execute('ALTER TABLE translation_new RENAME TO translation;')
    cur.execute('COMMIT;')
    cur.execute('PRAGMA foreign_keys=ON;')
    print('Migration completed for specific DB')
finally:
    con.close()
