# 新程序员接手 Prompt

## 工作方式（最重要，先读）

**自主决策，不询问，不等待确认。** 对每个决策，选择你认为最优的方案直接执行。遇到分叉点时，记录推理（一句话），执行，继续。只有在两种后果都不可逆且差异巨大时才暂停——日常编码、测试、文档修改从不暂停。

**永远不说"我打算…你确认吗"，永远不说"需要我继续吗"。** 接到任务就做到完成，中途汇报进展而非请示。

**遇到错误不问，直接诊断修复**。如果一条路走不通，换路，记录切换原因。

---

## 两个仓库的当前状态

### weil-first-prime（主仓库，`~/github/weil-first-prime`）

**数学结论**：FP-0.35 成立。L=7/20 两扇区 Schur 最小主元均为正（偶 min_pivot=+0.0087，奇 min_pivot=+0.053），使用完整四项 S⁰=S_VV+S_VK+S_KV+S_KK、真实 c_L≈1.36527、min-pivot 判据，经两个独立实现逐元素比对确认（max|C_A−C_B|=4e-3）。**有限尺度 Weil 正性，不蕴含 RH。**

**认证链状态**：`proofctl release --dry-run` 通过全部 13 个条件（C01–C11），17/17 claims ACCEPTED，124 tests 通过。近期收尾（N1–N6）完成。干净证书：`pilots/cert_fp035_clean.json`（even min_eig 9.5×10⁻⁴，odd min_eig 1.9×10⁻²）。

**唯一剩余人工动作**：N7 — arXiv endorsement 等待回复（Suzuki/Groskin）。**这不是你的任务**，等待即可。

**代码可信度地图**（做任何计算前对照）：

| 文件 | 状态 |
|---|---|
| `checker/fp035/recompute_schur.py` | ✅ 可信 — 正确四项 S0 + min-pivot |
| `checker/fp035/check_fp035.py` | ✅ 可信 — 真重算 + mutation metadata |
| `checker/fp035/mutation_catalog.py` | ✅ 可信 — 6 mutant，kill=100% |
| `checker/first_prime/mutation_catalog_o1b.py` | ✅ 可信 — o1b 两扇区各 6/6 kill |
| `pilots/cert_fp035_clean.json` | ✅ 权威证书 |
| `scripts/scan_lambda_profile.py` | ✅ 已修（2026-08-08，四项 S0 + 真 S2） |
| `pilots/cert_schur_correct_cL.json` | ❌ 废弃，勿复用 — S_KK-only，虚高 15.7× |

**中期未完任务**（参见 PLAN.md 第三编）：
- M1：L=0.46 even 的 Arb 负见证认证（R_eta 区间依赖爆炸，需更紧 R 组装方法）
- M3：方法论论文 `paper/proofctl-methodology.tex` 投 JAR/CICM（初稿完成，待人工投稿）
- M4：Lean 4 形式化扩展（`lean4/`）

---

### weil-second-prime（新仓库，`~/github/weil-second-prime`）

**状态**：脚手架阶段，无数学计算，无证书。GitHub: `github.com/telleroutlook/weil-second-prime`。

**双重目的**：(1) 第二素数窗口 L∈(½log3, log2) 的新数学；(2) proofctl 的真实进化宿主——只有真实研究才能暴露内核盲区（C10/C11 就是被 weil-first 的真实 bug 逼出来的，自测永远发现不了盲区）。

**S2–S5 任务（PLAN.md 第二编）**：

| # | 任务 | 状态 |
|---|---|---|
| S2 | 移植 archimedean 机件（integrator_a/b, interval, ldlt, log_moments, kernel, bernstein）+ 单素数极限自检 | ⬜ |
| S3 | 完成 `legendre_shift_2prime.py` 双平移交叉项 | ⬜ |
| S4 | per-sector 素数影响 profile（certify 级精度，不对称分配算力） | ⬜ |
| S5 | schema + domain + 第一份 pilot 证书 | ⬜ |

---

## 三条操作纪律（今晚血的教训）

**1. S0 必须四项**。任何地方只要写了 S0，必须是 S_VV+S_VK+S_KV+S_KK。省掉任何一项→残差偏小→判据假通过→整个 λ(L) 廓线是谎言（weil-first 今晚犯过此错，scan_lambda_profile.py 被修了）。移植 weil-second 时，拿当前修复版（commit 8月8日之后），不带 S_KK-only 残留。

**2. 探路精度不下判决**。depth=2 快扫把 −0.022 算成 −0.0007（30× 误差），差点把算力引错方向。任何"这个扇区影响大/小"的结论，必须有 certify 级（Arb interval）数字支撑，并明确标注精度等级。初筛可以用快扫，但决策不能用探路数字。

**3. 移植后立即单素数极限自检（S2 完成前不算完）**。weil-second 在 τ₃→0（3号素数不参与）时，Schur 矩阵各元素必须逐元素复现 weil-first 在同 L 点的结果（max|C_second−C_first| < 1e-10，float64）。等到 S3 才检查等于把移植错误带进后续所有计算。

---

## 环境前置

```bash
# proofctl
~/bin/proofctl      # 已部署，v0.3.16（含 C10/C11）
~/github/proofctl   # 源码（可修改并发布）

# 长任务（>30s）必须用，禁裸 &
~/.local/bin/run_and_wait.sh -t <秒> -- <命令>

# Python 环境
python-flint (Arb), numpy, mpmath, jsonschema
# LaTeX
tectonic  # paper/compile.sh

# 推送 github 若需代理，用环境变量
HTTPS_PROXY="${HTTPS_PROXY:-}" git push ...
```

certify 级四项 S0 重算耗时：even 扇区 ~40 分钟，odd ~25 分钟。长任务必须用 run_and_wait.sh 前台阻塞，每步打印进度（`print(..., flush=True)`），并写 checkpoint。

---

## 三份必读文档

- `docs/PROOF_CONSTITUTION.md` — 计算/证明/交接纪律（PART A-E）：难度守恒、禁放缩、叙事抵抗、diff artifacts before narrating、过程缺陷≠结论错误。每一个今晚暴露的 bug 都违反了其中一条。
- `PLAN.md` — 战略地图（第一编铁律 + 第二/三/四编任务表）
- `HANDOFF.md` — 操作交接（代码可信度地图、收尾链精确命令）

---

## 一句话给下一位维护者

**这里最大的风险不是数学难度，而是隐含假设没有被检验**——今晚所有 bug 都来自这里。对任何数字，问：S0 是四项吗？判据是 min-pivot 吗？这个脚本在可信度地图上是什么状态？一个诚实的"卡住了"或负向结果，比一个没经过检验的"通过"值钱得多。
