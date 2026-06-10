const fs = require('fs'), vm = require('vm');
const path = process.argv[2];
if (!path) { console.error('usage: node check_js_syntax.js <html>'); process.exit(2); }
const html = fs.readFileSync(path, 'utf8');
const re = /<script>([\s\S]*?)<\/script>/g;
let m, i = 0, bad = 0;
while ((m = re.exec(html))) {
  i++;
  const code = m[1];
  if (code.trim().length < 50) continue;          // ข้าม <script src=...> / บล็อกสั้น
  try {
    new vm.Script(code, { filename: 'inline#' + i });
  } catch (e) {
    bad++;
    const ln = html.slice(0, m.index).split('\n').length;
    const near = (e.stack || '').split('\n').slice(1, 3).join(' | ');
    console.error('  ✗ inline script #' + i + ' (~html line ' + ln + '): ' + e.message);
    if (near) console.error('    ' + near);
  }
}
if (bad) { console.error('❌ JS SYNTAX CHECK FAILED — ' + bad + ' script block(s) เสีย (อย่า deploy!)'); process.exit(1); }
console.log('✅ JS syntax OK (' + i + ' script blocks)');
