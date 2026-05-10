/**
 * test-article.js
 * shiroari-kujo-hiyo の全画像（5枚）を生成して配置・デプロイする
 *
 * ボット検知回避策：
 * Playwrightで新しいChromeを起動するのではなく、
 * ユーザーのChromeにデバッグポート経由で「接続」する。
 * 実際のChromeプロファイル・Cookie・セッションをそのまま使うのでBotと判定されない。
 *
 * 実行手順：
 *   1. ターミナルAで Chrome をデバッグモードで起動:
 *      open -a "Google Chrome" --args --remote-debugging-port=9222
 *   2. 開いたChromeで chatgpt.com にログイン（済みなら不要）
 *   3. ターミナルBで: node test-article.js
 */

const { chromium } = require('playwright');
const path = require('path');
const fs   = require('fs');
const { execSync } = require('child_process');

const SLUG       = 'shiroari-kujo-hiyo';
const ASSETS_DIR = path.resolve(__dirname, '..', '..', 'public', 'assets', SLUG);
const CHATGPT_URL = 'https://chatgpt.com/';
const MAX_WAIT_MS = 4 * 60 * 1000;

const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---- 生成する5枚 ----
const IMAGES = [
  {
    file: '00-eyecatch.png',
    label: 'アイキャッチ（サムネイル）',
    prompt: `「シロアリ駆除の費用相場｜坪単価・一軒家の料金と業者の選び方」というブログ記事のサムネイル画像を作って。横長16:9。フラットイラスト風。左側に大きなタイトル文字と費用目安「30,000〜150,000円」バッジ、右側に床下で木材を調べる白い防護服の業者と侵食された木のイラスト。カラーは茶色・木目・濃い緑。下部に点検・見積もり・駆除・保証の4アイコン。`
  },
  {
    file: '01-cost-chart.png',
    label: '坪数別費用相場',
    prompt: `シロアリ駆除の費用を坪数別に示したブログ記事用のインフォグラフィック画像を作って。横長16:9。フラットイラスト風。タイトル「坪数別｜シロアリ駆除の費用相場」。中央に費用表：10坪→6〜10万円、20坪→12〜20万円、30坪→18〜30万円、40坪→24〜40万円。表の横に床下の木材とシロアリのイラスト。カラーは木目・濃い緑・オレンジ。`
  },
  {
    file: '02-methods.png',
    label: '工法別比較',
    prompt: `シロアリ駆除のバリア工法とベイト工法を比較したブログ記事用インフォグラフィック画像を作って。横長16:9。フラットイラスト風。タイトル「バリア工法 vs ベイト工法」。左半分：バリア工法（薬剤散布イラスト・即効性・安価・5年保証）。右半分：ベイト工法（毒餌ステーションイラスト・環境に優しい・高価・時間がかかる）。中央に大きな「VS」。カラーは緑・オレンジ・白。`
  },
  {
    file: '03-cost-factors.png',
    label: '費用が高くなる4ケース',
    prompt: `シロアリ駆除費用が高くなる4つのケースを説明したブログ記事用インフォグラフィック画像を作って。横長16:9。フラットイラスト風。タイトル「費用が上がる4つのケース」。4枚のカードを2×2に配置：①点検口がない②被害が広範囲・木材交換必要③コンクリート基礎への穿孔④放置で被害が大規模。各カードに関連イラスト。警告オレンジ・茶・濃い緑カラー。`
  },
  {
    file: '04-free-inspection-trap.png',
    label: '無料点検の落とし穴',
    prompt: `シロアリ無料床下点検の悪質業者を警告するブログ記事用インフォグラフィック画像を作って。横長16:9。フラットイラスト風。タイトル「無料点検の落とし穴！」（赤文字）。3つの手口カードを横並び：①過剰に不安を煽る②虚偽の写真・報告③突然の訪問。右端に「見分け方チェックリスト」。警告赤・オレンジ・ダークグレーカラー。`
  }
];

// ---- ダウンロード ----
async function downloadViaPageFetch(page, url, destPath) {
  const data = await page.evaluate(async (imageUrl) => {
    const res = await fetch(imageUrl);
    if (!res.ok) throw new Error(`fetch ${res.status}`);
    return Array.from(new Uint8Array(await res.arrayBuffer()));
  }, url);
  fs.writeFileSync(destPath, Buffer.from(data));
}

function downloadViaNode(url, destPath) {
  return new Promise((resolve, reject) => {
    const mod = url.startsWith('https') ? require('https') : require('http');
    const file = fs.createWriteStream(destPath);
    mod.get(url, res => {
      if ([301,302].includes(res.statusCode)) {
        file.close();
        return downloadViaNode(res.headers.location, destPath).then(resolve).catch(reject);
      }
      res.pipe(file);
      file.on('finish', () => { file.close(); resolve(); });
    }).on('error', err => { file.close(); reject(err); });
  });
}

// ---- 1枚生成 ----
async function generateOne(page, prompt, destPath, label) {
  console.log(`\n  [生成] ${label}`);

  await page.goto(CHATGPT_URL, { waitUntil: 'domcontentloaded', timeout: 30_000 });
  await sleep(2500);

  // ポップアップを閉じる
  try {
    const btn = page.locator('button[aria-label="Close"]').first();
    if (await btn.isVisible({ timeout: 1500 })) await btn.click();
  } catch { /**/ }

  // 入力欄を探す
  let input = null;
  for (const sel of ['#prompt-textarea', 'div[contenteditable="true"]']) {
    try {
      const el = page.locator(sel).first();
      await el.waitFor({ state: 'visible', timeout: 8000 });
      input = el; break;
    } catch { /**/ }
  }
  if (!input) throw new Error('入力欄が見つかりません');

  await input.click();
  await sleep(300);
  await page.keyboard.press('Meta+a');
  await sleep(150);

  // クリップボード経由で貼り付け
  await page.evaluate((text) => navigator.clipboard.writeText(text), prompt).catch(() => {});
  await page.keyboard.press('Meta+v');
  await sleep(700);

  // 入力確認
  const val = await input.textContent().catch(() => '');
  if (!val || val.trim().length < 5) {
    await input.click();
    await page.keyboard.type(prompt, { delay: 8 });
  }
  await sleep(400);

  // 送信
  let sent = false;
  for (const sel of ['[data-testid="send-button"]', 'button[aria-label="送信"]', 'button[type="submit"]']) {
    try {
      const btn = page.locator(sel).first();
      if (await btn.isVisible({ timeout: 2000 }) && await btn.isEnabled()) {
        await btn.click(); sent = true; break;
      }
    } catch { /**/ }
  }
  if (!sent) await input.press('Enter');

  process.stdout.write('  待機中 ');

  // 画像が現れるまでポーリング
  const start = Date.now();
  let imgSrc = null;
  while (Date.now() - start < MAX_WAIT_MS) {
    await sleep(3000);
    process.stdout.write('.');
    try {
      const imgs = await page.locator('[data-message-author-role="assistant"] img[src]').all();
      for (const img of imgs.reverse()) {
        const src = await img.getAttribute('src').catch(() => null);
        if (src && (src.startsWith('https://') || src.startsWith('blob:'))) {
          imgSrc = src; break;
        }
      }
    } catch { /**/ }
    if (imgSrc) break;
  }
  console.log('');

  if (!imgSrc) throw new Error('タイムアウト：画像が生成されませんでした');

  // 保存
  fs.mkdirSync(path.dirname(destPath), { recursive: true });
  if (imgSrc.startsWith('blob:')) {
    const data = await page.evaluate(async (u) =>
      Array.from(new Uint8Array(await (await fetch(u)).arrayBuffer())), imgSrc);
    fs.writeFileSync(destPath, Buffer.from(data));
  } else {
    try { await downloadViaPageFetch(page, imgSrc, destPath); }
    catch { await downloadViaNode(imgSrc, destPath); }
  }

  const kb = Math.round(fs.statSync(destPath).size / 1024);
  console.log(`  ✓ ${path.basename(destPath)} 保存完了 (${kb}KB)`);
}

// ---- メイン ----
async function main() {
  console.log('='.repeat(55));
  console.log(`記事: ${SLUG}  全${IMAGES.length}枚生成`);
  console.log('='.repeat(55));

  const todo = IMAGES.filter(img => {
    const exists = fs.existsSync(path.join(ASSETS_DIR, img.file));
    if (exists) console.log(`  スキップ（既存）: ${img.file}`);
    return !exists;
  });

  if (todo.length === 0) { console.log('\n✓ 全画像が既に存在します。'); return; }
  console.log(`\n生成対象: ${todo.length}枚`);

  // ---- Chromeのデバッグポートに接続 ----
  console.log('\nChromeのデバッグポートに接続中...');
  let browser;
  try {
    browser = await chromium.connectOverCDP('http://localhost:9222');
  } catch (err) {
    console.error('\n❌ Chromeに接続できませんでした。');
    console.error('   以下の手順でChromeをデバッグモードで起動してください:\n');
    console.error('   1. 今開いているChromeをすべて閉じる（Cmd+Q）');
    console.error('   2. ターミナルで実行:');
    console.error('      open -a "Google Chrome" --args --remote-debugging-port=9222');
    console.error('   3. 開いたChromeで chatgpt.com にログイン');
    console.error('   4. このスクリプトを再実行\n');
    process.exit(1);
  }

  console.log('✓ Chrome接続成功！');

  const context = browser.contexts()[0];
  const page = await context.newPage();

  // ログイン確認
  await page.goto(CHATGPT_URL, { waitUntil: 'domcontentloaded', timeout: 30_000 });
  await sleep(2000);
  const loggedIn = await page.locator('#prompt-textarea, div[contenteditable="true"]')
    .first().isVisible({ timeout: 5000 }).catch(() => false);

  if (!loggedIn) {
    console.log('\n🔐 ChatGPTにログインしてください（ブラウザで）...');
    await page.locator('#prompt-textarea, div[contenteditable="true"]')
      .first().waitFor({ state: 'visible', timeout: 5 * 60_000 });
    console.log('✓ ログイン確認\n');
    await sleep(1500);
  } else {
    console.log('✓ ログイン済み\n');
  }

  // 生成ループ
  const results = { ok: [], ng: [] };
  for (let i = 0; i < todo.length; i++) {
    const img = todo[i];
    const destPath = path.join(ASSETS_DIR, img.file);
    console.log(`\n[${i+1}/${todo.length}] ${img.file}`);
    try {
      await generateOne(page, img.prompt, destPath, img.label);
      results.ok.push(img.file);
    } catch (err) {
      console.error(`  ✗ 失敗: ${err.message}`);
      results.ng.push(img.file);
    }
    if (i < todo.length - 1) {
      console.log('  5秒待機...');
      await sleep(5000);
    }
  }

  await browser.close();

  console.log('\n' + '='.repeat(55));
  console.log(`完了: 成功 ${results.ok.length}枚 / 失敗 ${results.ng.length}枚`);

  if (results.ng.length > 0) {
    console.log('失敗:', results.ng.join(', '));
    console.log('再実行すると失敗分のみ再試行します。');
    return;
  }

  if (results.ok.length > 0) {
    // 生成した画像を全部プレビューで開く
    console.log('\n📸 生成した画像をプレビューで開きます...');
    for (const file of results.ok) {
      const p = path.join(ASSETS_DIR, file);
      execSync(`open "${p}"`);
      await sleep(500);
    }

    // 確認を求める
    console.log('\n' + '='.repeat(55));
    console.log('画像を確認してください。');
    console.log('問題なければ Claude に「OK、pushして」と伝えてください。');
    console.log('='.repeat(55));
    console.log(`\n保存先: ${ASSETS_DIR}`);
    console.log('\n（git push はまだ実行していません）');
  }
}

main().catch(err => { console.error('\n❌', err.message); process.exit(1); });
