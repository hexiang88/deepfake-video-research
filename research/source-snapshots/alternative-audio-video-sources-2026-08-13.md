# 音视频替代来源核验快照（2026-08-13）

## 批次边界

- 本批次未访问 GitHub，GitHub 请求次数为 `0`；未使用 GitHub Token。
- 目标是验证作者/机构论文与候选实现的对应关系，并寻找不依赖 GitHub 的原始来源。
- 论文存在不等于代码开源；本快照不据此提升候选的核验等级。

## 请求记录

以下为本批次可确认的非 GitHub 只读请求记录：

| 来源 | 请求次数 | 结果 | 处理 |
|---|---:|---|---|
| arXiv export API | 2 | HTTP 200 | 确认 Raw-PC-DARTS 与 DiMoDif 的标题、作者和版本信息 |
| CVF Open Access | 2 | HTTP 404 | 不据此判断论文或实现不存在 |
| Zenodo API | 2 | 音频查询连接关闭；视频查询 HTTP 200 | 未确认作者/机构归属，不采信为官方实现 |
| Hugging Face Models API | 1 | HTTP 200 | 命中个人或未确认组织账号，许可证与作者对应关系不足，仅作线索 |
| OpenReview API | 1 | HTTP 403 | 停止继续请求，不作不存在判断 |
| Semantic Scholar API | 1 | HTTP 429 | 停止继续请求，不作不存在判断 |
| **合计** | **9** |  |  |

## 已确认的原始论文来源

### Raw-PC-DARTS

- 原始论文：[arXiv:2107.12212v2](https://arxiv.org/abs/2107.12212)
- 标题：*Raw Differentiable Architecture Search for Speech Deepfake and Spoofing Detection*
- 作者：Wanying Ge、Jose Patino、Massimiliano Todisco、Nicholas Evans
- arXiv 版本日期：2021-07-26
- 论文来源只能确认论文和作者关系；代码开放范围、许可证、数据划分和 README 证据仍以已有官方仓库快照为准。
- 当前状态：官方候选、部分核验；不计入完全核验数量和精度排名。

### DiMoDif

- 原始论文：[arXiv:2411.10193v2](https://arxiv.org/abs/2411.10193)
- 标题：*DiMoDif: Discourse Modality-information Differentiation for Audio-visual Deepfake Detection and Localization*
- 作者：Christos Koutlis、Symeon Papadopoulos
- arXiv 版本日期：2024-11-15
- 论文来源只能确认论文和作者关系；绝对 AUC/AP、完整划分和扰动参数仍未从可采信的公开原始证据中补齐。
- 当前状态：官方候选、部分核验；不计入完全核验数量和精度排名。

## 未采信来源

- Zenodo 通用检索结果未确认上传者与作者/机构对应关系，不能作为官方代码或权重证据。
- Hugging Face 命中模型均未建立作者/机构官方对应关系，且许可证字段为空或不足，不能进入正式候选表。
- CVF 的 404、OpenReview 的 403 和 Semantic Scholar 的 429 只表示本次访问结果，不表示论文、模型或实现不存在。

## 对覆盖状态的影响

本批次只补强了 Raw-PC-DARTS 和 DiMoDif 的论文可追溯性，没有新增满足“官方实现、许可证/开放范围、绑定数据条件和可复核指标”全部要求的完全核验方案。音频、视频各细分方向仍保持未完成/深核验状态。
