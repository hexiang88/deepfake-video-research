# 视频合成内容检测调研

> 给后续测试人员：先看 **§1 总决策卡** 和 **§2 赛道入准表**，再按入准结果打开方案卡片。数据集台账见 [`datasets/video.md`](../datasets/video.md)。论文表快照见 [`source-snapshots/audio-video-paper-tables-2026-08-13.md`](../source-snapshots/audio-video-paper-tables-2026-08-13.md)。AuViRe 分表口径见 [`source-snapshots/auvire-metrics-2026-08-12.md`](../source-snapshots/auvire-metrics-2026-08-12.md)。**本机首批复测台账**见 [`video-eval-first-batch-2026-08-18.md`](video-eval-first-batch-2026-08-18.md)（换脸 LipForensics / RealForensics / PwTF-DVD 见该文件 §3.1–§3.3；**VLAForge 本机不可用，已取消检测**；**Talking Face / 唇音 / TFL 见该文件 §4**，不要并入 §3.1，不要把论文 JSON 当成本机数字，不要写入 `cross_dataset.json`。AuViRe 无 FakeAVCeleb 行。**AV-Deepfake1M 是 LAV-DF 的升级集**：未知威胁与本机主报优先 AVD 训练头、AVD val；LAV 只作前代对照与迁移诊断，不要当成第二条赛道。AuViRe / DiMoDif 本机 DFD/TFL 已填：主看 `avd1m_official_val_subset_800`（AuViRe 实 n=792，DiMoDif 实 n=800，validation 子集，非 Codabench）；LAV 子集 `lavdf_official_test_subset_800` 仅用于跨域格。**不是**仓库全量 JSON。方案互补看 AuViRe vs DiMoDif。本批可报官方协议可复现与跨域失效边界；不能写可部署、已覆盖真实业务、唇音同步已过关。）。三模型本机视频级 AUC / AP 已填在该台账 §3.1，测试集为导师换脸抽样 `mentor_swap_200`（seed=20260818），**不是**论文 Table 2，也不是 Celeb-DF / FF++ / DFDC，也不是鲁棒性或跨数据集泛化结论。RealForensics leave-one-out 本机视频级 AUC 已填在该台账 §3.2 / §3.3，测试集为 `ffpp_official_test_available`，**不是**论文 Table 1，也不是 `mentor_swap_200`。TFL 不能用导师换脸集补（无伪造区间标注）。

**怎么下判断：**`可测` = 已核验或已指定的联合/相邻候选，可以开测。`可对照` = 许可证或代码未齐，可跑但不与已核验混排。`须备注` = 稀缺方向用联合模型代理，结果表头必须写清测的是什么、不是什么。跨数据集 AUC、跨操纵 AUC、DFD、TFL、Codabench **分表**，禁止合成总榜。

**DeepfakeBench 是评测框架，FaceForensics 是数据集入口，都不是检测算法。6 个方案不是开测前提。**

## 1. 总决策卡

| 测试人员要问的事 | 结论 |
|---|---|
| Q3 现在能开测什么？ | 换脸跨数据集、换脸跨操纵、换脸同域（GenConViT 另表）、时序、Talking Face DFD、时间定位；**人脸重演、唇音同步也开测**，用下面指定的联合/相邻模型并加备注 |
| 哪些只能对照？ | FakeSTormer、FTCN、AltFreezing、ICS-AV、AVSSDeepfakeDet |
| 已核验检测器 | LipForensics、RealForensics、PwTF-DVD、VLAForge、GenConViT、AuViRe、DiMoDif |
| 数量够不够才能测？ | **够。** 找到几个标几个；约 6 个只是理想规模 |
| 绝对禁止 | 混合 c0/c23、帧级/视频级、DFD 与 TFL、validation 与 Codabench；把重演/唇音结果写成“已有专项检测器”或与换脸总榜合并 |

## 2. 赛道入准表

| 赛道 | 判定 | 用哪些模型 | 数据与划分 | 指标 | 禁止 |
|---|---|---|---|---|---|
| 换脸跨数据集 | **可测** | LipForensics、RealForensics、PwTF-DVD、VLAForge | FF++ 训练 → Celeb-DF / DFDC / FaceShifter / DeeperForensics / DFD 等；标明 c23、视频级 | 视频级 AUC / AUROC | 不与帧级混排；VLAForge 视频级是帧平均，需在表头写明 |
| 换脸跨操纵 | **可测** | RealForensics Table 1 | FF++ leave-one-manipulation，c23：DF / FS / F2F / NT | 视频级 AUC | DF/FS 与 F2F/NT 可同表分列；重演赛道单独引用 F2F/NT 两列，见下一行 |
| 人脸重演 | **可测（须备注）** | **主候选** RealForensics（F2F、NT）；**辅助** LipForensics | FF++ c23，Face2Face / NeuralTextures | 视频级 AUC | **备注：** 这是换脸基准上的重演类操纵，不是音频/姿态驱动专项检测器。结果表标题写成“FF++ 重演类操纵（联合/相邻模型）”，不要与 DF/FS 换脸列合成重演总分 |
| 换脸 in-domain 混合训练 | **可测（另表）** | GenConViT | 作者在 DFDC / FF++ / TIMIT / Celeb-DF v2 上混合训练并同域评测 | Acc / AUC / F1，按数据集分列 | **不得**与 FF++→跨数据集 AUC 合并；作者写明测试子集通常不共享 |
| 时序一致性 | **可测主模型 + 对照** | 主：PwTF-DVD。对照：FTCN、AltFreezing | FF++ 训练后的跨数据集 AUC | 视频级 AUC | 对照模型无完整训练代码，不与主模型混排 |
| Talking Face / DFD | **可测** | AuViRe、DiMoDif | **主：AV-Deepfake1M val**（优先 AVD 训练头）。LAV-DF 为前代对照，只进跨域格。FakeAVCeleb 仅 DiMoDif。按训练域×测试域分表 | DFD AUC（及论文给出的 AP/ACC） | 不与换脸跨数据集表合并；不把 LAV 与 AVD 并列为两个赛道；DiMoDif Table 5 的 ACC 带 * 为验证集 |
| 时间定位 TFL | **可测** | AuViRe（JSON）、DiMoDif（论文 Table 7/8） | **主：AV-Deepfake1M val**；LAV-DF 只作迁移诊断 | AP@IoU、AR | 不与 DFD 混排；不与 Codabench test 拼接；LAV 训练头在 AVD 上的低 AP 不得当主结论 |
| 唇音同步 | **可测（须备注）** | **联合模型候选** AuViRe、DiMoDif；对照 ICS-AV | 同上，主报 AVD | DFD AUC、TFL AP；DiMoDif Table 6 的 RVFA 列必报 | **备注：** 没有毫秒/帧偏移官方协议。本赛道测的是音视频是否不一致、假片段在哪，**不是**偏移误差。表头写“联合模型代理唇音/跨模态不一致”，不要写成 sync EER |
| FakeSTormer c23 对照 | **可对照** | FakeSTormer | FF++ c23，T=4 | 六数据集视频级 AUC | 许可证未声明；不与 c0 行合并 |
| 编排 | 框架，不计方案数 | DeepfakeBench | 由具体模型协议决定 | — | 不把框架算成检测器 |

## 3. 各方向已标注模型

数量不是门槛。下表供测试人员对号入座。

| 方向 | 已核验 / 测试候选 | 测试含义 |
|---|---|---|
| 换脸 | LipForensics、RealForensics、PwTF-DVD、VLAForge；GenConViT 另表 | 跨数据集与同域不要合并 |
| 时序一致性 | PwTF-DVD；对照 FTCN、AltFreezing | 可开测 |
| 人脸重演 | RealForensics 的 F2F/NT；辅助 LipForensics | **开测，须备注**联合/相邻代理 |
| 说话人脸合成 | AuViRe、DiMoDif；对照 ICS-AV、AVSSDeepfakeDet | 可开测 |
| 唇音同步 | AuViRe、DiMoDif（联合模型）；对照 ICS-AV | **开测，须备注**用 DFD/TFL 代理，不是偏移误差 |

公开专项检测器仍然少：没有独立的音频驱动重演器，也没有官方偏移分层协议。这不阻止用上表候选开测，只要求备注写在结果表头。

### 备注要写什么（复制即可）

- 重演：「候选为 RealForensics / LipForensics；评测对象是 FF++ Face2Face 与 NeuralTextures，不是独立重演检测器。」
- 唇音：「候选为 AuViRe / DiMoDif；指标为音视频检测 AUC 与伪造区间 AP，不是唇音偏移毫秒/帧误差。」

## 4. 方案卡片

### 4.1 已核验 · 换脸跨数据集（同一协议族，可同表）

训练域默认 FF++。数字为视频级 AUC（%），除非另行标明。

| 方案 | 仓库 / 许可 | 绑定数字 | 测试时怎么用 |
|---|---|---|---|
| **LipForensics** | [ahaliassos/LipForensics](https://github.com/ahaliassos/LipForensics)，MIT；[arXiv:2012.07657](https://arxiv.org/abs/2012.07657) | Table 2：Celeb-DF-v2 **82.4**、DFDC **73.5**、FaceShifter HQ **97.1**、DeeperForensics **97.6**，平均 87.7 | 嘴部时空基线。DFDC 最低，跨域不要只报平均值。本机 `mentor_swap_200` 视频级 AUC/AP 见首批台账 §3.1，勿与本列论文 Table 2 合并 |
| **RealForensics** | [ahaliassos/RealForensics](https://github.com/ahaliassos/RealForensics)，MIT；[arXiv:2201.07131](https://arxiv.org/abs/2201.07131) | Table 2：CDF **86.9**、DFDC **75.9**、FaceShifter **99.7**、DeeperForensics **99.3**，平均 90.5。Table 1（c23 leave-one-out）：DF **100.0**、FS **97.1**、F2F **99.7**、NT **99.2** | 跨数据集用 Table 2。重演赛道只引用 Table 1 的 **F2F / NT** 两列，并加 §3 备注。本机 `mentor_swap_200` 视频级 AUC/AP 见首批台账 §3.1，勿与本列论文 Table 2 合并。本机 leave-one-out 视频级 AUC 见首批台账 §3.2 / §3.3（`ffpp_official_test_available`），勿与本列论文 Table 1 合并 |
| **PwTF-DVD** | [rama0126/PwTF-DVD](https://github.com/rama0126/PwTF-DVD)，MIT；[arXiv:2507.02398](https://arxiv.org/abs/2507.02398) | Table 2：CDF **89.7**、DFDC **75.2**、FaceShifter **99.3**、DeeperForensics **99.4**、DFD **97.3**，平均 92.2。Table 3 KoDF **91.3**（作者复现对照） | 时序主模型，同时可进跨数据集表。本机 `mentor_swap_200` 见首批台账主表（AUC/AP）与附录（P/R/F1/EER），勿与本列论文 Table 2 合并 |
| **VLAForge** | [mala-lab/VLAForge](https://github.com/mala-lab/VLAForge)，MIT；[arXiv:2603.24454](https://arxiv.org/abs/2603.24454) | Table 1，FF++ c23。帧级 AUROC：CDF-v1 93.9、CDF-v2 91.2、DFDC 87.0、DFD 93.6。视频级（帧平均）：CDF-v2 **96.8**、DFDC **89.6**、DFD **97.2** | 与上列同表时只用**视频级**行；帧级另表 |

### 4.2 已核验 · 换脸 in-domain（另表，不与 4.1 合并）

| 方案 | 仓库 / 许可 | 绑定数字 | 测试时怎么用 |
|---|---|---|---|
| **GenConViT** | [erprogs/GenConViT](https://github.com/erprogs/GenConViT)，MIT；[arXiv:2307.07036](https://arxiv.org/abs/2307.07036) | Table IV Acc：DFDC **98.50**、FF++ **97.00**、TIMIT **98.28**、Celeb-DF v2 **90.94**。Table V AUC：DFDC **99.9**、FF++ **99.6**、Celeb-DF v2 **98.1**。Table VI F1：DFDC 99.1、FF++ 95.5、TIMIT 98.3、Celeb-DF v2 91.6。作者称平均 Acc 95.8%、AUC 99.3%，**不要用平均值排名** | 只作为混合训练同域表。Table X：Celeb-DF v2 完全 held-out 时 fake Acc **11.56%**，说明 OOD 会垮，内部复测必须做 unseen 生成器 |

### 4.3 已核验 · Talking Face / 定位（与换脸分表）

| 方案 | 仓库 / 许可 | 绑定数字 | 测试时怎么用 |
|---|---|---|---|
| **AuViRe** | [mever-team/auvire](https://github.com/mever-team/auvire)，Apache-2.0；[arXiv:2511.18993](https://arxiv.org/abs/2511.18993) | 仓库 JSON：按训练域/测试域给出 DFD AUC 与 TFL AP@0.5/0.75/0.9/0.95。`results/test/*.json` 的 `tauc`/`tap@*` 为百分数；Codabench 相关 `metrics.json` 为 0–1 小数 | **默认用 AVD 训练头**（未知威胁 / 本机主报）。LAV 训练头只用于对照：LAV→AVD 的 DFD AUC ~65.7、TFL AP@0.5 ~16 是能力边界，不是第二条方案。validation 与 Codabench test 分表。细节以 auvire 快照为准。**本机部署/复测只写台账 §4**，不要把本列论文/仓库 JSON 改成本机格。无 FakeAVCeleb 行 |
| **DiMoDif** | [mever-team/dimodif](https://github.com/mever-team/dimodif)，Apache-2.0；[arXiv:2411.10193](https://arxiv.org/abs/2411.10193) | **DFD in-dataset：** Table 3 FakeAVCeleb ACC **99.4** / AUC **99.7**；Table 4 LAV-DF AUC **99.84**；Table 5 AV-Deepfake1M AUC **96.3**、ACC **96.3\***（\*验证集）。**跨操纵** Table 6 FakeAVCeleb：AVG-FV AUC **99.9**，但 RVFA（真视频假音频）AUC **51.6**。**TFL** Table 7 LAV-DF AP@0.5 **95.5** / AP@0.75 **87.9** / AP@0.95 **20.6**；Table 8 AV-Deepfake1M AP@0.5 **86.93** / AP@0.75 **75.95** / AP@0.9 **28.72** / AP@0.95 **5.43**。**跨数据集 DFD** Table 9 按训练域×测试域，见 §5 | DFD 与 TFL 分表。RVFA 51.6 说明假音频真视频仍难，测试报告必须保留该列。不要用摘要里的“+30.5 AUC”相对值。**本机只写台账 §4**（AVD 训练头、`*_whole.pth`、AutoAVSR 特征；FakeAVCeleb / RVFA 仍 `data_missing`） |

### 4.4 可对照（不进精度表）

| 方案 | 缺口 | 可引用数字 | 测试时怎么用 |
|---|---|---|---|
| **FakeSTormer** | 许可证 `NOASSERTION` | Table 1，FF++ c23，T=4：CDF2 92.4、DFD 98.5、DFDCP 90.0、DFDC 74.6、WildDeepfake 74.2、DiffSwap 96.9 | c23 对照行；不与 c0 合并 |
| **FTCN** | 无训练代码；许可证未声明 | Table 4，FF++ HQ：CDF 86.9、DFDC 74.0、FaceShifter 98.8、DeeperForensics 98.8 | 时序论文对照 |
| **AltFreezing** | 训练完整性未核 | Table 1：CDF 89.5、DFD 98.5、FaceShifter 99.4、DeeperForensics 99.3 | 时序论文对照 |

### 4.5 官方候选，本轮不够测

| 方案 | 状态 | 测试人员动作 |
|---|---|---|
| MesoNet | Apache-2.0；作者自建数据 Acc，不是 FF++ 官方划分 | 历史轻量基线，不进现代跨域表 |
| ICS-AV | 训练/评测+checkpoint；许可证未声明；README 无绝对表 | 唇音/Talking Face **对照**，不与 AuViRe/DiMoDif 混排 |
| AVSSDeepfakeDet | 仅推理与 checkpoint | Talking Face 对照 |
| TI2Net / StyleFlow | 无预训练或推理不完整 | 不安排正式测试 |
| ISTVT、MSAVR-TDL、From Talking to Singing | Coming soon 或仅架构 | 排除 |

## 5. DiMoDif Table 9：跨数据集 DFD（抄表用）

来源：[arXiv:2411.10193](https://arxiv.org/abs/2411.10193) Table 9。\* 为验证集。单位 AP / AUC。

| 训练域 ↓ / 测试域 → | FakeAVCeleb AP | FakeAVCeleb AUC | LAV-DF AP | LAV-DF AUC | AVD1M\* AP | AVD1M\* AUC |
|---|---:|---:|---:|---:|---:|---:|
| FakeAVCeleb | 99.99 | 99.71 | 93.10 | 84.47 | 77.91 | 54.00 |
| LAV-DF | 99.69 | 90.25 | 99.94 | 99.84 | 88.46 | 70.40 |
| AV-Deepfake1M | 99.69 | 90.69 | 94.98 | 86.30 | 99.72 | 99.18 |

**测试读法：**对角是闭集，高；FakeAVCeleb→AVD1M AUC **54.00** 是跨域检测风险。报告跨域时必须写训练域，不能只报 99.7。LAV-DF→AVD1M AUC **70.40** 同样说明前代集训出来的头盖不住升级集；工程上优先 AVD 训练域。

### 5.1 LAV-DF 与 AV-Deepfake1M：升级关系，不是两条赛道

AVD 论文写明 LAV 是同一任务的前代：规模小、生成器伪迹粗、定位 SOTA 已打满。本机口径：

- **主报 / 未知威胁：** AV-Deepfake1M（本地评 **val**，不是 Codabench hidden test）+ AVD 训练头。
- **LAV-DF：** 只保留跨域格，用来证明「前代头迁不到升级集」；不要把 LAV 闭集 99 当成 Talking Face 主结论。
- **方案互补**看 AuViRe vs DiMoDif（机制不同），不看 AuViRe 的 LAV 头 vs AVD 头。

**改稿方式不是检测器训练步骤。** 它发生在造假数据集生成阶段：先改口播稿（替换 / 插入 / 删除词句），再用 TTS 和唇形生成器合成对应音视频片段。检测器训练只吃已经造好的 mp4 与伪造区间标签，超参里没有「改稿」。LAV 用规则反义词且只有替换；AVD 用 LLM 且含插入、删除。这是两集难度不同的原因之一，不是 AuViRe/DiMoDif 的网络结构差异。

## 6. 任务边界

| 细分方向 | 测的是什么 | 现在用什么开测 |
|---|---|---|
| 换脸 | 人脸纹理/身份，跨数据集或跨操纵 | LipForensics 等已核验模型 |
| 人脸重演 | 表情/几何被驱动后是否可检出 | RealForensics 的 F2F/NT（须备注：FF++ 重演类操纵） |
| Talking Face | 音视频联合真假，可含局部伪造 | AuViRe、DiMoDif；**主测试域 AVD val** |
| 唇音同步 | 声音与口型是否不一致 | AuViRe、DiMoDif 的 DFD/TFL（须备注：不是偏移误差；主报 AVD） |
| 时序一致性 | 连续帧运动/编码伪影 | PwTF-DVD |

## 7. 排除项

- **DeepfakeBench**、**FaceForensics**：框架 / 数据，不计检测器。
- **Open-AVFF**：非官方实现。
- **ISTVT**、**MSAVR-TDL**、**From Talking to Singing**：无完整可运行代码。
- Ashutosh Anshul [arXiv:2511.10212](https://arxiv.org/abs/2511.10212) **不是** ICS-AV。

## 8. 后续补强（不影响当前开测）

若以后出现作者官方的音频/姿态驱动重演器，或带毫秒/帧偏移协议的唇音检测器，再单列专项表，不必替换现在的联合模型结果。ICS-AV 补齐许可证和绝对指标后，可从对照升为唇音/Talking Face 正式候选。

推荐工程顺序：DeepfakeBench 只编排 → 换脸 LipForensics / RealForensics / PwTF-DVD / VLAForge → 重演用 RealForensics F2F/NT（加备注）→ Talking Face / 唇音 / 定位用 AuViRe 与 DiMoDif（**优先 AVD 训练头与 AVD val**；唇音加备注）。内部复测前不得对外宣称 SOTA。
