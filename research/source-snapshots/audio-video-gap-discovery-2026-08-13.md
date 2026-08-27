# 音视频缺口候选发现快照

核验日期：2026-08-13。来源为 GitHub 官方 API 搜索结果；搜索结果仅用于发现候选，不证明作者归属、官方原始实现、许可证、指标或实验条件。

## 请求记录

- 本批次计划：先读取 1 次 `rate_limit`，再执行 2 个官方仓库搜索请求；不读取候选仓库详情，除非配额明确且候选能通过作者/机构来源初筛。
- `rate_limit`：1 次，HTTP 200；`limit=60`、`remaining=58`、`used=2`、`reset=1786590267`。
- 搜索请求：2 次；第 1 次 `audio deepfake detection` 返回 HTTP 200，第 2 次 `audio visual deepfake detection` 在传输阶段以 `unexpected EOF or 0 bytes from the transport stream` 失败。
- 因第 2 次请求失败且未返回新的 rate-limit 头，本轮停止全部 GitHub 请求。最后可确认的剩余配额是搜索前的 58，搜索后的精确剩余值不作推断。
- 未读取新的仓库 README、提交、LICENSE、论文页或模型文件；未新增可进入主报告的性能证据。

## 音频搜索发现

| 候选 | 搜索结果显示的角色 | 处理结论 |
|---|---|---|
| `media-sec-lab/Audio-Deepfake-Detection` | speech deepfake detection 的研究进展、数据集和公开代码聚合 | 不作为检测算法；综述/聚合仓库不能替代作者原始实现 |
| `sksmta/audio-deepfake-detection` | CNN 音频深伪检测系统 | 仅搜索摘要，无法确认论文对应关系、作者身份、数据划分和指标，保持待核验 |
| `noorchauhan/DeepFake-Audio-Detection-MFCC` | MFCC 音频深伪检测 | 仅搜索摘要，无法确认作者官方性和可溯源实验，保持待核验 |
| `piotrkawa/audio-deepfake-adversarial-attacks` | 声音深伪检测对抗攻击防御实现 | 可能补充扰动/对抗鲁棒性方向，但尚未核验作者原始实现、任务协议和逐模型指标，不进入主清单 |
| `dessa-oss/fake-voice-detection`、`LetterLiGo/SafeEar`、`QiShanZhang/SLSforASVspoof-2021-DF` | 已存在于本地快照的项目 | 不重复审计 |

## 视频/音视频搜索结果

第 2 个搜索请求未返回候选列表，故没有新增视频或音视频模型证据。现有可用证据仍以 `audio-video-repositories-2026-08-12.md`、`auvire-metrics-2026-08-12.md` 和既有音视频报告为准。

## 缺口结论

- 音频 TTS、VC、克隆、统一扰动预算和流式延迟仍缺少足够多的作者/机构官方原始实现及绑定指标；搜索摘要不能补齐这些硬字段。
- 视频重演、Talking Face、唇音同步仍缺少逐偏移指标、统一时间协议和足量官方联合检测器；本批次未获得新证据。
- 音频和视频所有细分方向继续保持 `深核验`，不能改为 `完成`。
