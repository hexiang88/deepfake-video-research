# 音频合成内容检测调研

> 给后续测试人员：先看 **§1 总决策卡** 和 **§2 赛道入准表**，再按入准结果打开方案卡片。数据集台账见 [`datasets/audio.md`](../datasets/audio.md)。论文表快照见 [`source-snapshots/audio-video-paper-tables-2026-08-13.md`](../source-snapshots/audio-video-paper-tables-2026-08-13.md)。

**怎么下判断：**`可测` = 已核验或已指定的代理候选，可以开测。`可对照` = 许可证未齐，可跑但不与已核验混排。`须备注` = 稀缺方向用通用反欺骗/离线模型代理。跨赛道数字一律分表，禁止合成总榜。**约 6 个方案不是开测前提。**

## 1. 总决策卡

| 测试人员要问的事 | 结论 |
|---|---|
| Q3 现在能开测什么？ | 闭集反欺骗、逐攻击拆分、跨年/跨域；**VC、克隆、实时也开测**，用下面指定模型并加备注 |
| 哪些只能对照、不与已核验混排？ | 未知 codec（Codecfake）、混合音频（MixFake）、隐私约束（SafeEar）、SLS README EER |
| 已核验模型 | AASIST、RawGAT-ST、Raw-PC-DARTS、XLSR-MamBo |
| 数量够不够才能测？ | **够。** 找到几个标几个 |
| 绝对禁止 | 把池化 EER 写成“全部 TTS/全部 VC”；把 2019 与 2021/ITW/Codecfake/MixFake 混排；把离线 EER 写成官方实时指标 |

## 2. 赛道入准表

测试人员按行决定：测 / 对照 / 停。同一模型可出现在多行，但只在该行协议下计分。

| 赛道 | 判定 | 用哪些模型 | 数据与划分 | 指标 | 禁止 |
|---|---|---|---|---|---|
| 闭集反欺骗 | **可测** | AASIST、RawGAT-ST、Raw-PC-DARTS | ASVspoof 2019 LA **evaluation**；攻击 A07–A19 | 池化 EER、min t-DCF | 不写成“全部 TTS”；不与跨年结果混排 |
| 逐攻击拆分 | **可测** | AASIST Table 1；同文复现的 RawGAT-ST | 同上，按 A07–A19 分列 | 逐攻击 EER | 不要用 AASIST 复现值替代 RawGAT-ST 原文池化值 |
| 语音转换（VC） | **可测（须备注）** | AASIST、RawGAT-ST（通用反欺骗代理） | 2019 LA eval，Table 1 分列 | 逐攻击 EER | **备注：** 尚无官方攻击→VC 家族清单，先按攻击 ID 报，不要合成一个 VC 总分。Raw-PC-DARTS 可作闭集对照，不要只用 A08 代表 VC |
| 跨年 / 跨域 | **可测** | XLSR-MamBo（主）；SLS（对照） | 2019 LA 训练 → 21LA / 21DF / ITW；MamBo 另测 DFADD | EER | DFADD 的 D1–D3=扩散、F1–F2=flow-matching，不是 ASVspoof 攻击 |
| 语音克隆 | **可测（须备注）** | **主候选** XLSR-MamBo 的 ITW；对照 ArcFace_ADD | 2019 LA 训练 → In-the-Wild；有参考路线另列 | EER | **备注：** ITW 是名人/政客跨域集，不是克隆专项检测器。ArcFace_ADD 指标未齐，只对照、不与无参考模型混排 |
| 未知 codec | **可对照** | Codecfake W2V2-AASIST | Codecfake 训练；C7 unseen；C1–C7 CAVG | EER / CAVG | 不与 19LA 闭集或 MixFake 合并；数据集 CC BY-NC-ND 4.0 |
| 混合音频 | **可对照** | MixFake | Foreground 与 Background **分列**；ITW 另表 | EER | 两套标签不可合并；仓库许可证未声明 |
| 隐私约束 | **可对照** | SafeEar | ASVspoof 2019/2021；CVoiceFake 五语 | EER / t-DCF | 2.02% 是五语平均，不是“四基准最低”；许可证冲突 |
| 有参考声纹 | **可对照** | ArcFace_ADD | 参考语音 + 待测语音 | — | 指标未绑定；可作克隆赛道对照环境 |
| 实时 / 流式 | **可测（须备注）** | AASIST、RawGAT-ST、Raw-PC-DARTS（离线模型代理） | 测试方自定窗口、步长 | 自定窗口下的 EER，并记录硬件与延迟 | **备注：** 无官方窗口/首检延迟实验。结果不得写成论文实时指标；Raw-PC-DARTS 输入本就是 4 s 窗口，可作起点 |

## 3. 各方向已标注模型

数量不是门槛。

| 方向 | 已核验 / 测试候选 | 测试含义 |
|---|---|---|
| TTS / 闭集反欺骗 | AASIST、RawGAT-ST、Raw-PC-DARTS、XLSR-MamBo | 可开测；池化值不要写成全部 TTS |
| 扰动泛化 | XLSR-MamBo；对照 Codecfake、MixFake、SafeEar | 分赛道，不要合成鲁棒性总分 |
| 语音转换（VC） | AASIST、RawGAT-ST（通用反欺骗代理） | **开测，须备注**按攻击 ID 分列 |
| 语音克隆 | XLSR-MamBo ITW；对照 ArcFace_ADD | **开测，须备注**ITW 是跨域集 |
| 实时音频 | AASIST、RawGAT-ST、Raw-PC-DARTS（离线代理） | **开测，须备注**窗口由测试方自定 |

### 备注要写什么（复制即可）

- VC：「候选为 AASIST / RawGAT-ST；按 ASVspoof 2019 LA 攻击 ID 报告，尚未按官方 VC 家族汇总。」
- 克隆：「候选为 XLSR-MamBo，测试集 In-the-Wild；不是说话人隔离的克隆专项协议。」
- 实时：「候选为离线反欺骗模型；窗口/步长/延迟由本次测试记录，不是论文官方实时指标。」

## 4. 方案卡片

开源类型：**完整代码** = 训练和推理都可见。`已核验` 才能进对应赛道精度表。

### 4.1 已核验（可测）

| 方案 | 仓库 / 许可 | 输入 → 输出 | 绑定数字（必须连条件一起抄） | 测试时怎么用 |
|---|---|---|---|---|
| **AASIST** | [clovaai/aasist](https://github.com/clovaai/aasist)，MIT；[arXiv:2110.01200](https://arxiv.org/abs/2110.01200) | 波形/声学特征 → spoof 分数 | Table 2：2019 LA eval 池化 min t-DCF **0.0347**（最佳种子 0.0275）、EER **1.13%**（最佳 0.83%）；三种子平均。逐攻击见 §5 | 闭集主基线。不要用池化值代表某一攻击 |
| **RawGAT-ST** | [eurecom-asp/RawGAT-ST-antispoofing](https://github.com/eurecom-asp/RawGAT-ST-antispoofing)，MIT；[arXiv:2107.12710](https://arxiv.org/abs/2107.12710) | 原始波形 → 分数 | 原文 Table 4：RawGAT-ST-mul 池化 min t-DCF **0.0335**、EER **1.06%**。对照 RawNet2 基线 0.1547 / 5.54% | 闭集结构对照。精度表用**原文池化值**，不要用 AASIST 文中的复现值 |
| **Raw-PC-DARTS** | [eurecom-asp/raw-pc-darts-anti-spoofing](https://github.com/eurecom-asp/raw-pc-darts-anti-spoofing)，MIT；[arXiv:2107.12212](https://arxiv.org/abs/2107.12212) | 4 s / 16 kHz 波形 → 分数 | Table 2 Mel-Fixed：min t-DCF **0.0517**、EER **1.77%**。Table 3 最差攻击 **A08 EER 4.96%** | 轻量闭集对照。A08 只说明最差攻击，不是 TTS 专项 |
| **XLSR-MamBo** | [saki-ciallo/XLSR-MamBo](https://github.com/saki-ciallo/XLSR-MamBo)，MIT；[arXiv:2601.02944](https://arxiv.org/abs/2601.02944) | XLSR-300M + Mamba/Hydra → 分数 | 2019 LA 训练。MamBo-3 EER（%）：21LA **0.81** / 21DF **1.70** / ITW **4.97**；D1–D3 / F1–F2 见仓库表。论文 §5.1：D1–D3 扩散、F1–F2 flow-matching | 跨域主基线。ITW/DFADD 不与 2019 闭集混排 |

### 4.2 可对照（不进精度表）

| 方案 | 缺口 | 已绑定、仅作对照的数字 | 测试时怎么用 |
|---|---|---|---|
| **Codecfake** W2V2-AASIST | 仓库许可证未声明；数据 CC BY-NC-ND 4.0 | Table VI：C7 unseen EER **0.884%**，C1–C7 CAVG **0.177%**。Table X CSAM：CAVG **0.077%**，C7 **0.431%** | 只跑未知 codec 赛道。禁止把仅 19LA 训练的 Table V 与 Table VI 合并 |
| **MixFake** | 仓库许可证未声明 | Table II：Foreground EER **0.95%** / Background **12.40%**。Table III：ITW **6.24%**。SNR 15 dB **0.36%**、−5 dB **3.10%** | 前景/背景分列。不要报一个混合总分 |
| **SafeEar** | SPDX `NOASSERTION` vs README CC BY 4.0 | Table 2：2019 EER **3.10%** / 2021 **7.22%**。Table 3：CVoiceFake 五语平均 **2.02%**（英 2.01 / 中 1.63 / 德 1.77 / 法 2.80 / 意 1.89） | 隐私赛道单列 |
| **SLS with XLS-R** | 许可证未声明；数字来自 README 非论文 PDF | 2019 LA 训练 → 2021 DF **1.92%**、LA **2.87%**、ITW **7.46%** EER | 跨域对照，次于 XLSR-MamBo |

### 4.3 官方候选，本轮不够测

| 方案 | 状态 | 测试人员动作 |
|---|---|---|
| RawNet2/3、NN-Pytorch 子项目、EBM、MSLA-XLS-R | 仓库在，论文表或任务拆分未齐 | 可作环境/前端对照，不进精度表 |
| ArcFace_ADD | Apache-2.0，有参考路线 | 克隆赛道对照；指标未绑定，不与无参考模型混排 |
| Dessa Fake Voice Detection | README Acc 85% / F1 0.58，缺划分与生成器 | 不当前沿代表 |
| WavLM voice deepfake detection | 许可证空、归属未齐 | 不进主清单计数 |

## 5. AASIST Table 1：逐攻击 EER（闭集拆表用）

来源：[arXiv:2110.01200](https://arxiv.org/abs/2110.01200) Table 1。单位 EER（%）。括号为三次随机种子中的最佳。P1 = 池化 min t-DCF，P2 = 池化 EER（%）。

| 系统 | A07 | A08 | A09 | A10 | A11 | A12 | A13 | A14 | A15 | A16 | A17 | A18 | A19 | P1 | P2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| RawGAT-ST（AASIST 文复现） | 1.19 | 0.33 | 0.03 | 1.54 | 0.41 | 1.54 | 0.14 | 0.14 | 1.03 | 0.67 | 1.44 | 3.22 | 0.62 | 0.0443（0.0333） | 1.39（1.19） |
| AASIST | 0.80 | 0.44 | 0.00 | 1.06 | 0.31 | 0.91 | 0.1 | 0.14 | 0.65 | 0.72 | 1.52 | 3.40 | 0.62 | 0.0347（0.0275） | 1.13（0.83） |

**测试读法：**最差列目前是 **A18**（AASIST 3.40%、复现 RawGAT-ST 3.22%）。A09 对 AASIST 为 0.00，不能理解成“所有 TTS 都可检出”。在 ASVspoof 官方攻击清单写入 [`datasets/audio.md`](../datasets/audio.md) 之前，不要把这些列标成 TTS 或 VC。RawGAT-ST **原文**池化 EER 是 1.06%，与本表复现 1.39% 不是同一实验，精度表用原文。

## 6. 技术路线（选型背景，不是测试步骤）

| 路线 | 原理 | 边界 |
|---|---|---|
| 原始波形 | 少手工特征 | 采样率、信道、压缩敏感 |
| 频谱 / 图注意力 | 谱时局部关系 | 窗口与实现复杂度 |
| SSL / OOD | 跨攻击、跨年 | 阈值与域偏移 |
| 参考声纹 | 特定说话人克隆 | 必须有可信参考，单独成赛道 |

## 7. 排除项

**Open-AVFF**（[JoeLeelyf/OpenAVFF](https://github.com/JoeLeelyf/OpenAVFF)）自称为闭源 AVFF 的非官方实现，不进官方主清单。

## 8. 后续补强（不影响当前开测）

若以后有官方 VC 家族清单、说话人隔离的克隆协议，或带窗口/延迟的流式实验，再单列专项表。当前用 §2 的代理候选即可开展测试。

内部复测前不得对外宣称 SOTA。推荐工程顺序：闭集 AASIST + RawGAT-ST + Raw-PC-DARTS → 跨域 / 克隆代理 XLSR-MamBo → VC 按 Table 1 分列 → 实时自定窗口。
