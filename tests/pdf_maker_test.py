"""PDF Maker (apps/pdf-maker): text + pictures -> a real PDF, made in the page with no libraries and no internet.
Runs the app under the player's rules, makes a PDF, then reads it back here (header, xref offsets, pages, picture).
    python tests/pdf_maker_test.py"""
import base64, re

import harness

MAKE = """(async () => { const P = F.PDFMAKER, d = F.document;
  const c = d.createElement('canvas'); c.width = 300; c.height = 200; const g = c.getContext('2d');
  g.fillStyle = '#c33'; g.fillRect(0, 0, 300, 200); g.fillStyle = '#fff'; g.fillRect(50, 50, 100, 60);
  const blob = await new Promise(ok => c.toBlob(ok, 'image/png'));
  P.pics.push(await P.toJpeg(new File([blob], 'red.png', {type: 'image/png'})));
  d.getElementById('title').value = 'Test (doc) \\\\ one';
  d.getElementById('text').value = 'Hello \\u201Cworld\\u201D \\u2014 caf\\u00e9.\\n\\n' + 'word '.repeat(2000) + '\\n---\\nPage after a break. \\u4f60\\u597d';
  const r = P.makePdf(); const buf = new Uint8Array(await r.blob.arrayBuffer());
  let s = ''; for (let i = 0; i < buf.length; i++) s += String.fromCharCode(buf[i]);
  window.__pdf = btoa(s); window.__pages = r.pages; })().catch(e => window.__err = String(e));"""


def test(page, check):
    base = harness.serve()
    page.go(base + "frame.html?/walled/apps/pdf-maker")
    check("PDF Maker opens in the player", page.until("F && F.PDFMAKER && !!F.document.getElementById('make')", 15))
    page.js(MAKE)
    check("it makes a PDF with no errors", page.until("!!window.__pdf || !!window.__err", 20) and not page.js("window.__err || ''"), page.js("window.__err || ''"))
    raw = base64.b64decode(page.js("window.__pdf || ''") or "")
    check("the file starts like a PDF and ends with %%EOF", raw.startswith(b"%PDF-1.4") and raw.rstrip().endswith(b"%%EOF"), raw[:20])
    m = re.search(rb"startxref\n(\d+)\n%%EOF", raw)
    xref = int(m.group(1)) if m else -1
    check("startxref points at the xref table", raw[xref:xref + 4] == b"xref", xref)
    rows = re.findall(rb"(\d{10}) 00000 n ", raw[xref:])
    bad = [i + 1 for i, r in enumerate(rows) if not raw[int(r):].startswith(b"%d 0 obj" % (i + 1))]
    check("every xref offset lands on its object", rows and not bad, bad)
    count = re.search(rb"/Type /Pages /Kids \[[^\]]*\] /Count (\d+)", raw)
    pages = len(re.findall(rb"/Type /Page /Parent", raw))
    check("long text flows onto more pages and --- starts a new one (3+ pages)", count and int(count.group(1)) == pages >= 3, pages)
    check("the picture is in as a JPEG", b"/Subtype /Image" in raw and b"/DCTDecode" in raw and b"\xff\xd8\xff" in raw)
    lens = re.findall(rb"/Length (\d+) >>\nstream\n", raw)
    ok = all(raw[mm.end():mm.end() + int(mm.group(1)) + 10].endswith(b"\nendstream") or
             raw[mm.end() + int(mm.group(1)):mm.end() + int(mm.group(1)) + 10] == b"\nendstream"
             for mm in re.finditer(rb"/Length (\d+) >>\nstream\n", raw))
    check("every stream's /Length is right", lens and ok)
    check("brackets and backslashes in text are escaped", b"(Test \\(doc\\) \\\\ one)" in raw)
    check("smart quotes/dashes become plain ones; other scripts become ?", b'Hello "world" -- caf\xe9.' in raw and b"break. ??" in raw)


harness.run(test)
