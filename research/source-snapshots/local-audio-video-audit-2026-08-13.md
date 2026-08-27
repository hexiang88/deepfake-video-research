# 音频与视频本地证据收敛快照

核验日期：2026-08-13。本文是对既有本地快照的结构化复核，不是新的 GitHub/API 取证。

## 请求记录

- 本轮 GitHub 请求：1 次（仅 rate-limit 尝试；未成功获得响应）。
- 本轮 GitHub API rate-limit 响应：无，因此没有新的剩余配额数字可报告。
- 使用的既有来源：`audio-video-repositories-2026-08-12.md`、`audio-repositories-2026-08-12.md`、`auvire-metrics-2026-08-12.md`、`xlsr-mambo-mixfake-2026-08-12.md`。
- 本地复核没有下载数据、模型权重或修改外部文件。

## 2026-08-13 后续请求记录

- 批次：音视频缺口补齐第一批，计划先读取 rate-limit，再读取 4 个未重复审计的官方候选。
- 已尝试请求：1 次 GitHub `rate_limit`。
- 返回：连接在接收阶段关闭，未获得 HTTP rate-limit 响应。
- 处理：按规则立即停止本轮全部 GitHub 请求；剩余配额无法确认，未读取任何新的仓库元数据或 README。

## 可直接进入基准记录的指标

以下数字在既有快照中已经同时绑定训练域/测试域或数据集、任务和结果口径，可以进入后续基准数据表；它们仍不是跨任务总排名。

| 方案 | 任务 | 已绑定条件 | 指标 | 来源快照 |
|---|---|---|---|---|
| SLS with XLS-R | 音频反欺骗 | ASVspoof 2019 LA 训练；ASVspoof 2021 DF、2021 LA 和 In-the-Wild 测试 | EER 1.92%、2.87%、7.46% | `audio-video-repositories-2026-08-12.md` |
| XLSR-MamBo | 音频反欺骗 | ASVspoof 2019 LA 训练；21LA、21DF、In-the-Wild、DFADD D1-D3/F1-F2 测试 | 各模型逐域 EER 表；DFADD 子集定义仍未展开 | `xlsr-mambo-mixfake-2026-08-12.md` |
| RealForensics | 视频真假检测 | FF++ 训练；跨操纵、跨数据集和噪声/压缩条件 | 视频级 AUC；条件按操纵/数据集分别记录 | `audio-video-repositories-2026-08-12.md` |
| LipForensics | 视频真假检测 | FF++ 四类操纵训练；Celeb-DF-v2、DFDC、FaceShifter、DeeperForensics 跨数据集测试 | 视频级 AUC 82.4%、73.5%、97.1%、97.6% | `audio-video-repositories-2026-08-12.md` |
| FakeSTormer | 视频跨域检测 | CDF2、DFW、DFD、DFDC、DFDCP、DiffSwap；c23/c0 编码条件 | 视频级 AUC，逐数据集/编码条件记录 | `audio-video-repositories-2026-08-12.md` |
| AuViRe | DFD 视频检测与 TFL 定位 | LAV-DF 与 AV-Deepfake1M 互训互测；`results/test` 与 Codabench 测试 JSON 分开 | DFD AUC；TFL AP@0.5/0.75/0.9/0.95 | `auvire-metrics-2026-08-12.md` |

## 暂不升级的证据

- SafeEar、AASIST、MesoNet 和 GenConViT 的 README 摘要没有在同一处完整给出模型版本、划分、阈值及全部退化条件；摘要数字保留为来源线索，不作为横向排名。
- MSLA-XLS-R、MixFake、PwTF-DVD、ICS-AV、VLAForge 和 AVSSDeepfakeDet 已有官方实现入口，但仍缺逐表指标、协议或许可证字段，状态保持“部分核验”。
- FTCN、StyleFlow 等项目的代码开放范围不足以按“完整训练/推理开源”计数；官方存在不等于满足硬性方案门槛。
- XLSR-MamBo 的 D1-D3/F1-F2 只记录为 DFADD 子集；MixFake 的 MixedAndBack/MixedAndFore 不能在标签定义和混合比例未核验前合并。
- AuViRe 的闭集高分、跨域下降、鲁棒性逐样本结果和 Codabench 测试结果必须分表记录，不能拼成单一成绩。

## 状态结论

音频和视频的五个细分方向继续保持 `深核验`。本地复核没有发现足以将任一方向改为 `完成` 的新证据：每个方向仍缺至少 6 个满足许可证、开源类型、绑定指标和数据集证据的合格方案，以及统一的横向评测与数据集许可核验。
