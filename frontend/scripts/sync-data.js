import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const frontendDir = resolve(scriptDir, "..");
const projectRoot = resolve(frontendDir, "..");
const dataDir = join(frontendDir, "public", "data");

const files = [
  "ranked_tech_resumes.csv",
  "skill_taxonomy.json",
  "skill_graph.json",
];

mkdirSync(dataDir, { recursive: true });

for (const file of files) {
  const source = join(projectRoot, file);
  const target = join(dataDir, file);

  if (!existsSync(source)) {
    throw new Error(`Missing source data file: ${source}`);
  }

  copyFileSync(source, target);
  console.log(`Copied ${file}`);
}
