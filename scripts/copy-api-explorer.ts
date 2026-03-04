import { cpSync, mkdirSync, existsSync } from "node:fs";
import { join } from "node:path";

const root = join(import.meta.dir, "..");
const src = join(root, "api-explorer", "dist");
const dest = join(root, "plugin", "dist", "api-docs");

if (!existsSync(src)) {
  console.error("api-explorer/dist not found. Run build in api-explorer first.");
  process.exit(1);
}
mkdirSync(dest, { recursive: true });
cpSync(src, dest, { recursive: true });
console.log("Copied api-explorer/dist → plugin/dist/api-docs");
