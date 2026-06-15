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
           buyLogs: 'สต็อก-ซื้อเข้า', salesLogs: 'สต็อก-ยอดขาย',
           parSheet: 'สต็อก-par', imgSheet: 'สต็อก-รูป',
           expenses: 'รายจ่าย', slipBills: 'สลิป-บิล',
           quests: 'เควส', achievements: 'ความสำเร็จ',
           plans: 'แผนงาน', loops: 'ลูป',
           questLog: 'บันทึกเควสรายวัน', questHistory: 'ประวัติเควส' };

function doGet(e) {
  if (e.parameter.action === 'loyverse') return loyverseProxy_(e.parameter);
  return json_(buildData_());
}

// ── Loyverse POS proxy ──────────────────────────────────────────────────────
// token เก็บใน: Project Settings → Script Properties → key LOYVERSE_TOKEN
// ห้ามเขียน token ในโค้ด (web นี้ public)
function loyverseProxy_(params) {
  var token = PropertiesService.getScriptProperties().getProperty('LOYVERSE_TOKEN');
  if (!token) return json_({ok: false, error: 'no_token'});
  try {
    var cats  = lvFetchAll_('categories', token);
    var items = lvFetchAll_('items',      token);
    var rec   = lvFetchReceipts_(token, params.from || '', params.to || '');
    if (rec.fetchErr) return json_({ok: false, error: String(rec.fetchErr)});
    return json_({
      ok:         true,
      receipts:   rec.list.map(function(r) {
        return {
          receipt_type: r.receipt_type,
          receipt_date: r.receipt_date,
          total_money:  r.total_money,
          line_items:   (r.line_items || []).map(function(li) {
            return {item_id: li.item_id, item_name: li.item_name,
                    quantity: li.quantity, total_money: li.total_money};
          })
        };
      }),
      items:      items.map(function(it) {
        return {id: it.id, item_name: it.item_name, category_id: it.category_id};
      }),
      categories: cats.map(function(c) { return {id: c.id, name: c.name}; }),
      count:      rec.list.length,
      pages:      rec.pages
    });
  } catch (err) {
    return json_({ok: false, error: String(err)});
  }
}

// ดึงทั้งหมดจาก endpoint ที่ไม่ต้องการ date filter (items, categories)
function lvFetchAll_(key, token) {
  var all = [], cursor = null;
  do {
    var qs = 'limit=250' + (cursor ? '&cursor=' + encodeURIComponent(cursor) : '');
    var resp = UrlFetchApp.fetch('https://api.loyverse.com/v1.0/' + key + '?' + qs, {
      headers: {Authorization: 'Bearer ' + token}, muteHttpExceptions: true
    });
    if (resp.getResponseCode() !== 200) break;
    var data = JSON.parse(resp.getContentText());
    var batch = data[key] || [];
    for (var i = 0; i < batch.length; i++) all.push(batch[i]);
    cursor = data.cursor || null;
  } while (cursor && all.length < 5000);
  return all;
}

// ดึง receipts แบบ cursor pagination (date filter เฉพาะหน้าแรก)
function lvFetchReceipts_(token, from, to) {
  var all = [], cursor = null, pages = 0;
  do {
    var qs = 'limit=250';
    if (!cursor) {
      if (from) qs += '&created_at_min=' + encodeURIComponent(from);
      if (to)   qs += '&created_at_max=' + encodeURIComponent(to);
    } else {
      qs += '&cursor=' + encodeURIComponent(cursor);
    }
    var resp = UrlFetchApp.fetch('https://api.loyverse.com/v1.0/receipts?' + qs, {
      headers: {Authorization: 'Bearer ' + token}, muteHttpExceptions: true
    });
    var code = resp.getResponseCode();
    if (code !== 200) return {list: all, pages: pages, fetchErr: code};
    var data = JSON.parse(resp.getContentText());
    var batch = data.receipts || [];
    for (var i = 0; i < batch.length; i++) all.push(batch[i]);
    cursor = data.cursor || null;
    pages++;
  } while (cursor && all.length < 10000);
  return {list: all, pages: pages};
}

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    if (data.action === 'uploadSlip') return handleUploadSlip_(data);
    writeData_(data);
    return json_({ ok: true, menus: (data.menus || []).length });
  } catch (err) {
    return json_({ ok: false, error: String(err) });
  }
}

function handleUploadSlip_(data) {
  try {
    var blob = Utilities.newBlob(Utilities.base64Decode(data.data), data.mime, data.filename);
    var folders = DriveApp.getFoldersByName('ร้านกาแฟ-สลิป');
    var folder = folders.hasNext() ? folders.next() : DriveApp.createFolder('ร้านกาแฟ-สลิป');
    var file = folder.createFile(blob);
    file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
    var id = file.getId();
    return json_({ ok: true, id: id,
      thumb: 'https://drive.google.com/thumbnail?id=' + id + '&sz=w800',
      view: 'https://drive.google.com/file/d/' + id + '/view' });
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

  // สต็อก-ซื้อเข้า (schema 10 คอลัมน์: วันที่,วัตถุดิบ,จำนวน,หน่วย,ปริมาณต่อหน่วย,ราคา/หน่วย,หมายเหตุ,ร้าน,เวลา,วิธีจ่าย)
  var purchases = [];
  var bv = rows_(SH.buyLogs);
  for (var i = 1; i < bv.length; i++) {
    var r = bv[i];
    var date = String(r[0] || '').trim(), ing = String(r[1] || '').trim();
    if (!date || !ing) continue;
    var qty = r[2] !== '' && r[2] != null ? Number(r[2]) : null;
    var unit = String(r[3] || '').trim() || 'แพ็ค';
    var size = r[4] !== '' && r[4] != null ? Number(r[4]) : null;
    var price = r[5] !== '' && r[5] != null ? Number(r[5]) : null;
    var note = String(r[6] || '').trim();
    var vendor = String(r[7] || '').trim();
    var time = String(r[8] || '').trim();
    var pay = String(r[9] || 'cash').trim();
    purchases.push({ date: date, ing: ing, qty: qty, unit: unit, size: size, price: price, note: note, vendor: vendor, time: time, pay: pay });
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

  // สต็อก-par (schema ใหม่: วัตถุดิบ,จำนวน,หน่วย,ปริมาณต่อหน่วย)
  var par = {}, stock_thr = Number(sm.stock_threshold_pct) || 60;
  var pv = rows_(SH.parSheet);
  for (var i = 1; i < pv.length; i++) {
    var k = String(pv[i][0] || '').trim(); if (!k) continue;
    var cnt = Number(pv[i][1]); if (!(cnt > 0)) continue;
    par[k] = { count: cnt, unit: String(pv[i][2] || 'แพ็ค').trim(), size: Number(pv[i][3]) || 1 };
  }

  // สต็อก-รูป
  var images = {};
  var iv = rows_(SH.imgSheet);
  for (var i = 1; i < iv.length; i++) {
    var k = String(iv[i][0] || '').trim(), url = String(iv[i][1] || '').trim();
    if (k && url) images[k] = url;
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

  // รายจ่าย — อ่านจากแท็บรายเดือน (รายจ่าย-YYYY-MM); fallback แท็บเดิมถ้ายังไม่มี
  var expenses = [];
  var expSheets = ss_().getSheets().filter(function(sh) { return /^รายจ่าย-\d{4}-\d{2}$/.test(sh.getName()); });
  var expSrc = expSheets.length > 0 ? expSheets : [ss_().getSheetByName(SH.expenses)].filter(Boolean);
  expSrc.forEach(function(sh) {
    var ev = sh.getDataRange().getValues();
    for (var i = 1; i < ev.length; i++) {
      var r = ev[i];
      var eid = String(r[0] || '').trim(), edate = String(r[1] || '').trim();
      if (!eid || !edate) continue;
      expenses.push({ id: eid, date: edate, group: String(r[2] || 'fixed').trim(),
        category: String(r[3] || '').trim(), label: String(r[4] || '').trim(),
        amount: Number(r[5]) || 0, color: String(r[6] || '#607d8b').trim(),
        slip: String(r[7] || '').trim(), note: String(r[8] || '').trim(),
        pay: String(r[9] || 'cash').trim(), vendor: String(r[10] || '').trim() });
    }
  });

  var expSlips = {};
  var slv = rows_(SH.slipBills);
  for (var i = 1; i < slv.length; i++) {
    var sk = String(slv[i][0] || '').trim(), su = String(slv[i][1] || '').trim();
    if (sk && su) expSlips[sk] = su;
  }
  // เควส
  var quests = [];
  var qv = rows_(SH.quests);
  for (var i = 1; i < qv.length; i++) {
    var r = qv[i], qid = String(r[0] || '').trim();
    if (!qid) continue;
    quests.push({ id: qid, title: String(r[1]||''), cat: String(r[2]||'plan'),
      time: String(r[3]||''), place: String(r[4]||''), pri: String(r[5]||'med'),
      repeat: String(r[6]||'once'), note: String(r[7]||'') });
  }

  // ความสำเร็จ
  var achievements = [];
  var av = rows_(SH.achievements);
  for (var i = 1; i < av.length; i++) {
    var r = av[i], aid = String(r[0] || '').trim();
    if (!aid) continue;
    var adone = (r[6]===true||r[6]==='TRUE'||r[6]==='true'||r[6]===1||r[6]==='1');
    achievements.push({ id: aid, title: String(r[1]||''), cat: String(r[2]||'milestone'),
      day: Number(r[3]) || 0, icon: String(r[4]||'🎯'), desc: String(r[5]||''),
      done: adone, doneDate: dateStr_(r[7]), doneNote: String(r[8]||'') });
  }

  // แผนงาน (flat rows: id, ประเภท, รายการ, ความสำคัญ, สำเร็จ) → nested object
  var plans = { daily: [], weekly: [], monthly: [] };
  var plv = rows_(SH.plans);
  for (var i = 1; i < plv.length; i++) {
    var r = plv[i], pid = String(r[0]||'').trim();
    if (!pid) continue;
    var ptype = String(r[1]||'daily').trim();
    var pdone = (r[4]===true||r[4]==='TRUE'||r[4]==='true'||r[4]===1||r[4]==='1');
    var item = { id: pid, text: String(r[2]||''), pri: String(r[3]||'med'), done: pdone };
    if (ptype === 'weekly') plans.weekly.push(item);
    else if (ptype === 'monthly') plans.monthly.push(item);
    else plans.daily.push(item);
  }

  // ลูป
  var loops = [];
  var lv = rows_(SH.loops);
  for (var i = 1; i < lv.length; i++) {
    var r = lv[i], lid = String(r[0]||'').trim();
    if (!lid) continue;
    loops.push({ id: lid, title: String(r[1]||''), stage: String(r[2]||''), note: String(r[3]||''), updatedAt: String(r[4]||'') });
  }

  // บันทึกเควสรายวัน: (วันที่, questId, สำเร็จ) → {"YYYY-MM-DD": {questId: true}}
  var questLog = {};
  var qlv = rows_(SH.questLog);
  for (var i = 1; i < qlv.length; i++) {
    var qldate = dateStr_(qlv[i][0]), qlqid = String(qlv[i][1]||'').trim();
    var qldone = (qlv[i][2]===true||qlv[i][2]==='TRUE'||qlv[i][2]==='true'||qlv[i][2]===1||qlv[i][2]==='1');
    if (qldate && qlqid && qldone) {
      if (!questLog[qldate]) questLog[qldate] = {};
      questLog[qldate][qlqid] = true;
    }
  }

  // ประวัติเควส
  var questHistory = [];
  var qhv = rows_(SH.questHistory);
  for (var i = 1; i < qhv.length; i++) {
    var r = qhv[i], hid = String(r[0]||'').trim();
    if (!hid) continue;
    questHistory.push({ id: hid, type: String(r[1]||''), title: String(r[2]||''), date: String(r[3]||''), note: String(r[4]||'') });
  }

  // meta จาก ตั้งค่า
  var questMeta = {
    startDate:      sm.quest_start_date    ? String(sm.quest_start_date)    : '2026-05-31',
    totalDays:      sm.quest_total_days    ? Number(sm.quest_total_days)    : 90,
    targetOpenDay:  sm.quest_target_open_day ? Number(sm.quest_target_open_day) : 30
  };

  return { source: 'Google Sheet', parsed_at: new Date().toISOString(),
           assumptions: asm, catalog: catalog, menus: menus,
           purchases: purchases, sales: sales, expenses: expenses,
           stock: { threshold_pct: stock_thr, par: par, images: images },
           expense_slips: expSlips,
           quests: quests, achievements: achievements, plans: plans, loops: loops,
           questLog: questLog, questHistory: questHistory, questMeta: questMeta };
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
  var qm = data.questMeta || {};
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
    ['stock_threshold_pct', stk.threshold_pct != null ? stk.threshold_pct : 55],
    ['quest_start_date', qm.startDate || '2026-05-31'],
    ['quest_total_days', qm.totalDays != null ? qm.totalDays : 90],
    ['quest_target_open_day', qm.targetOpenDay != null ? qm.targetOpenDay : 30]];
  writeSheet_(SH.settings, srows);

  // สต็อก-ซื้อเข้า (schema 10 คอลัมน์)
  var brows = [['วันที่', 'วัตถุดิบ', 'จำนวน', 'หน่วย', 'ปริมาณต่อหน่วย', 'ราคา/หน่วย', 'หมายเหตุ', 'ร้าน', 'เวลา', 'วิธีจ่าย']];
  (data.purchases || []).forEach(function(p) {
    brows.push([p.date || '', p.ing || '', blank_(p.qty), p.unit || 'แพ็ค', blank_(p.size), blank_(p.price), p.note || '', p.vendor || '', p.time || '', p.pay || 'cash']);
  });
  writeSheet_(SH.buyLogs, brows);

  // สต็อก-ยอดขาย
  var salrows = [['วันที่', 'เมนู', 'จำนวนแก้ว']];
  (data.sales || []).forEach(function(s) { salrows.push([s.date || '', s.menu || '', s.cups || 0]); });
  writeSheet_(SH.salesLogs, salrows);

  // สต็อก-par (schema ใหม่ 4 คอลัมน์)
  var par = stk.par || {};
  var prows = [['วัตถุดิบ', 'จำนวน', 'หน่วย', 'ปริมาณต่อหน่วย']];
  Object.keys(par).forEach(function(k) {
    var p = par[k];
    if (typeof p === 'object') { prows.push([k, p.count || 0, p.unit || 'แพ็ค', p.size || 1]); }
    else { prows.push([k, p, 'แพ็ค', 1]); }
  });
  writeSheet_(SH.parSheet, prows);

  // สต็อก-รูป
  var images = stk.images || {};
  var irows = [['วัตถุดิบ', 'url']];
  Object.keys(images).forEach(function(k) { if (images[k]) irows.push([k, images[k]]); });
  writeSheet_(SH.imgSheet, irows);

  // รายจ่าย — เขียนแยกแท็บรายเดือน (รายจ่าย-YYYY-MM)
  var EXP_HDR = ['id', 'วันที่', 'กลุ่ม', 'หมวด', 'รายการ', 'จำนวนเงิน', 'สี', 'สลิป', 'หมายเหตุ', 'วิธีจ่าย', 'ร้าน/ผู้รับเงิน'];
  var expByMonth = {};
  (data.expenses || []).forEach(function(e) {
    var ym = String(e.date || '').slice(0, 7);
    if (!/^\d{4}-\d{2}$/.test(ym)) return;
    (expByMonth[ym] = expByMonth[ym] || []).push(e);
  });
  var existingMonthTabs = ss_().getSheets()
    .filter(function(sh) { return /^รายจ่าย-\d{4}-\d{2}$/.test(sh.getName()); })
    .map(function(sh) { return sh.getName(); });
  Object.keys(expByMonth).forEach(function(ym) {
    var rows = [EXP_HDR];
    expByMonth[ym].forEach(function(e) {
      rows.push([e.id||'', e.date||'', e.group||'fixed', e.category||'', e.label||'', e.amount||0, e.color||'', e.slip||'', e.note||'', e.pay||'cash', e.vendor||'']);
    });
    writeSheet_('รายจ่าย-'+ym, rows);
  });
  existingMonthTabs.forEach(function(tabName) {
    var ym = tabName.replace('รายจ่าย-', '');
    if (!expByMonth[ym]) {
      var sh = sheet_(tabName); sh.clearContents();
      sh.getRange(1, 1, 1, EXP_HDR.length).setValues([EXP_HDR]);
    }
  });

  // สลิป-บิล [คีย์, ลิงก์]
  var expSlips = data.expense_slips || {};
  var slrows = [['คีย์', 'ลิงก์']];
  Object.keys(expSlips).forEach(function(k) { if (expSlips[k]) slrows.push([k, expSlips[k]]); });
  writeSheet_(SH.slipBills, slrows);

  // เควส
  var qrows = [['id','ชื่อ','หมวด','ช่วงเวลา','สถานที่','ความสำคัญ','ทำซ้ำ','หมายเหตุ']];
  (data.quests || []).forEach(function(q) {
    qrows.push([q.id||'', q.title||'', q.cat||'', q.time||'', q.place||'', q.pri||'', q.repeat||'', q.note||'']);
  });
  writeSheet_(SH.quests, qrows);

  // ความสำเร็จ
  var arows = [['id','ชื่อ','หมวด','เป้าหมายวัน','ไอคอน','รายละเอียด','สำเร็จ','วันที่สำเร็จ','บันทึก']];
  (data.achievements || []).forEach(function(a) {
    arows.push([a.id||'', a.title||'', a.cat||'', a.day||0, a.icon||'🎯', a.desc||'', a.done?'TRUE':'FALSE', a.doneDate||'', a.doneNote||'']);
  });
  writeSheet_(SH.achievements, arows);

  // แผนงาน (flat: id, ประเภท, รายการ, ความสำคัญ, สำเร็จ)
  var plrows = [['id','ประเภท','รายการ','ความสำคัญ','สำเร็จ']];
  var pldata = data.plans || {};
  ['daily','weekly','monthly'].forEach(function(type) {
    (pldata[type] || []).forEach(function(p) {
      plrows.push([p.id||'', type, p.text||'', p.pri||'med', p.done?'TRUE':'FALSE']);
    });
  });
  writeSheet_(SH.plans, plrows);

  // ลูป
  var lrows = [['id','หัวข้อ','ขั้นตอน','บันทึก','อัปเดตเมื่อ']];
  (data.loops || []).forEach(function(l) {
    lrows.push([l.id||'', l.title||'', l.stage||'', l.note||'', l.updatedAt||'']);
  });
  writeSheet_(SH.loops, lrows);

  // บันทึกเควสรายวัน (questLog → flat rows)
  var qlrows = [['วันที่','questId','สำเร็จ']];
  var ql = data.questLog || {};
  Object.keys(ql).sort().forEach(function(date) {
    var dayObj = ql[date] || {};
    Object.keys(dayObj).forEach(function(qid) {
      if (dayObj[qid]) qlrows.push([date, qid, 'TRUE']);
    });
  });
  writeSheet_(SH.questLog, qlrows);

  // ประวัติเควส
  var qhrows = [['id','ประเภท','ชื่อ','วันที่','บันทึก']];
  (data.questHistory || []).forEach(function(h) {
    qhrows.push([h.id||'', h.type||'', h.title||'', h.date||'', h.note||'']);
  });
  writeSheet_(SH.questHistory, qhrows);
}

function blank_(v) { return (v == null) ? '' : v; }

// แปลง Date object (จาก getValues) เป็น YYYY-MM-DD โดยใช้ local date ไม่ใช่ UTC
function dateStr_(v) {
  if (v instanceof Date) {
    var y = v.getFullYear(), m = v.getMonth()+1, d = v.getDate();
    return y + '-' + (m<10?'0':'') + m + '-' + (d<10?'0':'') + d;
  }
  return String(v||'').trim();
}

function writeSheet_(name, rows) {
  var sh = sheet_(name);
  sh.clearContents();
  if (rows.length) sh.getRange(1, 1, rows.length, rows[0].length).setValues(rows);
}
