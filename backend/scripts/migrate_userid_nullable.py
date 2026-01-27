import sqlite3
import os

# Try to locate the translation.db file by searching parent folders
candidate = None
here = os.path.abspath(os.path.dirname(__file__))
for i in range(4):
    cand = os.path.abspath(os.path.join(here, *(['..'] * i), 'instance', 'translation.db'))
    if os.path.exists(cand):
        candidate = cand
        break
# fallback: look for any translation.db in known upper-level path
if not candidate:
    alt = os.path.abspath(os.path.join(here, *(['..'] * 3), 'instance', 'translation.db'))
    if os.path.exists(alt):
        candidate = alt
if not candidate:
    # try root workspace location
    workspace_root = os.path.abspath(os.path.join(here, '..', '..'))
    possible = os.path.join(workspace_root, 'instance', 'translation.db')
    if os.path.exists(possible):
        candidate = possible

# explicit system-wide check (common path on this machine)
if not candidate:
    alt2 = os.path.abspath(os.path.join(os.sep, 'd:\\LuanVanToNghiep', 'instance', 'translation.db'))
    if os.path.exists(alt2):
        candidate = alt2

if not candidate:
    print('DB file not found, searched around', here)
    raise SystemExit(1)

DB = candidate
print('DB path:', DB)

con = sqlite3.connect(DB)
try:
    cur = con.cursor()
    cur.execute('PRAGMA foreign_keys=OFF;')
    cur.execute('BEGIN TRANSACTION;')

    # Create new table with user_id nullable
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

    # Copy data
    cur.execute('''
    INSERT INTO translation_new (id, user_id, original_text, translated_text, source_lang, target_lang, file_path, created_at)
    SELECT id, user_id, original_text, translated_text, source_lang, target_lang, file_path, created_at FROM translation;
    ''')

    # Drop old table and rename
    cur.execute('DROP TABLE translation;')
    cur.execute('ALTER TABLE translation_new RENAME TO translation;')

    cur.execute('COMMIT;')
    cur.execute('PRAGMA foreign_keys=ON;')
    print('Migration completed successfully')
finally:
    con.close()
