// gta6-meme-x-01 entrypoint (Node 22, stdlib only).
//
// The entry itself is the X post: the meme picture and the post text are
// what the house reads from X and hands to the judge. This program does
// exactly one job — hand the post's address to the grader by copying the
// repository's POST.json into the output directory.
//
// POST.json still holds the placeholder address until the meme is posted
// and the real post URL is filled in; with the placeholder the gate
// refuses the entry, which is the correct behaviour before posting.
//
// Locally, /bot and /output are stood in for by environment variables:
//   mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const repoRoot = process.env.MAKEFUN_BOT_DIR ?? '/bot';
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';

const source = join(repoRoot, 'POST.json');
const target = join(outDir, 'POST.json');

if (!existsSync(source)) {
  console.error(`No POST.json found in ${repoRoot}; nothing to hand in.`);
  process.exit(1);
}

mkdirSync(outDir, { recursive: true });
writeFileSync(target, readFileSync(source));
