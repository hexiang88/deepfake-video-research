# 音频模态数据集与基准核验台账

本表只把已确认有官方入口或作者论文页的项目列为“入口已发现”。规模、许可、伪造类型和官方下载方式必须继续从官方发布页/README/论文核对后才能进入最终数据集清单。数据集不计入检测算法方案数量。

| 数据集/基准 | 官方入口 | 角色 | 已记录字段 | 仍缺字段 | 当前状态 |
|---|---|---|---|---|---|
| ASVspoof 挑战与数据门户 | [asvspoof.org](https://www.asvspoof.org/)（2026-08-13 HTTP 200） | 逻辑访问/深伪反欺骗主训练与评测协议 | 官方门户可访问；2019 LA / 2021 LA+DF 被 AASIST、RawGAT-ST、SafeEar、XLSR-MamBo、Codecfake 等用作训练或测试域 | 许可条款、精确样本数、官方下载与注册流程、攻击家族官方清单 | 入口已发现 |
| ASVspoof 2019 LA | 论文引用见 [AASIST arXiv:2110.01200](https://arxiv.org/abs/2110.01200)；SafeEar Table 1 记 96,617 条、时长 0.470–16.548 s、英语、clean | TTS/VC 反欺骗闭集训练域 | 评测含 A07–A19 共 13 类攻击；池化 EER/min t-DCF 为官方指标；AASIST Table 1 已给出逐攻击 EER | 官方许可、**逐攻击生成器名称**（TTS/VC 家族）与下载包哈希 | 入口已发现；攻击家族清单待核，测试时按攻击 ID 分列、不汇总成 TTS/VC |
| ASVspoof 2021 LA/DF | SafeEar Table 1：173,556 条、时长 0.355–13.402 s、英语、telecom | 跨年/信道退化与深伪（DF）测试域 | 多数 SSL 模型以 2019 LA 训练、2021 LA/DF 测试 | 2021 官方评测包许可、LA 与 DF 拆分文件、编码条件 | 入口已发现 |
| In-the-Wild 音频深伪 | 论文 [arXiv:2203.16263](https://arxiv.org/abs/2203.16263)；[Hugging Face mueller91/In-The-Wild](https://huggingface.co/datasets/mueller91/In-The-Wild) | 真实世界名人/政客语音跨域测试 | 37.9 小时（伪造 17.2 h、真实 20.7 h）、58 名说话人、16 kHz；作者报告 ASVspoof 训练模型在此集上大幅退化 | 许可证全文、生成器清单、划分文件哈希 | 论文与 HF 入口已发现 |
| Codecfake | [xieyuankun/Codecfake](https://github.com/xieyuankun/Codecfake)；论文 [arXiv:2405.04880](https://arxiv.org/abs/2405.04880) | 未知 codec / ALM 泛化 | 论文：1,058,216 条；VCTK（EN）+ AISHELL3（CN）；F01–F06 可见 codec，C7 未见 codec；ALM 条件 A1–A3；数据集 CC BY-NC-ND 4.0 | 仓库代码 SPDX 未声明；官方下载镜像与文件哈希 | 论文规模已核；许可部分核验 |
| CVoiceFake | SafeEar 论文 [arXiv:2409.09272](https://arxiv.org/abs/2409.09272) Table 1 | 多语言媒体域 TTS 检测与隐私赛道 | 英/中/德/法/意样本约 25.8/25.4/23.9/28.4/22.0 万条；时长区间已记录 | 独立发布页、许可、生成器清单、下载 | 论文统计已核；发布页待核 |
| MixFake | 仓库指向 Hugging Face 数据卡；论文 [arXiv:2605.23201](https://arxiv.org/abs/2605.23201) | 前景/背景混合音频 | Foreground 与 Background 为独立子任务；16 kHz、4 秒裁剪；EER 为官方指标 | 混合比例、样本规模、HF 数据卡许可与作者归属 | 协议已见；规模/许可待核 |
| DFADD | XLSR-MamBo 论文 [arXiv:2601.02944](https://arxiv.org/abs/2601.02944) §5.1 | 扩散/flow-matching 音频伪造泛化 | **D1–D3 = 不同扩散生成器；F1–F2 = 不同 flow-matching 生成器** | 官方发布页、许可、各子集生成器名称与规模 | 子集定义已核；发布页待核 |

## 基准测试需要的音频数据分层

1. **闭集反欺骗层**：ASVspoof 2019 LA 官方 train/dev/eval，按攻击标签报告，不得把池化 EER 写成 TTS 或 VC 专项成绩。
2. **跨年/跨域层**：2019 LA 训练 → 2021 LA/DF、In-the-Wild。
3. **未知 codec / ALM 层**：Codecfake C1–C6 可见、C7 不可见、A1–A3 ALM；与 ASVspoof 分表。
4. **混合场景层**：MixFake Foreground 与 Background 分开；记录 SNR。
5. **多语言/隐私层**：CVoiceFake 与 SafeEar 的去语义约束单独成赛道。
6. **实时层**：当前无已核验的流式窗口/步长/首检延迟数据集协议。

## 许可与可追溯要求

- 人脸/声纹数据需记录研究用途限制；不能把“论文使用”推断为“可再发布”。
- Codecfake 数据集 CC BY-NC-ND 4.0 禁止再分发衍生数据，基准公开子集设计时必须单独处理。
- 数据集与检测模型分开计数。
