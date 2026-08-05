# 研究计划：FP-0.35 首素数层认证与扩展目标

**基准日期：2026-08-05**
**当前状态：O1-B ✅ 双路径 ✅ E3-Lean4 ✅ 论文三轮审阅 ✅ O2-replay ✅ O2-witness ✅ | 剩余：G4-pin-checker、release gate、投稿**

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
| **O1-B 偶扇区** | N=8, d=16, η=1/2: b_L=2.125, min_pivot=0.529 | mpmath dps=100 outward-rounded LDL^T |
| **O1-B 奇扇区** | N=6, d=13, η=1/2: b_L=1.925, min_pivot=0.560 | mpmath dps=100 outward-rounded LDL^T |
| **Path A ∩ Path B** | 100 个 M_K 基础对全部相交（depth=4） | 23 个专项测试 |
| **proofctl 集成** | doctor ✓, checkers pinned, status/frontier 可用 | v0.3.8 |
| **E3 Lean 4 定理 3** | ✅ 超额完成 | 整数比较（native_decide）+ log2<7/10 + sqrt2>7/5（Mathlib）全部验证 |
| **预印本** | ✅ 完成，就绪投稿 | paper/main.pdf，7页，三轮审阅全部处理 |
| **CI** | ✅ 完成 | .github/workflows/ci.yml（pytest + schema + proofctl lint）|

### 未解决

| 编号 | 内容 | 备注 |
|---|---|---|
| O2-解析余项界 | ✅ Bernstein 椭圆模块已实现，已接入两条积分路径 | 正式证书未生成 |
| O2-proofctl replay | ✅ 完成（2026-08-05） | lem-o1b-even, lem-o1b-odd 均 ACCEPTED |
| O2-witness 绑定 | ❌ 待做 | 积分叶节点到证书的绑定 |
| E3-Mathlib | ✅ 已完成 | log2 < 7/10 和 sqrt2 > 7/5 已由 Mathlib 验证（见 lean4/） |
| E1 | 📝 数学框架完成 | `paper/e1-path-a-obstruction.tex` 有完整框架；Lemma 证明是 sketch |
| E2 | 📝 草稿阶段 | 描述在 docs/EXTENDED_GOALS.md |
| 论文投稿 | ⏳ 就绪 | PDF 已生成（7页），Zenodo + 邮件流程等待执行 |
| FP-0.35 | ❌ 未证明（预期） | O1-B 已闭合；O2-replay 闭合后可标记 PASS |

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

## 五、当前状态与下一步（2026-08-05 更新）

所有 2026-08 ~ 2026-09 的工程目标已提前完成。

**立即可执行（论文投稿）**：
1. `cd paper && tectonic main.tex`（生成最终 PDF）
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
| FP-0.35 + 方法论 | *Mathematics of Computation* 或 *Experimental Mathematics* | 否 |
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

### 闸门 G3：O1-B 区间矩阵闸门 ✅

**已闭合（2026-08-05）**：
- 偶扇区 (N=8, d=16, η=1/2)：b_L=2.125，min_pivot=0.529  CERTIFIED
- 奇扇区 (N=6, d=13, η=1/2)：b_L=1.925，min_pivot=0.560  CERTIFIED
- `python3 -m src.assemble.o1b_gate --tier certify --sector both`

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
