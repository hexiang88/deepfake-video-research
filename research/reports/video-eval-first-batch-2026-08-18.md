# 视频检测复测台账（首批 · 换脸）

记录日期：2026-08-18。评测机：`eval-host`，工作区 `/data/USER/deepfake-bench`。账号 `USER`。  
LipForensics / RealForensics 全量指标于 2026-08-20 按各模型 `scores.csv` 补记。  
RealForensics leave-one-out（测试集 `ffpp_official_test_available`）于 2026-08-25 按本机评测日志补记。  
Talking Face / 唇音 / TFL（AuViRe、DiMoDif）于 2026-08-25 开始本机部署与评测闸门；**不得**并入 §3.1。AuViRe 与 DiMoDif 的 DFD/TFL 本机子集数字于 2026-08-26 写入 §4.2 / §4.3。  
GenConViT 于 2026-08-26 完成 `mentor_swap_200` 独立 custom 评测，结果于 2026-08-27 从测试机回传并经本机复核后写入 §3.4；论文 in-domain 复现仍未完成。  
调研口径仍以 `[video.md](video.md)` 为准。本文件只记**本机部署与复测**，不把论文表抄成复测结果。

**禁止：** 混合 c0/c23、帧级/视频级、DFDC 全量与 preview、把空表填成论文数字。跨数据集、跨操纵、in-domain **分表**，禁止合成总榜。

---



## 1. 导师发布的检测方案（本批范围）

下表对应导师给出的方案卡。工程成熟度/风险摘自该卡；绑定论文数字见 `[video.md](video.md)` §4。


| 方案            | 角色                    | 首选用途                          | 本机部署    | 复测安排                                                                                                            |
| ------------- | --------------------- | ----------------------------- | ------- | --------------------------------------------------------------------------------------------------------------- |
| LipForensics  | 嘴部时空换脸检测              | FF++ → 跨数据集 AUC 基线            | **已部署** | **首批测**                                                                                                         |
| RealForensics | 真实说话脸自监督              | 跨操纵 + 跨数据集；重演赛道用 F2F/NT       | **已部署** | **首批测**                                                                                                         |
| PwTF-DVD      | 像素时间频率                | 时序 / 跨数据集                     | **已部署** | **首批测**                                                                                                         |
| VLAForge      | 视觉语言 + 身份先验           | 帧级 / 视频级跨数据集                  | **不可用** | **取消检测计划**                                                                                                      |
| AuViRe        | 跨模态语音表征重建             | Talking Face DFD + TFL；唇音联合候选 | **已部署** | **本机子集已评** §4.2 / §4.3；无 FakeAVCeleb 行                                                                          |
| DiMoDif       | 音视频语音表征差异             | Talking Face DFD + TFL；唇音联合候选 | **已部署** | **本机子集已评** §4.2 / §4.3；骨干 AutoAVSR（Ma et al.），**不能**复用 AuViRe AV-Hubert 特征；RVFA 列必留；FakeAVCeleb 未核验前为 candidate |
| GenConViT     | ConvNeXt 换脸 in-domain | 混合训练同域 Acc/AUC/F1             | **已部署** | `mentor_swap_200` custom 评测已完成，见 §3.4；OOD 状态未核验，**不得**与 §3.1 合并；论文 in-domain 仍待补                                |


**VLAForge 不可用原因：** 官方 README Step 3 的 Google Drive 链接为空；Release / Hugging Face / 仓库内均无预训练检测器权重。Issues [#2](https://github.com/mala-lab/VLAForge/issues/2)、[#4](https://github.com/mala-lab/VLAForge/issues/4) 已有人问，作者未回复。结果列记 `weights_missing`，不编造数字。2026-08-18 起取消本机检测计划，并清理服务器残留。

---



## 2. 首批：三个换脸检测器（GenConViT 独立补测见 §3.4）

数据：导师目录 `/data/data_videos`（真约 1526 / 假约 17724）。**不跑全量。** 抽样 **200 真 + 200 假**，`seed=20260818`，软链在 `datasets/mentor_swap_200/{real,fake}`。测试集名 `mentor_swap_200`，不是 Celeb-DF / FF++/ DFDC。官方 FF++ / Celeb-DF 下载已暂停。

GPU：物理 GPU 0 已被占用。命令前 `export CUDA_VISIBLE_DEVICES=1`。yaml 里 `gpu: cuda:0` **不要改**。


| 方案            | conda 解释器                                            | 权重                                                         | 论文对照（视频级 AUC %，非本机结果）                                                     |
| ------------- | ---------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------- |
| LipForensics  | `/home/USER/miniconda3/envs/lipforensics/bin/python`  | `weights/lipforensics/lipforensics_ff.pth`（138M）           | Celeb-DF-v2 82.4、DFDC 73.5、FaceShifter 97.1、DeeperForensics 97.6          |
| RealForensics | `/home/USER/miniconda3/envs/realforensics/bin/python` | `weights/realforensics/realforensics_ff.pth` 等 5 个（各约 83M） | CDF 86.9、DFDC 75.9、FS 99.7、DFo 99.3；leave-one-out DF/FS/F2F/NT 见 video.md |
| PwTF-DVD      | `/home/USER/miniconda3/envs/pwtf_dvd/bin/python`      | `weights/pwtf_dvd/PwTF_weights.pth`（752M，可 `torch.load`）   | CDF 89.7、DFDC 75.2、FS 99.3、DFo 99.4、DFD 97.3                              |


冒烟：`mentor_swap_200_smoke`（8+8），作为全量前置已跑。PwTF 冒烟视频级 AUC **79.6875**（16 条，仅管道检查，不进正式表）。LipForensics / RealForensics 冒烟数字未另记，不编造、不进正式表。

---



## 3. 复测结果（首批三模型 + GenConViT 独立补测）

§3.1 三个首批换脸检测器已按 `scores.csv` 填本机数字（`mentor_swap_200`）。§3.2 / §3.3 已填 RealForensics leave-one-out 本机视频级 AUC（`ffpp_official_test_available`）。§3.4 单列 GenConViT custom 评测；其 OOD 状态未核验，不能补入 §3.1 或论文 in-domain 单元格。**不要**把本机数字换成论文 Table 1，也不要跨表合并。

### 3.1 换脸跨数据集（视频级 AUC）

训练域：权重为官方 FF++c23 预训练（LipForensics++ `lipforensics_ff.pth`++、RealForensics++ `realforensics_ff.pth`++、PwTF-DVD++ `PwTF_weights.pth`++）。测试日期：2026-08-18～20。++  
++测试集：++`mentor_swap_200`++（导师换脸抽样 200 真 + 200 假，seed=20260818）。**不是** Celeb-DF / FF++ / DFDC。

主指标：视频级 AUC。AP 同表并列。本表是该抽样上的本机检测精度，**不是**鲁棒性，**不是**相对论文表的跨数据集泛化，不得合成总榜。

**Acc@th：** LipForensics / RealForensics 为固定 logit>0（≡ sigmoid 0.5），非 val 调参。PwTF-DVD 为 score > 0.5（即原 [Acc@0.5](mailto:Acc@0.5)，数值不变）。均未在独立验证集上选阈值。未提供测试集扫阈值的 best-F1 / EER，附录不补。


| 方案            | 测试集             | n 视频                   | 本机 AUC %  | 本机 AP % | Acc@th %  | 论文对照            | 备注                                      |
| ------------- | --------------- | ---------------------- | --------- | ------- | --------- | --------------- | --------------------------------------- |
| LipForensics  | mentor_swap_200 | 394（200 真 + 194 假）     | 86.44     | 88.17   | 75.38     | 见 video.md，口径不同 | 8+8 冒烟已跑（管道检查，数字不进本表）；**已跑全量**。失败 6 条见下 |
| RealForensics | mentor_swap_200 | 394（200 真 + 194 假）     | 91.28     | 91.55   | 79.44     | 见 video.md，口径不同 | 8+8 冒烟已跑（管道检查，数字不进本表）；**已跑全量**。失败 6 条见下 |
| PwTF-DVD      | mentor_swap_200 | **398**（200 真 + 198 假） | **84.84** | 55.76   | **79.65** | 见 video.md，口径不同 | 见下                                      |
| VLAForge      | —               | —                      | —         | —       | —         | —               | **不可用** / `weights_missing`             |


**LipForensics / RealForensics 共同失败 6 条（均为假视频）**

`f_012_tx_133_141`，`f_014_tx_961_009`，`f_157_521`，`f_158_582`，`f_013_tx_678_027`，`f_130_233_`。  
两模型均为 n=394 = 200 真 + 194 假；`scores.csv` 395 行 = 表头 + 394。`infer.log` FAILED 计数 6。  
相对 PwTF 仅未计入的 `f_130_233_`（ffmpeg：`moov atom not found`）与 `f_158_582`（0 帧），多出 4 条（`f_012_tx_133_141`，`f_014_tx_961_009`，`f_157_521`，`f_013_tx_678_027`）属嘴部裁剪不足 25 帧 / FAN skip，是 data/preprocess，不是缺权重。不要为此重跑全量。

**LipForensics 本机细节**

- 分数文件：`results/logs/lipforensics/cross_dataset/mentor_swap_200/scores.csv`（395 行 = 表头 + 394 条）。
- `score_range=[-22.5477, 57.9114]`，`treat_as_logits=True`，阈值 logit>0（≡ sigmoid 0.5）。
- 混淆矩阵 @ logit>0：tp=105，tn=192，fp=8，fn=89。
- 不得把 86.44 / 88.17 写成 Celeb-DF 或 FF++ 结果。
- P / R / F1 见下方附录。无测试集扫阈值的 best-F1 / EER。

**RealForensics 本机细节**

- 分数文件：`results/logs/realforensics/cross_dataset/mentor_swap_200/scores.csv`（395 行 = 表头 + 394 条）。
- `score_range=[-11.1985, 18.8946]`，`treat_as_logits=True`，阈值 logit>0（≡ sigmoid 0.5）。
- 混淆矩阵 @ logit>0：tp=181，tn=132，fp=68，fn=13。
- 不得把 91.28 / 91.55 写成 Celeb-DF 或 FF++ 结果。
- P / R / F1 见下方附录。无测试集扫阈值的 best-F1 / EER。

**PwTF-DVD 本机细节**

- 分数文件：`results/logs/pwtf_dvd/cross_dataset/mentor_swap_200/scores.csv`（399 行 = 表头 + 398 条）。
- 阈值：score > 0.5 判假。混淆矩阵：TP 141、TN 176、FP 24、FN 57。
- 2 条假视频 **0 帧**，未计入：`f_130_233_`（ffmpeg：`moov atom not found`，文件损坏/未下完）、`f_158_582`（同样 `Processing 0 frames` 后 `IndexError`）。属数据问题，不是权重错误。
- `cross_dataset.json` 目前只有冒烟两条：`mentor_swap_200_smoke` `eval_failed`（08:47 UTC）与 `ok` AUC **79.6875**（09:39 UTC）。**尚无** `mentor_swap_200` 全量行；398 条指标以 `scores.csv` 为准。
- 不得把 84.84 写成 Celeb-DF 或 FF++ 结果。
- AP 已列入主表（55.76）。P / R / F1 / best-F1 / EER 见下方附录。Acc@th 仍为 score > 0.5。

同一行只写一个测试集；多测试集复制行。DFDC 若为 preview，测试集名必须写 `dfdc_preview`。

#### 附录：PwTF-DVD 补充精度（仅 `mentor_swap_200`）

由同一份 `scores.csv` 计算。这是 **PwTF-DVD** 在一份导师换脸抽样上的检测精度，无额外降质。  
**不是**鲁棒性。**不是**跨数据集泛化。**不是** Celeb-DF / FF++ / DFDC。不得与论文表或未填模型混排，也不进总榜。


| 项                           | 绑定条件 / 数值                                                         |
| --------------------------- | ----------------------------------------------------------------- |
| 数据集                         | `mentor_swap_200`（导师提供换脸抽样，seed=20260818；计划 200 真 + 200 假，实评 398） |
| 模型                          | PwTF-DVD（`PwTF_weights.pth`，官方 FF++ c23 预训练）                      |
| 条件                          | 无额外降质                                                             |
| n                           | 398（real=200，fake=198）                                            |
| AP %                        | 55.76                                                             |
| P / R / F1 @0.5 %           | 85.45 / 71.21 / 77.69                                             |
| [Acc@0.5](mailto:Acc@0.5) % | 79.65（与主表相同）                                                      |
| 混淆矩阵 @0.5                   | tp=141，tn=176，fp=24，fn=57                                         |
| best-F1 %（附录）               | 79.51；th=0.2630；tp/tn/fp/fn = 163/151/49/35                       |
| EER %（附录）                   | 21.11；th=0.3151；FPR=0.2100，FNR=0.2121                             |


**口径：** Acc / [F1@0.5](mailto:F1@0.5) 的阈值 0.5 **未**在独立验证集上选定。best-F1 与 EER 在**本测试集**上扫阈值，仅作附录，不得当作选定阈值后的正式精度。主指标仍为视频级 AUC（主表 84.84%）。

#### 附录：LipForensics 补充精度（仅 `mentor_swap_200`）

由同一份 `scores.csv` 计算。这是 **LipForensics** 在一份导师换脸抽样上的检测精度，无额外降质。  
**不是**鲁棒性。**不是**跨数据集泛化。**不是** Celeb-DF / FF++ / DFDC。不得与论文表混排，也不进总榜。


| 项                      | 绑定条件 / 数值                                                         |
| ---------------------- | ----------------------------------------------------------------- |
| 数据集                    | `mentor_swap_200`（导师提供换脸抽样，seed=20260818；计划 200 真 + 200 假，实评 394） |
| 模型                     | LipForensics（`lipforensics_ff.pth`，官方 FF++ c23 预训练）               |
| 条件                     | 无额外降质                                                             |
| n                      | 394（real=200，fake=194）                                            |
| AP %                   | 88.17                                                             |
| P / R / F1 @ logit>0 % | 92.92 / 54.12 / 68.40                                             |
| Acc@th %               | 75.38（与主表相同）                                                      |
| 混淆矩阵 @ logit>0         | tp=105，tn=192，fp=8，fn=89                                          |
| 失败视频                   | 6 条假视频，与 RealForensics 相同，见上文共同失败列表                               |


**口径：** Acc / P / R / F1 使用固定 logit>0（≡ sigmoid 0.5），**非** val 调参，也**未**在本测试集上扫阈值。未提供 best-F1 / EER，本附录不列。主指标仍为视频级 AUC（主表 86.44%）。

#### 附录：RealForensics 补充精度（仅 `mentor_swap_200`）

由同一份 `scores.csv` 计算。这是 **RealForensics** 在一份导师换脸抽样上的检测精度，无额外降质。  
**不是**鲁棒性。**不是**跨数据集泛化。**不是** Celeb-DF / FF++ / DFDC。不得与论文表混排，也不进总榜。


| 项                      | 绑定条件 / 数值                                                         |
| ---------------------- | ----------------------------------------------------------------- |
| 数据集                    | `mentor_swap_200`（导师提供换脸抽样，seed=20260818；计划 200 真 + 200 假，实评 394） |
| 模型                     | RealForensics（`realforensics_ff.pth`，官方 FF++ c23 预训练）             |
| 条件                     | 无额外降质                                                             |
| n                      | 394（real=200，fake=194）                                            |
| AP %                   | 91.55                                                             |
| P / R / F1 @ logit>0 % | 72.69 / 93.30 / 81.72                                             |
| Acc@th %               | 79.44（与主表相同）                                                      |
| 混淆矩阵 @ logit>0         | tp=181，tn=132，fp=68，fn=13                                         |
| 失败视频                   | 6 条假视频，与 LipForensics 相同，见上文共同失败列表                                |


**口径：** Acc / P / R / F1 使用固定 logit>0（≡ sigmoid 0.5），**非** val 调参，也**未**在本测试集上扫阈值。未提供 best-F1 / EER，本附录不列。主指标仍为视频级 AUC（主表 91.28%）。

### 3.2 换脸跨操纵（仅 RealForensics，leave-one-out）

测试日期：2026-08-25。  
测试集：`ffpp_official_test_available`。来源：导师机 LipForensics `datasets/FF++` + `MyDataSets/Real/real_ff_youtube`，按官方 `Forensics/splits/test.json` ID 过滤到磁盘上存在的视频。**不是** `mentor_swap_200`，**不是**官方 test 全量 140+140，**不是** Celeb-DF。  
压缩：**导师 FF++ 布局，路径未标 c23**。论文对照列为 Table 1（c23），不把本机单元格改成论文数字。  
官方 test 为每类 140 真 + 140 假；缺假视频（Deepfakes 缺 23、FaceSwap 缺 18、Face2Face 缺 23、NeuralTextures 缺 28）是因为导师 FF++ 树不完整。协议仍为 **test-split only**，未使用各类型 800 条 train dump。  
权重：各行 `realforensics_allbut*.pth`（**不用** `realforensics_ff.pth`）。只评 Real + 留出类型，故不另记 Aggregate_AUC（与类型 AUC 相同）。  
主指标：视频级 AUC。本表**不是**鲁棒性，**不得**与 §3.1 `mentor_swap_200` 合并。Acc_Inclreal（logit>0）仅附录，非 val 调参。


| 留出操纵           | 测试集                          | n 视频               | 本机 AUC % | 论文对照  | 备注                                                                    |
| -------------- | ---------------------------- | ------------------ | -------- | ----- | --------------------------------------------------------------------- |
| Deepfakes      | ffpp_official_test_available | 257（140 真 + 117 假） | 98.43    | 100.0 | `realforensics_allbutdf.pth`；test-available 子集；非 train 视频             |
| FaceSwap       | ffpp_official_test_available | 262（140 真 + 122 假） | 93.69    | 97.1  | `realforensics_allbutfs.pth`；test-available 子集；非 train 视频             |
| Face2Face      | ffpp_official_test_available | 257（140 真 + 117 假） | 99.26    | 99.7  | `realforensics_allbutf2f.pth`；test-available 子集；非 train 视频；重演类，见 §3.3 |
| NeuralTextures | ffpp_official_test_available | 252（140 真 + 112 假） | 95.05    | 99.2  | `realforensics_allbutnt.pth`；test-available 子集；非 train 视频；重演类，见 §3.3  |




#### 附录：RealForensics leave-one-out Acc（仅 `ffpp_official_test_available`）

由官方 `stage2/eval.py` 打印的 `*_Acc_Inclreal`（logit>0 ≡ sigmoid 0.5）。**非 val 调参**，也未在本测试集上扫阈值。不进主表。主指标仍为视频级 AUC。


| 留出操纵           | 权重                          | n                  | Acc_Inclreal % |
| -------------- | --------------------------- | ------------------ | -------------- |
| Deepfakes      | realforensics_allbutdf.pth  | 257（140 真 + 117 假） | 92.61          |
| FaceSwap       | realforensics_allbutfs.pth  | 262（140 真 + 122 假） | 84.35          |
| Face2Face      | realforensics_allbutf2f.pth | 257（140 真 + 117 假） | 96.50          |
| NeuralTextures | realforensics_allbutnt.pth  | 252（140 真 + 112 假） | 80.56          |




### 3.3 人脸重演（须备注，不与 DF/FS 合成总分）

备注：候选为 RealForensics；评测对象是 FF++Face2Face 与 NeuralTextures，不是独立重演检测器。表题写成「FF++ 重演类操纵（联合/相邻模型）」。  
数字与 §3.2 同行：测试集 `ffpp_official_test_available`，**不是** `mentor_swap_200`，**不是**论文 Table 1 替换值。LipForensics 本机 leave-one-out 无数字，保持可选空行。


| 方案               | F2F AUC % | NT AUC % | n 视频                                         | 备注                                                                 |
| ---------------- | --------- | -------- | -------------------------------------------- | ------------------------------------------------------------------ |
| RealForensics    | 99.26     | 95.05    | F2F 257（140 真 + 117 假）；NT 252（140 真 + 112 假） | 候选为 RealForensics；评测对象是 FF++ Face2Face 与 NeuralTextures，不是独立重演检测器。 |
| LipForensics（辅助） |           |          |                                              | 可选                                                                 |




### 3.4 GenConViT custom evaluation（OOD status unverified；不并入 §3.1）

**报告标签（固定）：** `mentor_swap_200 custom evaluation / OOD status unverified`。测试集仍为导师目录的 200 真 + 200 假固定抽样，`seed=20260818`；不是 Celeb-DF、FF++、DFDC，也未核验与 GenConViT 作者训练域、测试 split 或压缩档一致。因此本节只构成内部 custom 评测证据，**不是**论文 Table IV–VI 复现，不写入 `indomain.json`，也不与 §3.1 三模型形成总榜。

运行日期为 2026-08-26；模型按官方仓库 commit `2c1d0bd7eecea94926595781a744e3f4b8b55290` 严格加载 ED（588 keys）与 VAE（614 keys），禁用 timm 额外预训练下载。每视频抽 15 帧，官方人脸裁剪与分数方向，FP32，固定阈值 `score >= 0.5`（fake 为正类，阈值未调优）；失败视频排除并显式列出，**未**用 0.5 补分。


| 状态          | 请求 / 成功        | 成功分层        | Coverage % | AUC %（95% CI）          | AP %（95% CI）           | [Accuracy@0.5](mailto:Accuracy@0.5) %（95% CI） | [macro-F1@0.5](mailto:macro-F1@0.5) %（95% CI） | EER %（95% CI）          |
| ----------- | -------------- | ----------- | ---------- | ---------------------- | ---------------------- | --------------------------------------------- | --------------------------------------------- | ---------------------- |
| **partial** | 400 / 393；失败 7 | 真 196；假 197 | 98.25      | **85.54**（81.65–89.07） | **87.27**（83.79–90.32） | **76.84**（72.77–80.66）                        | **76.71**（72.57–80.62）                        | **20.92**（17.35–25.51） |



| 固定阈值补充项                                              | 本机结果                |
| ---------------------------------------------------- | ------------------- |
| fake [Precision@0.5](mailto:Precision@0.5) %（95% CI） | 81.93（76.79–86.93）  |
| fake [Recall@0.5](mailto:Recall@0.5) %（95% CI）       | 69.04（62.94–75.13）  |
| 混淆矩阵（TP / TN / FP / FN）                              | 136 / 166 / 30 / 61 |


置信区间为对成功视频按类别分层 bootstrap 2,000 次的 95% 区间，bootstrap seed 为 `20260818`，2,000 次均有效；区间仅描述 393 个成功视频上的抽样不确定性，**没有**纳入 7 个处理失败视频造成的选择偏差。`scores.csv` 独立复算与 `summary.json` 一致；400 条 manifest、400 条 prediction、393 条 score 均为唯一视频 ID。

失败清单（4 真 + 3 假）：

- `real/r_032_0e3d5890f471921ad375c607a38d1ae8.mp4`、`real/r_047_-Z1lkcEEF_w_1.mp4`、`real/r_080_Dus8r5l5cys_0.mp4`、`real/r_095_KDXK5R3f01I_0.mp4`：15 帧均未检测到人脸（`preprocess/no_face`）。
- `fake/f_130_233_.mp4`、`fake/f_156_464.mp4`、`fake/f_158_582.mp4`：解码失败（`decode/decode_error`）；其中 `f_130_233_`、`f_158_582` 也在 PwTF-DVD 运行中因无有效视频帧失败，`f_156_464` 为本次 decord/FFmpeg filter graph 错误。

复现与审计信息：

- 环境：物理 GPU 2，NVIDIA GeForce RTX 3090；PyTorch 2.1.2+cu118、torchvision 0.16.2+cu118、CUDA 11.8、dlib 19.24.6（CNN/CUDA）、decord 0.6.0、NumPy 1.26.4、timm 0.6.5；确定性算法开启。
- 权重：Hugging Face revision `32d6e9e3c931a37971cc756da706cf1eef643372`；ED SHA256 `86f0c2e875016435def7d031b357bda5dc0061367290d73de121186df3f03f8c`，VAE SHA256 `53c627c82d1439fc80e18ac462c1ed6969a3babe5376124a5c38d1c0c88c9042`。官方代码为 MIT；权重标注 CC-BY-NC-4.0，结果元数据保留该限制。
- 数据 manifest 内容指纹：`cc92b6439abc5aba583d6ef082ed227dd817c2e5f12b34db9e3fe078ba8b785c`。回传文件字节 SHA256：`scores.csv` 为 `9527d82bc606147914c7a685725a2dce29e5fafb5f4c4bdc98d7881d1e23d539`，`summary.json` 为 `275c68a8e24dd6c19219d77cc6d71e790c1edca94a0f866d1ebed7e6fc63a493`。
- 运行耗时 357.67 秒（2026-08-26 18:29:25Z–18:35:23Z）。冒烟集 8 真 + 8 假全部成功；同一输入、seed、GPU、环境的重复抽查 16 条分数逐条一致（`atol=0.0`）。冒烟数字只作为管道与重复性证据，不作为性能证据。
- 回传证据目录：`path\to\genconvit-results\mentor_swap_200`，包含 `summary.json`、`scores.csv`、`predictions.csv`、`failures.json`、`dataset_manifest.csv`、`progress.jsonl`、`eval.log`。官方 clone 在运行前后均为 clean。

---



## 4. Talking Face / 唇音 / TFL（第二批 · AuViRe、DiMoDif）

记录日期：2026-08-25 起。评测机仍是 `eval-host`，工作区 `/data/USER/deepfake-bench`，账号 `USER`。  
AuViRe 于 2026-08-26 用官方 `scripts/test.py` 在 **分层子集** 上评完（特征为 AV-Hubert `base_lrs3_iter4.pt`）。DiMoDif 于同日用 AutoAVSR（Ma et al. `LRS3_V_WER19.1` + `LRS3_A_WER1.0`，detector `mediapipe`）特征与 `*_whole.pth`（AVD）评完同一批清单；**不能**复用 AV-Hubert `features.npz`。yaml `gpu: cuda:0` **未改**（`CUDA_VISIBLE_DEVICES=1`）。

**主报口径（2026-08-26）：AVD 优先于 LAV。** AV-Deepfake1M 是 LAV-DF 同一任务线上的升级集（更多说话人、更新 TTS/唇形生成器、LLM 改稿含插入/删除）。本机 Talking Face / 唇音 / TFL **主看 AVD 训练头 →** `avd1m_official_val_subset_800`（AuViRe 实 n=792，DiMoDif 实 n=800；validation 子集，非 Codabench）。LAV 闭集与 LAV↔AVD 跨域格只作迁移诊断，不要当第二条赛道或第二个检测器。未知威胁若只能上一个 AuViRe 头，用 AVD 训练权重。方案是否互补，对照 **AuViRe vs DiMoDif**，不要对照两个 AuViRe 训练域。改稿方式是造假数据生成步骤（改口播稿再 TTS/唇形合成），不是检测器训练超参。

**本批可报 / 不可报：** 可报官方协议可复现，以及已知跨域失效边界（尤其 LAV 训练头 → AVD 的 TFL）。导师未提供说话人脸/唇音业务集；公开集几乎没有中文野外口播。因此**不能**写可部署、已覆盖真实业务、唇音同步已过关。换脸业务向证据仍只用 `mentor_swap_200`；TFL **不能**用导师换脸集补（没有伪造区间标注）。闭集高是复现，不是野外；LAV↔AVD 是相关域迁移，不是完全 OOD。结果 JSON 只写 Talking Face / TFL 分表，**不要**写入 `cross_dataset.json`。

**禁止：** 并入 §3.1 换脸 AUC；把唇音写成毫秒/帧偏移；丢掉 DiMoDif RVFA 列；给 AuViRe 编 FakeAVCeleb 行；把 wav2lip / MyDataSets 生成器目录或 34 万条当官方 LAV-DF / FakeAVCeleb / TFL；把 clone 自带的 `results/` 论文 JSON 抄进本机格；把 LAV 闭集 99 写成 Talking Face 主结论。

**唇音备注（表头复制）：** 候选为 AuViRe / DiMoDif；指标为音视频检测 AUC 与伪造区间 AP，不是唇音偏移毫秒/帧误差。

ICS-AV 只对照、本批不部署。GenConViT 的 custom 评测已在 §3.4 完成；作者精确 split 与压缩档未核验，论文 in-domain 复现仍是后续另表。

GPU：`export CUDA_VISIBLE_DEVICES=1`（或 2/3）。yaml `gpu: cuda:0` **不要改**。解释器必须是 conda `auvire` / `dimodif`（Python 3.10），**禁止** base 3.13。

### 4.0 部署闸门（执行后把状态改成 verified / weights_missing / 待核验）


| 项                                 | 期望                                                                                                                  | 本机状态                                                                                                                                                                                          |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| conda `auvire` Python 3.10        | `/home/USER/miniconda3/envs/auvire/bin/python`，`python -V` 非 3.13                                                    | **verified**（3.10.20；torch 2.4.1+cu121）                                                                                                                                                       |
| AuViRe 检测器权重                      | Zenodo [17698401](https://zenodo.org/records/17698401)：LAV-DF 145514674 / AVD1M 107377358；md5 与官方一致；`torch.load` 能开 | **verified**                                                                                                                                                                                  |
| AV-HuBERT Base penultimate / LRS3 | `src/avhubert/base_lrs3_iter4.pt`（1237095857 字节，含 optimizer）；`encoder.layers` **12**                                | **verified**                                                                                                                                                                                  |
| conda `dimodif` Python 3.10       | `/home/USER/miniconda3/envs/dimodif/bin/python`                                                                      | **verified**（torch 2.5.1+cu121；13 个 pth `ok`，含 `*_rvfa.pth`）                                                                                                                                  |
| DiMoDif `ckpt/*.pth`              | DFD 约 4MB，TFL 约 80MB，非 LFS 指针                                                                                       | **verified**                                                                                                                                                                                  |
| 仓库自带 JSON                         | 已挪到 `$DATA/results/paper_json/{auvire,dimodif}/`                                                                    | **verified**。AuViRe 本机：`models/AuViRe/results/test` 与 `$DATA/results/auvire_subset_2026-08-26`。DiMoDif 本机：`models/DiMoDif/results/generalization` 与 `$DATA/results/dimodif_subset_2026-08-26` |




### 4.1 数据闸门

2026-08-25 **eval-host** 复检：`/data/MENTOR_DATASETS` **不存在**。该路径属于导师机 **MENTOR_HOST**，从未假定挂在 eval-host。这只说明评测机没有该挂载，**不能**证明实验室已无 FakeAVCeleb。首批换脸拷贝在 `/data/USER/deepfake-bench/datasets/`（`mentor_swap_200` 等）。根盘 13T 已用 11T，剩 **1.6T（87%）**，禁止下 AVD1M **train / hidden test**、FakeAVCeleb 全量、DFDC 全量。

**已落地子集（seed=**`20260825`**，每类拟 200）：**


| 测试集名                             | 划分                                     | 计划 n | AuViRe 特征 n | DiMoDif 特征 n | 说明                                                                                                                    |
| -------------------------------- | -------------------------------------- | ---- | ----------- | ------------ | --------------------------------------------------------------------------------------------------------------------- |
| `lavdf_official_test_subset_800` | LAV-DF 官方 **test**                     | 800  | **795**     | **800**      | AuViRe 缺 5 条（只改音频 2、音视频都改 3）：`test/095753.mp4`、`133926`、`075811`、`134020`、`094859`。DiMoDif AutoAVSR 这 5 条抽成功。不进覆盖图主视觉 |
| `avd1m_official_val_subset_800`  | AVD1M 官方 **val**（磁盘 57340 条，非论文 54730） | 800  | **792**     | **800**      | AuViRe 抽特征失败 8 条；DiMoDif 800 全抽出。**不是** Codabench test                                                                |


不要评 `fake_fakeavceleb` 990 作为 AuViRe 行。


| 数据集                         | 官方协议角色                        | 路径口径                                                       | 状态                                                     |
| --------------------------- | ----------------------------- | ---------------------------------------------------------- | ------------------------------------------------------ |
| LAV-DF                      | 前代对照；跨域格用                     | `$DATA/datasets/LAV-DF`（仅 test + `metadata.min.json`）      | AuViRe / DiMoDif **已评**（不进覆盖图主视觉）                      |
| AV-Deepfake1M               | 本地评 **validation**；**本批主测试域** | `$DATA/datasets/AV-Deepfake1M/{val,val_metadata.json}`，20G | AuViRe / DiMoDif **已评**（优先报此行；DiMoDif 用 `*_whole.pth`） |
| FakeAVCeleb 官方              | **仅 DiMoDif**；AuViRe **无此行**  | 需 `FakeAVCeleb_v1.2` + `meta_data.csv` + RVFA/FV           | **未部署**                                                |
| `fake_fakeavceleb` ~990 mp4 | 仅 **candidate**               | 导师机路径                                                      | 待核验；不能当 verified FakeAVCeleb                           |


无音频流 → 不能跑 AuViRe/DiMoDif。不要评 MyDataSets 全量。不要把 wav2lip 文件夹当 TFL。

### 4.2 Talking Face DFD（视频级；不与 §3.1 合并）

论文对照为仓库全量 JSON / 论文表（见 `[auvire-metrics-2026-08-12.md](../source-snapshots/auvire-metrics-2026-08-12.md)` 与 `[video.md](video.md)` Table 9），**不要**把本机子集格改成论文数字，也**不要**宣称复现了全量 test/val。`tacc` 进附录，主指标 **tauc**。日期：2026-08-26。`GPU`：`CUDA_VISIBLE_DEVICES=1`。

**读表顺序：**先看 **AVD 训练头 →** `avd1m_official_val_subset_800`：AuViRe AUC **100.00**（n=792）、DiMoDif AUC **99.00**（n=800）。两行都是 val 子集，不对标 Codabench / 论文全量。LAV 同行与跨域行不要放进覆盖图主视觉。方案互补看这两行，不要看 AuViRe 的 LAV 头 vs AVD 头。


| 方案      | 训练域           | 测试集                              | n   | 本机 AUC %   | 本机 AP % | 论文/仓库对照                                        | 状态                                  |
| ------- | ------------- | -------------------------------- | --- | ---------- | ------- | ---------------------------------------------- | ----------------------------------- |
| AuViRe  | lav_df        | `lavdf_official_test_subset_800` | 795 | **99.84**  | 99.96   | 仓库 tauc 99.94（全量 test 26100）                   | 本机子集；不进主视觉                          |
| AuViRe  | lav_df        | `avd1m_official_val_subset_800`  | 792 | **65.14**  | 86.06   | 仓库 tauc 65.71（全量 val）                          | 跨域；能力边界                             |
| AuViRe  | av_deepfake1m | `lavdf_official_test_subset_800` | 795 | **92.70**  | 97.72   | 仓库 tauc 93.33                                  | 跨域                                  |
| AuViRe  | av_deepfake1m | `avd1m_official_val_subset_800`  | 792 | **100.00** | 100.00  | 仓库 tauc 99.99（全量 val）                          | **主报**；val 子集，不对标全量/Codabench       |
| AuViRe  | —             | FakeAVCeleb                      | —   | —          | —       | **无官方行**                                       | **不适用**                             |
| DiMoDif | fakeavceleb   | fakeavceleb                      |     |            |         | Table 3 ACC 99.4 / AUC 99.7                    | **data_missing**（官方集缺失）             |
| DiMoDif | fakeavceleb   | fakeavceleb-wo-rvfa（RVFA）        |     |            |         | Table 6 RVFA AUC **51.6**                      | **data_missing**；**此列不得删**          |
| DiMoDif | lav_df        | `lavdf_official_test_subset_800` | 800 | **99.88**  | 99.96   | Table 4 / Table 9 AUC 99.84                    | 本机子集；不进主视觉                          |
| DiMoDif | lav_df        | `avd1m_official_val_subset_800`  | 800 | **71.04**  | 88.16   | Table 9 AUC 70.40 / AP 88.46                   | 跨域；能力边界                             |
| DiMoDif | av_deepfake1m | `lavdf_official_test_subset_800` | 800 | **86.70**  | 95.44   | Table 9 AUC 86.30 / AP 94.98                   | 跨域                                  |
| DiMoDif | av_deepfake1m | `avd1m_official_val_subset_800`  | 800 | **99.00**  | 99.67   | Table 5 AUC 96.3（全量 val ACC）；Table 9 AUC 99.18 | **主报**；val 子集，n=800，不对标全量/Codabench |


AuViRe Acc（logit 口径，非 val 调参，不进主榜）：LAV 测试域 74.84%；AVD 测试域 74.81%。源文件：`models/AuViRe/results/test/task_dfd_training_on_{lavdf,avdeepfake1m}.json`。  
DiMoDif Acc（阈值 0.5，不进主榜）：LAV→LAV 98.5；LAV→AVD **39.25**（AUC 仍 71.04，说明跨域排序与默认阈值不一致）；AVD→LAV 77.5；AVD→AVD 95.63。源文件：`models/DiMoDif/results/generalization/dfd_{lavdf,avdeepfake1m}.json` 与 `$DATA/results/dimodif_subset_2026-08-26/`。

### 4.3 时间定位 TFL（AP@IoU；不与 DFD / Codabench test 混排）

AuViRe 与 DiMoDif 已在同一批清单上评完（n 因抽特征成败不同，见 §4.1）。**主报** AVD→AVD：AuViRe [AP@0.5](mailto:AP@0.5) **99.22**（n=792）、DiMoDif [AP@0.5](mailto:AP@0.5) **95.32**（n=800）。LAV 训练头在 AVD 上 AuViRe [AP@0.5](mailto:AP@0.5) **15.53**、DiMoDif **17.73** 是迁移失败，不是「需要再并联一个 LAV 检测器」。跨域 TFL 下降是能力边界，不要只抄同域高 AP。禁止用 wav2lip 文件夹或导师换脸集冒充 TFL（后者无伪造区间标注）。


| 方案      | 训练域           | 测试集                | 本机 [AP@0.5](mailto:AP@0.5) | [AP@0.75](mailto:AP@0.75) | [AP@0.9](mailto:AP@0.9) | [AP@0.95](mailto:AP@0.95) | 论文/仓库对照                                      | 状态                                  |
| ------- | ------------- | ------------------ | -------------------------- | ------------------------- | ----------------------- | ------------------------- | -------------------------------------------- | ----------------------------------- |
| AuViRe  | lav_df        | lavdf 子集 n=795     | **98.68**                  | **94.88**                 | **73.90**               | **47.77**                 | 98.91 / 96.03 / 72.10 / 46.52                | 本机子集；不进主视觉                          |
| AuViRe  | lav_df        | avd1m val 子集 n=792 | **15.53**                  | **6.36**                  | **0.50**                | **0.07**                  | 16.05 / 6.68 / 0.65 / 0.05                   | 跨域；能力边界                             |
| AuViRe  | av_deepfake1m | lavdf 子集 n=795     | **54.96**                  | **45.56**                 | **14.56**               | **0.96**                  | 53.76 / 43.26 / 13.92 / 0.85                 | 跨域                                  |
| AuViRe  | av_deepfake1m | avd1m val 子集 n=792 | **99.22**                  | **90.79**                 | **46.34**               | **15.56**                 | 98.81 / 92.17 / 45.56 / 13.17                | **主报**；val 子集，非 Codabench           |
| DiMoDif | lav_df        | lavdf 子集 n=800     | **95.42**                  | **87.80**                 | **58.47**               | **20.80**                 | Table 7 95.5 / 87.9 / 20.6                   | 本机子集；不进主视觉                          |
| DiMoDif | lav_df        | avd1m val 子集 n=800 | **17.73**                  | **3.51**                  | **0.28**                | **0.04**                  | 无官方跨域 TFL 表                                  | 跨域；能力边界                             |
| DiMoDif | av_deepfake1m | lavdf 子集 n=800     | **62.74**                  | **26.41**                 | **2.19**                | **0.25**                  | 无官方跨域 TFL 表                                  | 跨域                                  |
| DiMoDif | av_deepfake1m | avd1m val 子集 n=800 | **95.32**                  | **84.98**                 | **37.46**               | **8.64**                  | Table 8 86.93 / 75.95 / 28.72 / 5.43（全量 val） | **主报**；val 子集，n=800，不对标全量/Codabench |


结果 JSON 在 `models/AuViRe/results/test/`、`models/DiMoDif/results/generalization/` 与 `$DATA/results/{auvire,dimodif}_subset_2026-08-26/`。编排层可写 `talking_face.json` / `tfl.json`，**不要**写入 `cross_dataset.json`。

### 4.4 仍属后续、本批不做


| 批次           | 方案        | 条件                                                             |
| ------------ | --------- | -------------------------------------------------------------- |
| 换脸 in-domain | GenConViT | custom 结果见 §3.4；论文 in-domain 仍待作者 split / 压缩档核验，另表且不得与 §3.1 合并 |
| 唇音对照         | ICS-AV    | 对照，不与 AuViRe/DiMoDif 混排                                        |
| VLAForge     | —         | 作者公布官方权重前不恢复检测                                                 |


---

