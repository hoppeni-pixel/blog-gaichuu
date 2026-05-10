#!/usr/bin/env python3
"""
shiroari-kujo-hiyo の記事画像5枚を gpt-image-1 で自動生成して配置するスクリプト
"""
import os, base64, time, subprocess
from pathlib import Path
from openai import OpenAI

# .env からAPIキー読み込み
env = (Path(__file__).parent.parent / '.env').read_text()
for line in env.splitlines():
    if line.startswith('OPENAI_API_KEY='):
        os.environ['OPENAI_API_KEY'] = line.split('=',1)[1].strip().strip('"').strip("'")

client = OpenAI()

SLUG = 'shiroari-kujo-hiyo'
OUT_DIR = Path(__file__).parent.parent / 'public' / 'assets' / SLUG
OUT_DIR.mkdir(parents=True, exist_ok=True)

IMAGES = [
    {
        'file': '00-eyecatch.png',
        'label': 'アイキャッチ',
        'prompt': 'シロアリ駆除費用相場のブログサムネイル。横長16:9。フラットイラスト風。タイトル「シロアリ駆除の費用相場」大きく左に配置。「30,000〜150,000円」オレンジバッジ。右側に床下点検する白い防護服の業者と、シロアリに侵食された木材のイラスト。カラーは濃い緑・茶・木目・オレンジ。下部に4アイコン：点検・見積もり・駆除・保証。日本語テキストあり。プロフェッショナルなブログデザイン。'
    },
    {
        'file': '01-cost-chart.png',
        'label': '坪数別費用表',
        'prompt': 'シロアリ駆除の坪数別費用相場インフォグラフィック。横長16:9。フラットイラスト風。タイトル「坪数別の費用相場」。中央に費用一覧表：10坪→6〜10万円、20坪→12〜20万円、30坪→18〜30万円、40坪→24〜40万円。右にシロアリと床下木材のイラスト。カラーは濃い緑・木目・オレンジ・白。日本語テキストあり。'
    },
    {
        'file': '02-methods.png',
        'label': '工法比較',
        'prompt': 'バリア工法とベイト工法の比較インフォグラフィック。横長16:9。フラットイラスト風。タイトル「バリア工法 vs ベイト工法」。左半分：バリア工法（薬剤散布イラスト、即効性・安価・5年保証のテキスト）。右半分：ベイト工法（毒餌ステーションイラスト、環境優しい・高価・時間がかかるのテキスト）。中央に大きな「VS」。緑・オレンジ・白。日本語テキストあり。'
    },
    {
        'file': '03-cost-factors.png',
        'label': '費用が高くなる4ケース',
        'prompt': 'シロアリ駆除費用が高くなる4ケースのインフォグラフィック。横長16:9。フラットイラスト風。タイトル「費用が上がる4つのケース」。2行×2列の4カード：①点検口がない、②被害が広範囲・木材交換必要、③コンクリート基礎への穿孔、④放置で大規模被害。各カードにイラストと説明テキスト。警告オレンジ・茶・濃い緑。日本語テキストあり。'
    },
    {
        'file': '04-free-inspection-trap.png',
        'label': '無料点検の落とし穴',
        'prompt': '悪質なシロアリ無料点検業者の警告インフォグラフィック。横長16:9。フラットイラスト風。タイトル「無料点検の落とし穴！」赤文字で大きく。3つの手口カードを横並び：①過剰に不安を煽る（驚く主婦イラスト）、②虚偽の写真・報告（偽写真イラスト）、③突然の訪問（怪しい業者イラスト）。右端に見分け方チェックリスト。赤・オレンジ・ダークグレー。日本語テキストあり。'
    },
]

def generate(img):
    out = OUT_DIR / img['file']
    if out.exists():
        print(f"  スキップ（既存）: {img['file']}")
        return True

    print(f"  生成中: {img['label']}...")
    try:
        resp = client.images.generate(
            model='gpt-image-1',
            prompt=img['prompt'],
            size='1536x1024',
            quality='medium',
            n=1,
        )
        data = base64.b64decode(resp.data[0].b64_json)
        out.write_bytes(data)
        kb = len(data) // 1024
        print(f"  ✓ {img['file']} ({kb}KB)")
        return True
    except Exception as e:
        print(f"  ✗ 失敗: {e}")
        return False

print('='*50)
print(f'記事: {SLUG}  全{len(IMAGES)}枚生成')
print('='*50)

ok, ng = [], []
for i, img in enumerate(IMAGES):
    print(f"\n[{i+1}/{len(IMAGES)}] {img['file']}")
    if generate(img):
        ok.append(img['file'])
    else:
        ng.append(img['file'])
    if i < len(IMAGES) - 1:
        time.sleep(2)

print(f'\n{"="*50}')
print(f'完了: 成功{len(ok)}枚 / 失敗{len(ng)}枚')

if ok:
    print('\n生成した画像をプレビューで開きます...')
    for f in ok:
        subprocess.Popen(['open', str(OUT_DIR / f)])
        time.sleep(0.3)

if ng:
    print('失敗:', ng)
else:
    print('\n✓ 全画像生成完了！')
    print('OKなら「pushして」と伝えてください。')
