/**
 * ต้นทุนเครื่องดื่ม — Google Apps Script Web App (backend จิ๋วสำหรับ dashboard)
 * ----------------------------------------------------------------------------
 * แท็บที่ใช้ (สร้างให้อัตโนมัติถ้ายังไม่มีตอนเขียน): 'วัตถุดิบ', 'เมนู', 'สูตร', 'ตั้งค่า'
 *
 * Deploy:
 *   Extensions > Apps Script > วางโค้ดนี้ > Deploy > New deployment
 *   ประเภท: Web app · Execute as: Me · Who has access: Anyone
 *   คัดลอก "Web app URL" (ลงท้าย /exec) ไปวางใน dashboard (ปุ่ม "เชื่อม Sheet")
 *
 * dashboard:
 *   • GET  /exec            → ส่ง JSON ข้อมูลทั้งหมด (catalog + menus + assumptions)
 *   • POST /exec (text)     → รับ JSON แล้วเขียนทับทุกแท็บ
 */

var SH = { cat: 'วัตถุดิบ', menu: 'เมนู', recipe: 'สูตร', settings: 'ตั้งค่า',
           buyLogs: 'สต็อก-ซื้อเข้า', salesLogs: 'สต็อก-ยอดขาย', parSheet: 'สต็อก-par' };

function doGet(e) {
  return json_(buildData_());
}

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    writeData_(data);
    return json_({ ok: true, menus: (data.menus || []).length });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function ss_() { return SpreadsheetApp.getActiveSpreadsheet(); }
function sheet_(name) {
  var s = ss_().getSheetByName(name);
  if (!s) s = ss_().insertSheet(name);
  return s;
}
function rows_(name) {
  var sh = ss_().getSheetByName(name);
  if (!sh) return [];
  return sh.getDataRange().getValues();
}
function num_(x) { return (x === '' || x == null) ? null : Number(x); }

// ── อ่านทุกแท็บ → โครงสร้างเดียวกับ data/drink-costs.json ──
function buildData_() {
  // คลังวัตถุดิบ
  var catalog = {};
  var cv = rows_(SH.cat);
  for (var i = 1; i < cv.length; i++) {
    var r = cv[i], name = String(r[0] || '').trim();
    if (!name) continue;
    var price = Number(r[1]) || 0, qty = Number(r[2]) || 0;
    catalog[name] = { price: price, qty: qty, unit_cost: qty ? +(price / qty).toFixed(5) : 0, unit: String(r[3] || '') };
  }

  // ตั้งค่า
  var asm = {
    overhead: 0.30, margin_factor: 1.6, fixed_cost_monthly: 30000, days_per_month: 30,
    channels: {
      store:   { label: 'หน้าร้าน', gp: 0,     vat: 0 },
      lineman: { label: 'Lineman',  gp: 0.30,  vat: 0.07 },
      shoppee: { label: 'Shoppee',  gp: 0.32,  vat: 0.07 },
      grab:    { label: 'Grab',     gp: 0.251, vat: 0.07 }
    }
  };
  var sv = rows_(SH.settings), sm = {};
  for (var i = 1; i < sv.length; i++) { var k = String(sv[i][0] || '').trim(); if (k) sm[k] = sv[i][1]; }
  if (sm.overhead !== undefined && sm.overhead !== '') asm.overhead = Number(sm.overhead);
  if (sm.margin_factor) asm.margin_factor = Number(sm.margin_factor);
  if (sm.fixed_cost_monthly) asm.fixed_cost_monthly = Number(sm.fixed_cost_monthly);
  if (sm.days_per_month) asm.days_per_month = Number(sm.days_per_month);
  if (sm.gp_lineman !== undefined && sm.gp_lineman !== '') asm.channels.lineman.gp = Number(sm.gp_lineman);
  if (sm.vat_lineman !== undefined && sm.vat_lineman !== '') asm.channels.lineman.vat = Number(sm.vat_lineman);
  if (sm.gp_shoppee !== undefined && sm.gp_shoppee !== '') asm.channels.shoppee.gp = Number(sm.gp_shoppee);
  if (sm.vat_shoppee !== undefined && sm.vat_shoppee !== '') asm.channels.shoppee.vat = Number(sm.vat_shoppee);
  if (sm.gp_grab !== undefined && sm.gp_grab !== '') asm.channels.grab.gp = Number(sm.gp_grab);
  if (sm.vat_grab !== undefined && sm.vat_grab !== '') asm.channels.grab.vat = Number(sm.vat_grab);
  if (sm.stock_threshold_pct !== undefined && sm.stock_threshold_pct !== '') asm.stock_threshold_pct = Number(sm.stock_threshold_pct);

  // สต็อก-ซื้อเข้า
  var purchases = [];
  var bv = rows_(SH.buyLogs);
  for (var i = 1; i < bv.length; i++) {
    var r = bv[i];
    var date = String(r[0] || '').trim(), ing = String(r[1] || '').trim();
    if (!date || !ing) continue;
    purchases.push({ date: date, ing: ing, packs: Number(r[2]) || 0, note: String(r[3] || '').trim() });
  }

  // สต็อก-ยอดขาย
  var sales = [];
  var salv = rows_(SH.salesLogs);
  for (var i = 1; i < salv.length; i++) {
    var r = salv[i];
    var date = String(r[0] || '').trim(), menu = String(r[1] || '').trim();
    if (!date || !menu) continue;
    sales.push({ date: date, menu: menu, cups: Number(r[2]) || 0 });
  }

  // สต็อก-par
  var par = {}, stock_thr = Number(sm.stock_threshold_pct) || 55;
  var pv = rows_(SH.parSheet);
  for (var i = 1; i < pv.length; i++) {
    var k = String(pv[i][0] || '').trim(); if (!k) continue;
    var v = Number(pv[i][1]); if (v > 0) par[k] = v;
  }

  // สูตร (จับกลุ่มตามชื่อเมนู)
  var recByMenu = {};
  var rv = rows_(SH.recipe);
  for (var i = 1; i < rv.length; i++) {
    var mn = String(rv[i][0] || '').trim(), ing = String(rv[i][1] || '').trim();
    if (!mn || !ing) continue;
    (recByMenu[mn] = recByMenu[mn] || []).push({ ing: ing, qty: Number(rv[i][2]) || 0 });
  }

  // เมนู
  var menus = [];
  var mv = rows_(SH.menu);
  for (var i = 1; i < mv.length; i++) {
    var r = mv[i], name = String(r[0] || '').trim();
    if (!name) continue;
    menus.push({
      id: name, name: name, category: String(r[1] || 'coffee').trim(),
      prices: { store: num_(r[2]), lineman: num_(r[3]), shoppee: num_(r[4]), grab: num_(r[5]) },
      seed_cost_cup: num_(r[6]),
      image: String(r[7] || '').trim(),
      recipe: recByMenu[name] || []
    });
  }

  return { source: 'Google Sheet', parsed_at: new Date().toISOString(),
           assumptions: asm, catalog: catalog, menus: menus,
           purchases: purchases, sales: sales,
           stock: { threshold_pct: stock_thr, par: par } };
}

// ── เขียนทับทุกแท็บจาก JSON ที่ dashboard ส่งมา ──
function writeData_(data) {
  data = data || {};

  var cat = data.catalog || {};
  var crows = [['ชื่อ', 'ราคา', 'ปริมาณ', 'หน่วย']];
  Object.keys(cat).forEach(function (k) { var c = cat[k]; crows.push([k, c.price || 0, c.qty || 0, c.unit || '']); });
  writeSheet_(SH.cat, crows);

  var menus = data.menus || [];
  var mrows = [['ชื่อ', 'หมวด', 'หน้าร้าน', 'Lineman', 'Shoppee', 'Grab', 'ต้นทุนตั้งต้น', 'รูปภาพ']];
  menus.forEach(function (m) {
    var p = m.prices || {};
    mrows.push([m.name, m.category || '', blank_(p.store), blank_(p.lineman), blank_(p.shoppee), blank_(p.grab), blank_(m.seed_cost_cup), m.image || '']);
  });
  writeSheet_(SH.menu, mrows);

  var rrows = [['เมนู', 'วัตถุดิบ', 'ปริมาณ']];
  menus.forEach(function (m) { (m.recipe || []).forEach(function (l) { rrows.push([m.name, l.ing, l.qty]); }); });
  writeSheet_(SH.recipe, rrows);

  var a = data.assumptions || {}, ch = a.channels || {}, stk = data.stock || {};
  var srows = [['คีย์', 'ค่า'],
    ['overhead', a.overhead == null ? 0.3 : a.overhead],
    ['margin_factor', a.margin_factor || 1.6],
    ['fixed_cost_monthly', a.fixed_cost_monthly || 30000],
    ['days_per_month', a.days_per_month || 30],
    ['gp_lineman', (ch.lineman || {}).gp || 0],
    ['vat_lineman', (ch.lineman || {}).vat || 0],
    ['gp_shoppee', (ch.shoppee || {}).gp || 0],
    ['vat_shoppee', (ch.shoppee || {}).vat || 0],
    ['gp_grab', (ch.grab || {}).gp || 0],
    ['vat_grab', (ch.grab || {}).vat || 0],
    ['stock_threshold_pct', stk.threshold_pct != null ? stk.threshold_pct : 55]];
  writeSheet_(SH.settings, srows);

  // สต็อก-ซื้อเข้า
  var brows = [['วันที่', 'วัตถุดิบ', 'จำนวนแพ็ค', 'หมายเหตุ']];
  (data.purchases || []).forEach(function(p) { brows.push([p.date || '', p.ing || '', p.packs || 0, p.note || '']); });
  writeSheet_(SH.buyLogs, brows);

  // สต็อก-ยอดขาย
  var salrows = [['วันที่', 'เมนู', 'จำนวนแก้ว']];
  (data.sales || []).forEach(function(s) { salrows.push([s.date || '', s.menu || '', s.cups || 0]); });
  writeSheet_(SH.salesLogs, salrows);

  // สต็อก-par
  var par = (stk.par) || {};
  var prows = [['วัตถุดิบ', 'สต็อกเต็มแพ็ค']];
  Object.keys(par).forEach(function(k) { prows.push([k, par[k]]); });
  writeSheet_(SH.parSheet, prows);
}

function blank_(v) { return (v == null) ? '' : v; }

function writeSheet_(name, rows) {
  var sh = sheet_(name);
  sh.clearContents();
  if (rows.length) sh.getRange(1, 1, rows.length, rows[0].length).setValues(rows);
}
