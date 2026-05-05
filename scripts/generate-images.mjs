import OpenAI from 'openai';
import { createWriteStream, mkdirSync, readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import https from 'https';

const __dirname = dirname(fileURLToPath(import.meta.url));

const SLUG = process.argv[2];
const API_KEY = process.env.OPENAI_API_KEY;

if (!API_KEY) {
  console.error('❌ OPENAI_API_KEY が設定されていません');
  console.error('   export OPENAI_API_KEY=sk-xxxx を実行してから再試行してください');
  process.exit(1);
}

if (!SLUG) {
  console.error('❌ 記事スラッグを指定してください');
  console.error('   使い方: node scripts/generate-images.mjs suzumebachi-kuchujo-hiyo');
  process.exit(1);
}

const promptsPath = join(__dirname, 'prompts', `${SLUG}.json`);
let prompts;
try {
  prompts = JSON.parse(readFileSync(promptsPath, 'utf-8'));
} catch {
  console.error(`❌ プロンプトファイルが見つかりません: ${promptsPath}`);
  process.exit(1);
}

const outputDir = join(__dirname, '..', 'src', 'assets', SLUG);
mkdirSync(outputDir, { recursive: true });

const client = new OpenAI({ apiKey: API_KEY });

function downloadImage(url, dest) {
  return new Promise((resolve, reject) => {
    const file = createWriteStream(dest);
    https.get(url, (res) => {
      res.pipe(file);
      file.on('finish', () => { file.close(); resolve(); });
    }).on('error', reject);
  });
}

console.log(`\n🎨 ${SLUG} の画像生成を開始します（${prompts.length}枚）\n`);

for (const { filename, prompt } of prompts) {
  console.log(`⏳ 生成中: ${filename}`);
  try {
    const res = await client.images.generate({
      model: 'dall-e-3',
      prompt,
      n: 1,
      size: '1792x1024',
      quality: 'standard',
    });
    const url = res.data[0].url;
    const dest = join(outputDir, filename);
    await downloadImage(url, dest);
    console.log(`✅ 保存: src/assets/${SLUG}/${filename}`);
  } catch (err) {
    console.error(`❌ 失敗: ${filename} — ${err.message}`);
  }
}

console.log('\n✨ 完了！');
