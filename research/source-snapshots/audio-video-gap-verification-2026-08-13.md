# 音视频缺口候选核验快照

核验日期：2026-08-13。来源为 GitHub 官方 API 仓库元数据和 README；本快照只记录可追溯页面事实，不把个人项目或 README 自报数字直接纳入基准排名。

## 请求记录

- 本批次计划：1 次 `rate_limit`，2 次定向搜索，1 次配额复核，随后核验 2 个候选的仓库元数据和 README，共 8 次请求。
- 第一次 `rate_limit`：HTTP 200，核心资源 `limit=60`、`remaining=58`、`used=2`、`reset=1786590267`。
- 定向搜索：`voice conversion deepfake detection` 和 `lip sync deepfake detection` 均 HTTP 200；搜索资源剩余头分别显示 9、8。
- 第二次 `rate_limit`：HTTP 200，核心资源仍显示 `remaining=58`、`used=2`。资源头与请求计数不一致，因此不据此推算搜索资源的精确消耗。
- 候选读取：4 次均 HTTP 200；核心资源剩余头依次为 57、56、55、53。
- 本批次最后一次成功请求可见的核心剩余配额为 53；搜索资源最后一次可见为 8。未收到 429，之后停止 GitHub 请求。

## 音频候选

### `fahad-kacchi/Deep_Fake_Voice_Recognition`

- API 元数据：MIT；未归档；9 Stars；最近更新时间 2026-02-21；默认分支 `main`。
- README 明确将项目定位为使用 RVC 生成语音的 DEEP-VOICE 数据集和检测项目，数据下载指向 Kaggle；提供 `train_model.py`、`evaluate_model.py` 和 `real_time_detection.py` 入口。
- README 仅列出拟使用 Accuracy、Precision、Recall、F1 等评估指标，没有给出实际数值、明确 train/validation/test 划分、RVC 攻击子类型、说话人隔离、压缩/噪声条件或论文对应关系。
- 结论：可作为 RVC/实时检测缺口的待核验数据与代码候选，但不能作为已核验官方算法、VC 指标或实时性能证据；不计入六方案门槛。

## 视频/音视频候选

### `PRADUMAN-KR/Multimodal-Lip-Sync-Deepfake-Detection-System`

- API 元数据：Apache-2.0；未归档；3 Stars；最近更新时间 2026-08-08；默认分支 `main`。
- README 自称为音视频唇音同步检测系统，描述 3D 视频编码、声谱图音频编码、双向跨模态注意力和 Transformer，并提供 FastAPI 推理入口。
- README 自报 `Accuracy: 98%+`、验证集 `2500`、`False Positives: 0.4%`，另称数据集有 `50K+` 视频片段；但没有给出数据集名称/发布方、真实与伪造划分、生成器或 Wav2Lip 版本、同步偏移量、语言/帧率、压缩/噪声协议，也没有逐实验结果文件。README 中还出现 `R2Plus1D-Sync-Defense-Resnet-` 的不同仓库路径，复现入口的一致性需进一步核对。
- 结论：不能用其自报数字支持唇音同步指标、实时延迟或鲁棒性排名；保持待核验，不计入官方原始检测器门槛。

## 缺口结论

- 本批次没有新增可进入音频或视频主报告的绑定指标。
- 音频 VC/TTS/克隆仍缺少公开的作者/机构官方原始实现与逐攻击家族 EER/AUC；实时检测仍缺窗口、步长、首检延迟和吞吐的可复现实验。
- 视频唇音同步仍缺少公开的偏移量分层指标、生成器隔离、数据集划分和统一退化协议；个人应用仓库的 README 汇总值不能替代这些证据。
- 音频和视频各细分方向继续保持 `深核验`，没有方向可改为 `完成`。
