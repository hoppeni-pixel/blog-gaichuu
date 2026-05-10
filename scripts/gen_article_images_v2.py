#!/usr/bin/env python3
"""
2段階生成：
Step1: gpt-image-1 でテキストなしの背景イラストを生成
Step2: Pillow + 日本語フォントで正確なテキストを重ねる
"""
import os, base64, time
from pathlib import Path
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

# APIキー読み込み
env = (Path(__file__).parent.parent / '.env').read_text()
for line in env.splitlines():
    if line.startswith('OPENAI_API_KEY='):
        os.environ['OPENAI_API_KEY'] = line.split('=',1)[1].strip().strip('"').strip("'")

client = OpenAI()
SLUG    = 'shiroari-kujo-hiyo'
OUT_DIR = Path(__file__).parent.parent / 'public' / 'assets' / SLUG
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 日本語フォント
FONT_PATHS = [
    '/System/Library/Fonts/ヒラギノ角ゴシック W7.ttc',
    '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc',
    '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc',
    '/Library/Fonts/Arial Unicode MS.ttf',
]
FONT_PATH = next((p for p in FONT_PATHS if Path(p).exists()), None)

def font(size): return ImageFont.truetype(FONT_PATH, size) if FONT_PATH else ImageFont.load_default()

def text_w(draw, text, f): return draw.textlength(text, font=f)

# ─── 画像定義 ───────────────────────────────────────────

IMAGES = [

  # 00: アイキャッチ
  { 'file': '00-eyecatch.png',
    'bg_prompt': 'Flat vector illustration for Japanese pest control blog. RIGHT side only: a pest control worker in white protective suit and helmet, crouching under wooden floor beams with a flashlight, inspecting for termites. Visible termite damage on wood. Dark forest green background. Left 45% of image is EMPTY dark green space for text overlay. No text, no letters, no numbers anywhere.',
    'draw': lambda img: draw_eyecatch(img) },

  # 01: 坪数別費用
  { 'file': '01-cost-chart.png',
    'bg_prompt': 'Flat vector illustration. Right side: a cute cartoon termite next to a wooden pillar. Left and center: dark forest green background, completely empty space for a cost table. No text, no numbers, no letters anywhere in the image.',
    'draw': lambda img: draw_cost_chart(img) },

  # 02: 工法比較
  { 'file': '02-methods.png',
    'bg_prompt': 'Flat vector illustration split in two halves. Left half light green: pest control worker spraying chemical under floor (barrier method). Right half orange: a bait station cylinder in the ground near house foundation. White center divider strip. No text anywhere.',
    'draw': lambda img: draw_methods(img) },

  # 03: 費用が高くなる4ケース
  { 'file': '03-cost-factors.png',
    'bg_prompt': 'Flat vector illustration with 4 panels in 2x2 grid on cream/beige background. Top-left: floor with no inspection hatch. Top-right: severely damaged wooden beam. Bottom-left: concrete foundation with drill. Bottom-right: damaged house exterior. No text anywhere.',
    'draw': lambda img: draw_cost_factors(img) },

  # 04: 無料点検の落とし穴
  { 'file': '04-free-inspection-trap.png',
    'bg_prompt': 'Flat vector illustration with 3 panels side by side on white/light background. Left panel: worried Japanese woman with scary termite. Middle panel: suspicious man showing a document. Right panel: a suspicious salesman at a front door. No text anywhere.',
    'draw': lambda img: draw_trap(img) },
]

# ─── テキスト描画関数 ─────────────────────────────────────

GREEN  = '#1a5c1a'
ORANGE = '#e8820a'
WHITE  = '#ffffff'
DARK   = '#222222'
RED    = '#cc2200'
CREAM  = '#fffdf5'

def draw_eyecatch(img):
    W, H = img.size
    d = ImageDraw.Draw(img)
    # 左側に半透明の緑オーバーレイ
    overlay = Image.new('RGBA', (int(W*0.48), H), (20, 70, 20, 210))
    img.paste(Image.new('RGB', (int(W*0.48), H), (20, 70, 20)), (0, 0))
    d = ImageDraw.Draw(img)

    # タイトル
    f_big  = font(72)
    f_med  = font(44)
    f_sm   = font(30)
    d.text((40, 60),  'シロアリ駆除の', font=f_big, fill=WHITE)
    d.text((40, 148), '費用相場',       font=f_big, fill=WHITE)

    # 価格バッジ
    badge = [40, 238, 440, 298]
    d.rounded_rectangle(badge, radius=8, fill=ORANGE)
    d.text((56, 244), '30,000〜150,000円', font=f_sm, fill=WHITE)

    # 下部アイコンラベル
    icons = ['🔍 点検', '💴 見積もり', '🚿 駆除', '🛡 保証']
    x_start, y_icon = 30, H - 80
    for i, label in enumerate(icons):
        x = x_start + i * (int(W*0.48)//4)
        d.rectangle([x, y_icon-4, x+int(W*0.48)//4-8, y_icon+46], fill=(10,50,10))
        d.text((x+6, y_icon), label, font=font(26), fill='#aaffaa')

def draw_cost_chart(img):
    W, H = img.size
    d = ImageDraw.Draw(img)
    # 背景を濃い緑で上書き（左3/4）
    img.paste(Image.new('RGB', (int(W*0.65), H), (20, 70, 20)), (0,0))
    d = ImageDraw.Draw(img)

    f_title = font(60)
    f_row   = font(38)
    d.text((30, 30), '坪数別の費用相場', font=f_title, fill=WHITE)

    rows = [
        ('10坪', '6〜10万円'),
        ('20坪', '12〜20万円'),
        ('30坪', '18〜30万円'),
        ('40坪', '24〜40万円'),
    ]
    colors = ['#2d8a2d','#236b23','#2d8a2d','#236b23']
    for i,(tsubo, cost) in enumerate(rows):
        y = 130 + i*120
        d.rounded_rectangle([20, y, int(W*0.62), y+100], radius=8, fill=colors[i])
        d.text((36, y+22), tsubo, font=f_row, fill='#aaffaa')
        d.text((180, y+22), cost, font=f_row, fill=WHITE)

def draw_methods(img):
    W, H = img.size
    d = ImageDraw.Draw(img)
    f_title = font(54)
    f_sub   = font(32)
    f_sm    = font(26)

    # 左帯
    d.rectangle([0,0, W//2-10, H], fill='#1a7a1a')
    # 右帯
    d.rectangle([W//2+10,0, W, H], fill='#c85a00')
    # 中央VSバー
    d.rectangle([W//2-30, 0, W//2+30, H], fill=WHITE)
    d.text((W//2-22, H//2-50), 'VS', font=font(64), fill='#333333')

    # 左：バリア工法
    d.text((30, 30), 'バリア工法', font=f_title, fill=WHITE)
    for i, txt in enumerate(['・即効性が高い','・安価（坪6,000〜）','・5年保証が標準']):
        d.text((30, 150+i*70), txt, font=f_sm, fill=WHITE)

    # 右：ベイト工法
    d.text((W//2+50, 30), 'ベイト工法', font=f_title, fill=WHITE)
    for i, txt in enumerate(['・環境への負荷が少ない','・費用は高め','・効果が出るまで数ヶ月']):
        d.text((W//2+50, 150+i*70), txt, font=f_sm, fill=WHITE)

def draw_cost_factors(img):
    W, H = img.size
    d = ImageDraw.Draw(img)
    # クリーム背景
    img.paste(Image.new('RGB', img.size, '#fffdf0'), (0,0))
    d = ImageDraw.Draw(img)

    # タイトル帯
    d.rectangle([0,0,W,90], fill=ORANGE)
    d.text((20, 14), '費用が上がる4つのケース', font=font(54), fill=WHITE)

    cards = [
        ('①点検口がない',      '床下への入口がなく\n新設で2〜5万円追加'),
        ('②被害が広範囲',      '木材補強・交換で\n別途数十万円'),
        ('③コンクリート基礎',  '穿孔（穴あけ）工事で\n追加費用が発生'),
        ('④放置して大規模被害','被害が広がるほど\n修繕費も増加'),
    ]
    positions = [(20,110),(W//2+10,110),(20,370),(W//2+10,370)]
    for (title, body), (x,y) in zip(cards, positions):
        d.rounded_rectangle([x,y,x+W//2-30,y+230], radius=10, fill='#fff8ee', outline=ORANGE, width=3)
        d.rounded_rectangle([x,y,x+W//2-30,y+54], radius=10, fill=ORANGE)
        d.text((x+10, y+8), title, font=font(34), fill=WHITE)
        for i, line in enumerate(body.split('\n')):
            d.text((x+14, y+66+i*50), line, font=font(30), fill=DARK)

def draw_trap(img):
    W, H = img.size
    d = ImageDraw.Draw(img)
    img.paste(Image.new('RGB', img.size, '#fafafa'), (0,0))
    d = ImageDraw.Draw(img)

    # タイトル帯
    d.rectangle([0,0,W,90], fill=RED)
    d.text((20, 12), '⚠ 無料点検の落とし穴！', font=font(52), fill=WHITE)

    # 3カード
    cards = [
        ('①不安を過剰に煽る', '「このままでは\n家が倒壊します」\nなど脅してくる'),
        ('②虚偽の写真を見せる', 'シロアリがいない\nのに被害写真を\n見せて契約を迫る'),
        ('③突然の訪問', '「近所で作業中」\nと突然訪問して\nくる業者に注意'),
    ]
    card_w = (W - 40) // 3
    for i, (title, body) in enumerate(cards):
        x = 10 + i*(card_w+10)
        d.rounded_rectangle([x,100,x+card_w,H-20], radius=10, fill='#fff3f0', outline=RED, width=2)
        d.rounded_rectangle([x,100,x+card_w,154], radius=10, fill=RED)
        d.text((x+8, 108), title, font=font(28), fill=WHITE)
        for j, line in enumerate(body.split('\n')):
            d.text((x+10, 164+j*58), line, font=font(28), fill=DARK)

# ─── 生成＋描画 ──────────────────────────────────────────

for i, img_def in enumerate(IMAGES):
    out = OUT_DIR / img_def['file']
    tmp = OUT_DIR / f"_bg_{img_def['file']}"
    print(f"\n[{i+1}/{len(IMAGES)}] {img_def['file']}")

    # Step1: 背景生成
    print('  Step1: 背景イラスト生成中...')
    resp = client.images.generate(
        model='gpt-image-1',
        prompt=img_def['bg_prompt'],
        size='1536x1024',
        quality='medium',
        n=1,
    )
    tmp.write_bytes(base64.b64decode(resp.data[0].b64_json))

    # Step2: テキスト重ね
    print('  Step2: 日本語テキストを重ねる...')
    img = Image.open(tmp).convert('RGB')
    img_def['draw'](img)
    img.save(out, quality=92)
    tmp.unlink()
    print(f'  ✓ 完成: {out.name} ({out.stat().st_size//1024}KB)')

    if i < len(IMAGES)-1:
        time.sleep(3)

print('\n\n✅ 全5枚完成！')
