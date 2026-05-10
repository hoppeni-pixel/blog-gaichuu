#!/usr/bin/env python3
"""
v3: 背景イラスト（AI生成）＋半透明テキストオーバーレイ（Pillow）
イラストを活かしながら正確な日本語テキストを重ねる
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

# ────────────────────────────────────────────
# テキスト描画（半透明オーバーレイ方式）
# ────────────────────────────────────────────

def draw_eyecatch(img):
    """左半分に半透明緑帯＋テキスト、右はイラストそのまま"""
    img = img.convert('RGBA')
    W, H = img.size
    ov = Image.new('RGBA', img.size, (0,0,0,0))
    d  = ImageDraw.Draw(ov)
    # 左45%に半透明の濃い緑
    d.rectangle([0, 0, int(W*0.47), H], fill=(15, 60, 15, 210))
    img = Image.alpha_composite(img, ov).convert('RGB')
    d2 = ImageDraw.Draw(img)

    d2.text((30, 55),  'シロアリ駆除の', font=font(68), fill='white')
    d2.text((30, 138), '費用相場',       font=font(68), fill='white')

    # 価格バッジ
    d2.rounded_rectangle([30, 228, 420, 288], radius=8, fill='#e8820a')
    d2.text((46, 234), '30,000〜150,000円', font=font(28), fill='white')

    # 下部アイコンラベル（左帯内）
    icons = ['🔍 点検', '💴 見積もり', '💊 駆除', '🛡 保証']
    for i, label in enumerate(icons):
        x = 18 + i * (int(W*0.47)//4)
        d2.rounded_rectangle([x, H-72, x+int(W*0.47)//4-6, H-12], radius=6, fill=(10,45,10))
        d2.text((x+6, H-66), label, font=font(22), fill='#88ff88')
    return img

def draw_cost_chart(img):
    """左60%に半透明帯＋費用表、右はシロアリイラストそのまま"""
    img = img.convert('RGBA')
    W, H = img.size
    ov = Image.new('RGBA', img.size, (0,0,0,0))
    d  = ImageDraw.Draw(ov)
    d.rectangle([0, 0, int(W*0.62), H], fill=(15, 60, 15, 215))
    img = Image.alpha_composite(img, ov).convert('RGB')
    d2 = ImageDraw.Draw(img)

    d2.text((24, 22), '坪数別の費用相場', font=font(54), fill='white')

    rows   = [('10坪','6〜10万円'),('20坪','12〜20万円'),('30坪','18〜30万円'),('40坪','24〜40万円')]
    colors = ['#2d8a2d','#236b23','#2d8a2d','#236b23']
    for i, (tsubo, cost) in enumerate(rows):
        y = 108 + i*108
        d2.rounded_rectangle([16, y, int(W*0.60), y+90], radius=8, fill=colors[i])
        d2.text((30, y+18), tsubo, font=font(34), fill='#aaffaa')
        d2.text((160, y+18), cost,  font=font(34), fill='white')
    return img

def draw_methods(img):
    """左右に半透明カラー帯＋テキスト、イラストが透けて見える"""
    img = img.convert('RGBA')
    W, H = img.size
    ov = Image.new('RGBA', img.size, (0,0,0,0))
    d  = ImageDraw.Draw(ov)
    d.rectangle([0, 0, W//2-15, H], fill=(20, 100, 20, 180))
    d.rectangle([W//2+15, 0, W, H], fill=(160, 60, 0, 180))
    # 中央白帯
    d.rectangle([W//2-20, 0, W//2+20, H], fill=(255,255,255,230))
    img = Image.alpha_composite(img, ov).convert('RGB')
    d2 = ImageDraw.Draw(img)

    # VS
    d2.text((W//2-28, H//2-44), 'VS', font=font(66), fill='#333333')

    # 左：バリア工法
    d2.text((24, 24), 'バリア工法', font=font(56), fill='white')
    for i, t in enumerate(['・即効性が高い', '・安価（坪6,000〜）', '・5年保証が標準']):
        d2.text((24, 130+i*72), t, font=font(30), fill='white')

    # 右：ベイト工法
    d2.text((W//2+34, 24), 'ベイト工法', font=font(56), fill='white')
    for i, t in enumerate(['・環境への負荷が少ない', '・費用は高め', '・効果まで数ヶ月']):
        d2.text((W//2+34, 130+i*72), t, font=font(30), fill='white')
    return img

def draw_cost_factors(img):
    """タイトル帯＋4カード（半透明）、背景イラストが透ける"""
    img = img.convert('RGBA')
    W, H = img.size
    ov = Image.new('RGBA', img.size, (0,0,0,0))
    d  = ImageDraw.Draw(ov)
    # タイトル帯
    d.rectangle([0, 0, W, 88], fill=(200, 100, 0, 235))
    # 4カード（半透明クリーム）
    positions = [(14,100),(W//2+8,100),(14,360),(W//2+8,360)]
    for (x,y) in positions:
        d.rounded_rectangle([x,y,x+W//2-22,y+230], radius=10, fill=(255,250,235,210))
        d.rounded_rectangle([x,y,x+W//2-22,y+52],  radius=10, fill=(200,100,0,230))
    img = Image.alpha_composite(img, ov).convert('RGB')
    d2 = ImageDraw.Draw(img)

    d2.text((18, 14), '費用が上がる4つのケース', font=font(50), fill='white')

    cards = [
        ('①点検口がない',     '床下入口の新設\n2〜5万円追加'),
        ('②被害が広範囲',     '木材補強・交換で\n別途数十万円'),
        ('③コンクリート基礎', '穿孔工事で\n追加費用発生'),
        ('④放置で大規模被害', '被害が広がるほど\n修繕費も増加'),
    ]
    for (title, body), (x,y) in zip(cards, positions):
        d2.text((x+10, y+8), title, font=font(32), fill='white')
        for j, line in enumerate(body.split('\n')):
            d2.text((x+14, y+64+j*52), line, font=font(28), fill='#222222')
    return img

def draw_trap(img):
    """タイトル帯＋3カード（半透明）、背景の人物イラストが透ける"""
    img = img.convert('RGBA')
    W, H = img.size
    ov = Image.new('RGBA', img.size, (0,0,0,0))
    d  = ImageDraw.Draw(ov)
    # タイトル帯
    d.rectangle([0, 0, W, 88], fill=(180, 20, 0, 240))
    # 3カード（半透明）
    card_w = (W-40)//3
    for i in range(3):
        x = 10 + i*(card_w+10)
        d.rounded_rectangle([x, 96, x+card_w, H-14], radius=10, fill=(255,245,240,195))
        d.rounded_rectangle([x, 96, x+card_w, 150],  radius=10, fill=(180,20,0,225))
    img = Image.alpha_composite(img, ov).convert('RGB')
    d2 = ImageDraw.Draw(img)

    d2.text((20, 14), '⚠ 無料点検の落とし穴！', font=font(50), fill='white')

    cards = [
        ('①不安を過剰に煽る', '「このままでは\n家が倒壊します」\nなど脅してくる'),
        ('②虚偽の写真を見せる','シロアリがいない\nのに被害写真で\n契約を迫る'),
        ('③突然の訪問',        '「近所で作業中」\nと突然訪問して\nくる業者に注意'),
    ]
    for i, (title, body) in enumerate(cards):
        x = 10 + i*(card_w+10)
        d2.text((x+8, 102), title, font=font(26), fill='white')
        for j, line in enumerate(body.split('\n')):
            d2.text((x+10, 160+j*58), line, font=font(26), fill='#222222')
    return img

# ────────────────────────────────────────────
# 画像定義
# ────────────────────────────────────────────

IMAGES = [
  { 'file': '00-eyecatch.png',
    'bg': 'Flat vector illustration. Japanese pest control worker in white protective suit crouching under wooden floor beams with a flashlight, inspecting for termites. Termite damage visible on wood. Dark forest green background. RIGHT side of image only. LEFT 45% is empty dark green space. NO text, NO letters anywhere.',
    'draw': draw_eyecatch },
  { 'file': '01-cost-chart.png',
    'bg': 'Flat vector illustration. RIGHT side: a cute cartoon termite next to a wooden pillar on dark green background. LEFT 60%: empty dark forest green space. NO text, NO numbers anywhere.',
    'draw': draw_cost_chart },
  { 'file': '02-methods.png',
    'bg': 'Flat vector illustration split vertically. LEFT half: pest control worker in green uniform spraying chemical under a house floor (barrier treatment). RIGHT half: a cylindrical bait station in soil near house foundation (bait method). Warm lighting. NO text anywhere.',
    'draw': draw_methods },
  { 'file': '03-cost-factors.png',
    'bg': 'Flat vector illustration with 4 scenes in a 2x2 grid. Top-left: floor with no inspection hatch door. Top-right: severely termite-damaged wooden beam. Bottom-left: concrete foundation with a power drill. Bottom-right: a deteriorating old Japanese house exterior. Cream/beige background. NO text anywhere.',
    'draw': draw_cost_factors },
  { 'file': '04-free-inspection-trap.png',
    'bg': 'Flat vector illustration with 3 separate scenes side by side. Left: worried Japanese woman pointing at a large termite. Middle: suspicious man in dark clothes showing a document. Right: a suspicious uniformed salesman at a front door. Light background. NO text anywhere.',
    'draw': draw_trap },
]

# ────────────────────────────────────────────
# 生成＋合成
# ────────────────────────────────────────────

for i, img_def in enumerate(IMAGES):
    out = OUT_DIR / img_def['file']
    tmp = OUT_DIR / f"_bg_{img_def['file']}"
    print(f"\n[{i+1}/{len(IMAGES)}] {img_def['file']}")

    print('  Step1: 背景イラスト生成...')
    resp = client.images.generate(
        model='gpt-image-1',
        prompt=img_def['bg'],
        size='1536x1024',
        quality='medium',
        n=1,
    )
    tmp.write_bytes(base64.b64decode(resp.data[0].b64_json))

    print('  Step2: 日本語テキストを半透明で重ねる...')
    base_img = Image.open(tmp).convert('RGB')
    result   = img_def['draw'](base_img)
    result.save(out, quality=92)
    tmp.unlink()
    kb = out.stat().st_size // 1024
    print(f'  ✓ {out.name} ({kb}KB)')

    if i < len(IMAGES)-1:
        time.sleep(3)

print('\n\n✅ 全5枚完成！確認してください。')
