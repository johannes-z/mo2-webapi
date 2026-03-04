import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const dist = join(import.meta.dir, "..", "dist", "index.html");
let html = readFileSync(dist, "utf-8");
html = html.replace('src="../src/main.tsx"', 'src="./main.js"');
writeFileSync(dist, html);
