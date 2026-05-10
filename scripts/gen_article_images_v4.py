#!/usr/bin/env python3
"""
v4: イラスト主役・テキストは最小限のラベルのみ
"""
import os, base64, time
from pathlib import Path
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

env = (Path(__file__).parent.parent / '.env').read_text()
for line in env.splitlines():
    if line.startswith('OPENAI_API_KEY='):
        os.environ['OPENAI_API_KEY'] = line.split('=',1)[1].strip().strip('"').strip("'")

client = OpenAI()
SLUG    = 'shiroari-kujo-hiyo'
OUT_DIR = Path(__file__).parent.parent / 'public' / 'assets' / SLUG
OUT_DIR.mkdir(parents=True, exist_ok=True)

FONT_PATHS = [
    '/System/Library/Fonts/ヒラギノ角ゴシック W7.ttc',
    '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc',
    '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc',
]
FONT_PATH = next((p for p in FONT_PATHS if Path(p).exists()), None)
def font(size): return ImageFont.truetype(FONT_PATH, size) if FONT_PATH else ImageFont.load_default()

def overlay_rect(img, x1, y1, x2, y2, color_rgba):
    ov = Image.new('RGBA', img.size, (0,0,0,0))
    ImageDraw.Draw(ov).rectangle([x1,y1,x2,y2], fill=color_rgba)
    return Image.alpha_composite(img.convert('RGBA'), ov)

def rounded_overlay(img, x1, y1, x2, y2, color_rgba, radius=8):
    ov = Image.new('RGBA', img.size, (0,0,0,0))
    ImageDraw.Draw(ov).rounded_rectangle([x1,y1,x2,y2], radius=radius, fill=color_rgba)
    return Image.alpha_composite(img.convert('RGBA'), ov)

# ── 00: アイキャッチ ──────────────────────────────────────
def draw_eyecatch(img):
    W, H = img.size
    # 左1/3だけ濃い緑帯
    img = overlay_rect(img, 0, 0, int(W*0.42), H, (10, 55, 10, 220))
    img = img.convert('RGB')
    d = ImageDraw.Draw(img)
    d.text((28, 50),  'シロアリ駆除の', font=font(62), fill='white')
    d.text((28, 126), '費用相場',       font=font(62), fill='white')
    # 価格バッジ
    d.rounded_rectangle([28, 214, 390, 270], radius=8, fill='#e8820a')
    d.text((42, 220), '30,000〜150,000円', font=font(26), fill='white')
    # 下部ラベル
    for i, t in enumerate(['🔍点検','💴見積','🚿駆除','🛡保証']):
        x = 14 + i * (int(W*0.42)//4)
        d.text((x+4, H-54), t, font=font(20), fill='#ccffcc')
    return img

# ── 01: 坪数別費用 ────────────────────────────────────────
def draw_cost_chart(img):
    W, H = img.size
    img = overlay_rect(img, 0, 0, int(W*0.58), H, (10, 55, 10, 215))
    img = img.convert('RGB')
    d = ImageDraw.Draw(img)
    d.text((20, 18), '坪数別の費用相場', font=font(52), fill='white')
    rows   = [('10坪','6〜10万円'),('20坪','12〜20万円'),('30坪','18〜30万円'),('40坪','24〜40万円')]
    colors = ['#2d8a2d','#1e6b1e','#2d8a2d','#1e6b1e']
    for i,(tsubo,cost) in enumerate(rows):
        y = 98 + i*104
        d.rounded_rectangle([12, y, int(W*0.56), y+86], radius=8, fill=colors[i])
        d.text((26, y+18), tsubo, font=font(32), fill='#aaffaa')
        d.text((150, y+18), cost,  font=font(32), fill='white')
    return img

# ── 02: 工法比較 ──────────────────────────────────────────
def draw_methods(img):
    W, H = img.size
    # 上部タイトル帯のみ
    img = overlay_rect(img, 0, 0, W, 72, (20, 80, 20, 230))
    # 左上ラベル
    img = rounded_overlay(img, 10, 80, 220, 130, (20,80,20,200), radius=6)
    # 右上ラベル
    img = rounded_overlay(img, W//2+10, 80, W//2+230, 130, (160,60,0,200), radius=6)
    # 中央VSバッジ
    img = rounded_overlay(img, W//2-48, H//2-44, W//2+48, H//2+44, (255,255,255,220), radius=50)
    img = img.convert('RGB')
    d = ImageDraw.Draw(img)
    d.text((20, 10), 'バリア工法 vs ベイト工法', font=font(46), fill='white')
    d.text((20, 84), 'バリア工法', font=font(32), fill='white')
    d.text((W//2+18, 84), 'ベイト工法', font=font(32), fill='white')
    d.text((W//2-34, H//2-36), 'VS', font=font(58), fill='#333333')
    # 左下メモ
    d2 = ImageDraw.Draw(img)
    for i,t in enumerate(['・即効性が高い', '・安価（坪6,000〜）', '・5年保証が標準']):
        d.rounded_rectangle([10, H-200+i*58, 340, H-152+i*58], radius=6, fill=(10,55,10,180))
        d.text((18, H-196+i*58), t, font=font(26), fill='white')
    for i,t in enumerate(['・環境への負荷が少ない','・費用は高め','・効果まで数ヶ月']):
        d.rounded_rectangle([W//2+10, H-200+i*58, W-10, H-152+i*58], radius=6, fill=(140,50,0,180))
        d.text((W//2+18, H-196+i*58), t, font=font(26), fill='white')
    return img

# ── 03: 4ケース ───────────────────────────────────────────
def draw_cost_factors(img):
    W, H = img.size
    # 上部タイトル帯
    img = overlay_rect(img, 0, 0, W, 74, (200, 100, 0, 235))
    # 4隅に小さなラベルバッジ
    labels = [
        (10, 80, '①点検口がない'),
        (W//2+6, 80, '②被害が広範囲'),
        (10, H//2+6, '③コンクリート基礎'),
        (W//2+6, H//2+6, '④放置で大規模被害'),
    ]
    for (x, y, txt) in labels:
        img = rounded_overlay(img, x, y, x+int(W*0.46), y+54, (200,100,0,215), radius=8)
    # 中央の十字線（薄く）
    img = overlay_rect(img, W//2-3, 74, W//2+3, H, (200,100,0,80))
    img = overlay_rect(img, 0, H//2-3, W, H//2+3, (200,100,0,80))
    img = img.convert('RGB')
    d = ImageDraw.Draw(img)
    d.text((16, 12), '費用が上がる4つのケース', font=font(48), fill='white')
    for (x, y, txt) in labels:
        d.text((x+10, y+10), txt, font=font(28), fill='white')
    return img

# ── 04: 落とし穴 ──────────────────────────────────────────
def draw_trap(img):
    W, H = img.size
    card_w = (W - 30) // 3
    # 上部タイトル帯のみ（高さ70px）
    img = overlay_rect(img, 0, 0, W, 70, (180, 20, 0, 240))
    # 各イラストの上に小さなラベルバッジ（邪魔しない程度）
    for i, title in enumerate(['①不安を過剰に煽る', '②虚偽の写真を見せる', '③突然の訪問']):
        x = 6 + i*(card_w+6)
        img = rounded_overlay(img, x, 76, x+card_w, 130, (180,20,0,210), radius=6)
    # 下部に各カードの説明（下1/4だけ）
    descs = [
        '脅し文句で\n高額契約を迫る',
        'シロアリがいないのに\n被害写真を見せる',
        '突然訪問してくる\n業者は要注意',
    ]
    for i, desc in enumerate(descs):
        x = 6 + i*(card_w+6)
        img = rounded_overlay(img, x, H-120, x+card_w, H-6, (0,0,0,170), radius=6)
    # 右上「見分け方」ボックス
    img = rounded_overlay(img, W-260, 76, W-6, 260, (50,50,50,210), radius=8)
    img = img.convert('RGB')
    d = ImageDraw.Draw(img)
    d.text((16, 12), '⚠ 無料点検の落とし穴！', font=font(46), fill='white')
    for i, title in enumerate(['①不安を過剰に煽る', '②虚偽の写真を見せる', '③突然の訪問']):
        x = 6 + i*(card_w+6)
        d.text((x+8, 84), title, font=font(24), fill='white')
    for i, desc in enumerate(descs):
        x = 6 + i*(card_w+6)
        for j, line in enumerate(desc.split('\n')):
            d.text((x+8, H-114+j*50), line, font=font(24), fill='white')
    # 見分け方ボックス
    d.text((W-252, 84), '見分け方', font=font(26), fill='#ffdd88')
    for j, txt in enumerate(['・突然の訪問は断る','・見積は書面でもらう','・複数社に相談する']):
        d.text((W-252, 122+j*42), txt, font=font(22), fill='white')
    return img

# ────────────────────────────────────────────
IMAGES = [
  {'file':'00-eyecatch.png', 'draw':draw_eyecatch,
   'bg':'Flat vector illustration. Pest control worker in white protective suit crouching under Japanese house floor beams with flashlight, inspecting for termites. Dark forest green background. Termite damage on wooden beams. Right side of image. LEFT 42% empty dark green space. NO text.'},
  {'file':'01-cost-chart.png', 'draw':draw_cost_chart,
   'bg':'Flat vector illustration. Cute cartoon termite peeking around a wooden pillar. Dark green background. RIGHT side only. LEFT 58% empty dark green space. NO text.'},
  {'file':'02-methods.png', 'draw':draw_methods,
   'bg':'Flat vector illustration. LEFT half light green: pest control worker in uniform crouching and spraying chemicals under floor. RIGHT half warm orange: a cylindrical bait station in garden soil near house wall. Natural warm lighting. NO text anywhere.'},
  {'file':'03-cost-factors.png', 'draw':draw_cost_factors,
   'bg':'Flat vector illustration, 4 quadrant panels on cream background. Top-left: floor panel with no inspection hatch. Top-right: termite-damaged wooden beam close-up. Bottom-left: electric drill on concrete foundation. Bottom-right: old deteriorating Japanese house exterior. NO text anywhere.'},
  {'file':'04-free-inspection-trap.png', 'draw':draw_trap,
   'bg':'Flat vector illustration. 3 panels side by side on white background: LEFT panel shows a worried Japanese woman in orange top with large termite. MIDDLE panel shows suspicious man in dark hoodie holding a document with photos. RIGHT panel shows a door-to-door salesman in uniform ringing a doorbell. NO text anywhere. Leave top 70px and bottom 130px of each panel relatively plain.'},
]

for i, img_def in enumerate(IMAGES):
    out = OUT_DIR / img_def['file']
    tmp = OUT_DIR / f"_bg_{img_def['file']}"
    print(f"\n[{i+1}/{len(IMAGES)}] {img_def['file']}")
    print('  Step1: 背景生成...')
    resp = client.images.generate(
        model='gpt-image-1', prompt=img_def['bg'],
        size='1536x1024', quality='medium', n=1)
    tmp.write_bytes(base64.b64decode(resp.data[0].b64_json))
    print('  Step2: テキスト重ね...')
    result = img_def['draw'](Image.open(tmp).convert('RGB'))
    if hasattr(result, 'convert'):
        result.convert('RGB').save(out, quality=92)
    tmp.unlink()
    print(f'  ✓ {out.name} ({out.stat().st_size//1024}KB)')
    if i < len(IMAGES)-1: time.sleep(3)

print('\n✅ 全5枚完成！')
