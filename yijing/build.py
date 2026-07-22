#!/usr/bin/env python3
"""易經文章 — 選用的本機預覽產生器。

讀取 yijing/articles/ 底下的 Markdown 文章（含 front matter），
產生一個可在瀏覽器預覽的靜態網站到 docs/。

注意：docs/ 只是預覽用，已被 .gitignore，**不是**你的正式網站
（正式網站在你本機、獨立維護）。這支腳本只是讓你白天生成內容時，
也能先看看渲染效果；晚上回家再由 CLI 把文章併入既有網站。

用法：
    python3 yijing/build.py            # 建置
    python3 yijing/build.py --clean    # 先清空 docs/ 再建置

不需要任何第三方套件（yaml 為選用，沒有也能跑）。
"""
from __future__ import annotations

import argparse
import html
import re
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

# --- 路徑設定 ---------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent          # .../yijing
REPO_ROOT = SCRIPT_DIR.parent                          # repo 根目錄
ARTICLES_DIR = SCRIPT_DIR / "articles"                 # 原始 Markdown
OUTPUT_DIR = REPO_ROOT / "docs"                        # 產生的網站
SITE_TITLE = "易經筆記"
SITE_SUBTITLE = "六十四卦研讀與隨筆"


# --- Front matter 解析 ------------------------------------------------------
def parse_front_matter(text: str) -> tuple[dict, str]:
    """拆出開頭以 --- 包住的 front matter 與正文。"""
    if text.startswith("﻿"):
        text = text.lstrip("﻿")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("\n")
    if parts[0].strip() != "---":
        return {}, text
    end = None
    for i in range(1, len(parts)):
        if parts[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text
    fm_block = "\n".join(parts[1:end])
    body = "\n".join(parts[end + 1:])
    meta = _load_yaml(fm_block)
    return meta, body.lstrip("\n")


def _load_yaml(block: str) -> dict:
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(block)
        return data if isinstance(data, dict) else {}
    except Exception:
        return _naive_yaml(block)


def _naive_yaml(block: str) -> dict:
    """沒有 yaml 套件時的極簡 key: value 解析。"""
    meta: dict = {}
    for line in block.splitlines():
        line = line.rstrip()
        if not line or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip("'\"")
        if value.startswith("[") and value.endswith("]"):
            value = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
        meta[key] = value
    return meta


# --- 極簡 Markdown -> HTML --------------------------------------------------
_INLINE_CODE = re.compile(r"`([^`]+)`")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*(?!\*)([^*]+)\*(?!\*)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _inline(text: str) -> str:
    """處理行內語法。text 尚未 escape。"""
    # 先抽出行內程式碼，避免內部再被其他規則處理
    placeholders: list[str] = []

    def _stash_code(m: re.Match) -> str:
        placeholders.append(html.escape(m.group(1)))
        return f"\x00{len(placeholders) - 1}\x00"

    text = _INLINE_CODE.sub(_stash_code, text)
    text = html.escape(text)
    text = _BOLD.sub(r"<strong>\1</strong>", text)
    text = _ITALIC.sub(r"<em>\1</em>", text)
    text = _LINK.sub(r'<a href="\2">\1</a>', text)

    def _restore(m: re.Match) -> str:
        return f"<code>{placeholders[int(m.group(1))]}</code>"

    text = re.sub(r"\x00(\d+)\x00", _restore, text)
    return text


def markdown_to_html(md: str, heading_shift: int = 1) -> str:
    """把正文轉成 HTML 片段。標題層級 +heading_shift（# -> h2）。"""
    lines = md.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        # 圍欄程式碼
        if stripped.startswith("```"):
            i += 1
            code: list[str] = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(html.escape(lines[i]))
                i += 1
            i += 1  # 跳過結尾 ```
            out.append("<pre><code>" + "\n".join(code) + "</code></pre>")
            continue

        # 空行
        if not stripped:
            i += 1
            continue

        # 水平線
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            out.append("<hr>")
            i += 1
            continue

        # 標題
        m = re.match(r"(#{1,6})\s+(.*)", stripped)
        if m:
            level = min(len(m.group(1)) + heading_shift, 6)
            out.append(f"<h{level}>{_inline(m.group(2).strip())}</h{level}>")
            i += 1
            continue

        # 引用
        if stripped.startswith(">"):
            quote: list[str] = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].lstrip())
                i += 1
            inner = markdown_to_html("\n".join(quote), heading_shift)
            out.append(f"<blockquote>{inner}</blockquote>")
            continue

        # 無序清單
        if re.match(r"[-*+]\s+", stripped):
            items: list[str] = []
            while i < n and re.match(r"[-*+]\s+", lines[i].strip()):
                items.append(re.sub(r"[-*+]\s+", "", lines[i].strip(), count=1))
                i += 1
            lis = "".join(f"<li>{_inline(it)}</li>" for it in items)
            out.append(f"<ul>{lis}</ul>")
            continue

        # 有序清單
        if re.match(r"\d+\.\s+", stripped):
            items = []
            while i < n and re.match(r"\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"\d+\.\s+", "", lines[i].strip(), count=1))
                i += 1
            lis = "".join(f"<li>{_inline(it)}</li>" for it in items)
            out.append(f"<ol>{lis}</ol>")
            continue

        # 段落（連續非空行）
        para: list[str] = []
        while i < n and lines[i].strip() and not _is_block_start(lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        out.append("<p>" + _inline(" ".join(para)) + "</p>")

    return "\n".join(out)


def _is_block_start(stripped: str) -> bool:
    return bool(
        stripped.startswith("```")
        or stripped.startswith(">")
        or re.match(r"#{1,6}\s+", stripped)
        or re.match(r"[-*+]\s+", stripped)
        or re.match(r"\d+\.\s+", stripped)
        or re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped)
    )


# --- 文章模型 ---------------------------------------------------------------
class Article:
    def __init__(self, path: Path):
        raw = path.read_text(encoding="utf-8")
        self.meta, self.body = parse_front_matter(raw)
        self.source = path
        self.slug = str(self.meta.get("slug") or path.stem).strip()
        self.slug = re.sub(r"\s+", "-", self.slug)
        self.title = str(
            self.meta.get("title") or self._first_heading() or path.stem
        ).strip()
        self.hexagram = str(self.meta.get("hexagram", "")).strip()
        self.number = self.meta.get("number")
        self.date = self._parse_date(self.meta.get("date"))
        self.tags = self._parse_tags(self.meta.get("tags"))
        self.summary = str(self.meta.get("summary", "")).strip() or self._auto_summary()

    def _first_heading(self) -> str:
        for line in self.body.splitlines():
            m = re.match(r"#{1,6}\s+(.*)", line.strip())
            if m:
                return m.group(1).strip()
        return ""

    def _auto_summary(self) -> str:
        for line in self.body.splitlines():
            s = line.strip()
            if s and not s.startswith("#") and not s.startswith(">"):
                return s[:80]
        return ""

    @staticmethod
    def _parse_date(value) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if value:
            for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
                try:
                    return datetime.strptime(str(value).strip(), fmt).date()
                except ValueError:
                    continue
        return date.min

    @staticmethod
    def _parse_tags(value) -> list[str]:
        if not value:
            return []
        if isinstance(value, list):
            return [str(v).strip() for v in value if str(v).strip()]
        return [t.strip() for t in re.split(r"[,，]", str(value)) if t.strip()]

    @property
    def sort_key(self):
        num = self.number if isinstance(self.number, int) else 9999
        return (self.date, num, self.title)

    @property
    def date_str(self) -> str:
        return "" if self.date == date.min else self.date.isoformat()

    def content_html(self) -> str:
        return markdown_to_html(self.body)


# --- HTML 版型 --------------------------------------------------------------
def page_shell(title: str, body: str, css_path: str = "assets/style.css") -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{css_path}">
</head>
<body>
<div class="wrap">
{body}
<footer class="site-footer">以 <code>yijing/build.py</code> 自動產生 · {date.today().isoformat()}</footer>
</div>
</body>
</html>
"""


def render_index(articles: list[Article]) -> str:
    cards = []
    for a in articles:
        meta_bits = []
        if a.hexagram:
            meta_bits.append(f'<span class="badge">{html.escape(a.hexagram)}</span>')
        if a.date_str:
            meta_bits.append(f'<span class="date">{a.date_str}</span>')
        tags = "".join(
            f'<span class="tag">{html.escape(t)}</span>' for t in a.tags
        )
        cards.append(
            f"""<article class="card">
  <h2><a href="p/{html.escape(a.slug)}.html">{html.escape(a.title)}</a></h2>
  <div class="card-meta">{''.join(meta_bits)}</div>
  <p class="excerpt">{html.escape(a.summary)}</p>
  <div class="tags">{tags}</div>
</article>"""
        )
    listing = "\n".join(cards) if cards else '<p class="empty">目前還沒有文章。在 <code>yijing/articles/</code> 新增 <code>.md</code> 檔後重新建置即可。</p>'
    body = f"""<header class="site-header">
  <h1>{SITE_TITLE}</h1>
  <p class="subtitle">{SITE_SUBTITLE}</p>
  <p class="count">共 {len(articles)} 篇</p>
</header>
<main class="cards">
{listing}
</main>"""
    return page_shell(SITE_TITLE, body)


def render_article(a: Article) -> str:
    meta_bits = []
    if a.hexagram:
        meta_bits.append(f'<span class="badge">{html.escape(a.hexagram)}</span>')
    if isinstance(a.number, int):
        meta_bits.append(f'<span class="num">第 {a.number} 卦</span>')
    if a.date_str:
        meta_bits.append(f'<span class="date">{a.date_str}</span>')
    tags = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in a.tags)
    body = f"""<p class="back"><a href="../index.html">← 回目錄</a></p>
<article class="post">
  <h1>{html.escape(a.title)}</h1>
  <div class="post-meta">{''.join(meta_bits)}</div>
  <div class="post-body">
{a.content_html()}
  </div>
  <div class="tags">{tags}</div>
</article>"""
    return page_shell(a.title, body, css_path="../assets/style.css")


CSS = """:root{
  --bg:#f7f4ec; --ink:#2b2a26; --muted:#7a746a; --line:#e2dccf;
  --accent:#8a5a2b; --card:#fffdf8;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:-apple-system,"PingFang TC","Noto Sans TC","Microsoft JhengHei",sans-serif;
  line-height:1.8}
.wrap{max-width:760px;margin:0 auto;padding:2.5rem 1.25rem 4rem}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.site-header{text-align:center;border-bottom:2px solid var(--line);padding-bottom:1.5rem;margin-bottom:2rem}
.site-header h1{font-size:2rem;margin:0;letter-spacing:.15em}
.subtitle{color:var(--muted);margin:.4rem 0 0}
.count{color:var(--muted);font-size:.85rem;margin:.75rem 0 0}
.cards{display:flex;flex-direction:column;gap:1rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;
  padding:1.1rem 1.3rem;transition:box-shadow .15s}
.card:hover{box-shadow:0 4px 18px rgba(80,60,30,.10)}
.card h2{margin:0 0 .4rem;font-size:1.2rem}
.card-meta,.post-meta{display:flex;gap:.6rem;align-items:center;flex-wrap:wrap;
  color:var(--muted);font-size:.82rem;margin-bottom:.5rem}
.badge{background:var(--accent);color:#fff;border-radius:5px;padding:.05rem .5rem;
  font-size:.85rem;letter-spacing:.05em}
.excerpt{margin:.3rem 0 .6rem;color:#555}
.tags{display:flex;gap:.4rem;flex-wrap:wrap}
.tag{font-size:.72rem;color:var(--muted);background:#efe9dc;border-radius:20px;
  padding:.1rem .6rem}
.empty{text-align:center;color:var(--muted);padding:3rem 0}
.post h1{font-size:1.6rem;line-height:1.4;margin:.2rem 0 .6rem}
.post-body h2{border-left:4px solid var(--accent);padding-left:.6rem;margin-top:2rem}
.post-body h3{margin-top:1.6rem}
.post-body blockquote{border-left:3px solid var(--line);margin:1rem 0;
  padding:.2rem 1rem;color:var(--muted);background:#fbf8f0}
.post-body pre{background:#2b2a26;color:#f2ede0;padding:1rem;border-radius:8px;
  overflow:auto}
.post-body code{background:#efe9dc;padding:.1rem .35rem;border-radius:4px;
  font-size:.9em}
.post-body pre code{background:none;padding:0}
.back{margin-bottom:1rem;font-size:.9rem}
.site-footer{margin-top:3rem;padding-top:1.5rem;border-top:1px solid var(--line);
  text-align:center;color:var(--muted);font-size:.78rem}
@media(prefers-color-scheme:dark){
  :root{--bg:#1c1a17;--ink:#e8e2d6;--muted:#a49a88;--line:#3a352d;
    --accent:#c99a5b;--card:#242019}
  .excerpt{color:#c3bcaa}.tag{background:#2e2a22}
  .post-body blockquote{background:#221f18}.post-body code{background:#2e2a22}
}
"""


# --- 建置流程 ---------------------------------------------------------------
def build(clean: bool = False) -> int:
    if not ARTICLES_DIR.exists():
        ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

    if clean and OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    (OUTPUT_DIR / "p").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "assets").mkdir(parents=True, exist_ok=True)

    md_files = sorted(
        p for p in ARTICLES_DIR.glob("*.md")
        if not p.name.startswith("_") and not p.name.startswith(".")
    )
    articles = [Article(p) for p in md_files]
    articles.sort(key=lambda a: a.sort_key, reverse=True)

    (OUTPUT_DIR / "assets" / "style.css").write_text(CSS, encoding="utf-8")
    (OUTPUT_DIR / "index.html").write_text(render_index(articles), encoding="utf-8")

    # 為避免舊文章殘留，先清掉 p/ 底下的 html 再重寫
    for old in (OUTPUT_DIR / "p").glob("*.html"):
        old.unlink()
    for a in articles:
        (OUTPUT_DIR / "p" / f"{a.slug}.html").write_text(
            render_article(a), encoding="utf-8"
        )

    # .nojekyll 讓 GitHub Pages 原樣提供檔案
    (OUTPUT_DIR / ".nojekyll").write_text("", encoding="utf-8")

    print(f"✓ 建置完成：{len(articles)} 篇文章 → {OUTPUT_DIR.relative_to(REPO_ROOT)}/")
    for a in articles:
        print(f"    · {a.title}  ({a.source.name})")
    if not articles:
        print("    （尚無文章，只產生了空目錄頁）")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="易經專案網站建置")
    parser.add_argument("--clean", action="store_true", help="建置前先清空 docs/")
    args = parser.parse_args()
    return build(clean=args.clean)


if __name__ == "__main__":
    sys.exit(main())
