# 认证 API 音视频官方候选核验快照

核验日期：2026-08-13。通过 GitHub 官方 REST API 和用户确认的 HTTP 代理 `LAB_HTTP_PROXY` 读取；认证令牌只通过环境变量使用，未写入文件。

## 请求记录

- 批次计划：1 次认证 `rate_limit`、4 次定向搜索、6 次仓库元数据/README，共 11 次请求。
- `rate_limit`：HTTP 200；核心资源 `limit=5000`、`remaining=5000`、`used=0`、`reset=1786595409`。
- 定向搜索：4 次，均 HTTP 200；搜索结果剩余头依次为 29、28、27、26。
- 仓库核验：6 次，均 HTTP 200；核心资源剩余头依次为 4995、4994、4993、4992、4991、4990。
- 未收到 401、403 或 429；本批次停止后不再发起 GitHub 请求。搜索资源与核心资源分开计数，按响应头分别记录。

## 音频

### Raw-PC-DARTS

- 官方仓库：[eurecom-asp/raw-pc-darts-anti-spoofing](https://github.com/eurecom-asp/raw-pc-darts-anti-spoofing)；API 显示 MIT、未归档、11 Stars，最近更新 2024-10-30。
- README 明确对应论文 *Raw Differentiable Architecture Search for Speech Deepfake and Spoofing Detection*（ASVspoof 2021 workshop，arXiv:2107.12212），作者为 Wanying Ge、Jose Patino、Massimiliano Todisco、Nicholas Evans，并说明 EURECOM/ExTENSoR 支持关系。
- 开源范围：架构搜索 `train_search.py`、从头训练 `train_model.py`、评测 `evaluate.py`、协议文件和预训练模型入口；README 说明最终模型分数在 `/scores`，模型可从 EURECOM Nextcloud 获取。
- 数据和协议：ASVspoof 2019 LA；README 明确 `train`、`dev`、`eval` 目录及官方协议文件，并提供训练/评测命令。伪造条件仍需按论文表拆分，README 未给逐攻击数值。
- 状态：**部分核验**。可作为官方完整训练/评测音频基线；当前不能填入数值排名，也不能把 LA 结果外推为 TTS/VC/实时指标。

### WavLM voice deepfake detection

- 仓库：[fedorova-av/wavlm-voice-deepfake-detection](https://github.com/fedorova-av/wavlm-voice-deepfake-detection)；API 显示未归档、0 Stars，最近更新 2026-07-28；许可证字段为空。
- README 描述冻结 WavLM Large、聚合 25 层隐藏状态并使用轻量分类器，包含 baseline、层聚合、MLP、微调和 RawBoost 实验 notebook。
- 条件绑定：ASVspoof 2019 LA train/dev 训练和验证，ASVspoof 2021 LA eval 最终评估；指标为 EER 和官方 min-tDCF，并讨论未知攻击泛化。
- README 数值：Weighted Sum + Linear 在 2019 LA dev 的 EER 约 0.11%；2021 LA eval 的 EER 约 6.8%。未给出逐攻击、压缩或跨域拆表。
- 状态：**部分核验**。仓库身份和协议清楚，但作者/机构官方归属与许可证仍待核验，且结果以 notebook/摘要形式给出，不作为完整官方方案或横向排名。

## 视频/音视频

### DiMoDif

- 官方仓库：[mever-team/dimodif](https://github.com/mever-team/dimodif)；API 显示 Apache-2.0、未归档、7 Stars，最近更新 2026-07-27。
- README 明确对应作者 Christos Koutlis、Symeon Papadopoulos 的论文 *Discourse Modality-information Differentiation for Audio-visual Deepfake Detection and Localization*，arXiv:2411.10193。
- 方法和输出：使用音频/视觉语音识别表征、层级跨模态融合、自适应时间对齐和 discrepancy mapping，输出帧级检测分数与伪造区间定位结果。
- 数据和实验入口：FakeAVCeleb、VoxCeleb2、LAV-DF、AV-Deepfake1M、DFDC、KoDF；提供 DFD、TFL、FakeAVCeleb 跨操纵、跨数据集和 `robustness.py` 评测脚本，并提供 AV-Deepfake1M Codabench 预测流程。
- README 只报告相对提升摘要（AV-Deepfake1M DFD 相对提升 30.5 AUC、TFL AP@0.75 相对提升 47.88），没有在 README 中给出可直接绑定的绝对值、划分和退化参数；不与 AuViRe 的绝对 JSON 结果合并。
- 状态：**部分核验**。这是新的作者官方音视频联合检测/定位候选，可补 Talking Face、唇音同步和时序定位覆盖，但仍不能据 README 摘要做精度排名。

## 缺口结论

- 音频新增 Raw-PC-DARTS 和 WavLM 候选，但 VC/TTS 逐生成器指标、电话/流式延迟和统一扰动预算仍不足。
- 视频新增 DiMoDif 官方联合检测/定位实现，但唇音偏移分层指标、统一跨域协议和逐扰动结果仍需论文表或结果文件核验。
- 音频和视频所有细分方向继续保持 `深核验`；本批次没有方向达到“至少 6 个满足全部硬字段方案”的完成条件。
