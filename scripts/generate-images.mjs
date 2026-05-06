import OpenAI from 'openai';
import { mkdirSync, readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const SLUG = process.argv[2];
const API_KEY = process.env.OPENAI_API_KEY;

if (!API_KEY) {
  console.error('Error: OPENAI_API_KEY is not set');
  process.exit(1);
}
if (!SLUG) {
  console.error('Usage: node scripts/generate-images.mjs suzumebachi-kuchujo-hiyo');
  process.exit(1);
}

const promptsPath = join(__dirname, 'prompts', `${SLUG}.json`);
const prompts = JSON.parse(readFileSync(promptsPath, 'utf-8'));

const outputDir = join(__dirname, '..', 'src', 'assets', SLUG);
mkdirSync(outputDir, { recursive: true });

const client = new OpenAI({ apiKey: API_KEY });

console.log(`\nGenerating ${prompts.length} images for: ${SLUG}\n`);

for (const { filename, prompt } of prompts) {
  console.log(`Generating: ${filename}`);
  try {
    const res = await client.images.generate({
      model: 'dall-e-3',
      prompt,
      n: 1,
      size: '1792x1024',
      quality: 'standard',
      response_format: 'b64_json',
    });
    const b64 = res.data[0].b64_json;
    const dest = join(outputDir, filename);
    writeFileSync(dest, Buffer.from(b64, 'base64'));
    console.log(`Done: ${filename}`);
  } catch (err) {
    console.error(`Failed: ${filename}`);
    console.error(err);
  }
}

console.log('\nAll done!');
