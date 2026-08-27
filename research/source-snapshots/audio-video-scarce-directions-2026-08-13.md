# 音视频稀缺方向定向检索快照（2026-08-13）

本批次在论文表核验之后，按替代来源策略检索 VC、语音克隆、实时音频、人脸重演、Talking Face 和唇音同步的**新官方实现**。未访问 GitHub。arXiv export API 在本阶段返回 429 后停止继续 API 搜索；HTML `/search` 返回 403。随后仅用 `arxiv.org/abs/{id}` 逐条核验已知候选 ID。

## 请求记录

- arXiv API `id_list`：1 次 HTTP 429，立即停止 API。
- arXiv `/search`：连接关闭或 HTTP 403，不作“论文不存在”解释。
- arXiv abs 页（WebFetch / HTTP 200）：`2203.16263`、`1901.08971`、`2108.05080`、`2311.15308`。
- 错误 ID 已记录，不采信：`2204.08321` 不是 Self-Blended Images；`2311.16103` 不是 AV-Deepfake1M。
- GitHub 请求：0。

## 数据集侧补强（不是新检测器）

这些结果写入 [`datasets/audio.md`](../datasets/audio.md) 与 [`datasets/video.md`](../datasets/video.md)，**不计入**官方检测方案数量。

| 对象 | 论文 | 已确认字段 | 用途 |
|---|---|---|---|
| In-the-Wild 音频 | [arXiv:2203.16263](https://arxiv.org/abs/2203.16263) *Does Audio Deepfake Detection Generalize?* | 37.9 小时（伪造 17.2 h + 真实 20.7 h）、58 位名人/政客、16 kHz；发布 [Hugging Face mueller91/In-The-Wild](https://huggingface.co/datasets/mueller91/In-The-Wild)；作者强调 ASVspoof 训练模型在该集上显著退化 | 跨域测试集，不是实时或 VC 专项模型 |
| FaceForensics++ | [arXiv:1901.08971](https://arxiv.org/abs/1901.08971) | DeepFakes / Face2Face / FaceSwap / NeuralTextures；官方仓库 [ondyari/FaceForensics](https://github.com/ondyari/FaceForensics)；论文称 180 万+ 操纵图像与隐藏测试集 | 换脸闭集与压缩协议；**不是检测算法** |
| FakeAVCeleb | [arXiv:2108.05080](https://arxiv.org/abs/2108.05080) | 音视频联合、唇同步克隆语音、多族裔英语名人；含视频与对应合成音频标签 | Talking Face / 唇音数据层 |
| AV-Deepfake1M | [arXiv:2311.15308](https://arxiv.org/abs/2311.15308) ACM MM 2024 | >2K 主体、约 114.7 万视频（真实 286,721 / 伪造 860,039）；任务为检测+时间定位；代码/数据入口 [ControlNet/AV-Deepfake1M](https://github.com/ControlNet/AV-Deepfake1M) | Talking Face 与 TFL 数据层 |
| LAV-DF（同文 Table 1 对照） | 被 AV-Deepfake1M 引用为 Cai et al. 2022 | 153 主体、真实 36,431、伪造 99,873、合计 136,304；内容驱动 RE/TTS | 局部伪造定位对照集；本批次未单独打开 LAV-DF 原文 |

AV-Deepfake1M Table 1 还给出可对照的公开规模：FF++ 1,000 真实 / 4,000 伪造；Celeb-DF 590 / 5,639；DFDC 23,654 / 104,500；DeeperForensics 50,000 / 10,000；KoDF 62,166 / 175,776；ASVspoof 2021 DF 20,637 / 572,616。这些数字来自该论文汇总表，正式许可仍以后续官方发布页为准。

## 未新增的官方检测实现

| 方向 | 本批次结果 | 恢复搜索的最低证据 |
|---|---|---|
| VC | 无新作者仓库。ASVspoof 2019 LA 含 TTS 与 VC 攻击，但本轮未转录 AASIST Table 1 逐攻击 EER，不能把池化 EER 写成 VC 专项 | 官方实现 + 按 VC 攻击家族拆分的 EER/AUC |
| 语音克隆 | 无新有参考/无参考对照实验。In-the-Wild 是名人克隆素材测试集，不是克隆检测器 | 说话人隔离、有无参考声纹的分表指标 |
| 实时音频 | 无窗口、步长、首检延迟、吞吐的官方实验 | 流式协议 + 延迟数字绑定硬件 |
| 人脸重演 | 无新专项检测器。FF++ 的 Face2Face/NeuralTextures 仍只作为 RealForensics 辅助覆盖 | 音频/姿态驱动生成器拆表 |
| Talking Face | 无新检测器。数据层补强 FakeAVCeleb / LAV-DF / AV-Deepfake1M；检测器仍为 AuViRe、ICS-AV、DiMoDif | 音视频联合 + 伪造片段条件的绝对指标 |
| 唇音同步 | 无偏移量分层官方指标。LipFD 检索未完成（403），既有非官方个人仓继续排除 | 明确偏移协议、语言/帧率、sync AUC 或定位 AP |

Self-Blended Images（SBI）因错误 arXiv ID 与搜索 403，**本轮不登记为官方方案**。ICS-AV 原文仍未取得，Ashutosh Anshul 的 [arXiv:2511.10212](https://arxiv.org/abs/2511.10212) 不得替代 ICS-AV 仓库。

## 对覆盖状态的影响（已按测试开测口径修订）

数量 6/3 不是开测硬门槛。稀缺方向**用已核验联合/相邻模型作测试候选**，结果加备注：

- VC：AASIST / RawGAT-ST，按攻击 ID 分列。
- 克隆：XLSR-MamBo ITW。
- 实时：离线反欺骗模型 + 测试方自定窗口。
- 人脸重演：RealForensics 的 F2F/NT。
- Talking Face：AuViRe、DiMoDif。
- 唇音：AuViRe、DiMoDif 的 DFD/TFL 代理，不是偏移误差。

专项检测器仍然少，这只要求备注，不停止测试。入准表见 [`reports/audio.md`](../reports/audio.md) 与 [`reports/video.md`](../reports/video.md)。
