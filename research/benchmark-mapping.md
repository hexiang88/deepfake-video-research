# 基准测试映射基线

该映射根据现有《基准测试方案》整理，后续以正式评测方案和试验数据为准。

| 维度 | 建议记录项 | 必须控制的条件 |
|---|---|---|
| 检测精度 | ROC-AUC、AP、Precision、Recall、F1；音视频补充 EER | 固定数据划分、类别比例、阈值选择和置信区间 |
| 鲁棒性 | 压缩/降质性能衰减、扰动攻击防御成功率 | 编码器、码率、分辨率/采样率、扰动预算和攻击类型 |
| 泛化 | 跨生成模型、跨地域/语言、少样本/零样本、OOD | 训练生成器与测试生成器严格隔离，并报告未知类别 |
| 效率 | 作为选型附录记录延迟、吞吐、部署依赖 | 硬件、批大小、精度、预处理和端到端边界一致 |
| 可解释性 | 热力图定位、IoU、置信度校准 | 只在有像素/帧级标注和统一校准协议时横向比较 |

## 与方案文档的阶段映射

- **2026 Q3**：视频、音频深伪检测。
- **2026 Q4**：图片、文本深伪检测。
- **2027 Q1**：实时音视频伪造检测。
- **2027 Q2**：数字人、虚拟场景检测。

## 2026 Q3 音视频短名单（互不合并）

短名单来自 2026-08-13 论文表核验，只用于分赛道设计，不是总榜。详见 [`reports/audio.md`](reports/audio.md) 与 [`reports/video.md`](reports/video.md)。

| 赛道 | 可用方案 | 绑定协议 | 测试判定 |
|---|---|---|---|
| 音频闭集 EER/t-DCF | AASIST、RawGAT-ST、Raw-PC-DARTS | ASVspoof 2019 LA eval | **可测** |
| 音频逐攻击 EER | AASIST Table 1 | A07–A19 分列 | **可测**。按攻击 ID 报 |
| VC（代理） | AASIST、RawGAT-ST | 同上，分列 | **可测（须备注）**。不要合成一个 VC 总分 |
| 音频跨数据集 EER | XLSR-MamBo；SLS（许可证待补） | 2019 LA → 21LA/21DF/ITW | **可测**（MamBo）/ 对照（SLS） |
| 克隆（代理） | XLSR-MamBo ITW | 2019 LA → In-the-Wild | **可测（须备注）**。ITW 不是克隆专项协议 |
| 实时（代理） | AASIST 等离线模型 | 测试方自定窗口 | **可测（须备注）**。不是官方实时指标 |
| 未知 codec | Codecfake W2V2-AASIST | C7 / CAVG | **可对照** |
| 混合音频 | MixFake | Foreground / Background 分列 | **可对照** |
| 隐私约束 | SafeEar | CVoiceFake 五语平均与 ASVspoof | **可对照** |
| 视频跨数据集 AUC | LipForensics、RealForensics、PwTF-DVD、VLAForge | FF++ 训练，标明 c23/视频级 | **可测** |
| 视频跨操纵 | RealForensics Table 1 | DF/FS/F2F/NT | **可测**。F2F/NT 同时供重演赛道引用 |
| 人脸重演（代理） | RealForensics F2F/NT；辅助 LipForensics | FF++ c23 | **可测（须备注）**。FF++ 重演类操纵 |
| 视频 in-domain 混合训练 | GenConViT | 作者混合训练同域 Acc/AUC | **可测另表** |
| 时间定位 | AuViRe、DiMoDif | LAV-DF / AV-Deepfake1M | **可测** |
| Talking Face DFD | AuViRe、DiMoDif | 按训练域×测试域 | **可测** |
| 唇音同步（代理） | AuViRe、DiMoDif | 同上 | **可测（须备注）**。DFD/TFL 代理，不是偏移误差 |

目标数据规模（方案文档）：文本 100 万条、图片 10 万张、音频 100 小时、视频 2 万个；公开子集分别为 1 万条、5000 张、10 小时和 1000 个。规模目标不等于已完成数据，实际发布时必须补充采集、授权、标注和哈希清单。数据集台账见 [`datasets/audio.md`](datasets/audio.md)、[`datasets/video.md`](datasets/video.md)。
