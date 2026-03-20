PoC generation + ingest (Claude)

Files in tools/:
- generation_claude.py   -- generate recipes via Claude API (JSONL)
- ingest_to_sqlite.py    -- ingest JSONL into db/recipes.db (SQLite)

Quick start
1) Put your Claude API key in ~/.env:
   CLAUDE_API_KEY="sk-..."
   (Then run: source ~/.env )
2) Install requirements (recommended in venv):
   pip3 install requests
3) Generate 50 samples (PoC):
   python3 tools/generation_claude.py --count 50 --out data/recipes_claude_sample.jsonl
4) Ingest into SQLite:
   python3 tools/ingest_to_sqlite.py data/recipes_claude_sample.jsonl db/recipes.db
5) Commit & push generated data (if desired):
   cd /Users/brad/Desktop/my_ai_bot/f_chef
   git add data/recipes_claude_sample.jsonl db/recipes.db
   git commit -m "chore(data): add claude PoC samples"
   git push origin main

Notes
- If your Claude provider uses a different API contract, set CLAUDE_API_URL env var to the correct endpoint.
- The generation script does basic parsing of model output; if responses are not strict JSON adjust send_request/extract_text_from_response logic.
