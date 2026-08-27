# 音视频论文实验表核验快照（2026-08-13）

本批次未访问 GitHub。来源为 arXiv 官方摘要 API 与 `arxiv.org/pdf/{id}.pdf` 原文。直连 arXiv HTTP 200；检索后期出现 429 后停止继续搜索。未下载权重或数据集。PDF 文本由本地 PyMuPDF 抽取；表格数字仅在原文能定位到表号、任务和条件时转录。

## 请求记录

- arXiv export API：已知 ID 批量查询 1 次 HTTP 200；标题检索约 30 次，末次 429 后停止。
- arXiv PDF：19 篇成功；VLAForge `2603.24454` 首次传输失败后本地仍得到 14 页 PDF 并完成抽取，不另作成功下载声明。
- GitHub 请求：0。

## 已确认论文与可绑定指标

指标格式：`指标 = 数值；任务/数据集/划分；伪造类型或生成器；压缩/扰动/跨域条件；来源位置。`

### 音频

#### AASIST — arXiv:2110.01200

- 标题：*AASIST: Audio Anti-Spoofing using Integrated Spectro-Temporal Graph Attention Networks*
- 作者：Jee-weon Jung, Hee-Soo Heo, Hemlata Tak 等
- 官方代码对应：clovaai/aasist（既有 MIT 快照）
- 绑定：`min t-DCF = 0.0347（最佳种子 0.0275），EER = 1.13%（最佳种子 0.83%）；ASVspoof 2019 LA evaluation 池化结果；攻击 A07–A19；无额外压缩声明；论文 Table 2 / §4.3，括号为三次随机种子中的最佳。`
- Table 1 逐攻击 EER（%）已转录。AASIST：A07 0.80、A08 0.44、A09 0.00、A10 1.06、A11 0.31、A12 0.91、A13 0.1、A14 0.14、A15 0.65、A16 0.72、A17 1.52、A18 3.40、A19 0.62；P1 0.0347（0.0275）、P2 1.13（0.83）。同表 RawGAT-ST 为 AASIST 文三种子复现，池化 P2 1.39（1.19），**不得**替代原文 Table 4 的 1.06%。在官方攻击→生成器清单写入数据集台账前，不得把 13 列汇总为 TTS 或 VC 家族分。
- 升级建议：**已核验**（官方论文+MIT 完整代码+池化指标已绑定）。不得外推为 TTS/VC/实时专项。

#### RawGAT-ST — arXiv:2107.12710v2

- 标题：*End-to-End Spectro-Temporal Graph Attention Networks for Speaker Verification Anti-Spoofing and Speech Deepfake Detection*
- 作者：Hemlata Tak 等
- 官方代码对应：eurecom-asp/RawGAT-ST-antispoofing（既有 MIT 快照）
- 绑定：`min t-DCF = 0.0335，EER = 1.06%；ASVspoof 2019 LA evaluation 池化；RawGAT-ST-mul 配置；相对 RawNet2 基线 t-DCF 0.1547 / EER 5.54%；论文 Table 4 与 §6.1。`
- 升级建议：**已核验**。不得外推为 2021 DF 或实时结果。

#### Raw-PC-DARTS — arXiv:2107.12212v2

- 标题：*Raw Differentiable Architecture Search for Speech Deepfake and Spoofing Detection*
- 作者：Wanying Ge, Jose Patino, Massimiliano Todisco, Nicholas Evans
- 官方代码：eurecom-asp/raw-pc-darts-anti-spoofing，MIT
- 绑定：`min t-DCF = 0.0517，EER = 1.77%；ASVspoof 2019 LA evaluation；Mel-Fixed sinc 前端；论文 Table 2。` `最差攻击 A08 EER = 4.96%；同协议；论文 Table 3。` 输入固定 4 秒、16 kHz。
- 升级建议：**已核验**。不得外推为 VC/TTS 专项或流式延迟。

#### SafeEar — arXiv:2409.09272

- 标题：*SafeEar: Content Privacy-Preserving Audio Deepfake Detection*
- 作者：Xinfeng Li 等（浙大/清华，ACM CCS 2024）
- 仓库许可证仍为 API `NOASSERTION` / README CC BY 4.0，代码与数据许可未拆清
- 绑定：`EER = 3.10%，t-DCF = 0.149；ASVspoof 2019；Table 2。` `EER = 7.22%，t-DCF = 0.336；ASVspoof 2021；Table 2。` `EER = 2.02%（英/中/德/法/意平均）；CVoiceFake；Table 3。该 2.02% 是五语平均，不是“四基准最低值”。`
- 升级建议：指标可进协议表，状态保持 **部分核验**（许可证冲突）。

#### Codecfake — arXiv:2405.04880v3

- 标题：*The Codecfake Dataset and Countermeasures for the Universally Detection of Deepfake Audio*
- 作者：Yuankun Xie 等；官方仓库 xieyuankun/Codecfake；数据集 CC BY-NC-ND 4.0，仓库 SPDX 未声明
- 数据规模（论文）：1,058,216 条；真实+七种 codec（F01–F06 训练可见，C7 为未见 codec）；来源 VCTK（EN）与 AISHELL3（CN）
- 绑定（Table VI，Codecfake 训练集）：`W2V2-AASIST：19LA EER 3.806%，ITW 9.606%，C7 unseen 0.884%，C1–C7 CAVG 0.177%，AVG 1.628%。`
- 绑定（Table X，19LA+Codecfake 共训 + CSAM）：`W2V2-AASIST(CSAM)：19LA 0.313%，ITW 4.689%，C7 0.431%，CAVG 0.077%，AVG 0.616%。`
- Table V 显示仅用 19LA 训练时 CAVG 约 41.6%，不能与 Table VI 合并。
- 升级建议：未知 codec 赛道可引用 Table VI/X；仓库许可证未声明，保持 **部分核验**。

#### XLSR-MamBo — arXiv:2601.02944v3

- 标题：*XLSR-MamBo: Scaling the Hybrid Mamba-Attention Backbone for Audio Deepfake Detection*，ACL 2026 Findings
- 作者：Kwok-Ho Ng, Tingting Song, Yongdong Wu, Zhihua Xia；仓库 MIT
- DFADD 子集定义（论文 §5.1）：**D1–D3 为不同扩散生成器，F1–F2 为不同 flow-matching 生成器**。此前 README 未解释的标签以此为准。
- 训练域：ASVspoof 2019 LA。评测：21LA / 21DF / ITW / DFADD。仓库 README 的逐模型 EER 表仍可与论文 Table 1–2 对照使用；论文另报 Best/Avg checkpoint。
- 升级建议：**已核验**。D1–D3/F1–F2 不得写成 ASVspoof 攻击类型。

#### MixFake — arXiv:2605.23201v1

- 标题：*MixFake: Benchmarking and Enhancing Audio Deepfake Detection in Diverse Real-world Mixed Audio*，ICME 2026 Spotlight
- 作者：Qingcao Li 等；仓库 saltfish233/MixFake，SPDX 未声明
- 绑定：`Foreground EER = 0.95%，Background EER = 12.40%；MixFake 子任务；Table II。` 前景/背景标签不可合并。
- 绑定：`ITW EER = 6.24%；ASVspoof 2019 LA 训练 → In-the-Wild；Table III。`
- 绑定：`混合源 SNR 15 dB EER = 0.36%，−5 dB EER = 3.10%；§D。`
- 升级建议：混合音频赛道可引用；许可证未声明，保持 **部分核验**。

### 视频

#### MesoNet — arXiv:1809.00888

- 标题：*MesoNet: a Compact Facial Video Forgery Detection Network*，WIFS 2018
- 作者：Darius Afchar, Vincent Nozick, Junichi Yamagishi, Isao Echizen；Apache-2.0
- 绑定：论文结论为作者自建 Deepfake 集平均检测率约 98%、Face2Face（压缩 qp=23）约 95%；Table 3/4/6 与作者数据划分，**不是 FF++ 官方划分**。
- 升级建议：历史基线线索，保持 **部分核验**，不与现代跨数据集 AUC 合并。

#### LipForensics — arXiv:2012.07657v3

- 标题：*Lips Don't Lie: A Generalisable and Robust Approach to Face Forgery Detection*，CVPR 2021
- 作者：Alexandros Haliassos 等；MIT
- 绑定：`视频级 AUC = CDF-v2 82.4%，DFDC 73.5%，FaceShifter HQ 97.1%，DeeperForensics 97.6%，平均 87.7%；训练 FF++；论文 Table 2。`
- 鲁棒性协议：未压缩 FF++ 训练，测试 saturation/contrast/block-wise/Gaussian noise/blur/pixelation/H.264，五档强度；图示结果，本快照不转录曲线点。
- 升级建议：**已核验**。

#### RealForensics — arXiv:2201.07131v3

- 标题：*Leveraging Real Talking Faces via Self-Supervision for Robust Forgery Detection*，CVPR 2022
- 作者：Alexandros Haliassos 等；MIT
- 绑定（Table 1，FF++ leave-one-manipulation，c23）：`AUC Deepfakes 100.0，FaceSwap 97.1，Face2Face 99.7，NeuralTextures 99.2。`
- 绑定（Table 2，FF++ 训练跨数据集）：`CDF 86.9，DFDC 75.9，FaceShifter 99.7，DeeperForensics 99.3，平均 90.5。`
- 升级建议：**已核验**。Face2Face/NeuralTextures 可作重演辅助覆盖，不是专门重演检测器。

#### FTCN — arXiv:2108.06693

- 标题：*Exploring Temporal Coherence for More General Video Face Forgery Detection*，ICCV 2021
- 作者：Yinglin Zheng 等
- 绑定（Table 4，FF++ HQ 训练）：`视频级 AUC CDF 86.9，DFDC 74.0，FaceShifter 98.8，DeeperForensics 98.8，平均 89.6。`
- 仓库主要为推理代码，训练代码未发布。
- 升级建议：指标可引用，保持 **部分核验**（开放范围不足）。

#### AltFreezing — arXiv:2307.08317

- 标题：*AltFreezing for More General Video Face Forgery Detection*，CVPR 2023 Highlight
- 作者：Zhendong Wang 等；MIT
- 绑定（Table 1，FF++ 训练）：`视频级 AUC CDF 89.5，DFD 98.5，FaceShifter 99.4，DeeperForensics 99.3，平均 96.7。`
- 实现细节：3D ResNet50，训练随机连续 32 帧。仓库以推理/权重为主。
- 升级建议：指标可引用，保持 **部分核验**（训练完整性仍待仓库核对）。

#### FakeSTormer — arXiv:2501.01184v3

- 标题：*Vulnerability-Aware Spatio-Temporal Learning for Generalizable Deepfake Video Detection*，ICCV 2025
- 作者：Dat Nguyen 等；仓库 API `NOASSERTION`
- 绑定（Table 1，FF++ c23 训练，T=4）：`视频级 AUC CDF2 92.4，DFD 98.5，DFDCP 90.0，DFDC 74.6，WildDeepfake 74.2，DiffSwap 96.9。` 与既有 README c23 表一致。
- c0 训练的跨数据集表存在（README 96.5 等），本快照以 c23 行为准。
- 升级建议：指标已绑定，许可证未声明，保持 **部分核验**。

#### PwTF-DVD — arXiv:2507.02398v2

- 标题：*Beyond Spatial Frequency: Pixel-wise Temporal Frequency-based Deepfake Video Detection*，ICCV 2025
- 作者：Taehoon Kim 等；MIT
- 绑定（Table 2，FF++ 训练，视频级 AUC）：`CDF 89.7，DFDC 75.2，FaceShifter 99.3，DeeperForensics 99.4，DFD 97.3，平均 92.2。`
- 另报 KoDF AUC 91.3（Table 3，作者复现对照）。
- 升级建议：**已核验**。

#### VLAForge — arXiv:2603.24454v1

- 标题：*Unleashing Vision-Language Semantics for Deepfake Video Detection*，CVPR 2026
- 作者：Jiawen Zhu 等；mala-lab/VLAForge，MIT
- 协议：FF++ c23 训练；视频级分数为帧级平均
- 绑定（Table 1）：`帧级 AUROC CDF-v1 93.9，CDF-v2 91.2，DFDC 87.0，DFD 93.6。` `视频级 AUROC CDF-v2 96.8，DFDC 89.6，DFD 97.2。`
- Table 2 另含 VQGAN/StyleGAN/SiT/DiT/PixArt 全脸生成，与换脸跨数据集表分开。
- 升级建议：**已核验**。帧级与视频级不得混排。

#### StyleFlow — arXiv:2403.06592v3

- 标题：*Exploiting Style Latent Flows for Generalizing Deepfake Video Detection*，CVPR 2024
- 作者：Jongwook Choi 等；MIT；README 仍标推理 Demo 待办
- 论文有跨数据集/跨操纵 AUC 表；因官方推理发布不完整，不把论文表升为可复现完整方案。
- 升级建议：保持 **部分核验**。

#### GenConViT — arXiv:2307.07036v2

- 标题：*GenConViT: Deepfake Video Detection Using Generative Convolutional Vision Transformer*
- 作者：Deressa Wodajo Deressa 等；MIT
- 协议：多数据集混合训练并同域评测；作者明确 DFDC/FF++ 测试子集通常不共享，**不得**与 LipForensics 等 FF++→跨数据集 AUC 合并。
- 绑定（Table IV Acc %）：`DFDC 98.50，FF++ 97.00，TIMIT 98.28，Celeb-DF v2 90.94。`
- 绑定（Table V AUC %）：`DFDC 99.9，FF++ 99.6，Celeb-DF v2 98.1。`
- 绑定（Table VI F1 %）：`DFDC 99.1，FF++ 95.5，TIMIT 98.3，Celeb-DF v2 91.6。`
- 论文汇总平均 Acc 95.8%、AUC 99.3% **不用于排名**。
- Table X OOD：Celeb-DF v2 完全 held-out 时 overall Acc 55.67%、fake Acc 11.56%。
- 升级建议：**已核验**（MIT + 完整训练/测试 + 逐数据集表）。仅进入 in-domain 另表。

#### AuViRe — arXiv:2511.18993v1

- 标题：*AuViRe: Audio-visual Speech Representation Reconstruction for Deepfake Temporal Localization*，WACV 2026
- 作者：Christos Koutlis 等；Apache-2.0
- 论文 Table 1 给出 LAV-DF 时间定位 AP；既有仓库 JSON 的 DFD AUC / TFL AP 仍按文件口径使用，不与论文相对表述合并。
- 升级建议：**已核验**（论文+官方 JSON 分表）。闭集、跨域、Codabench 继续分表。

#### DiMoDif — arXiv:2411.10193v2

- 标题：*DiMoDif: Discourse Modality-information Differentiation for Audio-visual Deepfake Detection and Localization*
- 作者：Christos Koutlis, Symeon Papadopoulos（MEVER / CERTH）；Apache-2.0；[mever-team/dimodif](https://github.com/mever-team/dimodif)
- 绑定 DFD in-dataset：`FakeAVCeleb ACC 99.4 / AUC 99.7；Table 3。` `LAV-DF AUC 99.84；Table 4。` `AV-Deepfake1M AUC 96.3，ACC 96.3（验证集）；Table 5。`
- 绑定跨操纵 FakeAVCeleb Table 6：`AVG-FV AUC 99.9；RVFA（真视频假音频）AUC 51.6。`
- 绑定 TFL：`LAV-DF AP@0.5 95.5，AP@0.75 87.9，AP@0.95 20.6；Table 7。` `AV-Deepfake1M AP@0.5 86.93，AP@0.75 75.95，AP@0.9 28.72，AP@0.95 5.43；Table 8。`
- 绑定跨数据集 DFD Table 9：训练 FakeAVCeleb → 测试 AVD1M 验证集 AUC 54.00；对角闭集均 >99。
- 升级建议：**已核验**。相对提升摘要（+30.5 AUC）不得替代上表绝对值。DFD 与 TFL 分表。

#### Next-Frame Feature Prediction（Ashutosh Anshul）— arXiv:2511.10212

- 同作者相关音视频定位论文，**不是 ICS-AV ICCV 2025 的替代实现**。不计入 ICS-AV，不进入视频主清单，除非后续确认与 ICS-AV 仓库的官方对应关系。

## 本批次未取得原文的已有候选

SLS with XLS-R（ACM MM 2024）、MSLA-XLS-R、EBM、ArcFace_ADD、AVSSDeepfakeDet、ICS-AV、TI2Net：arXiv 检索未命中或 429 前未完成。沿用既有仓库快照，不降级也不升级。

## 对覆盖状态的影响

本批次把若干方案的论文表补进硬字段，可使 AASIST、RawGAT-ST、Raw-PC-DARTS、XLSR-MamBo、LipForensics、RealForensics、PwTF-DVD、VLAForge、AuViRe 在“官方实现 + 许可证 + 绑定指标”上达到 **已核验**。核心方向仍不足 6 个完全核验方案，覆盖矩阵保持 `深核验`，但 Q3 分赛道短名单可以扩大。

后续同日从本地 PDF 补转录 AASIST Table 1、DiMoDif Table 3–9、GenConViT Table IV–VI。DiMoDif 与 GenConViT 升为已核验。稀缺方向按不可补足原因改为 `完成（稀缺）`，见 [`audio-video-scarce-directions-2026-08-13.md`](audio-video-scarce-directions-2026-08-13.md) 补记。
