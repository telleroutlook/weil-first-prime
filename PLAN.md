# 研究计划 v2 — FP-0.35 首素数窗口认证与后续

**重写日期：2026-08-07**（旧版归档于 `docs/PLAN_v1_archive.md`）

> **新程序员接手请先读 `HANDOFF.md`**（代码可信度地图、已知 bug、环境前置、
> 收尾链的确切命令）。本 PLAN 是战略地图，HANDOFF 是操作交接。

---

## 状态快照（一句话真相）

**FP-0.35 数学成立**：L=7/20 两扇区 Schur 最小主元均为正
（偶 min_pivot=+0.008704 / min_eig=+0.00095；奇 min_pivot=+0.053134），
用完整四项 $S^{(0)}=S_{VV}+S_{VK}+S_{KV}+S_{KK}$、真实 $c_L=1.36527$、min-pivot 判据，
经两个独立实现逐元素比对确认（max|C_A−C_B|=4e-3）。

**证书正在重生成以满足合规**：原证书有两个过程缺陷（S_KK-only 致 min_eig 虚高 16 倍；
generator 是 shutil.copy）——均不改变符号结论，但必须以干净流程重做。

**proofctl 因本 pilot 增两道内核防线并发布**：v0.3.15 C10（禁 copy-only generator）、
v0.3.16 C11（要求 checker mutation 覆盖）。weil checker 已改为真重算 + mutation 100% kill。

---

## 第一编 · 铁律（长期方向筛选器）

任何新方向先过这三条，过不了直接毙（省算力）。来自 `docs/SPECULATIVE_ROADMAP.md`
与 `docs/PROOF_CONSTITUTION.md`。

1. **难度守恒**：任何“让 RH 变简单”的步骤是错觉；合法步骤只能无损搬运难度。
   凡“核心命题按构造自动成立”= 难度蒸发 = 该步必错。
2. **禁放缩 (C″)**：RH ⟺ Λ=0，系统零裕度临界。任何导出“≥ε 一致下界”的论证必错
   （蕴含 Λ<0，与 Rodgers–Tao 的 Λ≥0 矛盾）。允许：恒等式、保首项精确系数的
   渐近展开、极限取等的临界型不等式。
3. **叙事抵抗（宪法 PART D）**：支撑精彩叙事（“重大 bug”“突破”）的数字要提高
   而非降低验证标准。逐元素比对 artifact 再讲差异。区分“过程缺陷”与“结论错误”。

> 实测印证：EXTENDED_GOALS 的七个同构映射方向全部死于“目标定理结构前提在测量下崩塌”，
> 无一死于循环——这是难度守恒最硬的经验支撑。

---

## 第二编 · 近期收尾（1–2 周，让已完成的合规可发布）

| # | 动作 | 状态 |
|---|---|---|
| N1 | mutation catalog（C11 实体，6/6 kill，artifact 已固化） | ✅ 完成 |
| N2 | checker 改真重算 + 输出 mutation metadata | ✅ 完成 |
| N3 | attestation 重生成：`proofctl replay` 用真 checker 调用作 generator（非 copy）→ 解除 C10 | ✅ 完成 |
| N4 | 重新生成干净证书 `pilots/cert_fp035_clean.json`（正确四项值，真重算） | ✅ 完成 |
| N5 | `proofctl release --dry-run` 通过（C01–C11 全绿，13/13，无 blocker） | ✅ 完成 |
| N6 | 三处数值最终对齐核验：paper / cert / reproduce_fp035（odd min_eig 5.0e-2→1.9e-2 修正，废弃证书引用清除） | ✅ 完成 |
| N7 | arXiv endorsement 跟进（Zenodo v1.5 修正版已发） | ⏳ 等待人工 |

> **2026-08-07 收尾完成**（commit d6538be）：C11 不止封 thm-fp-035，也封
> lem-o1b-even/odd（`proofctl replay` 恒置 replay_mode=from_scratch）。已为 o1b
> checker 建独立 mutation catalog（`checker/first_prime/mutation_catalog_o1b.py`，
> 两扇区各 6/6 kill），并将 `exact_split` 重构出 `assemble_o1b_matrices`+
> `judge_o1b_pivot` 供 checker 与 catalog 共用（无重复逻辑）。唯一剩余人工动作是 N7。

---

## 第三编 · 中期（已有明确路径，数月）

- **M1 · E2 端点吸收窗口有效射程**：🟡 大部完成。数值定位 + 认证负见证已成。
  目标期刊：*Analysis and Mathematical Physics*。
  - L* 定位：even-sector L* ∈ (0.36, 0.37)（L≤0.36 以 λ≥7.8e-4 认证，L≥0.37 贴 2^-30 floor）；
    odd-sector L* ∈ (0.37, 0.39)。FP-0.35 (L=7/20) 处于吸收法认证射程的实际边缘。
  - **认证负见证（PLAN 附3 验收）已达成**：L=0.39 odd，
    w=(-37/167,12/611,-1/5,-56/197,-25/62,-370/453)，wᵀCw ∈ [-0.01555,-0.00994] < 0
    （Arb 认证，commit f70d0a8）。显式证明 Schur 正定判据在 L>L* 失效。
    工具 `scripts/lstar_negative_witness.py`。
  - 未完：L=0.46 even 浮点为负（min_eig=-1.2e-2）但 Arb 未认证——R_eta 区间依赖爆炸
    （rad 27.7 ≫ 信号 0.012），是 build_R 组装法问题（非精度/深度），需更紧的 R 组装
    （mpmath LDL 或仿射区间）才能认证。诚实态：float-negative, Arb-pending。
- **M2 · λ(L) 廓线重做**：✅ 完成（commit d746086，`pilots/lambda_profile.json`）。
  完整发现见 `docs/M1_M2_LAMBDA_PROFILE_FINDINGS.md`。
  四项 S0 + 真 S2，两扇区，3 点 certify 级；positive 只存活于 L=7/20。
  修复了 `scan_lambda_profile.py` 两个漏项 bug（S_KK-only + S2=0）并加 checkpoint/resume。
- **M3 · proofctl 方法论论文**：C10/C11 pilot 故事本身独立可发表——
  “一个真实数学 pilot 如何暴露并修复验证系统的两类盲区”。目标：*J. Automated Reasoning* / CICM。
- **M4 · E3 Lean 扩展**：定理 1–3 形式化已成，扩展至更多引理。ITP/CPP 2027。

---

## 第四编 · 长期（高风险探索，不承诺，受第一编铁律约束）

- **L1 · 第二素数窗口 `weil-second-prime`**（新仓库）：窗口 (½log3, log2)。
  **首要动作（短期发现驱动）**：先 profile 各扇区素数项影响——mutation 显示第一窗口
  even 扇区素数项 M2 近乎惰性（归零仅移动 pivot 0.003），故第二窗口**不要对称分配算力**，
  把硬算力花在 M2/交叉项 J(τ₂,τ₃) 真正起作用处（odd 扇区 / 更大 L）。
- **L2 · 思辨路线图** `docs/SPECULATIVE_ROADMAP.md`（纯思辨，核心引理 L 敞开，不承诺）：
  铁律已预筛掉多数死路——PSWF=坐标系非火力、反向热流无激波=τ(X,L)→0、
  任何强守恒律本身=RH。未闭合合法路标：自守正则化（= RH 的几何朗兰兹重述，难度守恒下不可能更弱）。

---

## 第四编-附 · 代码可信度地图（接手必读）

| 文件 | 状态 | 说明 |
|---|---|---|
| checker/fp035/recompute_schur.py | OK 可信 | 正确四项 S0 + min-pivot,独立重算。新工作以它为准。 |
| checker/fp035/check_fp035.py | OK 可信 | 调用 recompute_schur 真重算 + mutation metadata。 |
| checker/fp035/mutation_catalog.py | OK 可信 | 6 mutant,kill=100%。 |
| scripts/reproduce_fp035.py | OK 已修 | 四项 S0 + --out。原为 S_KK-only(虚高16x),已修。 |
| src/assemble/o1b_gate.py | OK 可信 | 生产级四项 S0,mpmath LDL。 |
| scripts/scan_lambda_profile.py | OK 已修 (2026-08-07) | 四项 S0 + 真 S2（原 S_KK-only + S2=0），两扇区，checkpoint/resume。S0 行与 recompute_schur 完全一致。commit 7325a8e。 |
| pilots/cert_schur_correct_cL.json | DEAD 废弃 | S_KK-only(虚高16x)+ shutil.copy。勿复用数值。 |

最危险 bug 模式:漏二阶矩项 -> 残差偏小 -> 判据假通过。S0 必须四项。

## 第四编-附2 · 环境前置

- proofctl 在 ~/github/proofctl,需 v0.3.16(含 C10/C11);~/bin/proofctl 为部署副本。
- Python:python-flint(Arb)、numpy;LaTeX 用 tectonic(paper/compile.sh)。
- 长任务(>2min)用 ~/.local/bin/run_and_wait.sh -t <秒> -- <命令>,前台阻塞,禁裸 &。
- certify 四项 S0 重算:偶 ~40min,奇 ~25min。禁用 depth=2 快扫下判决
  (教训:depth=2 把 -0.022 算成 -0.0007,误差 30x)。

## 第四编-附3 · 中长期任务入口 + 验收

- M1 E2 端点吸收射程:入口 kappa_edge 分析(定理2证明内),L* 满足 c2=kappa_edge(L*)。
  验收:证 L>L* 时存在显式反例 w_L 使 V(w_L)+P_{2,L}(w_L)<0。
- M2 lambda(L)廓线重做:入口 scan_lambda_profile.py,先修其 S_KK-only bug(参考
  recompute_schur 四项 S0)。验收:>=3 个 L 点 certify 级严格下界廓线。
- M3 proofctl 方法论论文:入口 C10/C11 pilot 故事 + docs/PROOF_CONSTITUTION.md。
  验收:可投 J. Automated Reasoning / CICM 草稿。
- M4 Lean 扩展:入口 lean4/(定理1-3已成)。验收:更多引理机器验证。
- L1 第二窗口:新仓库 weil-second-prime。首要:mutation-style 探针 profile 各扇区
  素数项影响(第一窗口 even 素数项近乎惰性,勿对称分配算力)。需写双平移耦合 J(tau2,tau3)。

---

## 第五编 · 结论边界（不可逾越）

- 结论只能是“L ≤ 7/20 的有限尺度 Weil 正性”。
- **不得**升级为 RH 或“接近 RH”。FP-0.35 → RH 存在两道无已知路径的鸿沟：
  有限尺度 → 全区间正性（无已知路径），再经 Weil 等价。
- **不得**声称 E1/E2/E3、第二窗口、思辨路线对 RH 有直接推论。
- 任何 certify 断言必须过 proofctl C01–C11；copy-generator 与漏项 checker 已被 C10/C11 封死。

---

## 附 · 与 proofctl 的关系（pilot 双向反馈）

weil-first-prime 是 proofctl 的首个真实 pilot。本轮 pilot 的核心价值不仅是
“用工具验证数学”，而是**用真实数学案例暴露并修复了工具的两类内核盲区**：
C08 只验 replay_mode 标签→C10 补验 generator 实质；无漏项防线→C11 补 mutation 覆盖。
这是 pilot 能给验证系统的最高价值反馈。
