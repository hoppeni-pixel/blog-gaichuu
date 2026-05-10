#!/usr/bin/env python3
"""テスト用：1枚だけ生成（写真背景 + 日本語テキスト）"""

import os, urllib.request, subprocess
from pathlib import Path
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

# .env からAPIキー読み込み
env_path = Path(__file__).parent.parent / ".env"
for line in env_path.read_text().splitlines():
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")

client = OpenAI()

# ---- テスト設定 ----
SLUG   = "shiroari-kujo-hiyo"
TITLE  = "シロアリ駆除の費用相場"
SUBTITLE = "一軒家の平均・坪単価・業者の選び方を解説"

PROMPT = (
    "Photorealistic photo. A Japanese pest control specialist in white protective suit "
    "using flashlight to inspect wooden beams under the floor of a traditional Japanese house. "
    "Natural dim lighting from below, realistic textures, cinematic composition. "
    "Dark atmospheric crawl space. No text, no watermark."
)

OUT_RAW  = Path("/tmp/test_raw.jpg")
OUT_FINAL = Path("/tmp/test_eyecatch_text.jpg")

# ---- Step1: DALL-E 3 で写真生成 ----
print("Step1: DALL-E 3 で背景画像を生成中...")
resp = client.images.generate(
    model="dall-e-3",
    prompt=PROMPT,
    size="1792x1024",
    quality="standard",
    n=1,
)
url = resp.data[0].url
urllib.request.urlretrieve(url, OUT_RAW)
print(f"  背景画像保存: {OUT_RAW}")

# ---- Step2: Pillow でテキストを重ねる ----
print("Step2: テキストオーバーレイ中...")

img = Image.open(OUT_RAW).convert("RGB")
W, H = img.size

draw = ImageDraw.Draw(img)

# フォント（システムの日本語フォントを使用）
font_candidates = [
    "/System/Library/Fonts/ヒラギノ角ゴシック W7.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/Library/Fonts/Arial Unicode MS.ttf",
]
font_path = None
for fp in font_candidates:
    if Path(fp).exists():
        font_path = fp
        break

if font_path:
    f_title    = ImageFont.truetype(font_path, 82)
    f_subtitle = ImageFont.truetype(font_path, 38)
else:
    f_title    = ImageFont.load_default()
    f_subtitle = ImageFont.load_default()

# 下部にグラデーション風の黒帯
BAND_H = 220
band_y = H - BAND_H
for y in range(band_y, H):
    alpha = int(210 * (y - band_y) / BAND_H)
    draw.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))

# タイトル（右寄せ）
tx = draw.textlength(TITLE, font=f_title)
x_title = W - tx - 60
y_title = H - BAND_H + 30
# 影
draw.text((x_title + 3, y_title + 3), TITLE, font=f_title, fill=(0, 0, 0, 180))
draw.text((x_title, y_title), TITLE, font=f_title, fill="white")

# サブタイトル（右寄せ）
sx = draw.textlength(SUBTITLE, font=f_subtitle)
x_sub = W - sx - 60
y_sub = y_title + 95
draw.text((x_sub + 2, y_sub + 2), SUBTITLE, font=f_subtitle, fill=(0, 0, 0, 160))
draw.text((x_sub, y_sub), SUBTITLE, font=f_subtitle, fill=(220, 220, 220))

# 左下にカテゴリラベル
CATEGORY = "シロアリ駆除"
if font_path:
    f_cat = ImageFont.truetype(font_path, 32)
else:
    f_cat = f_subtitle

cat_w = draw.textlength(CATEGORY, font=f_cat)
PADDING = 14
draw.rectangle([40, H - 68, 40 + cat_w + PADDING*2, H - 22],
               fill="#e8a000", outline=None)
draw.text((40 + PADDING, H - 64), CATEGORY, font=f_cat, fill="white")

img.save(OUT_FINAL, quality=93)
print(f"  完成: {OUT_FINAL}")

# プレビューを開く
subprocess.Popen(["open", str(OUT_FINAL)])
print("プレビューを開きました。")
