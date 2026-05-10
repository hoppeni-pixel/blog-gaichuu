#!/usr/bin/env python3
"""
アイキャッチ画像自動生成スクリプト
スタイル: 写真風・日本の住宅・自然な照明・リアル・テキストなし
"""

import os, sys, time, urllib.request
from pathlib import Path
from openai import OpenAI

# .env から APIキー読み込み
env_path = Path(__file__).parent.parent / ".env"
for line in env_path.read_text().splitlines():
    if line.startswith("OPENAI_API_KEY="):
        os.environ["OPENAI_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")

client = OpenAI()

# ---- スラッグ → プロンプト対応表 ----
PROMPTS = {
    # シロアリ
    "shiroari-kujo-hiyo":       "A Japanese pest control specialist in white protective suit using flashlight to inspect wooden beams under the floor of a traditional Japanese house. Photorealistic, natural dim lighting, realistic textures. No text.",
    "shiroari-higai-shoujou":   "Close-up of damaged wooden floor beam in a Japanese house showing signs of termite damage, fine sawdust scattered around. Photorealistic, natural indoor lighting. No text.",
    "shiroari-gyosha-erabi":    "Two pest control professionals in white hazmat suits reviewing a clipboard checklist outside a traditional Japanese wooden house. Photorealistic, natural daylight. No text.",
    "shiroari-akushitsu-gyosha":"A concerned Japanese homeowner reviewing a pest control contract document at a table, looking worried. Photorealistic, natural home lighting. No text.",
    "shiroari-hassei-jiki":     "Termite swarmers flying near a Japanese house window on a warm spring day, natural light coming through. Photorealistic macro-style photo. No text.",
    "shiroari-hoken-tekiyo":    "Japanese pest control company representative showing insurance documents to a homeowner in a living room setting. Photorealistic, natural lighting. No text.",
    "shiroari-jibunde-taisho":  "A Japanese homeowner in casual clothes using a spray bottle to treat wooden floor boards, looking cautious. Photorealistic, natural home lighting. No text.",
    "shiroari-yobo-hiyo":       "Pest control worker in protective gear carefully inspecting the foundation of a Japanese house exterior. Photorealistic, outdoor natural light. No text.",

    # ハチ
    "hachi-no-su-shurui-miwakekata": "Various wasp nests photographed side by side on a white surface, realistic macro photography showing textures. Japanese style homes in soft background. No text.",
    "hachi-no-su-houchi-kiken":      "A large paper wasp nest attached to the eaves of a Japanese house, naturalistic photo showing the layered structure. Photorealistic, natural lighting. No text.",
    "hachi-no-su-shiyakusho-muryo":  "A Japanese city hall building exterior on a sunny day, pest control van parked nearby. Photorealistic, natural outdoor light. No text.",
    "suzumebachi-jibunde-kujo":      "A cautious Japanese homeowner in protective gardening gear carefully approaching a small wasp nest with a spray can. Photorealistic, natural outdoor lighting. No text.",
    "suzumebachi-jiki-kiken":        "A hornets nest in autumn leaves near a Japanese house eave, dramatic natural light highlighting the nest texture. Photorealistic. No text.",
    "suzumebachi-kuchujo-hiyo":      "Pest control specialist in full protective suit using pole-mounted sprayer to treat a high hornets nest on a Japanese house. Photorealistic, natural light. No text.",
    "ashinagabachi-kujo-hiyo":       "A small paper wasp nest with wasps visible on the cells, photographed under the eave of a Japanese house. Photorealistic macro photo, natural lighting. No text.",
    "mitsubachi-kujo-hiyo":          "A honeybee swarm clustered on a tree branch near a Japanese suburban house, natural outdoor lighting. Photorealistic, warm sunlight. No text.",
    "hachi-kujo-akushitsu-gyosha":   "Japanese homeowner looking frustrated while reviewing a pest control invoice at home. Photorealistic, natural indoor lighting. No text.",
    "hachi-yobo-taisaku":            "Pest control professional sealing gaps in the eave of a Japanese house to prevent wasp nesting. Photorealistic, natural outdoor daylight. No text.",

    # ゴキブリ
    "gokiburi-kujo-gyosha-hiyo":  "Pest control technician in uniform placing gel bait in a Japanese kitchen cabinet. Photorealistic, natural indoor kitchen lighting. No text.",
    "gokiburi-shurui-miwakekata": "Several different cockroach specimens photographed from above on a plain surface, professional entomology-style photo. Photorealistic, studio lighting. No text.",
    "gokiburi-deta-taisho":       "A Japanese homeowner in a kitchen at night, surprised expression, holding a rolled newspaper. Clean kitchen background. Photorealistic, indoor lighting. No text.",
    "gokiburi-tamago-taisho":     "Close-up macro photo of cockroach egg case on a wooden surface in a dark cabinet corner. Photorealistic. No text.",
    "gokiburi-yobo-taisaku":      "Japanese homeowner carefully sealing kitchen cabinet gaps with caulk, pest prevention work in a clean modern kitchen. Photorealistic. No text.",
    "gokiburi-dairyou-hassei":    "Japanese homeowner looking disturbed at multiple cockroaches near a trash area in the kitchen. Photorealistic, indoor lighting. No text.",
    "gokiburi-fuyu-deru":         "A cockroach on a wooden floor near a warm heater in a Japanese home during winter. Photorealistic, warm indoor light. No text.",
    "gokiburi-akushitsu-gyosha":  "Concerned Japanese homeowner reviewing a pest control bill at a kitchen table with a worried expression. Photorealistic, natural indoor light. No text.",

    # ねずみ
    "nezumi-kujo-hiyo":        "Pest control professional placing a rodent trap under the floor of a Japanese house. Photorealistic, flashlight illuminating the dark crawl space. No text.",
    "nezumi-doko-kara-hairu":  "Close-up of a small gap in the foundation of a Japanese house where a mouse could enter, natural outdoor light. Photorealistic. No text.",
    "nezumi-houchi-kiken":     "Chewed electrical wiring in the wall cavity of a Japanese house, torch light revealing the damage. Photorealistic. No text.",
    "nezumi-jibunde-kujo":     "Japanese homeowner carefully setting a snap trap near a wall in a home storage room. Photorealistic, natural indoor lighting. No text.",
    "nezumi-yobo-hoho":        "Pest control worker sealing entry points at the base of a Japanese house exterior wall with steel wool and sealant. Photorealistic, natural daylight. No text.",
    "nezumi-fun-taisho":       "Pest control specialist in protective gloves and mask cleaning rodent droppings from a Japanese kitchen cabinet. Photorealistic. No text.",
    "nezumi-wana-ko-ka":       "Various rodent traps laid out on a wooden floor in a Japanese storage room. Photorealistic, natural indoor lighting. No text.",
    "nezumi-akushitsu-gyosha": "Japanese homeowner looking worried while on the phone, reviewing a high pest control invoice. Photorealistic, natural indoor light. No text.",

    # その他害虫
    "ari-kujo-hiyo":              "Pest control specialist spraying ant trails along the exterior base of a Japanese house. Photorealistic, natural outdoor daylight. No text.",
    "dani-kujo-hiyo":             "Close-up macro photo of a dust mite on a tatami mat fiber. Photorealistic microscopic-style. Natural indoor light. No text.",
    "mukade-kujo-hiyo":           "A centipede on a bathroom floor tile in a Japanese house at night, natural bathroom lighting. Photorealistic. No text.",
    "nomi-kujo-hiyo":             "A pet cat scratching itself in a Japanese living room, visible discomfort from flea irritation. Photorealistic, warm natural light. No text.",
    "tokojirami-kujo-hiyo":       "Close-up of a mattress seam showing bed bug evidence in a Japanese apartment. Photorealistic, natural light from window. No text.",
    "hakubishin-kujo-hiyo":       "A masked palm civet on a Japanese house rooftop at night, caught by motion light. Photorealistic, dramatic night lighting. No text.",
    "itachi-kujo-hiyo":           "A weasel sneaking into a Japanese house attic through a gap in the eave, natural outdoor light. Photorealistic. No text.",
    "karasu-taisaku-hiyo":        "A crow ripping open a garbage bag outside a Japanese house, morning light. Photorealistic, natural outdoor lighting. No text.",
    "koumori-kujo-hiyo":          "Bats roosting in the dark attic of a Japanese house, flashlight illuminating the scene. Photorealistic. No text.",
    "mogura-kujo-hiyo":           "Mole tunnel mounds visible in a Japanese garden lawn, natural daylight. Photorealistic, outdoor lighting. No text.",

    # 複数カテゴリ（その他）
    "gaichuu-kujo-hiyo-souba":    "Pest control professional in uniform handing an estimate document to a Japanese homeowner at the front door. Photorealistic, natural outdoor light. No text.",
    "gaichuu-kujo-hojokin":       "Japanese couple reviewing a city subsidy document for pest control at a kitchen table. Photorealistic, warm indoor light. No text.",
    "gaichuu-jibunde-kujo-genkai":"Japanese homeowner in protective gear spraying insecticide in a closet, looking determined. Photorealistic, natural indoor light. No text.",
    "gyosha-erabi-checklist":     "Pest control professional and Japanese homeowner shaking hands at front door after inspection. Photorealistic, natural outdoor daylight. No text.",
    "hikkoshi-gaichuu-yobo":      "Moving boxes in an empty Japanese apartment room, pest control spray can visible in the foreground. Photorealistic, natural indoor light. No text.",
    "chintai-gaichuu-taisho":     "Japanese landlord and tenant reviewing pest control options at a table. Photorealistic, natural indoor light. No text.",
}

BASE = "Photorealistic photo, natural lighting, realistic texture, no text, no watermark, no logo. "

def default_prompt(slug):
    """スラッグからカテゴリを推測してデフォルトプロンプトを返す"""
    if "shiroari" in slug:
        return BASE + "Pest control specialist in white protective suit inspecting wooden beams under the floor of a traditional Japanese house with a flashlight. Natural dim lighting."
    elif "hachi" in slug or "suzumebachi" in slug or "mitsubachi" in slug or "ashinagabachi" in slug:
        return BASE + "Pest control professional in protective suit removing a wasp nest from the eave of a Japanese house. Natural outdoor lighting."
    elif "gokiburi" in slug:
        return BASE + "Pest control technician in uniform inspecting a Japanese kitchen cabinet with a flashlight. Natural indoor lighting."
    elif "nezumi" in slug:
        return BASE + "Pest control specialist inspecting the crawl space under a Japanese house with a flashlight. Natural dim lighting."
    else:
        return BASE + "Pest control professional in uniform inspecting a Japanese house exterior. Natural outdoor daylight."

def generate_image(slug, output_path):
    prompt_text = PROMPTS.get(slug) or default_prompt(slug)
    full_prompt = BASE + prompt_text if not prompt_text.startswith(BASE) else prompt_text

    print(f"  生成中: {slug}")
    print(f"  プロンプト: {full_prompt[:80]}...")

    try:
        resp = client.images.generate(
            model="dall-e-3",
            prompt=full_prompt,
            size="1792x1024",
            quality="standard",
            n=1,
        )
        url = resp.data[0].url
        output_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, output_path)
        print(f"  ✓ 保存: {output_path}")
        return True
    except Exception as e:
        print(f"  ✗ エラー [{slug}]: {e}")
        return False

def main():
    public_dir = Path(__file__).parent.parent / "public" / "assets"

    # 未生成のスラッグを収集
    missing = []
    for slug in PROMPTS.keys():
        img = public_dir / slug / "00-eyecatch.png"
        if not img.exists():
            missing.append(slug)

    # PROMPTS に載っていないスラッグも拾う
    for d in public_dir.iterdir():
        if d.is_dir():
            img = d / "00-eyecatch.png"
            if not img.exists() and d.name not in missing and d.name not in PROMPTS:
                missing.append(d.name)

    # public/assets に存在しない＋content/blog に存在するスラッグを確認
    blog_dir = Path(__file__).parent.parent / "src" / "content" / "blog"
    all_slugs = set()
    for f in blog_dir.glob("*.mdx"):
        for line in f.read_text().splitlines():
            if line.startswith("heroImage:"):
                slug = line.split("/assets/")[1].split("/")[0].strip().strip("'")
                all_slugs.add(slug)

    for slug in all_slugs:
        img = public_dir / slug / "00-eyecatch.png"
        if not img.exists() and slug not in missing:
            missing.append(slug)

    print(f"未生成: {len(missing)} 件")
    print()

    ok = 0
    ng = []
    for i, slug in enumerate(missing):
        print(f"[{i+1}/{len(missing)}]", end=" ")
        output = public_dir / slug / "00-eyecatch.png"
        if generate_image(slug, output):
            ok += 1
        else:
            ng.append(slug)
        if i < len(missing) - 1:
            time.sleep(3)  # レート制限対策

    print()
    print(f"=== 完了: 成功 {ok}件 / 失敗 {len(ng)}件 ===")
    if ng:
        print("失敗スラッグ:", ng)

if __name__ == "__main__":
    main()
