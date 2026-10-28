// Rend cv-motion.html image par image et encode en MP4 via ffmpeg.
// Usage : node render.js [out.mp4] [fps] [--stills]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');

const out = process.argv[2] || path.join(__dirname, 'video.mp4');
const fps = Number(process.argv[3] || 60);
const stills = process.argv.includes('--stills');
const DUR = 15;

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto('file://' + path.join(__dirname, 'cv-motion.html') + '?capture');
  await page.evaluate(() => window.ready);

  if (stills) {
    for (const t of [0.9, 1.6, 2.2, 3.0, 4.8, 5.95, 6.4, 8.6, 10.6, 12.2, 13.4, 14.4]) {
      await page.evaluate(t => window.render(t), t);
      await page.screenshot({ path: path.join(path.dirname(out), `still_${t.toFixed(2)}.png`) });
    }
    await browser.close();
    return;
  }

  const ff = spawn('ffmpeg', ['-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.round(DUR * fps);
  for (let f = 0; f < n; f++) {
    await page.evaluate(t => window.render(t), f / fps);
    const buf = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 60 === 0) process.stderr.write(`frame ${f}/${n}\n`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
})();
