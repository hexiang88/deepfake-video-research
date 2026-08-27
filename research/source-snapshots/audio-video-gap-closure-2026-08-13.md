# 音视频缺口收敛快照（2026-08-13）

## 网络批次

- 计划非 GitHub 请求：6 次，目标为 SafeEar、Codecfake、EBM、RealForensics、FakeSTormer、ICS-AV 的 arXiv 原始记录。
- GitHub 请求：0 次。
- 实际结果：6 次均在连接阶段失败，未返回 HTTP 状态、论文内容或配额字段。
- 按停止规则未重试，未访问 GitHub，也未把本批次当作新增证据。

## 现有本地证据可直接使用的内容

### 音频

| 方案/协议 | 已绑定条件 | 可使用内容 | 仍缺字段 |
|---|---|---|---|
| SLS with XLS-R | ASVspoof 2019 LA 训练；2021 DF、2021 LA、In-the-Wild 测试 | EER 1.92%、2.87%、7.46% | 具体攻击/生成器拆分、统一扰动预算 |
| XLSR-MamBo | ASVspoof 2019 LA 训练；21LA、21DF、In-the-Wild、DFADD 子集测试 | 四个模型的逐域 EER 表 | DFADD D1-D3/F1-F2 的原始定义、攻击家族映射 |
| Codecfake | Codecfake、ASVspoof 2019 LA、In-the-Wild；codec-unseen C7/ALM | 可作为未知 codec 评测入口 | EER 表、codec 参数、样本划分和生成器标签 |
| SafeEar | ASVspoof 2019/2021、CVoiceFake | 可作为隐私/检测联合路线 | 2.02% 所属模型、track、划分、完整退化参数 |
| MixFake | MixedAndBack 与 MixedAndFore 独立协议；`phase=eval`、bonafide/spoof | 可作为混合音频场景协议 | 混合比例、标签定义、样本规模、汇总 EER |

### 视频

| 方案/协议 | 已绑定条件 | 可使用内容 | 仍缺字段 |
|---|---|---|---|
| RealForensics | 跨操纵、跨数据集、噪声/压缩 | 已有视频级 AUC 条件表 | 各扰动参数与完整表格来源定位 |
| LipForensics | FF++ 训练；Celeb-DF-v2、DFDC、FaceShifter、DeeperForensics 测试 | AUC 82.4%、73.5%、97.1%、97.6% | 具体 FF++ 压缩设置、采样/聚合细节 |
| FakeSTormer | 六数据集，c23/c0 | CDF2、DFW、DFD、DFDC、DFDCP、DiffSwap AUC 表 | 每个数据集的生成器/划分定义、压缩编码说明 |
| AuViRe | LAV-DF 与 AV-Deepfake1M 互训互测；DFD/TFL 分开 | DFD AUC、TFL AP、Codabench JSON 和音视频鲁棒性参数 | 逐样本结果汇总、视觉缩写参数释义、与其他模型统一协议 |
| ICS-AV | VoxCeleb2 自监督预训练；FakeAVCeleb 下游 | 可作为跨模态同步/定位候选 | sync 指标、偏移量、语言/帧率、划分 |

## 不能在本批次完成的事项

- 不把 README 的摘要数值升级为论文表格指标。
- 不把 ASVspoof LA/DF 的 EER 改写为 TTS、VC 或语音克隆专项结果。
- 不把普通视频真假 AUC 改写为唇音同步指标。
- 不把跨数据集、闭集、压缩和定位结果合并成单一排行榜。

## 后续最小核验单元

下一次联网恢复后，每个方案只需先取得一份作者/机构论文原文或附录，优先补齐：`表号；训练/开发/测试划分；生成器或攻击家族；压缩/扰动参数；指标单位；代码/权重对应关系`。缺任一关键字段仍保持部分核验。
