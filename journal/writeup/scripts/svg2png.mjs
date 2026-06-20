// Render an SVG to PNG for visual review. Uses the globally-installed `sharp`
// (bundles librsvg; no system packages / root needed).
//   NODE_PATH=$(npm root -g) node writeup/scripts/svg2png.mjs in.svg out.png [width]
import { readFileSync } from "node:fs"
import { createRequire } from "node:module"
import { execSync } from "node:child_process"

// Resolve the globally-installed sharp (ESM import ignores NODE_PATH).
const require = createRequire(import.meta.url)
const globalRoot = execSync("npm root -g").toString().trim()
const sharp = require(`${globalRoot}/sharp`)

const [, , input, output, width] = process.argv
if (!input || !output) {
  console.error("usage: svg2png.mjs <in.svg> <out.png> [width]")
  process.exit(1)
}
sharp(readFileSync(input), { density: 200 })
  .resize({ width: width ? Number(width) : 1120 })
  .png()
  .toFile(output)
  .then(() => console.log("wrote", output))
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
