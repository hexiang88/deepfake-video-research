# 视频换脸评测协议（第一批）

本批模型：LipForensics、RealForensics、PwTF-DVD、VLAForge。GenConViT 为第二阶段同域另表。Talking Face / 唇音 / TFL（AuViRe、DiMoDif）为第二批，写入 `talking_face.json` / `tfl.json`，**禁止**并入 `cross_dataset.json`。DeepfakeBench 不是检测器。

对照调研入准表：[research/reports/video.md](../research/reports/video.md) §2。统一字段规则：[research/evaluation-protocol.md](../research/evaluation-protocol.md)。

## 赛道与结果文件

| 赛道 `track` | 模型 | 结果文件 | 粒度 |
|---|---|---|---|
| `cross_dataset` | 四模型 | `results/cross_dataset.json` | 视频级 AUC |
| `cross_manipulation` | RealForensics | `results/cross_manipulation.json` | 视频级 AUC；F2F/NT 须带重演备注 |
| `vlaforge_frame` | 仅 VLAForge | `results/vlaforge_frame.json` | 帧级 AUROC |
| `indomain`（阶段 2） | GenConViT | `results/indomain.json` | 按数据集分列 Acc/AUC/F1 |
| `talking_face` | AuViRe、DiMoDif | `results/talking_face.json` | DFD 视频级 AUC/AP/ACC；唇音代理须备注；DiMoDif 保留 RVFA |
| `tfl` | AuViRe、DiMoDif | `results/tfl.json` | AP@IoU / AR；官方 LAV-DF / AVD1M 缺失则 `data_missing` |

**禁止**把上述文件合并成总榜，禁止混合 c0/c23、帧级/视频级、DFDC 全量与 preview。

## 数据申请入口

无许可不要下载。人脸视频禁止再分发、禁止提交 git。

| 数据集 | 入口 | 本批用途 |
|---|---|---|
| FaceForensics++ | [ondyari/FaceForensics](https://github.com/ondyari/FaceForensics) 按官方申请 | 训练域 / 跨操纵；压缩档必须标 **c23** |
| Celeb-DF v2 | 论文 [arXiv:1909.12962](https://arxiv.org/abs/1909.12962) 官方页 | 跨数据集 |
| DFDC | 官方 / Kaggle | 跨数据集；磁盘不够用 preview，`test_set: dfdc_preview` |
| FaceShifter / DeeperForensics / DFD | 各评测仓库 README | 缺数据则该列记 `data_missing`，不编造数字 |

落地后填写 `configs/datasets.manifest.json`（由 example 复制）。测试脚本只读清单。

## 备注句（写入 JSON `notes`）

- 跨操纵 F2F/NT：`候选为 RealForensics；评测对象是 FF++ Face2Face 与 NeuralTextures，不是独立重演检测器。`
- VLAForge 视频级：`视频级分数为帧级平均。`
- DFDC preview：`test_set 为 preview，不是全量 DFDC。`
- 导师 custom set：`test_set` 必须写 `mentor_swap_200` / `mentor_swap_200_smoke`，禁止写成 Celeb-DF / FF++ / DFDC。
- 唇音：`候选为 AuViRe / DiMoDif；指标为音视频检测 AUC 与伪造区间 AP，不是唇音偏移毫秒/帧误差。`
- AuViRe：`官方表只绑定 LAV-DF × AV-Deepfake1M，无 FakeAVCeleb 行；本机不编造该行。`
- DiMoDif RVFA：`跨操纵必须保留 RVFA（真视频假音频）列；论文对照 Table 6 AUC 51.6。`

## 命令

探测：

```bash
bash scripts/probe_server.sh
```

单模型冒烟（需已 clone、权重、至少若干视频）：

```bash
bash scripts/smoke_one_model.sh lipforensics
```

按赛道评测：

```bash
python -m src.video_eval.run_eval --config configs/video_eval.yaml --track cross_dataset --model lipforensics
python -m src.video_eval.run_eval --config configs/video_eval.yaml --track cross_manipulation --model realforensics
python -m src.video_eval.run_eval --config configs/video_eval.yaml --track vlaforge_frame --model vlaforge
# Talking Face / TFL（第二批；官方 LAV-DF/AVD1M 缺失时写 data_missing，不进 cross_dataset.json）
python -m src.video_eval.run_eval --config configs/video_eval.yaml --track talking_face --model auvire
python -m src.video_eval.run_eval --config configs/video_eval.yaml --track tfl --model auvire
python -m src.video_eval.run_eval --config configs/video_eval.yaml --track talking_face --model dimodif
python -m src.video_eval.run_eval --config configs/video_eval.yaml --track tfl --model dimodif
```

`--dry-run` 只打印将要执行的命令。`--smoke` 使用配置里的 `smoke_limit` 条样本（由各仓库命令自行解释，或由 adapter 传入）。

官方入口（clone 后以该仓库 README 为准，可在 yaml 里覆盖 `eval_command`）：

| 模型 | 官方评测 |
|---|---|
| LipForensics | `python evaluate.py --dataset CelebDF --weights_forgery ./models/weights/lipforensics_ff.pth` |
| RealForensics 跨数据集 | `python stage2/eval.py model.weights_filename=realforensics_ff.pth`（一次跑 Table 2 全部） |
| RealForensics 跨操纵 | `python stage2/eval.py model.weights_filename=realforensics_allbutdf.pth`（其余 allbut\* 权重） |
| PwTF-DVD | `python inference/test_on_raw_video.py --video VIDEO --out_dir OUT --model_path WEIGHTS`；数据集循环见 `scripts/pwtf_dvd_dataset_eval.py` |
| VLAForge | 在 `config/test.yaml` 设置 `test_dataset` 后 `bash test.sh`；帧级与视频级分文件 |
| AuViRe | 在 clone 根目录 `python scripts/test.py`（LAV-DF × AVD1M DFD+TFL）。先把仓库自带 `results/test` 挪走，否则 skip 且会把论文 JSON 当成已评。无 FakeAVCeleb 行 |
| DiMoDif | 在 clone 根目录 `python scripts/eval.py`（含 FakeAVCeleb 跨操纵 **RVFA**）。同样先挪走自带 `results/generalization` |

导师 custom set（`mentor_swap_200` / `mentor_swap_200_smoke`，`real/` + `fake/` 原视频）：**禁止**把 `--dataset CelebDF` 传给 LipForensics `evaluate.py`（stdout 会被 parse 成 celebdf_v2）。改走：

| 模型 | 自定义 runner |
|---|---|
| LipForensics | `scripts/lipforensics_dataset_eval.py`（FAN 68 点 + 官方嘴部 crop + `get_model` clip logit 平均） |
| RealForensics | `scripts/realforensics_dataset_eval.py`（FAN 68 点 + 官方 `extract_faces` + CSN/MeanLinear） |

yaml：`test_sets: [mentor_swap_200_smoke]`，RealForensics `eval_once: false`。`--smoke-limit` 切的是 **real 再 fake 的拼接列表**；冒烟请用 8+8 的 `mentor_swap_200_smoke`，不要对 200+200 开 `smoke_limit`。PwTF 正在 GPU 1 跑全量时，Lip/Real 冒烟用 `CUDA_VISIBLE_DEVICES=2`（yaml 里 `gpu: cuda:0` 不要改）。VLAForge 保持关闭。

论文锚点（仅对照，不是本次实验结论）：LipForensics 视频级 AUC Celeb-DF-v2 82.4 / DFDC 73.5 / FaceShifter 97.1 / DeeperForensics 97.6（FF++ 训练，Table 2）。
