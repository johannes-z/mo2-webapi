import { cpSync, mkdirSync, existsSync } from "node:fs";
import { join } from "node:path";

const root = join(import.meta.dir, "..");
const src = join(root, "frontend", "dist");
const dest = join(root, "plugin", "dist");

if (!existsSync(src)) {
  console.error("frontend/dist not found. Run build in frontend first.");
  process.exit(1);
}
mkdirSync(dest, { recursive: true });
cpSync(src, dest, { recursive: true });
console.log("Copied frontend/dist → plugin/dist");
