# 核验运行状态

最后更新：2026-08-13。

## 当前状态

- 本地工作区可读写，已建立证据台账、覆盖矩阵、统一评测协议，文本/图片阶段性报告，以及音频/视频论文表核验、数据集台账与测试入准表。
- 音视频各方向为 `已标注候选`。6/3 只是理想规模，不挡开测。稀缺方向用联合/相邻已核验模型作测试候选，结果须加备注。
- 默认直连仍可能受限；已通过用户确认的局域网 HTTP 代理 `LAB_HTTP_PROXY` 成功访问 GitHub API 和公开仓库内容。
- 网络访问采用只读 GitHub API、README 和公开论文页；未上传数据、登录账号或下载模型权重。
- 通过代理取得的一手证据已写入对应 `source-snapshots/` 文件；未成功读取或只有搜索摘要的字段仍保持“待核验/部分核验”。

## 恢复顺序

1. 先访问一个已知仓库页面，确认 HTTP 状态和标题。
2. 再读取 GitHub 官方 API 元数据，记录 Star、LICENSE、归档和更新时间快照。
3. 读取官方 README、LICENSE、论文/项目页，确认代码、权重和推理接口的开放类型。
4. 最后核对论文实验表和数据集官方发布页；指标必须绑定数据集、划分、生成器和退化条件。

## 已有可用断点

- 文本仓库：`research/source-snapshots/text-repositories-2026-08-12.md`
- 音视频仓库：`research/source-snapshots/audio-video-repositories-2026-08-12.md`
- AuViRe 指标：`research/source-snapshots/auvire-metrics-2026-08-12.md`
- XLSR-MamBo/MixFake：`research/source-snapshots/xlsr-mambo-mixfake-2026-08-12.md`
- 文本归因候选：`research/source-snapshots/text-attribution-candidates-2026-08-12.md`
- 图片仓库候选：`research/source-snapshots/image-repositories-2026-08-12.md`
- 图片数据集台账：`research/datasets/image.md`
- 音频数据集台账：`research/datasets/audio.md`
- 视频数据集台账：`research/datasets/video.md`
- 覆盖矩阵：`research/coverage-matrix.md`
- 统一评测协议：`research/evaluation-protocol.md`
- 2026-08-13 论文表：`research/source-snapshots/audio-video-paper-tables-2026-08-13.md`
- 2026-08-13 稀缺方向：`research/source-snapshots/audio-video-scarce-directions-2026-08-13.md`

## 2026-08-13 本轮记录

- 论文表核验批次：直连 arXiv HTTP 200，GitHub 请求 0 次。从原文补齐 AASIST、RawGAT-ST、Raw-PC-DARTS、SafeEar、Codecfake、XLSR-MamBo、MixFake、LipForensics、RealForensics、FTCN、AltFreezing、FakeSTormer、PwTF-DVD、VLAForge、AuViRe 的表号与条件。快照：`research/source-snapshots/audio-video-paper-tables-2026-08-13.md`。
- 升级为 `已核验`：音频 AASIST、RawGAT-ST、Raw-PC-DARTS、XLSR-MamBo；视频 LipForensics、RealForensics、PwTF-DVD、VLAForge、AuViRe。当时 10 个音视频方向仍为 `深核验`；同日后续批次已将稀缺六方向改为 `完成（稀缺）`，并增补 GenConViT、DiMoDif 为已核验。
- 新建 `research/datasets/audio.md` 与 `research/datasets/video.md`。稀缺方向未新增官方检测器；快照：`research/source-snapshots/audio-video-scarce-directions-2026-08-13.md`。Q3 分赛道短名单写入 `benchmark-mapping.md` 与音视频报告。
- 本轮先只复核既有 `source-snapshots/`，随后在音视频补缺批次尝试 1 次 GitHub `rate_limit` 请求；连接在接收阶段关闭，未获得 API rate-limit 响应或剩余配额数字。按规则停止后续 GitHub 请求，剩余配额保持未知。
- 音频和视频报告补充了可直接进入后续基准表的已绑定指标范围，并明确闭集、跨域、鲁棒性和 Codabench 结果不可合并排名。
- 音频和视频各细分方向在论文表批次结束时仍为 `深核验`；同日报告重构后，核心方向继续 `深核验`，稀缺六方向改为 `完成（稀缺）`。
- 本轮本地审计快照：`research/source-snapshots/local-audio-video-audit-2026-08-13.md`
- 本轮代理搜索快照：`research/source-snapshots/audio-video-gap-discovery-2026-08-13.md`。本批次共尝试 3 次 GitHub API 请求（1 次 rate-limit、2 次搜索）；第 2 个搜索请求传输失败，最后可确认的剩余配额为搜索前的 58，搜索后精确值未知，已停止后续 GitHub 请求。
- 本轮候选核验快照：`research/source-snapshots/audio-video-gap-verification-2026-08-13.md`。新增核验的两个候选均缺作者/机构对应关系或绑定指标，不进入主清单；本批次最后可见核心剩余配额为 53、搜索资源为 8，未收到 429，已停止后续 GitHub 请求。
- 本轮定向搜索快照：`research/source-snapshots/audio-video-gap-search-2026-08-13.md`。新增 1 次 rate-limit 和 2 次搜索；搜索剩余头降至 4、3，未获得可核验的官方新增方案，已停止 GitHub 请求。
- 认证 API 补缺快照：`research/source-snapshots/authenticated-audio-video-2026-08-13.md`。本批次 11 次请求均成功，核心配额从 5000 保持至 4990；新增 Raw-PC-DARTS、WavLM voice deepfake detection、DiMoDif，均保持部分核验，未改变完成状态。
- 音频和视频报告已改为测试人员决策卡 + 赛道入准表；核心方向仍为 `深核验`（TTS 4/6、扰动 1/6、换脸 5/6、时序 2/6）。稀缺六方向按“不可补足原因 + 恢复条件”标记为 `完成（稀缺）`，**不表示专项精度表可开测**。
- 本轮从本地 arXiv PDF 补齐：AASIST Table 1 逐攻击 EER；DiMoDif Table 3–9 绝对 AUC/AP（升为已核验）；GenConViT Table IV–VI 逐数据集 Acc/AUC/F1（升为已核验，仅 in-domain 另表）。未访问 GitHub。
- 升级为 `已核验` 累计：音频 AASIST、RawGAT-ST、Raw-PC-DARTS、XLSR-MamBo；视频 LipForensics、RealForensics、PwTF-DVD、VLAForge、GenConViT、AuViRe、DiMoDif。
- 本轮网络请求记录：计划 1 次认证 `rate_limit` 请求；通过代理 `LAB_HTTP_PROXY` 在接收阶段断开，未返回 HTTP 状态、rate-limit 信息或新证据。按规则停止后续 GitHub 请求；本轮请求次数为 1，剩余配额无法确认，不能用历史配额替代本轮确认。
- 重新联网尝试记录：计划 1 次认证 `rate_limit` 请求；通过代理 `LAB_HTTP_PROXY` 再次在接收阶段断开，未返回 HTTP 状态、rate-limit 信息或新证据。未发起搜索、仓库元数据或 raw 文件请求；本次 GitHub 请求次数为 1，因配额无法确认而停止后续请求。
- curl 代理尝试记录：计划 1 次认证 `rate_limit` 请求；`curl.exe` 通过 `LAB_HTTP_PROXY` 仅收到代理隧道的 `HTTP/1.1 200 Connection established`，随后 TLS 握手失败，错误为 `SEC_E_NO_CREDENTIALS (0x8009030e)`。未获得 GitHub API HTTP 状态、rate-limit 信息或新证据；未发起搜索和仓库读取，本次请求次数为 1，按规则停止后续 GitHub 请求。
- 终端连通性复试记录：计划 1 次认证 `rate_limit` 请求；当前执行环境通过 `Invoke-RestMethod` 经 `LAB_HTTP_PROXY` 仍在接收阶段断开，未返回 GitHub HTTP 状态或 rate-limit 字段。未发起搜索和仓库读取，本次请求次数为 1；由于配额无法确认，停止后续 GitHub 请求。用户终端的独立 HTTP 200 结果未在本执行环境中复现。
- 来源策略调整：新增 `research/source-acquisition-alternatives.md`。后续优先使用作者/机构项目页、论文原文和附录、Zenodo、作者或机构 Hugging Face、GitLab/机构 Git 服务；Papers with Code、搜索摘要和未确认镜像仅作发现线索。该调整不降低官方归属、许可证、实现类型和指标条件要求，也不改变覆盖矩阵状态。
- 替代来源核验记录：新增 `research/source-snapshots/alternative-audio-video-sources-2026-08-13.md`。本批次未访问 GitHub（请求 0 次）；非 GitHub 只读请求可确认记录为 9 次：arXiv 2 次 HTTP 200，CVF 2 次 HTTP 404，Zenodo 2 次（1 次连接关闭、1 次 HTTP 200），Hugging Face 1 次 HTTP 200，OpenReview 1 次 HTTP 403，Semantic Scholar 1 次 HTTP 429。仅补强 Raw-PC-DARTS（arXiv:2107.12212v2）和 DiMoDif（arXiv:2411.10193v2）的论文/作者可追溯性；没有新增完全核验方案，音视频覆盖状态不变。
- 本阶段本地一致性修订：将 Raw-PC-DARTS 在音频报告中的“官方完整音频基线”改为“官方候选基线”，与其 `部分核验` 状态及证据台账一致；未新增模型、指标或网络证据，未改变音频/视频覆盖矩阵。
- 缺口收敛批次：新增 `research/source-snapshots/audio-video-gap-closure-2026-08-13.md`。计划 6 次非 GitHub arXiv 请求，实际 6 次均连接失败，未返回 HTTP 状态或论文证据；GitHub 请求 0 次，按规则停止重试。基于既有本地快照整理了 Codecfake/SafeEar/MixFake 的音频协议边界，以及 RealForensics/LipForensics/FakeSTormer/AuViRe/ICS-AV 的视频任务分层；没有新增完全核验方案，音视频矩阵仍保持深核验。
