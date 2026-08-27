# 视频模态 Deepfake 检测评测

本仓库是视频模态（换脸 / Talking Face / TFL）的本机复测工程：包装官方评测入口、固定协议与结果口径，并把本机数字写入**分赛道 JSON** 与台账。不把多模型排成总榜。人脸视频、权重与实验结果不进 git。

本机复测台账见 [research/reports/video-eval-first-batch-2026-08-18.md](research/reports/video-eval-first-batch-2026-08-18.md)。调研入准表见 [research/reports/video.md](research/reports/video.md)。

协议与 SSH 说明：

- [docs/video-eval-protocol.md](docs/video-eval-protocol.md)
- [docs/server-setup.md](docs/server-setup.md)

已完成的本机评测（评测机 eval-host，数字只在台账，不在本仓库的 `results/`）：

- 换脸 `mentor_swap_200`：LipForensics、RealForensics、PwTF-DVD；GenConViT 为独立 custom 评测（OOD 未核验，不并入 §3.1 总榜）
- 换脸跨操纵 / 重演类：RealForensics leave-one-out（`ffpp_official_test_available`）
- Talking Face DFD / TFL：AuViRe、DiMoDif（主报 AVD 训练头 → AVD val 子集）
- VLAForge：官方权重缺失，检测计划已取消

## 安装（评测包装器）

```bash
pip install -r requirements.txt
```

服务器上每个检测器仍使用**独立 conda 环境**，按各官方 README 安装 PyTorch。本包装器只需要 PyYAML。

## 服务器探测与冒烟

```bash
bash scripts/probe_server.sh
cp configs/video_eval.example.yaml configs/video_eval.yaml
cp configs/datasets.manifest.example.json configs/datasets.manifest.json
# 编辑绝对路径；不要写入密码
bash scripts/smoke_one_model.sh lipforensics
```

## 按赛道评测

```bash
python -m src.video_eval.run_eval --config configs/video_eval.yaml --track cross_dataset --model lipforensics
python -m src.video_eval.run_eval --config configs/video_eval.yaml --track cross_manipulation --model realforensics
python -m src.video_eval.run_eval --config configs/video_eval.yaml --track vlaforge_frame --model vlaforge
python -m src.video_eval.run_eval --config configs/video_eval.yaml --track talking_face --model auvire
python -m src.video_eval.run_eval --config configs/video_eval.yaml --track tfl --model dimodif
```

`--dry-run` 只打印将执行的命令。`--smoke` 使用配置里的 `smoke_limit`。

结果文件（禁止合并；本地生成，不提交）：

- `results/cross_dataset.json`
- `results/cross_manipulation.json`
- `results/vlaforge_frame.json`
- `results/talking_face.json`
- `results/tfl.json`

缺数据的列写入 `status: data_missing`，不编造数字。DFDC preview 必须记为 `dfdc_preview`。Talking Face / TFL **不要**写入 `cross_dataset.json`。GenConViT custom 结果不写入 `indomain.json`。

## 测试

```bash
python -m pytest tests/video_eval -q
```

测试只用小 CSV / 文本夹具，不读取人脸视频。
