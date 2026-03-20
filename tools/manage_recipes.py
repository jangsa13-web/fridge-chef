#!/usr/bin/env python3
"""
Simple CLI to inspect and edit recipes stored in JSONL or SQLite.
Usage:
  python3 tools/manage_recipes.py --list --source data/recipes_claude_add100.jsonl
  python3 tools/manage_recipes.py --get sample_1 --source data/recipes_claude_add100.jsonl
  python3 tools/manage_recipes.py --edit sample_1 --field title --value "새 제목" --source data/recipes_claude_add100.jsonl
  python3 tools/manage_recipes.py --add --source data/recipes_claude_add100.jsonl --json '{"id":"new","title":"t",...}'

Supports JSONL files. For SQLite, pass --sqlite db/recipes.db and it will operate on payload column.
"""
import argparse, json, sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--source', type=str, help='path to JSONL file')
parser.add_argument('--sqlite', type=str, help='path to sqlite db')
parser.add_argument('--list', action='store_true')
parser.add_argument('--get', type=str)
parser.add_argument('--edit', type=str)
parser.add_argument('--field', type=str)
parser.add_argument('--value', type=str)
parser.add_argument('--add', action='store_true')
parser.add_argument('--json', type=str, help='json string for add')
args = parser.parse_args()

if not args.source and not args.sqlite:
    print('Specify --source JSONL or --sqlite DB'); sys.exit(1)

if args.source:
    path = Path(args.source)
    if not path.exists():
        print('Source not found:', path); sys.exit(1)
    # load lines
    lines = [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]
    id_map = {r.get('id'): r for r in lines}
    if args.list:
        for r in lines:
            print(r.get('id'), '-', r.get('title'))
        sys.exit(0)
    if args.get:
        r = id_map.get(args.get)
        if not r: print('Not found'); sys.exit(1)
        print(json.dumps(r, ensure_ascii=False, indent=2)); sys.exit(0)
    if args.edit:
        rid = args.edit
        if rid not in id_map:
            print('Not found'); sys.exit(1)
        if not args.field:
            print('Specify --field and --value'); sys.exit(1)
        id_map[rid][args.field] = json.loads(args.value) if args.value.strip().startswith(('{','[','"')) else args.value
        # write back
        new_lines = [json.dumps(id_map[r.get('id')], ensure_ascii=False) if r.get('id') in id_map else json.dumps(r, ensure_ascii=False) for r in lines]
        path.write_text('\n'.join(new_lines)+'\n', encoding='utf-8')
        print('Edited', rid); sys.exit(0)
    if args.add:
        if not args.json:
            print('Provide --json payload'); sys.exit(1)
        obj = json.loads(args.json)
        lines.append(obj)
        path.write_text('\n'.join([json.dumps(r, ensure_ascii=False) for r in lines])+'\n', encoding='utf-8')
        print('Added', obj.get('id'))
        sys.exit(0)

if args.sqlite:
    import sqlite3
    conn = sqlite3.connect(args.sqlite)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS recipes (id TEXT PRIMARY KEY, title TEXT, payload JSON)")
    if args.list:
        for row in cur.execute('SELECT id,title FROM recipes'):
            print(row[0], '-', row[1])
        sys.exit(0)
    if args.get:
        cur.execute('SELECT payload FROM recipes WHERE id=?', (args.get,))
        r = cur.fetchone()
        if not r: print('Not found'); sys.exit(1)
        print(json.dumps(json.loads(r[0]), ensure_ascii=False, indent=2)); sys.exit(0)
    if args.edit:
        rid = args.edit
        if not args.field or args.value is None:
            print('Need --field and --value'); sys.exit(1)
        cur.execute('SELECT payload FROM recipes WHERE id=?', (rid,))
        r = cur.fetchone()
        if not r: print('Not found'); sys.exit(1)
        obj = json.loads(r[0])
        obj[args.field] = json.loads(args.value) if args.value.strip().startswith(('{','[','"')) else args.value
        cur.execute('UPDATE recipes SET payload=? WHERE id=?', (json.dumps(obj, ensure_ascii=False), rid))
        conn.commit(); print('Edited', rid); sys.exit(0)
    if args.add:
        if not args.json: print('Provide --json'); sys.exit(1)
        obj = json.loads(args.json)
        cur.execute('INSERT OR REPLACE INTO recipes(id,title,payload) VALUES (?,?,?)', (obj.get('id'), obj.get('title'), json.dumps(obj, ensure_ascii=False)))
        conn.commit(); print('Added', obj.get('id'))
        sys.exit(0)
