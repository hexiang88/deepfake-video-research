# 视频模态数据集与基准核验台账

本表只把已确认有官方入口或作者论文页的项目列为“入口已发现”。规模、许可、伪造类型和官方下载方式必须继续从官方发布页核对后才能进入最终数据集清单。**DeepfakeBench 与 FaceForensics 是框架/数据入口，不计入检测算法数量。**

| 数据集/基准 | 官方入口 | 角色 | 已记录字段 | 仍缺字段 | 当前状态 |
|---|---|---|---|---|---|
| FaceForensics++（FF++） | 论文 [arXiv:1901.08971](https://arxiv.org/abs/1901.08971)；[ondyari/FaceForensics](https://github.com/ondyari/FaceForensics) | 换脸/重演闭集训练与压缩协议 | DeepFakes / Face2Face / FaceSwap / NeuralTextures；AV-Deepfake1M 对照表记 1,000 真实 / 4,000 伪造；论文称 180 万+ 操纵图像与隐藏测试集；压缩 **c0 / c23 / c40** | 申请流程、完整许可、官方下载哈希、精确划分文件 | 论文与官方仓库已确认；许可待深核验 |
| Celeb-DF v2 | 论文 [arXiv:1909.12962](https://arxiv.org/abs/1909.12962) | 换脸跨数据集测试 | AV-Deepfake1M 对照表记 590 真实 / 5,639 伪造；LipForensics/RealForensics 以视频级 AUC 报告 | 官方下载页、许可、训练/测试官方划分 | 论文入口已发现 |
| DFDC | 论文 [arXiv:2006.07397](https://arxiv.org/abs/2006.07397) | 大规模换脸跨数据集/竞赛测试 | AV-Deepfake1M 对照表记 23,654 真实 / 104,500 伪造；预览集（DFDCP）与全量 DFDC 不得混用 | 许可、Kaggle/官方包、预览集与全量对应关系 | 论文入口已发现 |
| FaceShifter | 作为 FF++ 生态后续换脸器，被 LipForensics/RealForensics/FTCN/AltFreezing/PwTF 用作跨数据集测试 | 未见换脸器泛化 | 通常按 FF++ 划分取测试视频 | 独立许可与下载 | 仅作为测试条件出现 |
| DeeperForensics | 同上，跨数据集测试 | 高质量换脸泛化 | 视频级 AUC 已在多篇官方表中绑定 | 独立许可与下载 | 仅作为测试条件出现 |
| DeepFake Detection（DFD） | FakeSTormer / PwTF / VLAForge 跨数据集列 | Google/Jigsaw 相关换脸测试 | 与 DFDC 不是同一数据集 | 官方入口、许可、规模 | 入口待核 |
| WildDeepfake | 论文 [arXiv:2101.01456](https://arxiv.org/abs/2101.01456) | 野外换脸 | FakeSTormer 以 DFW 列报告 c23/c0 AUC | 许可与下载 | 论文入口已发现 |
| KoDF | PwTF Table 3；AV-Deepfake1M 对照表 | 跨身份/跨种族泛化 | 对照表记 403 主体、62,166 真实 / 175,776 伪造；PwTF 报作者复现 AUC 91.3（FF++ 训练） | 官方许可、下载 | 论文引用已见；发布页待核 |
| DF40 | FakeSTormer / VLAForge 配置与论文提及 | 多生成器换脸/扩散伪造 | 含 DiffSwap 等子集 | 官方入口、许可、生成器清单 | 入口待核 |
| FakeAVCeleb | 论文 [arXiv:2108.05080](https://arxiv.org/abs/2108.05080) | Talking Face / 音视频联合、唇同步克隆语音 | 含视频及对应合成音频细粒度标签；多族裔英语名人；AV-Deepfake1M 对照表记约 570 真实 / 25,000+ 伪造 | 官方许可、精确划分、申请表 | 论文入口已发现；许可待核。导师盘 `MyDataSets/Fake/fake_fakeavceleb` 仅 **candidate**，须核音频与官方划分后才能进 DiMoDif；AuViRe 无 FakeAVCeleb 行 |
| LAV-DF | 被 [AV-Deepfake1M Table 1](https://arxiv.org/abs/2311.15308) 引用为 Cai et al. 2022；AuViRe 官方 JSON | 局部音视频伪造与时间定位的**前代对照集**（本机不作为 Talking Face 主报） | 153 主体、真实 36,431、伪造 99,873、合计 136,304；内容驱动 RE/TTS；改稿仅为规则替换 | 独立论文页、许可、偏移标注协议 | 规模来自对照表；原文待单独打开 |
| AV-Deepfake1M | 论文 [arXiv:2311.15308](https://arxiv.org/abs/2311.15308)；[ControlNet/AV-Deepfake1M](https://github.com/ControlNet/AV-Deepfake1M) | 大规模音视频伪造与时间定位 / Codabench；**本机 Talking Face 主测试域**（评 val，非 hidden test） | 2,068 主体、真实 286,721、伪造 860,039、合计 1,146,760；内容驱动 RE/TTS；LLM 改稿含替换/插入/删除 | 许可、官方下载哈希、标注粒度 | 论文与代码入口已确认；许可待核。相对 LAV-DF 为升级集，不是另一条赛道 |
| DeepfakeBench | [SCLBD/DeepfakeBench](https://github.com/SCLBD/DeepfakeBench) | 统一评测框架，不是检测器 | 可编排多模型与多数据集 | 框架 LICENSE `NOASSERTION`；内置模型需逐个登记 | 官方框架入口已确认 |

## 基准测试需要的视频数据分层

1. **换脸闭集层**：FF++ 四类操纵，必须标明 c0/c23/c40。
2. **跨数据集层**：FF++ 训练 → Celeb-DF / DFDC / FaceShifter / DeeperForensics / DFD / WildDeepfake。
3. **重演层**：FF++ 的 Face2Face、NeuralTextures 可作辅助，不能替代专门音频/姿态驱动数据。
4. **Talking Face / 定位层**：FakeAVCeleb、LAV-DF、AV-Deepfake1M；视频级 AUC 与 TFL AP 分表。
5. **鲁棒性层**：H.264 码率、模糊、噪声、丢帧；参数必须写明，不得用原始视频结果代表退化。

## 许可与可追溯要求

- 人脸视频默认敏感：记录申请制、禁止再分发和研究用途限制。
- FaceForensics 申请下载不等于可公开再发布基准子集。
- 数据集、评测框架与检测模型三者分开计数。
