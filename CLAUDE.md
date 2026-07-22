# 專案指引（給 Claude Code CLI）

這個 repo 同時是 GitHub 個人檔案頁（根目錄 `README.md`）與**易經筆記專案**（`yijing/`）。

## 易經專案結構

- `yijing/articles/*.md` — 文章原始檔（唯一需要手動編輯的地方）。
- `yijing/build.py` — 建置腳本，把 Markdown 轉成網站。
- `docs/` — 產生的靜態網站，GitHub Pages 發佈來源。**不要手動編輯**，一律用建置腳本重生。
- 詳細格式見 `yijing/README.md`；`yijing/articles/_template.md` 是新文章範本。

## 「同步今天的易經文章並更新網站」時，請這樣做

當使用者說要同步／更新易經文章、把白天寫好的內容放上網頁時：

1. **接收內容**：使用者會用以下任一方式提供白天完成的文章：
   - 直接把文字貼在對話中；
   - 指向某個檔案或資料夾路徑；
   - 已經自己把 `.md` 放進 `yijing/articles/`。
2. **整理成文章檔**：把每篇文章存成 `yijing/articles/<日期>-<slug>.md`，
   並補上 front matter（`title` / `hexagram` / `number` / `date` / `tags` / `summary`）。
   格式照 `yijing/articles/_template.md`。若使用者只給正文，請據內容合理補齊 front matter。
3. **建置**：執行 `python3 yijing/build.py --clean`，確認輸出無誤。
4. **提交並推送**：commit 訊息用中文簡述（例：`新增坤卦筆記並更新網站`），
   然後 `git push -u origin <目前分支>`。
5. **回報**：告訴使用者新增／更新了哪些文章、網站頁面連結（`docs/p/<slug>.html`）。

## 注意

- 不要動根目錄 `README.md` 的個人檔案內容，除非使用者明確要求。
- `docs/` 是產物；改文章請改 `yijing/articles/` 再重新建置，不要直接改 `docs/`。
- 建置不需第三方套件，Python 3 即可。
