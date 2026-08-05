# 研究计划：FP-0.35 首素数层认证

**基准日期：2026-08-05**
**当前状态：六个结构定理已闭合；路径 A 已严格淘汰；主路线为路径 B（O1-B）**

---

## 一、项目定位

本仓库是 `weil-lower-bound` 的后继，专注于首素数窗口 L = 7/20。

`weil-lower-bound` 已归档为 DEPRECATED，原因：
- 8 个 P0 级缺陷，`certified_radius` 始终为 null
- `integrate_M_K` 缺少求积截断误差包围
- `_rpp_mpmath` Taylor 三次项系数写错（s³/2880 → 7s³/11520）
- checker 与 schema 语义分离，不满足 fail-closed 要求

上述 P0 bug 已在本仓库的 `src/archimedean/` 重新实现时修复。

---

## 二、数学状态（2026-08-05）

### 已闭合

| 编号 | 内容 | 证据等级 |
|---|---|---|
| 定理 1 + 推论 1–2 | 截断平移精确谱、无小扰动 | 解析证明，可进入 Lean |
| 定理 2 | 端点势吸收首素数层 | 解析证明 |
| 定理 3 | 纯有理吸收证书 (69/100) | 纯有理级数证书 |
| 推论 3.1 | 势重分配降维 | 闭形次序直接推论 |
| 定理 4 | 首素数 Legendre 矩阵完全代数化 | Q[log2, sqrt(2)] 精确代数 |
| 定理 5 | 分裂残差 Schur 判据 | 解析证明 |
| 定理 6 | 路径 A 严格负见证 | 纯有理端点界 + Arb 认证一维积分 |
| L1–L3 | 边缘质量控制、H¹₀ 粗界、对数吸收 | 标准不等式 |

### 未解决

| 编号 | 内容 | 备注 |
|---|---|---|
| O1-B 偶扇区 | N=8, d=16, η=1/2 | Discovery 为正 (~8.81e-4)，未认证 |
| O1-B 奇扇区 | N=6, d=13, η=1/2 | Discovery 为正 (~3.44e-2)，未认证 |
| O2 | 可信证明链 | 工程/验证瓶颈 |
| FP-0.35 | 主猜想 λ(7/20) > 0 | 明确猜想 |

---

## 三、证明结构（路径 B）

路径 B 是当前唯一主路线（路径 A 由定理 6 严格淘汰）。

目标：证明 b_L > 0 且 b_L · F − R_η ≻ 0，其中：
- F = T_N + M^(0) + M^(2) − (c_L + L_0)G
- R_η = (1 + η)R_0 + (1 + 1/η)R_2，η = 1/2
- M^(2), S^(2), R_2 由定理 4 的 Q[τ] 代数计算
- M^(0), S^(0), R_0 由 Archimedean primitive（修复 P0 后）

证明充分条件不使用任何新的素数—Archimedean 交叉积分。

---

## 四、工程闸门（按顺序）

### 闸门 G1：Archimedean primitive 重建（当前阻塞点）

- 修复 `integrator_a.py`：`integrate_M_K` 必须调用带 GL-8/GL-4 余项的 `_integrate_1d_arb`
- 修复 `integrator_b.py`：将 `s³/2880` 改为 `7s³/11520`；余项必须使用 Bernstein 椭圆解析界
- 所有积分函数必须返回外向舍入的 Arb ball，不接受单侧估计
- 验收条件：`pytest tests/archimedean/` 全绿

### 闸门 G2：Legendre shift 精确代数

- `legendre_shift.py` 从 Legendre 递推用 `Fraction` 多项式精确计算 J_{ij}(τ)、E_{ij}(τ)
- 验证三个定向样例：J₀₀ = 4−2τ，J₁₁ = τ³/3−2τ+4/3，J₀₂ = −τ³+3τ²−2τ
- 验收条件：`pytest tests/prime_layer/` 全绿

### 闸门 G3：O1-B 区间矩阵闸门

- 偶扇区 (N=8, d=16)：组装 F_even, R_η_even，验证 b_L > 0 且 LDL^T 正定
- 奇扇区 (N=6, d=13)：组装 F_odd, R_η_odd，验证 b_L > 0 且 LDL^T 正定
- 两个扇区必须同时通过；任一失败则 FP-0.35 不可标记 PASS
- 所有数值必须是外向舍入区间，不接受浮点中心

### 闸门 G4：schema/checker 闭环

- `certificate-first-prime-v1.schema.json` 只允许 `exact_prime_split_v1`
- `check_first_prime_certificate.py` 从 primitive 独立重算全部矩阵
- mutation tests：改 θ、交换奇偶、零化 R_2、改 η → 全部拒绝
- 负测试：验证 4 个 PATH_A_REJECTED 元命题通过

### 闸门 G5：proofctl 集成

- `domains/fp035/` ContractV2 全部通过 `proofctl contract lint`
- `proofctl status` 正确显示所有 claim 状态
- `proofctl release --dry-run` 在 O1-B 未认证时报告正确 blockers
- 完整 replay：`proofctl replay` 冷启动退出码 0

---

## 五、GO / PIVOT / STOP

### GO
- O1-B 奇、偶扇区同时得到严格 CAP 证书，通过定理 5 得到 c* > 0
- 或得到更强的解析边缘补偿定理，可覆盖整个首素数窗口

### PIVOT
- O1-B 某扇区严格出现负方向：调整 N 或 η，不超过 3 次
- 发现更强的吸收定理可替代路径 B

### STOP（永久终止）
- 只有浮点最小特征值
- 只有有限维正定矩阵（无无限维闭包）
- 关键下界引用 RH 或等价正性命题
- "几何化""无源性""Frobenius 类比"等词出现在核心论证中

---

## 六、结论边界（不可逾越）

无论 FP-0.35 证明与否：

- 结论只能是"L ≤ 7/20 的有限尺度 Weil 正性"
- **不得**升级成 RH 或"接近 RH"
- **不得**在证书 JSON 中写入 PASS/RELEASED（由 fail-closed proofverify 决定）

---

## 七、与 proofctl 的关系

`proofctl`（`~/github/proofctl`）是本项目的编排层：
- 所有 claim 通过 `domains/fp035/contracts/*.json` 注册
- `archimedean_primitives_o2_v1` obligation 由 `checker/archimedean/` 实现
- `exact_prime_split_v1` obligation 由 `checker/first_prime/` 实现
- `proofctl replay` 提供冷重放；`proofverify` 提供离线验证

---

*本文件是唯一中文文件。其余所有文件使用英文。*
