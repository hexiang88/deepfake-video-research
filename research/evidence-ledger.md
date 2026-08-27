# 证据台账

## 状态定义

- `待核验`：尚未完成一手来源核验。
- `已核验`：官方论文/项目/仓库和关键字段已交叉核对。
- `部分核验`：方案真实存在，但仓库类型、协议、指标或实验条件仍缺字段。
- `排除`：无官方原始实现、来源不可靠或无法复现实验条件。

## 单方案必填字段

| 字段 | 要求 |
|---|---|
| 方案与版本 | 模型全称、论文年份、代码版本/提交日期 |
| 官方来源 | 论文 DOI/arXiv、作者/机构主页、官方仓库原始链接 |
| 开源类型 | 完整开源 / 仅推理开源 / 仅权重开源 |
| 协议 | 仓库 LICENSE 原文；缺失时标记“未声明” |
| 维护度 | GitHub Star 量级、最近提交、Issue/Release 状态；记录核验日期 |
| 方法 | 核心原理、输入、输出、训练/推理依赖 |
| 指标 | 指标值 + 数据集 + 划分 + 生成方式 + 压缩/扰动条件 |
| 边界 | 优势、失败模式、跨生成器/跨域/开放集表现 |
| 复现 | 权重、环境、推理脚本、数据获取是否可用 |

## 性能记录规则

禁止记录脱离实验条件的“最高 AUC/F1/准确率”。每个数字都必须写成：

`指标 = 数值；任务/数据集/划分；伪造类型或生成器；压缩、扰动、跨域或零样本条件；来源位置。`

若不同论文使用不同划分、后处理、采样比例或评测协议，不合并为单一排名，并在备注中解释差异。

## 音视频基准准入统计口径

本轮报告重构将候选分为三类：

- `已核验`：音频为 AASIST、RawGAT-ST、Raw-PC-DARTS、XLSR-MamBo；视频为 LipForensics、RealForensics、PwTF-DVD、VLAForge、GenConViT、AuViRe、DiMoDif。数值可进入对应赛道数据表，必须保留训练域、测试域、伪造类型、编码/扰动和输出粒度。GenConViT 只进 in-domain 混合训练表，不与 FF++→跨数据集 AUC 合并。
- `已绑定指标、许可证或开放范围待补`：SLS with XLS-R、SafeEar、Codecfake、MixFake、FakeSTormer、FTCN、AltFreezing。可进对照表，不计入完全核验数量。
- `官方候选、部分核验或排除`：作者归属、协议、开放范围或实现状态仍有缺口。

同一方案可出现在多个细分方向索引，但准入统计按方案而非出现次数计数。跨模态模型的 DFD/TFL、视频分类和同步定位指标必须分表；音频的 ASVspoof、DFADD、混合音频和实时流式条件也必须分表。覆盖矩阵以当前文件与 [`coverage-matrix.md`](coverage-matrix.md) 为准。

## 音频/视频新增核验记录

以下记录对应 2026-08-12 通过 GitHub API、官方 README 和仓库结果文件完成的快照；“部分核验”表示方案真实且有官方代码，但仍缺论文表、协议或许可证字段，不能据此宣布方向完成。

2026-08-13 的本地收敛复核见 [`source-snapshots/local-audio-video-audit-2026-08-13.md`](source-snapshots/local-audio-video-audit-2026-08-13.md)。该复核没有新增 GitHub 请求，只整理既有快照中已经绑定训练域/测试域、任务和结果口径的音频与视频指标；未改变任何方案或方向状态。

2026-08-13 的代理候选发现见 [`source-snapshots/audio-video-gap-discovery-2026-08-13.md`](source-snapshots/audio-video-gap-discovery-2026-08-13.md)。该批次仅完成官方 API 搜索，未读取候选仓库详情；搜索候选不计入官方原始实现，也未改变任何方案或方向状态。

2026-08-13 的候选核验见 [`source-snapshots/audio-video-gap-verification-2026-08-13.md`](source-snapshots/audio-video-gap-verification-2026-08-13.md)。`Deep_Fake_Voice_Recognition` 仅能确认 RVC/DEEP-VOICE 项目入口和训练/评测脚本，`Multimodal-Lip-Sync-Deepfake-Detection-System` 仅能确认音视频系统描述及未绑定的 README 自报数字；两者均保持待核验，不计入官方原始方案或横向指标。

2026-08-13 的定向搜索见 [`source-snapshots/audio-video-gap-search-2026-08-13.md`](source-snapshots/audio-video-gap-search-2026-08-13.md)。搜索没有取得新的作者/机构官方原始实现或绑定指标；`Khushi-2106/LipSync-Deepfake-Detection` 仅保留为待核验候选，不计入 LipFD 官方实现。

认证 API 批次的详细记录见 [`source-snapshots/authenticated-audio-video-2026-08-13.md`](source-snapshots/authenticated-audio-video-2026-08-13.md)。本批次新增 Raw-PC-DARTS、WavLM voice deepfake detection 和 DiMoDif 三条候选记录；其中 Raw-PC-DARTS 与 DiMoDif 已确认论文/作者仓库对应，WavLM 候选仍缺许可证和官方归属证据。三者均保持 `部分核验`，没有改变任何方向的完成状态。

替代来源批次见 [`source-snapshots/alternative-audio-video-sources-2026-08-13.md`](source-snapshots/alternative-audio-video-sources-2026-08-13.md)。该批次未访问 GitHub；arXiv 仅补强 Raw-PC-DARTS 与 DiMoDif 的论文/作者可追溯性，Zenodo 和 Hugging Face 搜索结果未确认官方归属，OpenReview/ Semantic Scholar 的访问异常不被解释为论文或实现不存在。该批次没有新增完全核验方案。

2026-08-13 论文表核验见 [`source-snapshots/audio-video-paper-tables-2026-08-13.md`](source-snapshots/audio-video-paper-tables-2026-08-13.md)。同日从本地 PDF 补转录 AASIST Table 1、DiMoDif Table 3–9、GenConViT Table IV–VI；据此将 DiMoDif、GenConViT 升为 `已核验`。稀缺方向完成判定见 [`source-snapshots/audio-video-scarce-directions-2026-08-13.md`](source-snapshots/audio-video-scarce-directions-2026-08-13.md)。测试入准见 [`reports/audio.md`](reports/audio.md) 与 [`reports/video.md`](reports/video.md)。

| 方案 | 官方来源与开源边界 | 绑定条件/指标 | 状态 |
|---|---|---|---|
| AASIST | clovaai/aasist，MIT；[arXiv:2110.01200](https://arxiv.org/abs/2110.01200) | 2019 LA eval 池化 EER 1.13%（最佳 0.83%）、min t-DCF 0.0347（最佳 0.0275）；Table 1 逐攻击 EER 已转录，最差列 A18=3.40% | 已核验 |
| RawGAT-ST | eurecom-asp/RawGAT-ST-antispoofing，MIT；[arXiv:2107.12710](https://arxiv.org/abs/2107.12710) | 2019 LA eval 池化 EER 1.06%、min t-DCF 0.0335（mul） | 已核验 |
| Raw-PC-DARTS | EURECOM 官方仓库，MIT；[arXiv:2107.12212](https://arxiv.org/abs/2107.12212) | 2019 LA eval Mel-Fixed min t-DCF 0.0517、EER 1.77%；最差攻击 A08 4.96% | 已核验 |
| XLSR-MamBo | saki-ciallo/XLSR-MamBo，MIT；[arXiv:2601.02944](https://arxiv.org/abs/2601.02944) | 2019 LA 训练；21LA/21DF/ITW/DFADD；D1–D3 扩散、F1–F2 flow-matching | 已核验 |
| LipForensics | ahaliassos/LipForensics，MIT；[arXiv:2012.07657](https://arxiv.org/abs/2012.07657) | FF++ 训练；CDF 82.4 / DFDC 73.5 / FSh 97.1 / DFo 97.6 | 已核验 |
| RealForensics | ahaliassos/RealForensics，MIT；[arXiv:2201.07131](https://arxiv.org/abs/2201.07131) | 跨操纵与跨数据集视频级 AUC，见论文 Table 1/2 | 已核验 |
| PwTF-DVD | rama0126/PwTF-DVD，MIT；[arXiv:2507.02398](https://arxiv.org/abs/2507.02398) | FF++ 训练；CDF 89.7 / DFDC 75.2 / FSh 99.3 / DFo 99.4 / DFD 97.3 | 已核验 |
| VLAForge | mala-lab/VLAForge，MIT；[arXiv:2603.24454](https://arxiv.org/abs/2603.24454) | FF++ c23；视频级 CDF-v2 96.8 / DFDC 89.6 / DFD 97.2 | 已核验 |
| AuViRe | mever-team/auvire，Apache-2.0；[arXiv:2511.18993](https://arxiv.org/abs/2511.18993) | LAV-DF / AV-Deepfake1M DFD 与 TFL，JSON 分表 | 已核验 |
| GenConViT | erprogs/GenConViT，MIT；[arXiv:2307.07036](https://arxiv.org/abs/2307.07036) | 混合训练同域：DFDC Acc 98.50 / AUC 99.9；FF++ Acc 97.00 / AUC 99.6；Celeb-DF v2 Acc 90.94 / AUC 98.1。不得与跨数据集表合并 | 已核验 |
| WavLM voice deepfake detection | 仓库提供 notebook；许可证为空，作者归属待补 | 2019 LA train/dev，2021 LA eval；dev EER≈0.11%，2021 LA EER≈6.8% | 部分核验 |
| DiMoDif | MEVER 作者仓库，Apache-2.0；[arXiv:2411.10193](https://arxiv.org/abs/2411.10193) | Table 3 FakeAVCeleb AUC 99.7；Table 4 LAV-DF AUC 99.84；Table 5 AVD1M AUC 96.3；Table 8 AVD1M TFL AP@0.5 86.93 / AP@0.75 75.95；Table 6 RVFA AUC 51.6 | 已核验 |

| 方案 | 官方仓库 | 开源类型 | 协议 | 指标/实验条件 | 状态 |
|---|---|---|---|---|---|
| SLS with XLS-R | [QiShanZhang/SLSforASVspoof-2021-DF](https://github.com/QiShanZhang/SLSforASVspoof-2021-DF) | 训练/测试代码与权重 | 未声明 | 2019 LA 训练；2021 DF/LA EER 1.92%/2.87%，In-the-Wild 7.46% | 部分核验 |
| SafeEar | [LetterLiGo/SafeEar](https://github.com/LetterLiGo/SafeEar) | 完整训练/测试代码 | API `NOASSERTION`；README 标注 CC BY 4.0 | Table 2：2019 EER 3.10%、2021 EER 7.22%；Table 3 CVoiceFake 平均 2.02% | 部分核验 |
| Codecfake | [xieyuankun/Codecfake](https://github.com/xieyuankun/Codecfake) | 训练/评测代码与权重 | 仓库未声明；数据集 CC BY-NC-ND 4.0 | Table VI W2V2-AASIST C7 0.884%、CAVG 0.177% | 部分核验 |
| MixFake | [saltfish233/MixFake](https://github.com/saltfish233/MixFake) | 训练/评测代码、模型和 score 文件 | 未声明 | Table II Foreground 0.95% / Background 12.40%；Table III ITW 6.24% | 部分核验 |
| FakeSTormer | [10Ring/FakeSTormer](https://github.com/10Ring/FakeSTormer) | 官方训练/推理代码与权重 | API `NOASSERTION` | FF++ c23 六数据集视频级 AUC，与论文 Table 1 一致 | 部分核验 |
| FTCN | [yinglinzheng/FTCN](https://github.com/yinglinzheng/FTCN) | 主要为推理代码与权重 | 未声明 | Table 4：CDF 86.9 / DFDC 74.0 / FSh 98.8 / DFo 98.8 | 部分核验 |
| AltFreezing | [ZhendongWang6/AltFreezing](https://github.com/ZhendongWang6/AltFreezing) | 推理代码与权重 | MIT | Table 1：CDF 89.5 / DFD 98.5 / FSh 99.4 / DFo 99.3 | 部分核验 |
| MSLA-XLS-R | [21Q017/MSLA-XLS-R](https://github.com/21Q017/MSLA-XLS-R) | 完整训练/评测代码 | 未声明 | 2019 LA 训练；2021 LA/DF、In-the-Wild、DFADD；官方 EER/min t-DCF 入口，数值待论文 | 部分核验 |
| MesoNet | [DariusAf/MesoNet](https://github.com/DariusAf/MesoNet) | 代码与权重 | Apache-2.0 | 作者数据上 deepfake >98%、Face2Face >95%；不与现代跨域 AUC 合并 | 部分核验 |
| TI2Net | [BaopingLiu/TI2Net](https://github.com/BaopingLiu/TI2Net) | 训练/预处理代码 | 未声明 | ArcFace 身份向量序列；未发布预训练模型 | 部分核验 |
| StyleFlow | [jongwook-Choi/StyleFlow](https://github.com/jongwook-Choi/StyleFlow) | 研究代码，推理未完整 | MIT | Style latent temporal changes；README 未列指标表 | 部分核验 |
| ICS-AV | [AshutoshAnshul/ics-av-deepfake](https://github.com/AshutoshAnshul/ics-av-deepfake) | 官方训练/评测代码与 checkpoint | 未声明 | VoxCeleb2 自监督、FakeAVCeleb 下游；同步/时间定位指标待补 | 部分核验 |
