# XLSR-MamBo 与 MixFake 核验快照（2026-08-12）

## XLSR-MamBo

- 官方仓库：[saki-ciallo/XLSR-MamBo](https://github.com/saki-ciallo/XLSR-MamBo)，约 5 Stars，MIT，仓库未归档。
- 出处：*XLSR-MamBo: Scaling the Hybrid Mamba-Attention Backbone for Audio Deepfake Detection*，ACL 2026 Findings，arXiv:2601.02944。
- 开源内容：训练/评测脚本、预训练模型链接、ASVspoof 官方评分入口。
- 训练域：ASVspoof 2019 LA。
- 评测域：ASVspoof 2021 LA、ASVspoof 2021 DF、In-the-Wild、DFADD 子集 D1/D2/D3/F1/F2。

| 模型 | 21LA EER% | 21DF EER% | ITW EER% | D1 | D2 | D3 | F1 | F2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| MamBo-1-Mamba2-N2 | 0.79 | 2.01 | 5.57 | 1.69 | 1.69 | 0.00 | 9.00 | 12.54 |
| MamBo-2-Hydra-N1 | 0.80 | 1.84 | 6.24 | 1.84 | 1.69 | 0.00 | 5.32 | 8.85 |
| MamBo-3-Hydra-N3 | 0.81 | 1.70 | 4.97 | 1.84 | 1.33 | 0.00 | 11.36 | 16.01 |
| MamBo-4-Hydra-N1 | 0.98 | 1.43 | 5.17 | 1.33 | 1.84 | 0.00 | 14.17 | 19.34 |

README 未进一步解释 D1–D3、F1–F2 的攻击/数据定义；主报告只把它们称为 DFADD 子集，不将其扩写为具体伪造类型。

## MixFake

- 官方仓库：[saltfish233/MixFake](https://github.com/saltfish233/MixFake)，约 4 Stars，GitHub API 未声明 SPDX 协议，仓库未归档。
- 出处：*MixFake: Benchmarking and Enhancing Audio Deepfake Detection in Diverse Real-world Mixed Audio*，ICME 2026 Spotlight（README 声明）。
- 代码证据：`RawBoost.py`、`main_SSL_LA_ddp.py`、`model_prompt_ddp.py`、`evaluate_metrics.py`，以及 mixed/fore/back 训练脚本与 score 文件。
- 数据入口：README 指向 Hugging Face 的 MixFake 数据集卡。
- 当前缺口：README 极简，未给出可直接引用的 EER/AUC 表、标签定义、混合比例、划分和扰动参数；暂不做性能排名。
- 评测源码：`evaluate_metrics.py` 读取 score 文件与协议文件，仅筛选 `phase=eval`，按 `bonafide`/`spoof` 标签计算 EER；未提供协议文件内容，因此目前不能从脚本单独恢复样本规模或混合比例。
- 训练/评测脚本分为 `MixedAndBack` 与 `MixedAndFore` 两套协议，分别对应 `new_MixFake_Mixed_and_Back_BackLabel.txt` 和 `new_MixFake_Mixed_and_Fore_ForeLabel.txt`；两种标签口径不可合并。
