# 專案指引（給 Claude Code CLI）

這個 repo 同時是 GitHub 個人檔案頁（根目錄 `README.md`），以及**易經文章的內容暫存／交接站**（`yijing/`）。

> 重點：**正式的易經網站在使用者本機、獨立維護，不在這個 repo 裡。**
> 這個 repo 只負責「白天遠端把內容生成好，晚上回本機取用」。工作分兩個階段。

## 檔案角色

- `yijing/articles/*.md` — **唯一要編輯的地方**：白天生成的文章原始檔。
- `yijing/articles/_template.md` — 新文章範本（底線開頭，不會被預覽建置）。
- `yijing/build.py` — **選用**的本機預覽產生器，輸出到 `docs/`。
- `docs/` — 選用預覽產物，已 `.gitignore`，**不是正式網站**，不要當成交付物。
- `yijing/site.local.md` — 本機網站設定（路徑、格式對應）；已 `.gitignore`，只存在本機。

## 階段一：白天（電腦不在身邊，遠端生成內容）

在 Claude Code on the web／手機等遠端環境。使用者會給主題與需求（哪一卦、切入角度、
篇幅、風格）。你要：

1. 依需求撰寫易經文章，存成 `yijing/articles/<日期>-<slug>.md`，
   補齊 front matter（`title` / `slug` / `hexagram` / `number` / `date` / `tags` / `summary`），
   格式照 `yijing/articles/_template.md`。
2. （選用）跑 `python3 yijing/build.py --clean` 產生 `docs/` 預覽，確認渲染正常。
   `docs/` 不進 git，也不是正式網站，只是讓使用者白天也能看效果。
3. 用中文 commit（例：`新增坤卦筆記`），`git push -u origin <目前分支>`。
   這些 `.md` 就是白天的產出，等晚上取用。**白天階段到此為止，不要碰本機網站。**

## 階段二：晚上（回家，在本機把內容併入既有網站）

在使用者本機（有既有網站的那台電腦）操作。當使用者說要「同步／更新既有網站」時：

1. `git pull` 取得白天新增／修改的文章。
2. 找出這次要處理的文章：用 git 比對上次同步後 `yijing/articles/` 的變動，或由使用者指定。
3. **對齊既有網站格式**：讀既有網站的結構與現有文章，把 staged 的 `.md` 轉成該網站吃的格式、
   放到正確位置。**第一次同步**時，請使用者告知：本機網站路徑、它用的產生器／文章格式與內容資料夾；
   談定後記到 `yijing/site.local.md`（不上傳），之後即可自動化。
4. 依既有網站原本的方式重建／部署。
5. 回報：這次把哪些文章併入了網站、對應的頁面。

## 注意

- 不要動根目錄 `README.md` 的個人檔案內容，除非使用者明確要求。
- `docs/` 只是選用預覽；正式網站在本機。改內容一律改 `yijing/articles/`。
- 預覽建置不需第三方套件，Python 3 即可。
