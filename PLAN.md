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

- **M1 · E2 端点吸收窗口有效射程**：🟡 大部完成。数值定位已成 + 认证负见证仅在 odd@0.39 达成。
  目标期刊：*Analysis and Mathematical Physics*。
  - L* 定位：even-sector L* ∈ (0.36, 0.37)（L≤0.36 以 λ≥7.8e-4 认证，L≥0.37 贴 2^-30 floor）；
    odd-sector L* ∈ (0.37, 0.39)。FP-0.35 (L=7/20) 处于吸收法认证射程的实际边缘。
    注意：L* 区间是数值定位，**非** Arb 全认证；even 的 9.3e-10 是搜索 floor 不是真裕量。
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

  **⚠️ 2026-08-08 重大更正（来自 FIRST_WINDOW_COLLAPSE_VERDICT.md §2 四任务执行）**：
  λ_profile.json 里的 L=0.42 认证下界（9.3×10⁻¹⁰）**不代表真特征值穿零**，而是
  **证书松弛（Certificate Relaxation）**。脚本 `scripts/lambda_separation.py` 测量：
  - L=0.42：λ_min^true = +3.19×10⁻⁵（正！），λ_lb = 9.31×10⁻¹⁰，比值 ~34,000×
  - L=0.45：λ_min^true = -1.32×10⁻³（负），真穿零在 L≈0.44，不是 0.42

  **以下结论从此撤回，不得在任何文档中援引**：
  - ❌ "Effect B 指数级坍缩" —— Task 4 证明是 Gibbs 截断假象（Scenario B）：
    L_c(d=14)≈0.40 → L_c(d=16)≈0.44 → d=20 时 [0.38,0.45] 全正无穿零。
    L_c(d) 单调右移，d=20 时穿零消失。
  - ❌ "Route 3 因指数坍缩而高优先级" —— 坍缩是截断假象，此紧迫性不存在。
  - ❌ "Legendre 基在深水区结构性失效" —— d=20 时全窗口为正，加大 d 即恢复。
  - ⚠️ "λ_profile.json 的 L=0.42 λ_lb=9.3e-10 是 Effect B 指数坍缩证据" —— 错误；
    该值是 d=16 截断下证书松弛，不是真特征值行为。

  **Scenario B 的诚实边界**：d=20 时 [0.38,0.45] 全正，L_c(d) 右移趋势强烈暗示
  Gibbs 假象，但"d→∞ 穿零消失"是外推，**仅在 d≤20 范围得到数值支撑**。要断言
  "第一窗口无限维稳健"，需将 Scenario B certify 到更大 d 或给出解析论证。
  结论只能是："到 d=20 为止，穿零点随 d 右移/消失，强烈暗示 Gibbs 截断假象；
  d=∞ 的最终行为仍是外推，未严格证明。"
- **M3 · proofctl 方法论论文**：✅ 完成初稿（commit d0c1b7f，`paper/proofctl-methodology.tex`，
  5 页，tectonic 编译通过；Zenodo metadata 就绪 `paper/ZENODO_METADATA_METHODOLOGY.txt`）。
  标题《When the Pilot Audits the Tool》——真实数学 pilot 暴露并修复 C10/C11 两类内核盲区，
  含 mutation kill-criterion 细节、叙事抵抗认识论、收尾时发现第二个同类实例。
  目标：*J. Automated Reasoning* / CICM。待人工投稿。
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

## 第五编 · 思辨路线审计（受第一编铁律约束）

> 本编工作产出为 `paper/d1-canonical-limit-point.tex`，
> **不进入 proofctl 证明链**。
> 论文定位：参考注记 + 逻辑漏洞审计；不证明 RH 或任何与 RH 等价的命题。

### D1 · 典范极限点审计论文（已重大变更）

**2026-08-09 版本转变说明**：经过多轮顶尖 LLM 与人工审稿，原来"三引理严格化"
框架被证明不可行（L1/L2 关键构造均失败），论文已彻底重构为：

- **正面结果（已完成）**：
  - `prop:weyl`（限点判据）：Remling Thm 3.5 的直接特化，含完整证明。
  - `prop:trivial`（对数导数构造）：$m_t = -H_t'/H_t$ 是 Herglotz 函数，
    给出唯一迹归一化半直线典范系统 $\widehat{H}_t$，并验证
    $E_t = H_t + iH_t'$ 是 Hermite–Biehler 函数
    （$|E_t|^2 - |E_t^\#|^2 = 4|H_t|^2\operatorname{Im}m_t > 0$，从 prop:trivial 严格推出）。
  - `cor:trivial`（自动且空洞的极限点）：迹归一化 → 自动满足 ∫TrH = ∞ → 极限点，
    但这是同义反复，不含算术信息。

- **负面结果（已完成）**：
  - 核心引理漏洞（`rem:coreL-defective`）：自伴算子有实谱，谱 = {γ_n}（零点虚部）
    对实部无约束，不蕴含 RH；路线图缺少从谱到零点实部的定理。
  - `prob:gen` 四项修补义务：(1) 构造 H_Φ（非循环）；(2) 迹发散（独立于谱论证）；
    (3) 离散谱 + 特征整函数 D_{θ₀}（由算子程序构造，非预设零点）；
    (4) 因子等式 div D_{θ₀} = div Ξ。仅此方向蕴含 RH，但比 RH 更难。
  - 三个障碍（`sec:open`）：实整函数永不是 Hermite–Biehler；|H_t|⁻²dτ 有不可积极点；
    无 t→0⁺ 极限控制。

- **亏指数更正**：左正则 + 右极限点 → (1,1)；左端仍需边界条件 θ₀，
  极限点不等于本质自伴，不给出唯一自伴实现。

**当前文件状态**：所有章节（sec:trivial, sec:open, sec:L3, sec:proof, sec:discussion）
已写完，数学独立审查无错误，LaTeX 编译零错误零警告，PDF 已生成。

| 任务 | 状态 |
|---|---|
| D1-A · 重构为审计论文（原三引理框架废弃） | ✅ 完成 |
| D1-B · prop:trivial：m_t Herglotz 构造 + E_t HB 验证（补充 4 Im m_t 计算） | ✅ 完成 |
| D1-C · prop:weyl：Remling 3.5 极限点判据参考证明 | ✅ 完成 |
| D1-D · sec:open 三障碍 + rem:coreL-defective 漏洞分析 | ✅ 完成 |
| D1-E · prob:gen 四项修补义务（有完整 PASS 条件） | ✅ 完成 |
| D1-F · cor:alpha 亏指数 (1,1) + θ₀ 参数 | ✅ 完成 |
| D1-G · 数学独立审查（顶尖 LLM 多轮）无实质性错误 | ✅ 完成 |
| D1-H · Λ≤0.2 引用改为 Saouter–Gourdon–Demichel 2011（正确一手来源） | ✅ 完成 |
| D1-Z · 投稿预备（确认期刊，润色摘要） | 🔲 待定 |

> **投稿判断**：论文定位为"参考注记 + 逻辑漏洞审计"，无新定理，
> 可投 *Expositiones Mathematicae* 或作 arXiv 预印本供路线图引用。
> D1-Z 决定前请人工确认定位与期刊匹配度。

### D3 · Conrey–Li 障碍

D1 审计论文 sec:discussion 已包含一个旁注（aside）说明：
- 有限链终止函数 $A_\infty = c\,\Xi$ 在半直线极限点设置中不适用；
- $E_\lambda = \Xi_\lambda$ "绕过障碍"的早期说法是错的；
- Conrey–Li 障碍与 D1 的半直线系统构造是独立问题。

D3 独立论文（`paper/d3-conrey-li-closure.tex`）暂缓，
等待 D1 审计论文投稿结论后再评估是否需要。

| 任务 | 状态 |
|---|---|
| D3-0 · 评估是否需要独立 D3 论文（D1 aside 是否足够） | 🔲 待 D1-Z 后决定 |

---

### 与外部研究纲领的对应关系（2026-08-09）

外部文件 `Riemann_Arithmetic_Spectral_Program_Final_Executable_Canvas_2026-08-09.md`
提出了一条系统化的非循环 RH 研究路径。以下记录本仓库 D1 审计工作与该纲领的对应关系，
以及两者的边界。

**D1 成果在新纲领中的定位：**

| D1 审计论文结论 | 新纲领对应位置 | 含义 |
|---|---|---|
| `rem:coreL-defective`：谱={γ_n} 不蕴含 RH | 新纲领终点 A 放弃 spec={γ_n}，改用 $F_j \to \Xi$ 局部一致收敛 | **直接采纳**：收敛到 $\Xi$ 本身保留了完整的零点因子信息，而谱集合相等只记录纵坐标 |
| `prop:trivial`：迹归一化系统是同义反复 | 新纲领 §5.2 中心瓶颈："任意有限自伴谱自动给出实零或正热迹，却未必具有正确算术字典" | **互相印证**：这正是"cheap 的实零"与"有算术含义的实零"之间的本质区别 |
| 三障碍中"实整函数永不是 HB 函数" | 新纲领 §7.5：HB 理论仅在真正构造出 HB 不等式时进入，且不得以 RH 为前提 | **一致**：新纲领明确禁止把"条件性 HB 正性"导入非循环证明 |
| `prob:gen` 四项修补义务（C0→C7） | 新纲领 §7.2 主线证明义务 C0–C7 | **结构对应**：D1 的"非循环构造 H_Φ"= 新纲领 C0/C1；"独立迹发散"= C2b；"因子等式"= C6/C7 |
| `cor:alpha`：亏指数 (1,1)，θ₀ 参数仍存在 | 新纲领 §8.1：Suzuki 路线中 deficiency indices (1,1)，自伴扩张由参数族描述 | **一致**：极限点不等于唯一自伴实现，左端参数不消失 |

**两种"热迹/热流"的边界（重要，防止混淆）：**

- **de Bruijn–Newman 热流** $H_t(z) = \int_0^\infty e^{tu^2}\Phi(u)\cos(zu)\,du$：
  关于谱变量 $z$ 的整函数族，是本仓库 D1 路线图的出发点。
  对数导数 $m_t = -H_t'/H_t$ 给出的典范系统是同义反复（`cor:trivial`）。
  **这条路产生不了算术信息。**

- **算术热迹** $\Theta_{\mathrm{arith}}(t) = \sum_{[\rho]} e^{-tz_\rho^2}$（由显式公式定义，等价地由 Laplace 变换链与算术预解式 $\mathcal{R}(x)$ 相连）：
  关于热时间 $t$ 的标量函数，是新纲领终点 B 的核心对象。
  其完全单调性等价于 RH（Bernstein–Widder + Stieltjes 唯一性）。
  **这是完全不同的对象，与 DBN 热流不是同一事物。**

将两者混淆（例如"DBN 热流也证明了完全单调性"）是 TYPE_ERROR，新旧两份文档均明确排斥。

**新纲领中 D1 尚未覆盖的部分（本仓库不承诺）：**

- M0 解析定理包（$\mathcal{D}$、$\mathcal{R}$、$\Theta_{\mathrm{arith}}$ 的严格构造与等价定理）
- C2b simple-even 机制（CCM 路线的谱隙问题）
- C5 本征向量–代理函数桥梁（$L^1_b$ 范数收敛，承担全部 RH 难度）
- 算术热迹的有限正测度逼近序列（终点 B）

这些属于新纲领的独立工作，D1 审计论文为其提供了逻辑基础（为什么旧论证不够、正确问题应如何表述），但不提供证明。

---

## 第六编 · 结论边界（不可逾越）

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
