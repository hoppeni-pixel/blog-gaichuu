#!/usr/bin/env python3
"""
ブログ記事の画像を DALL-E 3 で自動生成するスクリプト
使い方: python3 scripts/generate_images.py [slug]
  slug を指定すると、そのスラッグのみ生成
  省略すると scripts/prompts/*.json を全て処理
"""

import os
import sys
import json
import time
import urllib.request
from pathlib import Path

# .env を手動でパース（python-dotenv がなくても動く）
def load_env():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("'\"")

load_env()

try:
    from openai import OpenAI
except ImportError:
    print("openai ライブラリがありません。インストールします...")
    os.system(f"{sys.executable} -m pip install openai")
    from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

PROMPTS_DIR = Path(__file__).parent / "prompts"
ASSETS_DIR  = Path(__file__).parent.parent / "public" / "assets"


def generate_for_slug(slug: str):
    prompt_file = PROMPTS_DIR / f"{slug}.json"
    if not prompt_file.exists():
        print(f"[SKIP] プロンプトファイルが見つかりません: {prompt_file}")
        return

    with open(prompt_file, encoding="utf-8") as f:
        prompts = json.load(f)

    out_dir = ASSETS_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    for item in prompts:
        filename = item["filename"]
        prompt   = item["prompt"]
        out_path = out_dir / filename

        if out_path.exists():
            print(f"[SKIP] 既に存在します: {out_path.name}")
            continue

        print(f"[生成中] {slug}/{filename} ...")
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1792x1024",   # 横長（16:9 相当）
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url

            # ダウンロードして保存
            urllib.request.urlretrieve(image_url, out_path)
            print(f"[完了] 保存: {out_path}")

            # レート制限対策（1分あたり5回まで）
            time.sleep(13)

        except Exception as e:
            print(f"[ERROR] {filename}: {e}")


def main():
    if len(sys.argv) > 1:
        slugs = sys.argv[1:]
    else:
        slugs = [f.stem for f in sorted(PROMPTS_DIR.glob("*.json"))]

    if not slugs:
        print("prompts フォルダに JSON ファイルがありません。")
        return

    print(f"対象スラッグ: {slugs}\n")
    for slug in slugs:
        generate_for_slug(slug)
        print()


if __name__ == "__main__":
    main()
