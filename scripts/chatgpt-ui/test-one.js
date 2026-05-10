/**
 * テスト用：1枚だけ生成して /tmp/test_chatgpt_eyecatch.png に保存する
 */

const { chromium } = require('playwright');
const path = require('path');
const fs   = require('fs');

const CHROME_EXECUTABLE = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const CHROME_USER_DATA  = path.join(process.env.HOME, '.chatgpt-image-gen-profile');
const OUT_PATH          = '/tmp/test_chatgpt_eyecatch.png';
const CHATGPT_URL       = 'https://chatgpt.com/';
const MAX_WAIT_MS       = 3 * 60 * 1000;

const sleep = ms => new Promise(r => setTimeout(r, ms));

// テストするプロンプト（シロアリ駆除の費用相場）
const TEST_PROMPT = `「シロアリ駆除の費用相場｜坪単価・一軒家の料金と業者の選び方」というブログ記事のサムネイル画像を作って。横長16:9。フラットイラスト風。左側に大きなタイトル文字と費用目安「30,000〜150,000円」バッジ、右側に床下で木材を調べる白い防護服の業者と侵食された木のイラスト。カラーは茶色・木目・濃い緑。下部に点検・見積もり・駆除・保証の4アイコン。`;

async function downloadViaPageFetch(page, url, destPath) {
  const data = await page.evaluate(async (imageUrl) => {
    const res = await fetch(imageUrl);
    if (!res.ok) throw new Error(`fetch failed: ${res.status}`);
    const buf = await res.arrayBuffer();
    return Array.from(new Uint8Array(buf));
  }, url);
  fs.writeFileSync(destPath, Buffer.from(data));
}

function downloadViaNode(url, destPath) {
  return new Promise((resolve, reject) => {
    const https = require('https');
    const http  = require('http');
    const client = url.startsWith('https') ? https : http;
    const file = fs.createWriteStream(destPath);
    client.get(url, res => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        file.close();
        return downloadViaNode(res.headers.location, destPath).then(resolve).catch(reject);
      }
      res.pipe(file);
      file.on('finish', () => { file.close(); resolve(); });
    }).on('error', err => { file.close(); reject(err); });
  });
}

async function main() {
  console.log('='.repeat(50));
  console.log('テスト：1枚だけ生成');
  console.log('='.repeat(50));
  console.log(`保存先: ${OUT_PATH}\n`);

  const context = await chromium.launchPersistentContext(CHROME_USER_DATA, {
    executablePath: CHROME_EXECUTABLE,
    headless: false,
    viewport: { width: 1280, height: 800 },
    args: ['--no-first-run', '--no-default-browser-check'],
    ignoreDefaultArgs: ['--enable-automation'],
    slowMo: 80,
  });

  const page = await context.newPage();
  await page.goto(CHATGPT_URL, { waitUntil: 'domcontentloaded', timeout: 30_000 });
  await sleep(2000);

  // ログイン確認
  const loggedIn = await page.locator('#prompt-textarea, div[contenteditable="true"]')
    .first().isVisible({ timeout: 5000 }).catch(() => false);

  if (!loggedIn) {
    console.log('🔐 ChatGPTにログインしてください。ログイン後に自動で続きます...');
    await page.locator('#prompt-textarea, div[contenteditable="true"]')
      .first().waitFor({ state: 'visible', timeout: 5 * 60_000 });
    console.log('✓ ログイン確認\n');
    await sleep(1500);
  } else {
    console.log('✓ ログイン済み\n');
  }

  // 入力欄を探す
  const inputSels = ['#prompt-textarea', 'div[contenteditable="true"]'];
  let input = null;
  for (const sel of inputSels) {
    try {
      const el = page.locator(sel).first();
      await el.waitFor({ state: 'visible', timeout: 5000 });
      input = el;
      break;
    } catch { /**/ }
  }
  if (!input) throw new Error('入力欄が見つかりません');

  // プロンプト入力
  await input.click();
  await sleep(300);
  await page.keyboard.press('Meta+a');
  await sleep(200);

  // クリップボード経由でペースト
  await page.evaluate((text) => navigator.clipboard.writeText(text), TEST_PROMPT)
    .catch(() => {});
  await page.keyboard.press('Meta+v');
  await sleep(600);

  // 入力されたか確認、されていなければ直接入力
  const val = await input.textContent().catch(() => '');
  if (!val || val.trim().length < 5) {
    await input.click();
    await page.keyboard.press('Meta+a');
    await page.keyboard.type(TEST_PROMPT, { delay: 10 });
  }

  await sleep(400);

  // 送信
  const sendSels = ['[data-testid="send-button"]', 'button[aria-label="送信"]', 'button[type="submit"]'];
  let sent = false;
  for (const sel of sendSels) {
    try {
      const btn = page.locator(sel).first();
      if (await btn.isVisible({ timeout: 2000 }) && await btn.isEnabled({ timeout: 1000 })) {
        await btn.click(); sent = true; break;
      }
    } catch { /**/ }
  }
  if (!sent) await input.press('Enter');

  console.log('送信完了。生成待機中（最大3分）...');

  // 画像が出るまで待つ
  let imgSrc = null;
  const start = Date.now();
  while (Date.now() - start < MAX_WAIT_MS) {
    await sleep(3000);
    process.stdout.write('.');
    const imgs = await page.locator('[data-message-author-role="assistant"] img[src]').all();
    for (const img of imgs.reverse()) {
      const src = await img.getAttribute('src').catch(() => null);
      if (src && (src.startsWith('https://') || src.startsWith('blob:'))) {
        imgSrc = src; break;
      }
    }
    if (imgSrc) break;
  }
  console.log('');

  if (!imgSrc) {
    await page.screenshot({ path: '/tmp/debug_chatgpt.png' });
    throw new Error('タイムアウト：画像が生成されませんでした（/tmp/debug_chatgpt.png を確認）');
  }

  // ダウンロード
  console.log('ダウンロード中...');
  if (imgSrc.startsWith('blob:')) {
    const data = await page.evaluate(async (url) => {
      const buf = await (await fetch(url)).arrayBuffer();
      return Array.from(new Uint8Array(buf));
    }, imgSrc);
    fs.writeFileSync(OUT_PATH, Buffer.from(data));
  } else {
    try {
      await downloadViaPageFetch(page, imgSrc, OUT_PATH);
    } catch {
      await downloadViaNode(imgSrc, OUT_PATH);
    }
  }

  const sizeKB = Math.round(fs.statSync(OUT_PATH).size / 1024);
  console.log(`\n✓ 保存完了: ${OUT_PATH} (${sizeKB}KB)`);
  console.log('\nプレビューを開きます...');

  const { execSync } = require('child_process');
  execSync(`open "${OUT_PATH}"`);

  console.log('\n画像を確認してください。');
  console.log('OKなら本番46枚の生成に進みます。');

  await context.close();
}

main().catch(err => {
  console.error('\n❌ エラー:', err.message);
  process.exit(1);
});
