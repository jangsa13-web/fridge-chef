#!/usr/bin/env python3
"""
Ingest JSONL of recipes into SQLite for PoC.
Usage: python3 tools/ingest_to_sqlite.py data/recipes_claude_sample.jsonl db/recipes.db
"""
import sys
import json
from pathlib import Path
import sqlite3

infile = Path(sys.argv[1]) if len(sys.argv)>1 else Path('data/recipes_claude_sample.jsonl')
dbpath = Path(sys.argv[2]) if len(sys.argv)>2 else Path('db/recipes.db')

if not infile.exists():
    print('Input not found:', infile)
    sys.exit(1)

dbpath.parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(str(dbpath))
cur = conn.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS recipes (
    id TEXT PRIMARY KEY,
    title TEXT,
    payload JSON
)
''')
conn.commit()

inserted = 0
with infile.open('r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        rid = obj.get('id')
        title = obj.get('title')
        cur.execute('INSERT OR REPLACE INTO recipes (id,title,payload) VALUES (?,?,?)', (rid,title,json.dumps(obj, ensure_ascii=False)))
        inserted += 1
conn.commit()
print('Inserted', inserted, 'into', dbpath)
conn.close()
