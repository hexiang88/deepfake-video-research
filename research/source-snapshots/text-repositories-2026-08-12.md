# 文本仓库元数据快照

来源：GitHub REST API `repos/{owner}/{repo}`，核验日期：2026-08-12。Star 数和更新时间是动态字段，只代表该次快照，不是历史恒定事实。

| 仓库 | 官方链接 | Stars | LICENSE 字段 | Archived | 最近更新时间 |
|---|---|---:|---|---|---|
| `eric-mitchell/detect-gpt` | https://github.com/eric-mitchell/detect-gpt | 475 | MIT | false | 2026-07-27 |
| `baoguangsheng/fast-detect-gpt` | https://github.com/baoguangsheng/fast-detect-gpt | 420 | MIT | false | 2026-08-07 |
| `YuchuanTian/AIGC_text_detector` | https://github.com/YuchuanTian/AIGC_text_detector | 454 | Apache-2.0 | false | 2026-08-10 |
| `IBM/RADAR` | https://github.com/IBM/RADAR | 76 | Apache-2.0 | false | 2026-08-02 |
| `Xianjun-Yang/DNA-GPT` | https://github.com/Xianjun-Yang/DNA-GPT | 57 | MIT | false | 2026-06-29 |
| `liamdugan/raid` | https://github.com/liamdugan/raid | 205 | MIT | false | 2026-08-11 |
| `Hello-SimpleAI/chatgpt-comparison-detection` | https://github.com/Hello-SimpleAI/chatgpt-comparison-detection | 1426 | GitHub LICENSE 字段未声明 | 待补 | 待补 |
| `mbzuai-nlp/DetectLLM` | https://github.com/mbzuai-nlp/DetectLLM | 35 | 待补 | 待补 | 待补 |

## 页面级补充核验

GitHub 官方仓库页面在 2026-08-12 可访问（HTTP 200），页面标题分别明确显示：

- `mbzuai-nlp/DetectLLM`：**DetectLLM: Leveraging Log Rank Information for Zero-Shot Detection of Machine-Generated Text**。
- `Hello-SimpleAI/chatgpt-comparison-detection`：**Human ChatGPT Comparison Corpus (HC3), Detectors, and more**。
- `IBM/RADAR`：**RADAR: Robust AI-Text Detection via Adversarial Learning**。

页面可访问不等于协议、指标和完整复现条件已核验；这些字段仍按台账规则保留为待补状态。

## 解释与限制

- 仓库位于作者、实验室或机构账号下，仍需结合论文作者/机构信息确认“官方原始实现”；Star 数本身不能证明官方性或算法质量。
- `liamdugan/raid` 是评测数据集/工具，不计入检测模型数量。
- `Hello-SimpleAI/chatgpt-comparison-detection` 是 HC3 相关官方项目候选，协议、数据许可和论文指标尚未完成核验。
- `mbzuai-nlp/DetectLLM` 已发现机构账号仓库，但需要补充论文对应关系、LICENSE、版本、模型权重和实验条件。
- GitHub 搜索 API 随后触发匿名速率限制，因此 Ghostbuster、Binoculars、来源归因和跨语言候选不据此判定不存在；它们保持“待核验”。
