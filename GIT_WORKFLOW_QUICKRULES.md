# Git Workflow Quick Rules

給現在這個專案用的短版規則。

## 1. 不要直接在 `main` 上開發

先更新 `main`，再開新分支。

```bash
git checkout main
git pull origin main
git checkout -b feature/short-name
```

分支名稱建議：

- `feature/...`
- `fix/...`
- `docs/...`
- `infra/...`

## 2. 每次只做一件明確的事

一次 commit 只收一個主題，不要把不相關修改混在一起。

好例子：

- `Add www alias redirect support for frontend`
- `Fix GitHub CI SAM region handling`
- `Update Chapter 5 platform wording`

## 3. Push 前先跑最基本檢查

一般情況先跑：

```bash
python infra/run_ci_checks.py
```

如果這次有碰 deployment / release 流程，再加跑：

```bash
python infra/run_cd_release.py --dry-run
```

## 4. 一律走 branch -> push -> PR

不要把「反正只有我一個人」當成直接推 `main` 的理由。

流程固定：

1. 在工作分支完成修改
2. commit
3. push branch
4. 開 PR 到 `main`
5. 等 GitHub CI 和 CodeBuild bridge 綠燈
6. 用 squash merge 合回 `main`

## 5. Merge 前自己做一次簡短自查

至少問自己這 4 件事：

- 這次改動的範圍是不是清楚？
- 有沒有不小心帶進不相關檔案？
- CI 有沒有綠？
- 這次 merge 之後要不要手動 deploy？

## 6. Merge 後再回 `main`

```bash
git checkout main
git pull origin main
git branch -d feature/short-name
```

如果 GitHub 已自動刪遠端分支，本地也順手刪掉。

## 7. 什麼情況可以直接推 `main`

原則上不要。

只有這種很小、很明確、很低風險的改動才考慮：

- 單純補一行文件
- 修 report 路徑文字
- 不影響 code / infra / deployment 的小修

但就算是這種情況，能走 PR 還是走 PR。

## 8. 目前這個 repo 的現實邊界

現在是：

- private repo
- 有 CI
- 有 documented workflow

但不是：

- GitHub Pro branch protection
- 強制 PR approval
- 自動 deploy

所以現在靠的是：

- 自己守規則
- 不偷懶直接推 `main`

## 最短版本

如果只記 4 句，記這個就夠：

1. 先從 `main` 開分支，不要直接改 `main`
2. push 前先跑 `python infra/run_ci_checks.py`
3. 一律走 PR，等綠燈再 merge
4. merge 後如果有部署需求，再手動 deploy
