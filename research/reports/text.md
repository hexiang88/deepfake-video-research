# 文本模态：生成文本检测（阶段性核验稿）

> **核验日期：2026-08-12（Asia/Shanghai）**。本稿只写入已能从官方仓库和论文入口核验的事实；性能数字在完成论文实验表、数据划分和扰动条件复核前，不作为基准测试最终排名。

## 1. 技术路线框架

| 路线 | 核心原理 | 适用边界 |
|---|---|---|
| 监督式判别器 | 用人类/机器文本训练 Transformer 分类器 | 依赖训练分布，跨模型和跨领域容易退化 |
| 概率曲率/扰动式零样本 | 比较原文在模型概率面上的曲率或扰动响应 | 需要可访问的评分模型，长文本和改写会影响稳定性 |
| 生成过程/指纹式检测 | 利用生成轨迹、统计指纹或对抗训练信号 | 可提升已知生成器识别，但面对新生成器和人工改写需单独验证 |
| 评测型开放集检测 | 在多模型、多体裁、多攻击数据上检验检测器 | 不是单一检测器；用于比较泛化和鲁棒性 |

## 2. 已核验官方开源方案

“官方”在本表中指作者/机构账号的原始仓库；仓库元数据来自 GitHub 官方 API，Star 和更新时间均为核验时快照。

| 方案 | 出处/原始仓库 | 开源状态与协议 | 官方元数据快照 | 核心逻辑与输入输出 |
|---|---|---|---|---|
| DetectGPT | Eric Mitchell 等，《DetectGPT: Zero-Shot Machine-Generated Text Detection using Probability Curvature》，2023；[官方仓库](https://github.com/eric-mitchell/detect-gpt)；[论文](https://arxiv.org/abs/2301.11305) | 实验代码开源；MIT；权重/评分模型依赖需另行获取 | 475 Stars；未归档；2026-07-27 更新 | 对输入文本做模型扰动，基于 log-probability 曲率区分机器文本；输入文本和评分模型，输出检测分数 |
| Fast-DetectGPT | Bao Guangsheng 等，《Fast-DetectGPT: Efficient Zero-Shot Detection of Machine-Generated Text via Conditional Probability Curvature》，ICLR 2024；[官方仓库](https://github.com/baoguangsheng/fast-detect-gpt)；[论文](https://arxiv.org/abs/2310.05130) | 代码开源；MIT；需下载评分/采样模型 | 420 Stars；未归档；2026-08-07 更新 | 以条件概率曲率替代 DetectGPT 的大量随机扰动，降低采样开销；输入文本，输出机器生成概率/检测分数 |
| DNA-GPT | Xianjun Yang 等，《DNA-GPT: Divergent N-Gram Analysis for Training-Free Detection of GPT-Generated Text》，2023；[官方仓库](https://github.com/Xianjun-Yang/DNA-GPT)；[论文](https://arxiv.org/abs/2305.17359) | Demo/代码开源；MIT；需核验完整训练/推理依赖 | 57 Stars；未归档；2026-06-29 更新 | 通过生成/比较文本片段的 n-gram 差异寻找生成痕迹；输入文本，输出检测分数/分类结果 |
| RADAR | IBM Research 等，《RADAR: Robust AI-Text Detection via Adversarial Learning》，NeurIPS 2023；[官方仓库](https://github.com/IBM/RADAR)；[论文](https://proceedings.neurips.cc/paper_files/paper/2023/file/30e15e5941ae0cdab7ef58cc8d59a4ca-Paper-Conference.pdf) | 代码开源；Apache-2.0；模型卡和权重需单独记录 | 76 Stars；未归档；2026-08-02 更新 | 以 RoBERTa-large 为检测器并进行对抗训练，目标是提升对改写的鲁棒性；输入文本，输出 AI 概率 |
| Multiscale PU detector（MPU） | Yuchuan Tian 等，《Multiscale Positive-Unlabeled Detection of AI-Generated Texts》，ICLR 2024 Spotlight；[官方仓库](https://github.com/YuchuanTian/AIGC_text_detector)；[论文](https://arxiv.org/abs/2305.18149) | 代码开源；Apache-2.0；另提供 Hugging Face/ModelScope 模型与 Demo | 454 Stars；未归档；2026-08-10 更新 | 多尺度正例-未标注学习，针对不同长度/粒度和新模型版本提供检测器；输入英文/中文文本，输出检测分数或类别 |
| DetectLLM | MBZUAI NLP；[官方仓库](https://github.com/mbzuai-nlp/DetectLLM) | **已发现官方机构仓库，协议和版本状态待补核** | 待补录 | 作为 DetectLLM 系列方法的官方实现候选；在协议、论文对应关系、输入输出和公开指标核验完成前不进入最终排名 |

## 3. 性能证据（当前仅记录已绑定条件的摘要）

Fast-DetectGPT 官方 README 给出其摘要对比：在 README 所称的“5-Model Generations”场景，DetectGPT AUC 0.9554、Fast-DetectGPT AUC 0.9887；在 ChatGPT/GPT-4 Generations 场景分别为 0.7225 和 0.9338，并报告约 340× speedup。**这些数字仍需回到论文表格核对具体生成模型、数据集、划分、阈值和速度测量边界，暂不直接作为基准测试数字。**

RADAR 官方 README 明确声称覆盖 8 个 LLM（包括 Vicuna、LLaMA）并评估改写鲁棒性，但摘要页未提供足够实验条件，具体 AUC/F1 和改写设置待论文表格核验。

## 4. 数据集/评测基准候选

| 名称 | 官方来源 | 已核验信息 | 待补字段 |
|---|---|---|---|
| RAID | Liam Dugan 等；[官方仓库](https://github.com/liamdugan/raid)；[项目站](https://raid-bench.xyz)；[论文](https://arxiv.org/abs/2405.07940) | README 称超过 1000 万篇文档、11 个 LLM、11 个体裁、4 种解码策略、12 类对抗攻击；MIT；205 Stars | 官方下载/许可细则、真实/机器比例、拆分、每种攻击参数和基线表 |
| HC3 | Hello-SimpleAI；[官方仓库](https://github.com/Hello-SimpleAI/chatgpt-comparison-detection) | 官方仓库用于 ChatGPT 与人类回答比较检测；高 Star，但仓库 LICENSE 字段未声明 | 数据规模、语言/领域构成、下载地址、许可和官方论文指标 |
| WritingPrompts | DetectGPT README 指向 Kaggle 数据页 | 被官方 DetectGPT 实验说明使用 | 原始发布机构、许可、完整下载与划分核验 |

## 5. 当前能力边界与基准适配

- **零样本路线**适合测试“未知生成器/OOD”，但评分模型选择会显著影响结果，必须把评分模型和访问条件记录为实验变量。
- **监督式路线**通常更容易部署和校准，但训练生成器与测试生成器必须隔离，否则会夸大跨模型泛化。
- **改写/释义**是文本检测的关键失效模式；应至少设置原始生成、人工改写、LLM 改写、多轮改写四级条件。
- **长短文本混杂**会引入长度偏差；报告应按字符/词元长度分桶，同时报告宏平均和置信区间。
- **多语言**不能仅将英文模型直接迁移后给出单一结论；中文、英文、日文及跨语言改写应分别统计。

## 6. 未完成项

本方向尚未完成风格仿冒归因、生成来源溯源、跨语言泛化四个细分方向，也尚未完成每个方向不少于 6 个方案的最终筛选。DetectLLM、Binoculars、Ghostbuster、TuringBench 等候选将继续核验；没有作者/机构官方原始实现的项目会转入补充参考而非主清单。
