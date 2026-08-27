# AuViRe 指标核验快照（2026-08-12）

来源：[mever-team/auvire](https://github.com/mever-team/auvire)，WACV 2026 官方实现。以下数值直接读取仓库 `main` 分支的 JSON 文件；`results/test/*.json` 使用百分数，`results/avdeepfake1m_test_predictions/*/metrics.json` 使用 0–1 小数。

## `results/test`：任务结果

### DFD（视频级 deepfake detection）

| 训练域 | 测试域 | Accuracy | AP | AUC |
|---|---|---:|---:|---:|
| LAV-DF | LAV-DF | 73.5429% | 99.9815% | 99.9398% |
| LAV-DF | AV-Deepfake1M | 74.9663% | 86.8499% | 65.7084% |
| AV-Deepfake1M | LAV-DF | 73.5429% | 97.6592% | 93.3271% |
| AV-Deepfake1M | AV-Deepfake1M | 74.9663% | 99.9971% | 99.9919% |

文件：`results/test/task_dfd_training_on_lavdf.json`、`task_dfd_training_on_avdeepfake1m.json`。

### TFL（temporal forgery localization）

| 训练域 | 测试域 | AP@0.5 | AP@0.75 | AP@0.9 | AP@0.95 |
|---|---|---:|---:|---:|---:|
| LAV-DF | LAV-DF | 98.90596% | 96.03475% | 72.10230% | 46.52463% |
| LAV-DF | AV-Deepfake1M | 16.05148% | 6.68251% | 0.64680% | 0.05262% |
| AV-Deepfake1M | LAV-DF | 53.75679% | 43.26064% | 13.91504% | 0.85392% |
| AV-Deepfake1M | AV-Deepfake1M | 98.81280% | 92.16815% | 45.55694% | 13.16923% |

文件：`results/test/task_tfl_training_on_lavdf.json`、`task_tfl_training_on_avdeepfake1m.json`。这些是仓库结果文件的任务评测，不应自动解释为官方公开测试集排行榜。

## AV-Deepfake1M Codabench 测试预测

| 训练域 | DFD AUC | TFL AP@0.5 | TFL AP@0.75 | TFL AP@0.9 | TFL AP@0.95 |
|---|---:|---:|---:|---:|---:|
| LAV-DF | 0.6570427 | 0.1469821 | 0.0637014 | 0.0056623 | 0.0004681 |
| AV-Deepfake1M | 0.9978455 | 0.9654541 | 0.8928314 | 0.4290189 | 0.1171926 |

文件：`results/avdeepfake1m_test_predictions/lavdf/metrics.json`、`avdeepfake1m/metrics.json`。这里是 0–1 小数；例如 0.9978455 = 99.78455%。README 明确说明 AV-Deepfake1M 测试集需提交 Codabench，仓库 JSON 是提交结果的随附记录。

## 解释边界

- DFD 与 TFL 是不同任务：视频级真假判定和时间区间定位不能用同一指标替代。
- 跨数据集 TFL 的显著下降是 AuViRe 的重要能力边界，不能只引用闭集高 AP。
- 训练域、测试域、validation/test 以及百分数/小数口径必须同时记录。

## 鲁棒性文件索引

仓库 `results/robustness/` 提供多级逐样本结果：音频前缀包括 `audio_AC_*`、`audio_GN_*`、`audio_PS_*`、`audio_RV_*`，并有 `backbone_audio_*`。源码给出参数映射：AC 为 320k/256k/192k/128k/64k 音频压缩，GN 为 SNR 40/30/20/15/10 的高斯噪声，PS 为 2/4/6/8/10 步变调，RV 为 20/40/60/80/100 级混响。视觉前缀包括 `visual_BW_*`、`visual_CC_*`、`visual_CS_*`、`visual_GB_*`、`visual_GNC_*`、`visual_JPEG_*`、`visual_VC_*`；源码确认其中 GNC 为彩色高斯噪声，JPEG 质量级别为 2/3/4/5/6，VC 为视频压缩，其他缩写保留源码命名，避免在缺少注释时臆测具体变换。逐样本结果未自行重算汇总指标。
