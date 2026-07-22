# 易經筆記專案

用來撰寫易經文章、並自動產生靜態網站的小專案。
白天在任何地方寫好 Markdown 文章，回家後用 Claude Code CLI 一句話即可同步、更新網頁。

## 目錄結構

```
yijing/
├── README.md            # 本說明
├── build.py             # 建置腳本（Markdown → 網站）
└── articles/            # ★ 文章原始檔（在這裡寫作）
    ├── _template.md     # 新文章範本（底線開頭者不會被建置）
    └── 2026-07-22-qian.md
docs/                    # 產生的網站（GitHub Pages 發佈來源，勿手動編輯）
├── index.html
├── p/<slug>.html
└── assets/style.css
```

## 撰寫一篇文章

在 `yijing/articles/` 新增一個 `.md` 檔，開頭放 front matter：

```markdown
---
title: 坤卦——地勢坤，君子以厚德載物
slug: kun
hexagram: 坤
number: 2
date: 2026-07-23
tags: 上經, 六十四卦
summary: 一到兩句摘要，會顯示在目錄卡片上。
---

## 卦象
正文用一般 Markdown 撰寫……
```

Front matter 欄位：

| 欄位 | 必填 | 說明 |
|------|------|------|
| `title` | 建議 | 文章標題；省略時取正文第一個標題或檔名 |
| `slug` | 選填 | 產生的網址檔名 `p/<slug>.html`；省略時用檔名 |
| `hexagram` | 選填 | 卦名，顯示成標籤 |
| `number` | 選填 | 卦序（數字），用於排序與顯示 |
| `date` | 建議 | `YYYY-MM-DD`，用於排序（新到舊） |
| `tags` | 選填 | 逗號分隔或 `[a, b]` 陣列 |
| `summary` | 選填 | 目錄頁摘要；省略時自動取正文首段 |

支援的 Markdown：標題、段落、**粗體**、*斜體*、`行內碼`、清單、引用、
程式碼區塊、水平線、連結。檔名以 `_` 或 `.` 開頭者會被略過（例如範本）。

## 建置網站

```bash
python3 yijing/build.py          # 增量建置
python3 yijing/build.py --clean  # 先清空 docs/ 再全部重建
```

不需安裝任何第三方套件（有 `PyYAML` 會用它解析 front matter，沒有也能運作）。

## 本機預覽

```bash
python3 -m http.server 8000 --directory docs
# 瀏覽器打開 http://localhost:8000
```

## 發佈到 GitHub Pages

到 GitHub 專案的 **Settings → Pages**，把來源設為
**Branch: `main`／資料夾: `/docs`**（已放入 `.nojekyll`，Pages 會原樣提供）。
之後每次 push，網站就會自動更新。

## 回家後的同步流程

見 repo 根目錄的 `CLAUDE.md`：回家後打開 Claude Code CLI，
只要說「同步今天的易經文章並更新網站」，它就會把新文章放進 `articles/`、
執行建置、提交並推送。
