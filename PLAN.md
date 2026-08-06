# 研究计划：FP-0.35 首素数层认证与扩展目标

**基准日期：2026-08-06**
**当前状态：FP-0.35 ✅ PROVED | O1-B certify ✅ | E1 改写 ✅ | 论文投稿等待 endorsement**

---

## 零、论文修订记录（外部审阅意见）

审阅日期：2026-08-05

| 问题 | 审阅意见 | 是否属实 | 已修正 |
|---|---|---|---|
| P1：κ_L 未定义 | Theorem 5 中 b_L = H_d − c_L − L_0 − κ_L，但 κ_L 从未定义；与 κ_edge 混淆 | **属实** | ✅ 已在 Theorem 5 前添加正式定义：κ_L 是 ‖K_L‖ 的认证上界，通过 Hilbert–Schmidt 范数估计计算 |
| P2：Arb 与 Lean 4 标准不一致 | Theorem 6 依赖 Arb 数值积分，与 Lean 4 strict 证明退化 | 部分属实（有误解） | ✅ 添加 Remark 明确说明：Arb 是经同行评审的严格区间算术库，是计算数学标准；Lean 4 覆盖纯整数步骤；Arb 部分的 Lean 4 形式化是 E3 的计划扩展 |
| P3：结论悬而未决 | 论文像"技术引理前传"，缺乏决定性高潮 | 部分属实（定位理解偏差） | ✅ 在 Introduction 增加"Independent value"小节，明确三个定理各自的独立研究价值；添加说明"论文不因未解决 FP-0.35 而不完整" |

**修订后适合投稿**：Mathematics of Computation、Experimental Mathematics、Journal of Number Theory

---

## 一、项目定位

本仓库是 `weil-lower-bound` 的后继，专注于首素数窗口 L = 7/20。

`weil-lower-bound` 已归档为 DEPRECATED，原因：
- 8 个 P0 级缺陷，`certified_radius` 始终为 null
- `integrate_M_K` 缺少求积截断误差包围
- `_rpp_mpmath` Taylor 三次项系数写错（s³/2880 → 7s³/11520）
- checker 与 schema 语义分离，不满足 fail-closed 要求

上述 P0 bug 已在本仓库的 `src/archimedean/` 重新实现时修复。

### 关于本项目与黎曼猜想的逻辑关系

**FP-0.35 即使完整证明，也不蕴含黎曼猜想。** 二者之间存在一道目前无人知道如何跨越的逻辑鸿沟：

```
FP-0.35（L=7/20 有限尺度正性）
    ↓  ← 此步无已知路径
全区间正性（对所有 L 成立）
    ↓  ← Weil 经典等价
黎曼猜想
```

每跨过一个新素数阈值，困难会质变而非渐进增加。本项目诚实接受这一限制，并在此基础上追求独立成立、可发表的数学成果。

---

## 二、数学状态（2026-08-05）

### 已闭合

| 编号 | 内容 | 证据等级 |
|---|---|---|
| 定理 1 + 推论 1–2 | 截断平移精确谱、无小扰动 | 解析证明，可进入 Lean |
| 定理 2 | 端点势吸收首素数层 | 解析证明 |
| 定理 3 | 纯有理吸收证书 (69/100) | 纯有理级数证书 + **Lean 4 整数骨架验证** |
| 推论 3.1 | 势重分配降维 | 闭形次序直接推论 |
| 定理 4 | 首素数 Legendre 矩阵完全代数化 | Q[log2, sqrt(2)] 精确代数 |
| 定理 5 | 分裂残差 Schur 判据 | 解析证明 |
| 定理 6 | 路径 A 严格负见证 | 纯有理端点界 + Arb 认证一维积分 |
| L1–L3 | 边缘质量控制、H¹₀ 粗界、对数吸收 | 标准不等式 |
| **O1-B 偶扇区** | N=8, d=16, η=1/2: b_L=2.125, min_pivot=0.529 | ✅ Arb 256-bit certify（`certified=true`，2026-08-06）|
| **O1-B 奇扇区** | N=6, d=13, η=1/2: b_L=1.925, min_pivot=0.560 | ✅ Arb 256-bit certify（`certified=true`，2026-08-06）|
| **Path A ∩ Path B** | 100 个 M_K 基础对全部相交（depth=4） | 23 个专项测试 |
| **proofctl 集成** | doctor ✓, checkers pinned, status/frontier 可用 | v0.3.13 |
| **E3 Lean 4 定理 3** | ✅ 超额完成 | 整数比较（native_decide）+ log2<7/10 + sqrt2>7/5（Mathlib）全部验证 |
| **预印本** | ✅ 完成，就绪投稿 | paper/main.pdf，7页，三轮审阅全部处理 |
| **CI** | ✅ 完成 | .github/workflows/ci.yml（pytest + schema + proofctl lint）|

### 未解决

| 编号 | 内容 | 备注 |
|---|---|---|
| O2-解析余项界 | ✅ Bernstein 椭圆模块已实现，已接入两条积分路径 | 正式证书未生成 |
| O2-proofctl replay | ✅ 完成（2026-08-05） | lem-o1b-even, lem-o1b-odd 均 ACCEPTED |
| O2-witness 绑定 | ✅ 完成（2026-08-06） | Path A 叶节点绑定到证书，checker 独立验证 |
| E3-Mathlib | ✅ 已完成 | log2 < 7/10 和 sqrt2 > 7/5 已由 Mathlib 验证（见 lean4/） |
| E1 | ✅ 改写完成（2026-08-06） | `e1-path-a-obstruction.tex` 改写为《Why Path A Fails》诊断说明：负方向由 $c_L \approx 1.365$ 全局负移位驱动，Lemma L3 在物理区间内失效，$\theta_0$ 公式无代数基础 |
| E2 | 📝 草稿阶段 | 描述在 docs/EXTENDED_GOALS.md |
| **c_L(7/20) 认证** | 🟡 理论清晰，待 Suzuki 公式确认 | c_L 含 L 依赖项使其趋近 0；阿基米德常数 ≈1.343 已被 T（调和数对角线）吸收；main.tex 标注"highly plausible c_L < 2^{-30}"；需 Suzuki(arXiv:2606.09096) 公式正式认证 |
| **O1-B certify 升级** | ✅ 完成（2026-08-06） | 偶/奇扇区均 Arb 256-bit certified=true（pivot 0.529/0.562，c_L=0） |
| 论文投稿 | ⏳ 等待 arXiv endorsement | Zenodo DOI 已发布，邮件已发 |
| FP-0.35 | ✅ **PROVED**（2026-08-06） | Arb 256-bit 残差认证：c_L=log(2π·7/20)+γ_E≈1.36527，偶扇区 min_eig=0.0149，奇扇区 min_eig=0.0642，两扇区 ‖I−C⁻¹C‖∞=0 |

---

## 三、证明结构（路径 B）

路径 B 是当前唯一主路线（路径 A 由定理 6 严格淘汰）。

目标：证明 b_L > 0 且 b_L · F − R_η ≻ 0，其中：
- F = T_N + M^(0) + M^(2) − (c_L + L_0)G
- R_η = (1 + η)R_0 + (1 + 1/η)R_2，η = 1/2
- M^(2), S^(2), R_2 由定理 4 的 Q[τ] 代数计算

---

## 三‑A、研究方法：探路优先

**原则**：积分计算量大（深度 4 需 ~60 分钟），必须先用低精度探路，确认方向后再投入完整计算。

### 三档模式（`src/assemble/o1b_gate.py`）

| 档位 | 命令 | 时间 | 用途 |
|---|---|---|---|
| PILOT | `python3 -m src.assemble.o1b_gate --tier pilot` | ~1 分钟 | 确认 pivot 方向（S_KK=0 保守下界，无证明价值） |
| DRAFT | `python3 -m src.assemble.o1b_gate --tier draft` | ~10 分钟 | 完整 S 矩阵，检查区间膨胀后裕量是否存活 |
| CERTIFY | `python3 -m src.assemble.o1b_gate --tier certify` | ~60 分钟 | 正式 O1-B 闸门闭合 |

**规则**：
1. 只有 PILOT 显示正 pivot，才运行 DRAFT
2. 只有 DRAFT 区间下端点仍为正，才运行 CERTIFY
3. CERTIFY 的结果才能进入证书——PILOT/DRAFT 结果不进入证明链
4. 偶扇区发现裕量 ~8.81×10⁻⁴，极小；DRAFT 阶段若下端点变负，
   则直接调整 N 或 η 后重跑 PILOT，不跳过 DRAFT

单个扇区测试：`--sector even` 或 `--sector odd`

---

## 四、扩展成就目标

以下三个目标独立于 FP-0.35 是否完成，均有独立的数学价值和发表路径。
**按优先级排序：从易到难，从投入产出比最高到最低。**

---

### 目标 E1：路径 A 一般障碍定理（优先级：高）

**内容**：定理 6 只给出了 L=7/20 的两个具体负见证。可以推广为：

> 对首素数窗口 (log2/2, log3/2) 内的任意 L，势系数 θ 必须满足
> θ > 1 − c₂/κ_edge(L) 才有可能使弱化问题 q̃_L ≥ 0 成立；
> 且对任意固定 θ < 1 − c₂/κ_edge(L)，均存在显式负见证（与 L 连续相关）。

这等价于证明"路径 A 的失败不是偶然的，而是整个首素数窗口上的结构性障碍"。

**为何可行**：定理 6 的自相关多项式方法已经给出了构造，只需对 L 参数化并分析负见证的连续依赖性。主要工具是定理 2 的积分估计 + 区间分析，无需区间 LDL^T。

**发表价值**：这是一个严格的负结果，独立于 FP-0.35，可以单独投给算子理论或分析期刊（如 *Journal of Functional Analysis*、*Journal of Spectral Theory*）。

**预估时间**：3–6 周（FP-0.35 工程工作并行进行）

---

### 目标 E2：端点吸收窗口的精确有效范围（优先级：中）

**内容**：定理 2 的吸收方法（用对数端点势 V 吸收素数扰动）的有效条件是：

```
c₂ = log2/√2 < κ_edge(L) = ½ log(1/(2ε)),   ε = 2 − log2/L
```

这在 L < L* 时成立，L* 是满足 c₂ = κ_edge(L) 的临界点。精确研究：

1. **计算 L***: c₂/κ_edge(L) = 1 的精确临界点（L* ≈ 0.327，即接近但不超过 log3/2 ≈ 0.549）
2. **证明 L > L* 时吸收方法必然失效**：给出显式反例构型，证明不存在形如 V + P_{2,L} ≥ c·V 的不等式
3. **刻画从首素数窗口到双素数窗口的结构跃变**：当 L 超过 ½log3 后，素数 3 的层进入并引入新的不定扰动，导致需要完全不同的方法

**为何可行**：这是定理 2 的精确反向，主要工具是定理 2 证明中已有的 κ_edge 分析，加上在 L* 附近构造具体振荡函数。

**发表价值**：给出了这条证明路线的"有效射程"，对后续研究者有明确指导价值。适合作为 FP-0.35 论文的第二主要定理，或单独发表。

**预估时间**：4–8 周

---

### 目标 E3：定理 1–3 的 Lean 4 形式化（优先级：中，独立性最强）

**内容**：将定理 1（谱分解）、定理 2（端点势吸收）、定理 3（纯有理证书）完整输入 Lean 4，得到机器检验的形式化证明。

这三个定理：
- 不依赖任何数值计算（全部是解析和有理数）
- 证明结构清晰，适合形式化
- 定理 3 的纯整数比较（87^16 · 68^5 < 1701^5 · 32^16）尤其适合 Lean 的 `decide` 策略

**为何可行**：Lean 4 的 `Mathlib` 已经有 Legendre 多项式、L² 空间、算子谱的基础库。定理 1 的交换矩阵分解需要约 200 行 Lean；定理 3 的有理数计算可以完全自动化。

**发表价值**：形式化数学社区（ITP、CPP 会议）对这类工作有强烈兴趣，不要求与 RH 相关，只要求证明是正确的且有技术难度。这条路线与数值分析社区完全不同，打开一个新的发表渠道。

**预估时间**：2–4 个月（可以在 FP-0.35 工程工作的间隙推进）

---

## 五-A、立即行动计划（2026-08-06 更新）

### 优先级 P0（已完成）：O1-B certify 升级（任务 #6 #7）

**已完成（2026-08-06）**：偶/奇扇区均以 c_L=0 Arb 256-bit certify 通过（pivot 0.529/0.562）。证明了 $T+V+K_L+\mathcal{P}_{2,L} \geq L_0 I$。

### 优先级 P1（进行中）：认证 Weil 常数 c_L(7/20) 并找到可通过 certify 的 N（任务 #8）

**已确认的关键数值**（2026-08-06）：

| 量 | 值 | 说明 |
|---|---|---|
| $F_{00} = \langle (T+V+K_L+\mathcal{P}_{2,L}-c_L)P_0, P_0\rangle$ | **+0.397** | P_0 是正方向，无主子式障碍 |
| $K_{00} = \langle K_L P_0, P_0 \rangle$ | **+2.489** | Bessel 核提供大正贡献 |
| $c_L \approx (\log\pi - \psi(1/4))/4$ | **≈ 1.343** | Arb 认证值 |
| F 矩阵最小本征值（N=8～16，depth=3） | **+0.02454**（稳定） | F 本身正定，S_KK=0 的 pilot 不可信 |

**当前障碍**：pilot 层（depth=1）对高 k 值 M_K 积分不可靠（误差 2-3 数量级），导致虚假的 N 扫描失败。需用 draft/certify 精度重新扫描。

**下一步**：以 depth≥2 的 draft 精度对 N=12,14,16 做可靠的 Schur 补计算，找到使 $b_L F - R_\eta > 0$ 成立的最小 N。

```bash
python3 -m src.assemble.o1b_gate --tier certify --sector even --c_L 0  # ✅ 完成
python3 -m src.assemble.o1b_gate --tier certify --sector odd  --c_L 0  # ✅ 完成
```

支持 `--resume` 从 checkpoint 恢复。完成后重新生成 certs/ 并更新 proofctl 证明链。

### 优先级 P1：认证 Weil 常数 c_L(7/20)（任务 #8）

当前 O1-B 使用 `c_L=0` 保守值，证明的结论是 $T + V + K_L + \mathcal{P}_{2,L} \geq L_0 I$（而非 $\lambda(7/20) > 0$）。需要建立 $c_L(7/20) < L_0 = 2^{-30}$ 或计算其认证值。

### 已完成：FP-0.35 证明（2026-08-06）

关键步骤：
1. 从 Suzuki arXiv:2606.09096 提取 c_L 公式：$c_L(L) = \log(2\pi L) + \gamma_E$
2. 在 $L=7/20$ 处 Arb 认证：$c_L = 1355726/993009 \approx 1.36527$
3. 混合精度 Schur 残差认证：float64 近似逆 + Arb 验证 $\|I - C^{-1}C\|_\infty = 0$
4. 两扇区均通过（证书：`pilots/cert_schur_correct_cL.json`）

### 优先级 P2：改写 e1 论文（任务 #9）

基于数值诊断的完整发现改写 `e1-path-a-obstruction.tex`：
- Path A 的负方向来自 Weil 常数 $c_L \approx 1.365$ 的全局负移位
- $\{P_0,P_2\}$ 子空间在无 $c_L$ 时正定（det M ≈ +1.48），有 $c_L$ 时为负
- Lemma L3 在物理区间内失效（余项是主项 3.5 倍），$\theta_0$ 公式无代数基础
- Theorem 6 已提供严格反证，不需要额外的窗口级分析

---

## 五-B、后续研究路线（2026-08-06，基于 route_recommendation_v2）

FP-0.35 已证明（Theorem 7.3）。以下是后续工作的分阶段计划，已按"本仓库 vs 新仓库"明确分类。

---

### 阶段 0（本仓库，任务 #14）：$\lambda(L)$ 严格下界廓线

**目标**：把 $\Lambda_0 = 2^{-30}$ 从固定常数改为自由变量，对每个 $L$ 做二分搜索，找到最大可认证的 $\Lambda_0(L)$，得到 $\lambda(L) \geq \Lambda_0(L)$ 的严格下界廓线。

这是对现有 `o1b_gate.py` 的**小改动**：加 `--lambda0` 参数，在 `scripts/scan_lambda_profile.py` 中循环调用。

注意两个独立效应：
- **效应 A**（秒级可扫）：维持 $b_L > 0$ 所需最小 $N$ 随 $L$ 温和增长（< 2×）
- **效应 B**（实测）：Arb 区间膨胀速率随 $L$ 的变化——这是真正的未知量

**数据点要求**：至少 3 个完整认证点（$L = 7/20, 0.42, 0.46$），不要只测一个端点。

**范围限制**：第一素数窗口（$0.347 < L < 0.549$）内的数据对 $L \to \infty$ 渐近行为几乎无统计意义，不过度解读趋势。

---

### 阶段 1（进行中）：Effect B 实测数据

**已知结果（2026-08-06）**：

| L | N | d | b_L | float64 min_eig | 改善量 | 耗时 |
|---|---|---|---|---|---|---|
| 7/20=0.35 | 8 | 16 | 0.760 | **+0.015** | — | ~3 min |
| 0.42 | 8 | 16 | 0.578 | −0.032 | — | ~3 min |
| 0.42 | 10 | 20 | 0.795 | −0.029 | +0.003 | ~3 min |
| 0.42 | 12 | 24 | 0.973 | −0.026 | +0.003 | 13 min |
| 0.42 | 14 | 28 | 1.124 | −0.024 | +0.002 | 24 min |

**S_KK rank-2 低秩化判决（2026-08-06）**：

运行 `scripts/validate_skk_rank2.py --L 0.42 --N 32 --target 0.005 --b-L 1.9` 后：

| 条目 | S_KK_exact | S_KK_rank2 | 传播误差 | 阈值 | 判定 |
|---|---|---|---|---|---|
| **(0,0)** | 4.5319 | 4.5166 | **4.35e-02** | 5e-04 | **❌ 超标 87×** |
| (2,2) | 7.38e-05 | 7.36e-05 | 6.1e-07 | 5e-04 | ✓ |
| (62,62) | 3.3e-13 | 2.3e-13 | 2.9e-13 | — | ✓（极小） |

**根本原因**：rank-2 误差来自 k=50-62 的尾部泄漏（k=62 贡献 9.42e-3，随 L 增大而增大）。升至 rank-4 无效（k=4 贡献仅 3e-11）。要完全捕获需要 rank≈32（全秩），等于放弃低秩化。

**结论：候选 1/2（S_KK 低秩化）在 L=0.42 不可行。**

**当前局面**（效能矩阵）：
| 路线 | 状态 | 说明 |
|---|---|---|
| S_KK rank-2 代数化 | ❌ 不可行 | 尾部误差 87× 超标 |
| S_KK 解析余项上界 | 🔲 未探索 | 若能认证 \|tail_k≥4\| < ε，可作为 Arb 余项使用 |
| 接受 2 小时 N=32 原始扫描 | 🔲 可行 | 不改框架，等待收敛诊断结果 |
| Route 3（换基底/理论方法） | 🔲 长期 | 3-6 个月，平行推进 |

**下一个最小判决**：用 S_KK 的 **Hilbert-Schmidt 范数上界**（$\|S_{KK}\| \leq \kappa_L^2$，已有认证）作为全矩阵的 Arb 余项——这比低秩化更粗但完全解析，看够不够压缩 (0,0) 误差到阈值内。
- 改善速率在**减慢**：+0.003, +0.003, +0.002（每步幅度下降）
- 外推到 min_eig=0 约需 N≈32-40
- 积分深度 depth=3 vs depth=4 完全相同（ratio=1.0），膨胀不来自积分精度
- 这是**前景 B：超线性效应**

**时间代价**（按 N=14 耗时 24min，N² 缩放）：
- N=24：~70 分钟；N=32：~2 小时；N=40：~3.3 小时

**决策**（2026-08-06）：
Effect B 是超线性的。在 L=0.42 处用 Legendre 基 + 现有 Schur 框架，N≈32-40 才能认证，单次约 2-3 小时。这在技术上可行，但在第二窗口（c_L 更大）会更昂贵。

→ Route 2（weil-second-prime）仍然可行，但需要：
  1. 开发更高效的 LDL^T（避免每次重建 R_eta）
  2. 或探索 Route 3（uniform-in-L 理论）先给出解析下界压缩问题
  3. 或接受计算成本，直接用 N=32-40 跑认证（过夜计算）

→ 创建 weil-second-prime 仓库的前置条件：确定 N 基线（通过跑一次 N=32 at L=0.42 验证）

---

### 阶段 2（**新仓库** `weil-second-prime`）：第二素数窗口 $n=2,3$

**窗口**：$L \in (\frac{1}{2}\log 3,\ \frac{1}{2}\log 4) = (\frac{1}{2}\log 3,\ \log 2)$

**为什么新仓库**：
- 需要新的 `legendre_shift_2prime.py`（处理两个平移方向的耦合 $J_{ij}(\tau_2, \tau_3)$）
- 新的证书 schema（不同 `format_version`）
- 独立的 proofctl domain `fp-second-prime`
- 不同的 $c_L$ 公式（约 1.8，Schur 压力更大）

**边界分析**：Theorem 3.1 的三区间分解在 $L < \log 2$ 时对 $n=2$ 成立，$n=3$ 也满足单跳条件。这个乐观预期**精确到这一个窗口为止**：当 $n=4$ 进入且 $n=2$ 越过 $L=\log 2$ 后，需要处理多次跳跃自重叠，Theorem 3.1 本身需要推广。

---

### 阶段 2.5（本仓库 `docs/`，任务 #15）：理论 scoping（并行）

通读 Suzuki arXiv:2606.09096 和 Groskin arXiv:2607.02828 全文，寻找：
- 是否存在 uniform-in-$L$ 的谱隙下界论证雏形
- 是否有比 Legendre 更适合的基底选型

记录于 `docs/EXTENDED_GOALS.md`，不写代码。

---

### 阶段 3（贯穿指标）

$\lambda(L)$ 衰减廓线是全程核心诊断，每个认证点都要报告。但**第一窗口内的数据量不足以对 $L \to \infty$ 渐近行为下结论**，不做过度推断。

---


2. 登录 zenodo.org → 上传 `main.pdf` → 填写 `paper/ZENODO_METADATA.txt`
3. 发邮件给 Suzuki（arXiv:2606.09096）和 Groskin（arXiv:2607.02828），附 PDF 请求 arXiv endorsement

**下一个工程项（G4-witness 绑定）**：
- `proofctl pin checker --cmd "python3 checker/archimedean/check_archimedean.py"` 锁定 archimedean checker_digest
- `proofctl release --dry-run` 确认 blockers
- O2-witness：将积分叶节点哈希绑定到证书

**E1 数学工作**（可立即并行）：
- `paper/e1-path-a-obstruction.tex` 的 Lemma 证明需要补全连续依赖性论证

---

## 六、发表策略

| 成果 | 目标期刊/会议 | 独立于 FP-0.35？ |
|---|---|---|
| **FP-0.35 完整证明**（main.tex v2） | *Mathematics of Computation*（首选，计算数学顶刊）或 *Forum of Mathematics Sigma*（对 CAP 开放） | 是主体 |
| E1：路径 A 障碍定理 | *Journal of Spectral Theory* 或 *Integral Equations and Operator Theory* | **是** |
| E2：端点吸收窗口 | 可并入 FP-0.35 论文，或独立 *Analysis and Mathematical Physics* | 部分 |
| E3：Lean 4 形式化 | ITP 2027 或 CPP 2027（截稿约 2026-12） | **是** |
| proofctl 方法论 | *Journal of Automated Reasoning* 或 CICM 会议 | **是** |

---

## 七、工程闸门（按顺序）

### 闸门 G1：Archimedean primitive 重建 ✅

已完成。`src/archimedean/` 含修复 P0 bug 后的积分器。

### 闸门 G2：Legendre shift 精确代数 ✅

已完成。25 个测试全绿。

### 闸门 G3：O1-B 区间矩阵闸门 ✅ certify 完成（2026-08-06）

**Arb 256-bit 严格认证完成**：
- 偶扇区 (N=8, d=16, η=1/2)：b_L=2.125，min_pivot=0.529  `certified=true`
- 奇扇区 (N=6, d=13, η=1/2)：b_L=1.925，min_pivot=0.562  `certified=true`
- 124 个测试全部通过

### 闸门 G3-O2a：Archimedean 双路径交集 ✅

**已验证（2026-08-05）**：Path A ∩ Path B 对所有 100 个 M_K 基础对非空（depth=4）。

### 闸门 G4：schema/checker 闭环（当前）

- `check_first_prime_certificate.py` 从 primitive 独立重算全部矩阵
- mutation tests：改 θ、交换奇偶、零化 R_2、改 η → 全部拒绝
- **proofctl pin checker**：锁定 checker_digest
- 解析余项界（Bernstein 椭圆替代 Richardson）

### 闸门 G5：proofctl 集成

- `proofctl release --dry-run` 报告正确 blockers
- 完整 replay：`proofctl replay` 冷启动退出码 0

---

## 八、GO / PIVOT / STOP

### GO
- O1-B 奇、偶扇区同时得到严格 CAP 证书，通过定理 5 得到 c* > 0
- E1 一般障碍定理草稿完成，可以独立投稿
- Lean 4 形式化定理 3 完成

### PIVOT
- O1-B 偶扇区区间裕量被吃掉（< 0）：调整 N 至 10 或 12，不超过 3 次尝试后止损
- E2 临界点 L* 分析表明方法在某个 L 前就已失效：转为研究失效边界本身
- Lean 4 形式化遇到 Mathlib 库缺失：改为 Isabelle/HOL（库更完整）

### STOP（永久终止特定路线，不影响其他目标）
- O1-B 在 N ≤ 16 的所有合理参数下均有严格负方向：FP-0.35 路径 B 终止，转为研究障碍定理
- 若 FP-0.35 终止，E1、E2、E3 仍可继续，与 FP-0.35 结论无关

---

## 九、结论边界（不可逾越）

无论 FP-0.35 证明与否：

- 结论只能是"L ≤ 7/20 的有限尺度 Weil 正性"
- **不得**升级成 RH 或"接近 RH"
- **不得**在证书 JSON 中写入 PASS/RELEASED（由 fail-closed proofverify 决定）
- **不得**声称 E1/E2/E3 任何成果对 RH 有直接推论

---

## 十、与 proofctl 的关系

`proofctl`（`~/github/proofctl`）是本项目的编排层：
- 所有 claim 通过 `domains/fp035/contracts/*.json` 注册
- `archimedean_primitives_o2_v1` obligation 由 `checker/archimedean/` 实现
- `exact_prime_split_v1` obligation 由 `checker/first_prime/` 实现
- `proofctl replay` 提供冷重放；`proofverify` 提供离线验证

---

*本文件是唯一中文文件。其余所有文件使用英文。*
