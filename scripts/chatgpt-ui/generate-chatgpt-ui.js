/**
 * ChatGPT WebUIを自動操作してブログ用アイキャッチ画像を生成するスクリプト
 *
 * 動作の流れ:
 * 1. ユーザーのChromeプロファイルでChatGPTを開く（ログイン済みの状態を引き継ぐ）
 * 2. 日本語プロンプトをそのままChatGPTに入力・送信
 * 3. 画像生成完了を待機
 * 4. 生成された画像をダウンロード
 * 5. public/assets/{slug}/00-eyecatch.png に保存
 *
 * 実行前の注意:
 *   - Google Chrome を完全に終了してから実行すること（プロファイルの競合を避けるため）
 *   - Chromeで chatgpt.com にログイン済みであること
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

// ---- 設定 ----
const CHROME_EXECUTABLE = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
// 専用プロファイル（通常のChromeと競合しない）
const CHROME_USER_DATA  = path.join(process.env.HOME, '.chatgpt-image-gen-profile');
const ASSETS_BASE       = path.resolve(__dirname, '..', '..', 'public', 'assets');
const PROMPTS_FILE      = path.join(__dirname, 'prompts.json');
const CHATGPT_URL       = 'https://chatgpt.com/';

// 生成完了の最大待機時間（ミリ秒）
const MAX_WAIT_MS = 3 * 60 * 1000; // 3分

// 生成間のインターバル（ミリ秒）
const INTERVAL_MS = 6 * 1000; // 6秒

const sleep = ms => new Promise(r => setTimeout(r, ms));

// ---- ユーティリティ ----
function imageExists(slug) {
  return fs.existsSync(path.join(ASSETS_BASE, slug, '00-eyecatch.png'));
}

function ensureDir(slug) {
  const dir = path.join(ASSETS_BASE, slug);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

/**
 * ページのfetchを使って画像をダウンロード（認証Cookieを引き継ぐため）
 */
async function downloadViaPageFetch(page, url, destPath) {
  const data = await page.evaluate(async (imageUrl) => {
    const res = await fetch(imageUrl);
    if (!res.ok) throw new Error(`fetch failed: ${res.status}`);
    const buf = await res.arrayBuffer();
    // Uint8Array → 通常の配列に変換してpostMessageできるようにする
    return Array.from(new Uint8Array(buf));
  }, url);
  fs.writeFileSync(destPath, Buffer.from(data));
}

/**
 * Node.jsのhttpsでシンプルにダウンロード（公開URLの場合）
 */
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
    }).on('error', err => { file.close(); fs.unlink(destPath, () => {}); reject(err); });
  });
}

// ---- メイン処理 ----
async function generateImage(page, prompt, slug) {
  // --- ChatGPT の新しいチャット画面に遷移 ---
  await page.goto(CHATGPT_URL, { waitUntil: 'domcontentloaded', timeout: 30_000 });
  await sleep(2500);

  // ポップアップ・ダイアログを閉じる（あれば）
  try {
    const closeBtn = page.locator('button[aria-label="Close"]').first();
    if (await closeBtn.isVisible({ timeout: 2000 })) await closeBtn.click();
  } catch { /* なければ無視 */ }

  // --- テキスト入力欄を探す ---
  const inputCandidates = [
    '#prompt-textarea',
    '[data-testid="composer-text-input"]',
    'div[contenteditable="true"]',
    'textarea',
  ];

  let input = null;
  for (const sel of inputCandidates) {
    try {
      const el = page.locator(sel).first();
      await el.waitFor({ state: 'visible', timeout: 6000 });
      input = el;
      break;
    } catch { /* 次を試す */ }
  }
  if (!input) throw new Error('テキスト入力欄が見つかりません。ChatGPTのUIが変更された可能性があります。');

  // --- プロンプトを入力 ---
  await input.click();
  await sleep(300);

  // 既存テキストをクリア
  await page.keyboard.press('Control+a');
  await page.keyboard.press('Meta+a');
  await sleep(200);

  // クリップボードに書き込んでペースト（長い日本語テキストをそのまま渡すため）
  await page.evaluate((text) => {
    return navigator.clipboard.writeText(text);
  }, prompt).catch(async () => {
    // clipboard API が使えない場合は直接入力
    await page.keyboard.type(prompt, { delay: 15 });
  });

  // Ctrl+V でペースト
  try {
    await page.keyboard.press('Meta+v');
    await sleep(500);
    // 入力されたか確認
    const val = await input.textContent().catch(() => '');
    if (!val || val.trim().length < 5) {
      // ペーストが効かなかった場合はtype
      await input.click();
      await page.keyboard.press('Meta+a');
      await page.keyboard.type(prompt, { delay: 15 });
    }
  } catch {
    await page.keyboard.type(prompt, { delay: 15 });
  }

  await sleep(500);

  // --- 送信 ---
  const sendCandidates = [
    '[data-testid="send-button"]',
    'button[aria-label="送信"]',
    'button[aria-label="Send message"]',
    'button[type="submit"]',
  ];
  let sent = false;
  for (const sel of sendCandidates) {
    try {
      const btn = page.locator(sel).first();
      if (await btn.isVisible({ timeout: 2000 }) && await btn.isEnabled({ timeout: 1000 })) {
        await btn.click();
        sent = true;
        break;
      }
    } catch { /* 次を試す */ }
  }
  if (!sent) {
    // ボタンが見つからない場合はEnterで送信
    await input.press('Enter');
  }

  console.log('    → 送信完了。生成待機中...');

  // --- 画像が生成されるまで待つ ---
  const startTime = Date.now();
  let imgSrc = null;

  while (Date.now() - startTime < MAX_WAIT_MS) {
    await sleep(3000);

    // アシスタントのメッセージにある img 要素を探す
    try {
      const imgs = await page.locator('[data-message-author-role="assistant"] img[src]').all();
      for (const img of imgs.reverse()) { // 最新のものから
        const src = await img.getAttribute('src').catch(() => null);
        if (src && (src.startsWith('https://') || src.startsWith('blob:'))) {
          imgSrc = src;
          break;
        }
      }
    } catch { /* 取得失敗は無視してリトライ */ }

    if (imgSrc) break;

    // 「生成中」の状態を確認（ストップボタンが消えたら完了）
    const isGenerating = await page.locator('[data-testid="stop-button"]').isVisible({ timeout: 500 }).catch(() => false);
    if (!isGenerating && Date.now() - startTime > 10_000) {
      // 10秒以上経過してストップボタンもない → 生成完了 or エラー
      // もう一度imgを探す
      const imgs = await page.locator('[data-message-author-role="assistant"] img[src]').all();
      for (const img of imgs.reverse()) {
        const src = await img.getAttribute('src').catch(() => null);
        if (src && src.startsWith('http')) { imgSrc = src; break; }
      }
      if (imgSrc) break;
    }

    process.stdout.write('.');
  }
  console.log(''); // 改行

  if (!imgSrc) {
    // スクリーンショットを保存してデバッグ用
    await page.screenshot({ path: `/tmp/debug_${slug}.png` });
    throw new Error(`タイムアウト: ${MAX_WAIT_MS/1000}秒以内に画像が生成されませんでした`);
  }

  // --- ダウンロード ---
  ensureDir(slug);
  const destPath = path.join(ASSETS_BASE, slug, '00-eyecatch.png');

  if (imgSrc.startsWith('blob:')) {
    // blobURLの場合: Canvasに描画してデータを取得
    const pngData = await page.evaluate(async (blobUrl) => {
      const res  = await fetch(blobUrl);
      const buf  = await res.arrayBuffer();
      return Array.from(new Uint8Array(buf));
    }, imgSrc);
    fs.writeFileSync(destPath, Buffer.from(pngData));
  } else {
    // 通常のURLの場合: ページのfetchを試み、失敗したらNode.jsのhttpsを使う
    try {
      await downloadViaPageFetch(page, imgSrc, destPath);
    } catch {
      await downloadViaNode(imgSrc, destPath);
    }
  }

  const sizeKB = Math.round(fs.statSync(destPath).size / 1024);
  console.log(`    ✓ 保存完了: ${destPath} (${sizeKB}KB)`);
}

// ---- エントリポイント ----
async function main() {
  const prompts = JSON.parse(fs.readFileSync(PROMPTS_FILE, 'utf8'));
  const todo = prompts.filter(p => !imageExists(p.slug));

  console.log('='.repeat(60));
  console.log('ChatGPT UI 自動画像生成');
  console.log('='.repeat(60));
  console.log(`対象: ${todo.length}件 / 全${prompts.length}件`);

  if (todo.length === 0) {
    console.log('\n✓ 全ての画像が生成済みです。');
    return;
  }

  // 専用プロファイルが初回の場合はログインを促す
  const isFirstRun = !fs.existsSync(CHROME_USER_DATA);
  if (isFirstRun) {
    console.log('\n📌 初回実行です。ChatGPTへのログインが必要です。');
    console.log('   Chromeが開いたら chatgpt.com にログインしてください。');
    console.log('   ログイン完了後、スクリプトが自動で続きを実行します。\n');
  }
  console.log('3秒後に起動します...\n');
  await sleep(3000);

  // Chrome を起動（ユーザープロファイルを使用）
  let context;
  try {
    context = await chromium.launchPersistentContext(CHROME_USER_DATA, {
      executablePath: CHROME_EXECUTABLE,
      headless: false,          // 実際のウィンドウを表示して操作
      viewport: { width: 1280, height: 800 },
      args: [
        '--profile-directory=Default',
        '--no-first-run',
        '--no-default-browser-check',
        '--disable-blink-features=AutomationControlled', // Bot検知を回避
      ],
      ignoreDefaultArgs: ['--enable-automation'],
      slowMo: 100, // 人間らしい動作に近づけるため少し遅らせる
    });
  } catch (err) {
    console.error('\n❌ Chrome の起動に失敗しました:');
    console.error(err.message);
    console.error('\n対処法: Google Chrome を完全に終了してから再実行してください。');
    process.exit(1);
  }

  const page = await context.newPage();

  // ---- ログイン確認 ----
  await page.goto(CHATGPT_URL, { waitUntil: 'domcontentloaded', timeout: 30_000 });
  await sleep(2000);

  // ログイン済みかチェック（プロンプト入力欄があればOK）
  const isLoggedIn = await page.locator('#prompt-textarea, [data-testid="composer-text-input"], div[contenteditable="true"]')
    .first().isVisible({ timeout: 5000 }).catch(() => false);

  if (!isLoggedIn) {
    console.log('\n🔐 ChatGPTにログインしてください。');
    console.log('   ブラウザウィンドウでログインが完了するまで待機します...');
    // 入力欄が現れるまで最大5分待つ
    await page.locator('#prompt-textarea, [data-testid="composer-text-input"], div[contenteditable="true"]')
      .first().waitFor({ state: 'visible', timeout: 5 * 60_000 });
    console.log('   ✓ ログイン確認。画像生成を開始します。\n');
    await sleep(1500);
  } else {
    console.log('✓ ログイン済みを確認。\n');
  }

  // ---- 生成ループ ----
  const results = { ok: [], ng: [] };

  for (let i = 0; i < todo.length; i++) {
    const { slug, prompt } = todo[i];
    console.log(`\n[${i + 1}/${todo.length}] ${slug}`);
    console.log(`  プロンプト: ${prompt.substring(0, 60)}...`);

    try {
      await generateImage(page, prompt, slug);
      results.ok.push(slug);
    } catch (err) {
      console.error(`  ✗ 失敗: ${err.message}`);
      results.ng.push({ slug, reason: err.message });
    }

    // 次の生成まで少し待つ（ChatGPTへの連続リクエストを避けるため）
    if (i < todo.length - 1) {
      console.log(`  次まで ${INTERVAL_MS / 1000}秒 待機...`);
      await sleep(INTERVAL_MS);
    }
  }

  await context.close();

  // ---- 結果サマリー ----
  console.log('\n' + '='.repeat(60));
  console.log(`完了: 成功 ${results.ok.length}件 / 失敗 ${results.ng.length}件`);
  if (results.ng.length > 0) {
    console.log('\n失敗した記事:');
    results.ng.forEach(({ slug, reason }) => console.log(`  - ${slug}: ${reason}`));
    console.log('\n失敗した記事は再度 node generate-chatgpt-ui.js を実行すると再試行されます。');
  }
  if (results.ok.length > 0) {
    console.log('\n次のステップ: git add & push で本番反映');
    console.log('  cd ../..');
    console.log('  git add public/assets/');
    console.log('  git commit -m "feat: ブログアイキャッチ画像を追加"');
    console.log('  git push');
  }
}

main().catch(err => {
  console.error('\n予期しないエラー:', err.message);
  process.exit(1);
});
