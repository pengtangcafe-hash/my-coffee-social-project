/**
 * รับออเดอร์จากแอปเมนู (coffee_app) → บันทึกลง Google Sheet + แจ้งเตือนเข้า Slack
 * วิธีติดตั้ง: อ่าน README.md ในโฟลเดอร์นี้
 */

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('ออเดอร์');
    if (!sheet) sheet = createOrdersSheet_();

    var items = data.items || [];
    var itemsText = items.map(function (it) {
      return it.name + ' x' + it.qty;
    }).join(', ');

    sheet.appendRow([
      new Date(),
      data.table || '-',
      itemsText,
      data.totalCups || 0,
      data.totalPrice || 0,
      JSON.stringify(items),
    ]);

    notifySlack_(data);

    return ContentService.createTextOutput(JSON.stringify({ ok: true }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ ok: false, error: String(err) }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService.createTextOutput('Orders webhook is running.');
}

// แปลง ISO timestamp จากแอป → รูปแบบไทย พ.ศ. เช่น "11/8/2569 11:01"
function formatThaiTime_(isoString) {
  if (!isoString) return '-';
  var d = new Date(isoString);
  if (isNaN(d.getTime())) return '-';
  var beYear = d.getFullYear() + 543;
  var hh = ('0' + d.getHours()).slice(-2);
  var mm = ('0' + d.getMinutes()).slice(-2);
  return d.getDate() + '/' + (d.getMonth() + 1) + '/' + beYear + ' ' + hh + ':' + mm;
}

function createOrdersSheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.insertSheet('ออเดอร์');
  sheet.appendRow(['เวลา', 'โต๊ะ', 'รายการ', 'จำนวนแก้ว', 'ยอดรวม', 'รายละเอียด (JSON)']);
  sheet.setFrozenRows(1);
  return sheet;
}

function notifySlack_(data) {
  var webhookUrl = PropertiesService.getScriptProperties().getProperty('SLACK_WEBHOOK_URL');
  if (!webhookUrl) return; // ยังไม่ตั้งค่า Slack ไว้ — ข้ามไปเงียบๆ (ยังบันทึกชีทได้ตามปกติ)

  var items = data.items || [];
  var lines = items.map(function (it) {
    return '• ' + it.name + ' (' + it.nameTh + ') x' + it.qty + ' = ' + it.subtotal + '.-';
  }).join('\n');

  var text =
    ':bell: *ออเดอร์ใหม่* — โต๊ะ ' + (data.table || '-') + ' · ' + formatThaiTime_(data.timestamp) + '\n' +
    lines + '\n' +
    'รวม ' + (data.totalCups || 0) + ' แก้ว · ยอดชำระ ' + (data.totalPrice || 0) + '.-';

  UrlFetchApp.fetch(webhookUrl, {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify({ text: text }),
    muteHttpExceptions: true,
  });
}
