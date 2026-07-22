# 易經文章內容站

這個資料夾是**易經文章的內容暫存／交接站**，用來支援以下工作流程：

- **白天**（電腦不在身邊）：在遠端（Claude Code on the web／手機）依需求生成文章，存成
  Markdown 並 push。
- **晚上**（回家）：本機的 Claude Code CLI 讀取這些文章，併入你**既有的本機網站**並重建／部署。

> 正式網站在你本機、獨立維護，**不在這個 repo**。這裡只存文章原始檔（交接用），
> `docs/` 只是選用預覽，不是你的網站。

## 目錄結構

```
yijing/
├── README.md            # 本說明
├── build.py             # 選用：本機預覽產生器（Markdown → docs/）
├── site.local.md        # 本機網站設定（路徑/格式），gitignore、不上傳
└── articles/            # ★ 文章原始檔（白天在這裡生成）
    ├── _template.md     # 新文章範本（底線開頭者不會被預覽建置）
    └── 2026-07-22-qian.md
docs/                    # 選用預覽產物，gitignore、不是正式網站
```

## 文章格式（可攜，方便晚上轉成你網站的格式）

在 `yijing/articles/` 新增 `.md`，開頭放 front matter：

```markdown
---
title: 坤卦——地勢坤，君子以厚德載物
slug: kun
hexagram: 坤
number: 2
date: 2026-07-23
tags: 上經, 六十四卦
summary: 一到兩句摘要。
---

## 卦象
正文用一般 Markdown 撰寫……
```

| 欄位 | 必填 | 說明 |
|------|------|------|
| `title` | 建議 | 文章標題；省略時取正文第一個標題或檔名 |
| `slug` | 選填 | 建議網址／檔名用的英文代稱；省略時用檔名 |
| `hexagram` | 選填 | 卦名 |
| `number` | 選填 | 卦序（數字），用於排序 |
| `date` | 建議 | `YYYY-MM-DD`，用於排序（新到舊） |
| `tags` | 選填 | 逗號分隔或 `[a, b]` 陣列 |
| `summary` | 選填 | 摘要；省略時自動取正文首段 |

支援標題、段落、**粗體**、*斜體*、`行內碼`、清單、引用、程式碼區塊、水平線、連結。

## 白天：生成內容（遠端）

告訴 Claude 你的需求（哪一卦、切入角度、篇幅、風格），它會產生對應的
`yijing/articles/<日期>-<slug>.md` 並 push。你也可以自己貼草稿讓它整理成正式格式。

（選用）想在白天先看渲染效果：

```bash
python3 yijing/build.py --clean                    # 產生 docs/ 預覽
python3 -m http.server 8000 --directory docs       # http://localhost:8000
```

## 晚上：併入既有網站（本機）

在有既有網站的電腦上，對 Claude Code CLI 說「同步／更新既有網站」即可。流程見 repo 根目錄
`CLAUDE.md`：`git pull` → 取出新文章 → 依你本機網站的格式與位置轉入 → 重建／部署。
第一次會請你指定本機網站路徑與格式，記到 `yijing/site.local.md`（不上傳），之後自動化。
