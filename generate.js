import "dotenv/config";
import OpenAI from "openai";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { execSync } from "child_process";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// ============================================================
// 設定
// ============================================================
const TOTAL_IMAGES = 5;
const PROMPTS_DIR  = path.join(__dirname, "prompts");
const OUTPUT_DIR   = path.join(__dirname, "src", "assets", "shiroari-kujo-hiyo");
const MODEL        = "gpt-image-1";
const SIZE         = "1536x1024";

// ============================================================
// 初期化
// ============================================================
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

// 出力ディレクトリを自動作成
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

// ============================================================
// メイン処理
// ============================================================
async function generateImages() {
  console.log("🎨 シロアリ記事 画像生成スタート");
  console.log(`📁 保存先: ${OUTPUT_DIR}\n`);

  for (let i = 1; i <= TOTAL_IMAGES; i++) {
    const promptFile = path.join(PROMPTS_DIR, `image${i}.txt`);
    const outputFile = path.join(OUTPUT_DIR, `image${i}.png`);

    // プロンプトファイルの存在確認
    if (!fs.existsSync(promptFile)) {
      console.error(`❌ プロンプトファイルが見つかりません: ${promptFile}`);
      continue;
    }

    const prompt = fs.readFileSync(promptFile, "utf-8").trim();

    console.log(`🖼️  [${i}/${TOTAL_IMAGES}] image${i}.png を生成中...`);

    try {
      const result = await openai.images.generate({
        model: MODEL,
        prompt,
        size: SIZE,
        n: 1,
      });

      const b64 = result.data[0].b64_json;

      if (!b64) {
        throw new Error("b64_json が返ってきませんでした");
      }

      const buffer = Buffer.from(b64, "base64");
      fs.writeFileSync(outputFile, buffer);

      const sizeMB = (buffer.length / 1024 / 1024).toFixed(2);
      console.log(`   ✅ 保存完了: image${i}.png (${sizeMB} MB)`);

      // 使用量を自動記録
      try {
        execSync(
          `python3 /Users/yuukisatou/Documents/Claude/Projects/tool/show_balance.py --log openai_image generate 1 ${SIZE} medium "blog image ${i}"`,
          { stdio: "ignore" }
        );
      } catch (_) {}

    } catch (err) {
      console.error(`   ❌ エラー [image${i}]: ${err.message}`);
      if (err.status) {
        console.error(`   ステータス: ${err.status}`);
      }
    }

    // レート制限対策（1枚ごとに2秒待機）
    if (i < TOTAL_IMAGES) {
      await new Promise((r) => setTimeout(r, 2000));
    }
  }

  console.log("\n🎉 全画像生成完了！");
  console.log(`📂 確認: ${OUTPUT_DIR}`);
}

generateImages();
