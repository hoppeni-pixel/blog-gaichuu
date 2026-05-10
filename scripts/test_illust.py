#!/usr/bin/env python3
"""テスト：イラスト風アイキャッチ（gpt-image-1 で日本語テキスト込み生成）"""

import os, base64, subprocess
from pathlib import Path
from openai import OpenAI

# .env からAPIキー読み込み
env_path = Path(__file__).parent.parent / ".env"
for line in env_path.read_text().splitlines():
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")

client = OpenAI()

PROMPT = """
Japanese blog thumbnail illustration. Landscape 16:9 format.

Left side (60% width):
- Large bold Japanese title text: 「シロアリ駆除の費用相場」 in dark green or dark brown, very large font
- Subtitle text: 「一軒家の平均・坪単価・業者の選び方を解説」 in smaller font on a green rounded rectangle badge
- Price badge: 「30,000〜150,000円」 in large orange text on a cream/yellow rounded rectangle with a yen coin icon
- Bottom row of 4 small circular icons: shield with checkmark, pest control worker in green uniform with sprayer, clipboard with checkmark, Japanese house

Right side (40% width):
- Large cute flat illustration of wooden floor beams with termite damage, small white termites visible
- Japanese traditional house cross-section showing under-floor space

Overall style: flat vector illustration, clean and professional, color palette: cream/off-white background, forest green (#2d6a2d), warm orange (#e8820a), light beige accents. Similar to Japanese real estate or home maintenance blog thumbnails. No photorealistic elements. No English text.
"""

OUT = Path("/tmp/test_illust.jpg")

print("gpt-image-1 で生成中（30秒ほどかかります）...")
try:
    resp = client.images.generate(
        model="gpt-image-1",
        prompt=PROMPT,
        size="1536x1024",
        quality="medium",
        n=1,
    )
    # gpt-image-1 は b64_json で返す
    img_data = base64.b64decode(resp.data[0].b64_json)
    OUT.write_bytes(img_data)
    print(f"✓ 保存: {OUT}")
    subprocess.Popen(["open", str(OUT)])

except Exception as e:
    print(f"gpt-image-1 失敗: {e}")
    print("→ dall-e-3 にフォールバックします...")

    import urllib.request
    PROMPT_DALLE = """
    Japanese blog thumbnail, flat vector illustration style.
    Right side: large illustrated termite nest cross-section inside wooden floor beams, cute cartoon termites.
    Left side: Japanese title layout area with green and orange design elements, rounded badge shapes, coin icons, house icons.
    Color palette: cream background, forest green, warm orange. Clean professional infographic style. No photorealistic elements.
    """
    resp2 = client.images.generate(
        model="dall-e-3",
        prompt=PROMPT_DALLE,
        size="1792x1024",
        quality="standard",
        n=1,
    )
    urllib.request.urlretrieve(resp2.data[0].url, OUT)
    print(f"✓ DALL-E 3 で保存: {OUT}")
    subprocess.Popen(["open", str(OUT)])
