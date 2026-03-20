#!/usr/bin/env python3
"""
generation_claude.py

PoC: generate N recipe samples via Claude-style API and save to JSONL.

Usage:
  - Put your Claude API key in ~/.env as CLAUDE_API_KEY="sk-..."
  - Optionally set CLAUDE_API_URL if your provider uses a custom endpoint.
  - python3 tools/generation_claude.py --count 50 --out ../data/recipes_claude_sample.jsonl

Notes:
 - This script expects the Claude endpoint to accept a POST with JSON:
   {"prompt": "...", "max_tokens": 1000}
   and return a JSON with 'text' (adjust CLAUDE_API_URL/response parsing as needed).
 - If your provider has a different contract, adjust send_request() accordingly.
"""

import os
import sys
import json
import time
import argparse
import random
from pathlib import Path
import requests

# Simple prompt template: returns a JSON object per recipe
PROMPT_TEMPLATE = '''다음 재료 목록을 바탕으로 한국어 레시피 하나를 JSON 형태로 만들어주세요.
응답은 반드시 JSON 한 객체로만 반환하세요. 필드:
- title (문자열)
- ingredients (배열 of strings)
- keyIngredients (배열 of strings)
- optional (배열 of strings)
- steps (배열 of strings)
- time (정수, 분 단위)
- servings (정수)
- caloriesPerPerson (정수)
- cuisine (문자열)
- tags (배열 of strings)
- source (문자열, 예: "claude")

재료: {ingredients}

제약:
- ingredients는 2개 이상 포함
- steps는 최소 2단계
- time은 5~240 사이

출력 예시(반드시 JSON만):
{{
  "title":"...",
  "ingredients":["감자","계란"],
  "keyIngredients":["감자"],
  "optional":[],
  "steps":["1. ...","2. ..."],
  "time":20,
  "servings":2,
  "caloriesPerPerson":350,
  "cuisine":"한식",
  "tags":["간단","야식"],
  "source":"claude"
}}
'''

# Simple list of ingredients fallback (if cannot parse in repo)
FALLBACK_INGS = ["감자","양파","달걀","대파","돼지고기","소고기","두부","당근","호박","버섯","청양고추","마늘","생강","우유","치즈","토마토","파프리카","김치","참치","연근","옥수수"]


def load_all_ingredients_from_index_html():
    p = Path(__file__).resolve().parents[2] / 'Desktop' / 'my_ai_bot' / 'f_chef' / 'index.html'
    if not p.exists():
        # try workspace copy
        p2 = Path(__file__).resolve().parents[2] / 'f_chef' / 'index.html'
        if p2.exists():
            p = p2
        else:
            return FALLBACK_INGS
    txt = p.read_text(encoding='utf-8')
    import re
    m = re.search(r"const allIngredients = \[([\s\S]*?)\]\;", txt)
    if not m:
        return FALLBACK_INGS
    inner = m.group(1)
    items = re.findall(r"'([^']+)'", inner)
    return items if items else FALLBACK_INGS


def send_request(prompt, api_url, api_key, timeout=60):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    payload = {
        'prompt': prompt,
        'max_tokens': 800
    }
    # Simple POST — adjust if your Claude endpoint differs
    resp = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def extract_text_from_response(resp_json):
    # Try common shapes: {'text': '...'} or {'completion': '...'} or {'output': '...'}
    for k in ('text','completion','output','response'):
        if k in resp_json:
            return resp_json[k]
    # Anthropic style may return 'completion' nested; fall back to full JSON
    if isinstance(resp_json, dict):
        return json.dumps(resp_json, ensure_ascii=False)
    return str(resp_json)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=50)
    parser.add_argument('--out', type=str, default='../data/recipes_claude_sample.jsonl')
    parser.add_argument('--parallel', type=int, default=2)
    parser.add_argument('--api-url', type=str, default=os.getenv('CLAUDE_API_URL', 'https://api.anthropic.com/v1/complete'))
    args = parser.parse_args()

    api_key = os.getenv('CLAUDE_API_KEY')
    if not api_key:
        print('ERROR: CLAUDE_API_KEY not found in environment. Please set it in ~/.env and `source ~/.env` before running.')
        sys.exit(2)

    all_ings = load_all_ingredients_from_index_html()
    outp = Path(args.out).resolve()
    outp.parent.mkdir(parents=True, exist_ok=True)

    created = 0
    tries = 0
    max_tries = args.count * 3

    with outp.open('w', encoding='utf-8') as f:
        while created < args.count and tries < max_tries:
            tries += 1
            # pick a random combination of 2-6 ingredients
            k = random.randint(2, min(6, len(all_ings)))
            sel = random.sample(all_ings, k)
            prompt = PROMPT_TEMPLATE.format(ingredients=', '.join(sel))
            try:
                resp = send_request(prompt, args.api_url, api_key)
                text = extract_text_from_response(resp)
                text = text.strip()
                if text.startswith('```'):
                    text = '\n'.join(text.split('\n')[1:])
                obj = None
                try:
                    obj = json.loads(text)
                except Exception:
                    import re
                    m = re.search(r"\{[\s\S]*\}", text)
                    if m:
                        try:
                            obj = json.loads(m.group(0))
                        except Exception:
                            obj = None
                if not obj:
                    print('WARN: could not parse JSON from response; skipping. resp:', text[:200])
                    time.sleep(0.4)
                    continue
                if not isinstance(obj.get('ingredients'), list) or len(obj.get('ingredients',[]))<2:
                    print('WARN: invalid ingredients; skipping')
                    continue
                obj['source'] = 'claude'
                obj['id'] = obj.get('id') or f'claude_{int(time.time())}_{created}'
                f.write(json.dumps(obj, ensure_ascii=False) + '\n')
                f.flush()
                created += 1
                print(f'created {created}/{args.count} — {obj.get("title")[:40]}')
                time.sleep(0.2)
            except Exception as e:
                print('ERROR during request:', e)
                time.sleep(1.0)

    print('Done — wrote', outp, 'generated:', created)

if __name__ == '__main__':
    main()
