# GenConViT 独立部署与评测命令包

本目录是新增的独立交付物。它不接入当前项目的 adapter，不写
`results/indomain.json`，不修改 GenConViT 官方 clone，也不下载新数据集。

评测口径固定为：

- `mentor_swap_200_smoke`：8 真 + 8 假，仅作管道、解码、模型加载和显存检查；
- `mentor_swap_200`：200 真 + 200 假，正式内部 custom evaluation；
- 两者的报告标签均带 `OOD status unverified`；
- 论文 in-domain 单元格仍为未完成；
- 模型代码为 MIT，官方权重仓库标注为 CC-BY-NC-4.0。

## 文件

- `deploy_genconvit.sh`：在 `/data/USER/deepfake-bench` 创建独立环境、固定官方提交、
  优先使用上传的离线制品，必要时才联网，并校验提交与权重 SHA256；
- `prepare_genconvit_offline.ps1`：在联网的 Windows 本机生成固定提交 Git bundle，
  下载并校验两份权重，供测试机离线部署；
- `run_genconvit_eval.sh`：按 smoke → full → repeat-smoke 顺序运行；
- `genconvit_dataset_eval.py`：standalone runner；
- `verify_genconvit_result.py`：验收结果、重算指标、可选重复性对比；
- `common_success_subset.py`：可选的四模型共同成功 ID 附表，不形成排名；
- `tests/`：不依赖视频、模型或 GPU 的离线测试。

默认工作根目录已按测试机实际情况固定为：

```text
/data/USER/deepfake-bench
```

执行用户必须对该目录有写权限，数据集目录只读使用。

## 1. 推荐：在联网本机准备离线制品

在 Windows PowerShell 执行：

```powershell
powershell -ExecutionPolicy Bypass -File `
  "path\to\deepfake-video-research\scripts\genconvit_standalone\prepare_genconvit_offline.ps1" `
  -OutDir "path\to\genconvit-offline"
```

该脚本可安全重复执行：已通过 SHA256 的完整权重会跳过；缺失权重使用固定的
`.pth.part` 文件、HTTP Range 续传、单文件下载和自动重试。若进程、PowerShell 或网络
再次中断，原样重跑上面的命令即可继续。不要删除或改名
`path\to\genconvit-offline\genconvit_vae_inference.pth.part`。脚本只有在字节数和 SHA256
均通过后才把 `.part` 改为正式文件名。重跑前先确认旧脚本进程已结束，不要同时启动
两个实例写同一 `.part`。默认最多自动尝试 20 次；需要时可追加：

```powershell
-MaxDownloadAttempts 50 -RetryDelaySeconds 20
```

该命令只准备模型代码和权重，不下载评测数据。输出包括：

```text
path\to\genconvit-offline\GenConViT-2c1d0bd7eecea94926595781a744e3f4b8b55290.bundle
path\to\genconvit-offline\genconvit_ed_inference.pth
path\to\genconvit-offline\genconvit_vae_inference.pth
path\to\genconvit-offline\SHA256SUMS.txt
```

## 2. 从本机复制到测试机

以下命令由操作者执行；本交付过程没有连接 `EVAL_HOST`。

在 Windows PowerShell 执行：

```powershell
ssh USER@EVAL_HOST `
  'mkdir -p /data/USER/deepfake-bench/ops /data/USER/deepfake-bench/offline/genconvit'

scp -r "path\to\deepfake-video-research\scripts\genconvit_standalone" `
  USER@EVAL_HOST:/data/USER/deepfake-bench/ops/

scp "path\to\genconvit-offline\GenConViT-2c1d0bd7eecea94926595781a744e3f4b8b55290.bundle" `
  "path\to\genconvit-offline\genconvit_ed_inference.pth" `
  "path\to\genconvit-offline\genconvit_vae_inference.pth" `
  "path\to\genconvit-offline\SHA256SUMS.txt" `
  USER@EVAL_HOST:/data/USER/deepfake-bench/offline/genconvit/
```

先在测试机校验传输完整性：

```bash
cd /data/USER/deepfake-bench/offline/genconvit
sha256sum -c SHA256SUMS.txt
```

## 3. 部署模型

登录测试机后，先看所有 GPU，再显式选择一个空闲的物理编号。不要照抄示例编号：

```bash
cd /data/USER/deepfake-bench/ops/genconvit_standalone
chmod u+x deploy_genconvit.sh run_genconvit_eval.sh
nvidia-smi
export GENCONVIT_GPU=2  # 改成刚确认的空闲物理 GPU 编号
export GENCONVIT_OFFLINE_ARTIFACTS_ONLY=1
bash deploy_genconvit.sh
```

部署脚本会：

- clone `https://github.com/erprogs/GenConViT.git`，detached checkout 到
  `2c1d0bd7eecea94926595781a744e3f4b8b55290`；若已上传 Git bundle，则完全从
  bundle clone，不访问 GitHub；
- 创建 `/data/USER/deepfake-bench/envs/genconvit`（Python 3.10）；
- 安装 PyTorch 2.1.2 / torchvision 0.16.2 / cu118 和固定依赖；
- 优先复制已上传的两份权重；只有离线权重不存在时才通过 `hf download` 下载
  `Deressa/GenConViT` revision `32d6e9e3c931a37971cc756da706cf1eef643372`；
- 校验 ED 与 VAE 权重 SHA256；
- 把包版本、GPU、dlib 检测模式等写到
  `/data/USER/deepfake-bench/metadata/genconvit`。

PyPI 的 `decord==0.6.0` Linux wheel 文件名声明兼容 Python 3，但其内部 `WHEEL`
元数据误写为 `cp36`，因此 Python 3.10 的新版 `pip check` 会输出
`decord 0.6.0 is not supported on this platform`。部署脚本只在 Linux x86_64、实际
`import decord` 成功、版本为 0.6.0 且内部标签精确匹配该已知错误时豁免这一行，并把
豁免记录到 `metadata/genconvit/pip-check.txt`；任何其他依赖错误仍会终止部署。实际视频
解码继续由 smoke 评测验证。

`GENCONVIT_OFFLINE_ARTIFACTS_ONLY=1` 只禁止 GitHub/Hugging Face 回退：bundle 或任一
权重缺失时部署立即停止。它不代表 Conda/PyPI/PyTorch 依赖也已离线缓存。

首次环境安装和本机约 3 GB 权重下载可能耗时。部署脚本可重跑，但不会覆盖结果目录，
也不会自动清理一个错误或不完整的既有 clone。

离线制品只消除 GitHub 和 Hugging Face 依赖。创建 Conda 环境仍需访问 Conda channel、
PyPI 和 `download.pytorch.org`。若测试机连这些站点也不稳定，应在兼容的 Linux/CUDA
机器上另做 `conda-pack` 环境包；不要从 Windows 直接打包 Linux Python 环境。

## 4. 冒烟、正式评测和重复性抽查

每次运行前都重新检查 GPU 并显式导出同一物理编号：

```bash
cd /data/USER/deepfake-bench/ops/genconvit_standalone
nvidia-smi
export GENCONVIT_GPU=2  # 改成实际空闲编号
bash run_genconvit_eval.sh smoke
```

查看冒烟结果：

```bash
python -m json.tool \
  "/data/USER/deepfake-bench/results/genconvit/mentor_swap_200_smoke/summary.json" \
  | less
```

冒烟通过后，原样跑 200 + 200，不重新抽样：

```bash
cd /data/USER/deepfake-bench/ops/genconvit_standalone
nvidia-smi
export GENCONVIT_GPU=2  # 与冒烟相同的物理 GPU
bash run_genconvit_eval.sh full
```

完成后用同一 GPU 做 8 + 8 重复性检查；分数必须逐条完全一致：

```bash
cd /data/USER/deepfake-bench/ops/genconvit_standalone
nvidia-smi
export GENCONVIT_GPU=2
bash run_genconvit_eval.sh repeat-smoke
```

三个命令分别写入：

```text
/data/USER/deepfake-bench/results/genconvit/mentor_swap_200_smoke
/data/USER/deepfake-bench/results/genconvit/mentor_swap_200
/data/USER/deepfake-bench/results/genconvit/mentor_swap_200_smoke_repeat
```

为避免误覆盖，任一目标目录已存在时脚本会停止。如果此前运行失败，应先保留该目录
用于排障，然后改名归档；不要直接删除审计证据后重跑。

## 5. 直接调用 runner

下面的接口与接管方案一致；标准目录下的两份权重会由 `--repo-dir` 自动推导：

```bash
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES="$GENCONVIT_GPU"
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONHASHSEED=20260818
export PYTHONDONTWRITEBYTECODE=1
"/data/USER/deepfake-bench/envs/genconvit/bin/python" \
  "/data/USER/deepfake-bench/ops/genconvit_standalone/genconvit_dataset_eval.py" \
  --repo-dir "/data/USER/deepfake-bench/models/GenConViT" \
  --dataset-dir /data/USER/deepfake-bench/datasets/mentor_swap_200 \
  --dataset-name mentor_swap_200 \
  --out-dir "/data/USER/deepfake-bench/results/genconvit/mentor_swap_200" \
  --frames 15 \
  --seed 20260818 \
  --precision fp32 \
  --expected-real 200 \
  --expected-fake 200 \
  --hash-videos \
  --evidence-role custom_evaluation
```

runner 只接受 FP32。CUDA OOM 会终止整次运行；应换高显存 GPU，不可静默切 FP16、
减少帧数或更换模型。

## 6. 输出与失败策略

每次成功完成或可审计地部分完成后包含：

- `scores.csv`：仅成功视频，兼容三模型已有分数表；
- `predictions.csv`：每个请求视频一行，成功与失败都保留；
- `summary.json`：AUC、AP、Accuracy、macro-F1、fake Precision/Recall、EER、
  固定阈值 0.5、分层 bootstrap 95% CI、环境和许可证元数据；
- `failures.json`：解码、无脸、预处理、模型或输出校验失败；
- `dataset_manifest.csv`：相对 ID、标签、大小和内容 SHA256；
- `progress.jsonl`：逐视频追加的进度审计；
- `eval.log`：完整日志。

无脸或解码失败不会补成 `0.5`。指标只在成功视频上计算，coverage 和真实/伪造分别
失败数独立报告。若成功样本只剩一类，指标为 `null` 且状态为 `eval_failed`。

Accuracy、macro-F1、Precision 和 Recall 按本基准协议固定执行 `score >= 0.5`；
`predictions.csv` 另存经 real=0/fake=1 归一化的官方 argmax 判定。由于官方输出的
piecewise fake score 不是标准二分类后验概率，这两种判定在个别样本上可能不同，不能
把 0.5 阈值误写成官方模型的 argmax 规则。

## 7. 可选：四模型共同成功 ID 附表

只有在前三模型与 GenConViT 的 `scores.csv` 均存在时执行。先把三个路径改成测试机的
真实位置：

```bash
export LIP_SCORES=/absolute/path/to/lipforensics/scores.csv
export REAL_SCORES=/absolute/path/to/realforensics/scores.csv
export PWTF_SCORES=/absolute/path/to/pwtf_dvd/scores.csv
export GEN_SCORES="/data/USER/deepfake-bench/results/genconvit/mentor_swap_200/scores.csv"

"/data/USER/deepfake-bench/envs/genconvit/bin/python" \
  "/data/USER/deepfake-bench/ops/genconvit_standalone/common_success_subset.py" \
  --scores "lipforensics=$LIP_SCORES" \
  --scores "realforensics=$REAL_SCORES" \
  --scores "pwtf_dvd=$PWTF_SCORES" \
  --scores "genconvit=$GEN_SCORES" \
  --out-dir "/data/USER/deepfake-bench/results/genconvit/common_success_appendix"
```

该目录只报告共同 ID 上的 AUC/AP 与过滤后分数，不排名。GenConViT 的原生全集主结果
必须保留，附表不能替代它。

## 8. 最终只读验收

```bash
export GEN_ROOT="/data/USER/deepfake-bench"

printf '%s  %s\n' \
  86f0c2e875016435def7d031b357bda5dc0061367290d73de121186df3f03f8c \
  "$GEN_ROOT/weights/genconvit/genconvit_ed_inference.pth" \
  | sha256sum -c -

printf '%s  %s\n' \
  53c627c82d1439fc80e18ac462c1ed6969a3babe5376124a5c38d1c0c88c9042 \
  "$GEN_ROOT/weights/genconvit/genconvit_vae_inference.pth" \
  | sha256sum -c -

git -C "$GEN_ROOT/models/GenConViT" diff --exit-code
git -C "$GEN_ROOT/models/GenConViT" status --short

"$GEN_ROOT/envs/genconvit/bin/python" \
  "$GEN_ROOT/ops/genconvit_standalone/verify_genconvit_result.py" \
  --run-dir "$GEN_ROOT/results/genconvit/mentor_swap_200" \
  --expected-real 200 \
  --expected-fake 200
```

`git status --short` 应无输出。正式结果的唯一允许命名是
`mentor_swap_200 custom evaluation / OOD status unverified`；不要把它写成 FF++、DFDC、
Celeb-DF 或论文同域复现。
