# 音频与视频候选仓库核验快照（2026-08-12）

本快照记录通过 GitHub API 与仓库 README 读取到的公开事实。Star、更新时间和仓库状态是 2026-08-12 检索时的快照，不代表永久值。搜索结果只用于发现候选，主报告仅纳入作者/机构官方实现；非官方实现单独列出。

## 视频

| 仓库 | 论文/角色 | Star 量级 | 仓库协议 | 关键 README 证据 | 主报告状态 |
|---|---|---:|---|---|---|
| [DariusAf/MesoNet](https://github.com/DariusAf/MesoNet) | MesoNet，WIFS 2018，Afchar/Nozick 等 | 约305 | Apache-2.0 | 面向 deepfake 与 Face2Face 的轻量 mesoscopic 网络；README 报告 deepfake >98%、Face2Face >95% | 官方经典基线，已纳入 |
| [ahaliassos/RealForensics](https://github.com/ahaliassos/RealForensics) | CVPR 2022，Leveraging Real Talking Faces via Self-Supervision | 约103 | MIT | 提供跨操纵、跨数据集和扰动 AUC；代码含 stage1 自监督与 stage2 检测 | 官方实现，已纳入 |
| [erprogs/GenConViT](https://github.com/erprogs/GenConViT) | GenConViT，Wodajo 等 | 约111 | MIT | ConvNeXt-Swin + AE/VAE；README 汇总 DFDC、FF++、DeepfakeTIMIT、Celeb-DF v2 的平均 Accuracy/AUC | 官方实现，已纳入；逐场景指标待补 |
| [JoeLeelyf/OpenAVFF](https://github.com/JoeLeelyf/OpenAVFF) | AVFF 的非官方 PyTorch 实现 | 约67 | 未声明 | README 明确写明 *unofficial implementation*，目标包括音视频特征融合 | 不进入官方主清单 |
| [ahaliassos/LipForensics](https://github.com/ahaliassos/LipForensics) | CVPR 2021，Lips Don’t Lie | 约143 | MIT | 嘴部时空表征；跨数据集 AUC：CelebDF-v2 82.4%、DFDC 73.5%、FaceShifter 97.1%、DeeperForensics 97.6% | 官方实现，已纳入 |
| [yinglinzheng/FTCN](https://github.com/yinglinzheng/FTCN) | ICCV 2021，Temporal Coherence | 约126 | 未声明 | 全时序卷积 + Temporal Transformer；README 明确训练代码未发布，提供推理代码/权重 | 官方推理实现，已纳入但不计完整开源 |
| [ZhendongWang6/AltFreezing](https://github.com/ZhendongWang6/AltFreezing) | CVPR 2023 Highlight | 约97 | MIT | 交替冻结空间/时间权重，并使用视频增广提升跨域泛化 | 官方实现，已纳入 |
| [BaopingLiu/TI2Net](https://github.com/BaopingLiu/TI2Net) | WACV 2023，Temporal Identity Inconsistency | 约11 | 未声明 | ArcFace 身份向量序列；README 提供预处理和训练入口，但未发布预训练模型 | 官方实现，已纳入 |
| [jongwook-Choi/StyleFlow](https://github.com/jongwook-Choi/StyleFlow) | CVPR 2024，Style Latent Flows | 约26 | MIT | StyleGRU、对比学习和 style attention；README 标注推理 Demo 待办 | 官方研究代码，已纳入但开源不完整 |
| [10Ring/FakeSTormer](https://github.com/10Ring/FakeSTormer) | ICCV 2025，Vulnerability-Aware Spatio-Temporal Learning | 约51 | API NOASSERTION | 多任务空间/时间脆弱区域建模；六数据集 c23/c0 跨域 AUC 表 | 官方实现，已纳入 |
| [rama0126/PwTF-DVD](https://github.com/rama0126/PwTF-DVD) | ICCV 2025，Pixel-wise Temporal Frequency | 约22 | MIT | 像素时间轴 1D Fourier + attention proposal + joint transformer；有推理脚本和权重 | 官方实现，已纳入 |
| [AshutoshAnshul/ics-av-deepfake](https://github.com/AshutoshAnshul/ics-av-deepfake) | ICCV 2025，Intra/Cross-modal Synchronization | 约9 | 未声明 | VoxCeleb2 自监督预训练、FakeAVCeleb 下游，输出音视频伪造与时间定位结果 | 官方实现，已纳入 |
| [mala-lab/VLAForge](https://github.com/mala-lab/VLAForge) | CVPR 2026，Vision-Language Semantics for DFD | 约17 | MIT | ForgePerceiver + identity-aware VLA score；README 提供 FF++、CDF、DFDC、DFD 和 DF40 数据配置及训练/测试入口 | 官方实现，已纳入；指标待补 |
| [Vill-Lab/2023-TIFS-ISTVT](https://github.com/Vill-Lab/2023-TIFS-ISTVT) | TIFS 2023，ISTVT | 约15 | 未声明 | README 仅为 “Coming soon”，无可核验代码/权重/指标 | 排除，不计入 |

## 音频

| 仓库 | 论文/角色 | Star 量级 | 仓库协议 | 关键 README 证据 | 主报告状态 |
|---|---|---:|---|---|---|
| [dessa-oss/fake-voice-detection](https://github.com/dessa-oss/fake-voice-detection) | Dessa Fake Voice Detection | 约384 | Apache-2.0 | ASVspoof 2019 LA；README 报告测试集 Accuracy 85%、F1 0.58；另测 RealTalk | 官方实现，已纳入；传统基线 |
| [LetterLiGo/SafeEar](https://github.com/LetterLiGo/SafeEar) | SafeEar，ACM CCS 2024，浙大/清华 | 约189 | API NOASSERTION；README 标注 CC BY 4.0 | 使用 neural audio codec 解耦语义/声学信息；覆盖 ASVspoof 2019/2021 与 CVoiceFake；最低 EER 2.02% 摘要 | 官方实现，已纳入；代码/数据许可需分开核验 |
| [xieyuankun/Codecfake](https://github.com/xieyuankun/Codecfake) | Codecfake，arXiv 2405.04880 | 约76 | 未声明 | 提供 Codecfake 数据、countermeasure 代码、预训练模型；含 codec unseen C7 与 ALM 测试 | 官方作者实现，已纳入；仓库协议未声明 |
| [QiShanZhang/SLSforASVspoof-2021-DF](https://github.com/QiShanZhang/SLSforASVspoof-2021-DF) | ACM MM 2024，XLS-R + SLS | 约72 | 未声明 | 训练 2019 LA，评估 2021 DF/LA 与 In-the-Wild；README 给出 EER 1.92%、2.87%、7.46% | 官方作者实现，已纳入；结果需回论文表 |
| [21Q017/MSLA-XLS-R](https://github.com/21Q017/MSLA-XLS-R) | Computer Speech & Language 2026，层级 SSL 表征融合 | 约1 | 未声明 | XLS-R 全层多尺度注意力与加权聚合；配置 2019 LA 训练、2021 LA/DF 和 In-the-Wild 评测，提供官方 EER/min t-DCF 入口但未列数值表 | 官方作者实现，已纳入；指标待论文核对 |
| [saki-ciallo/XLSR-MamBo](https://github.com/saki-ciallo/XLSR-MamBo) | ACL 2026 Findings，Hybrid Mamba-Attention | 约5 | MIT | 2019 LA 训练；21LA/21DF/In-the-Wild/DFADD 子集 EER 表，提供代码和预训练模型 | 官方完整实现，已纳入 |
| [saltfish233/MixFake](https://github.com/saltfish233/MixFake) | ICME 2026 Spotlight，真实世界混合音频基准 | 约4 | 未声明 | 已有 RawBoost、SSL 训练、模型、评测脚本和 mixed/fore/back score 文件；README 未给完整数值表 | 官方实现，已纳入；指标与数据定义待补 |
| [aiiu-lab/AVSSDeepfakeDet](https://github.com/aiiu-lab/AVSSDeepfakeDet) | ICASSP，Audio-Visual Mutual Learning | 约5 | 未声明 | 官方推理入口和 checkpoint；README 未列数据集与指标 | 官方推理实现，已纳入；证据待补 |
| [mever-team/auvire](https://github.com/mever-team/auvire) | WACV 2026，Audio-visual Speech Representation Reconstruction | 约9 | Apache-2.0 | LAV-DF、AV-Deepfake1M、真实世界和鲁棒性脚本；官方 JSON 给出 DFD AUC 与 TFL AP 的训练域/测试域结果，另有 Codabench 测试预测指标 | 官方完整实现，已纳入；结果口径已分层 |
| [1129ljc/MSAVR-TDL](https://github.com/1129ljc/MSAVR-TDL) | Multi-Scale Audio-Visual Reconstruction for Temporal Deepfake Localization | 0 | 未声明 | README 明确只开放模型架构，完整代码待论文接收后发布 | 排除，不计完整开源 |
| [LiuKe3068LikWix/From-Talking-to-Singing](https://github.com/LiuKe3068LikWix/From-Talking-to-Singing) | ICML 2026，Talking-to-Singing challenge | 0 | 未声明 | README 明确代码和数据集均 Coming soon | 排除，不计主清单 |

## 核验限制

- GitHub API 能确认仓库身份、描述、Star、归档状态和 API 返回的许可证字段；许可证字段为 `NOASSERTION` 或空值时，不视为已确认开源协议。
- README 中的性能摘要不是统一复现实验；必须保留数据集、划分、训练域、测试域和扰动条件，不能直接横向排序。
- “官方仓库”不等于“完整开源”：代码、推理脚本、预训练权重和数据集许可需分别记录。
