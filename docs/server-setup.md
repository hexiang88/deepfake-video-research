# 服务器连接与目录

密码不要写入本仓库、不要发到聊天。只用环境变量或本机 SSH 配置。

## 1. 从 Windows 登录

PowerShell：

```powershell
ssh USER@HOST
```

有密钥时：

```powershell
ssh -i $env:USERPROFILE\.ssh\id_ed25519 USER@HOST
```

把 `USER`、`HOST` 换成导师给的账号和域名。首次会询问 host key，确认指纹后再继续。

本机先确认端口通，再开详细日志（不要把密码贴进聊天）：

```powershell
Test-NetConnection EVAL_HOST -Port 22
ssh -vvv USER@EVAL_HOST
```

`EVAL_HOST` 是内网地址。本机开了系统/TUN 代理时，SSH 可能被代理接走，表现为先 `Connection established` 再 `kex_exchange_identification` 被掐；关掉代理后变成 `Connection timed out`（Windows 错误 10060），说明当前网络到不了实验室网段。这两种都还不能断定是 sshd 坏了。

正确路径一般是：**校园网 / 导师指定的 VPN / 跳板机**，不要用科学上网代理去连内网 SSH。连上后再跑探测。

常见失败：

| 现象 | 含义 | 处理 |
|---|---|---|
| `Connection timed out` | 根本到不了 22 | VPN / 校园网 / 安全组 |
| `Connection refused` | 主机在，sshd 没开或端口不对 | 问导师真实端口（有时是 2222） |
| `Connection closed by HOST port 22` | TCP 已接通，服务端在握手或认证前掐线 | 见下方 |
| `Permission denied` | 用户名或密钥/密码不对 | 核对账号；密码登录确认键盘布局 |
| `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED` | 主机密钥变了 | 先向导师确认是否重装过机器，再更新 `known_hosts` |

`kex_exchange_identification: Connection closed by remote host` 发生在 **SSH 版本串交换**（尚未密码/密钥）。`identity file … type -1` 只是本机没有那些默认密钥，可以忽略。

按顺序试：

1. **换非 Windows 的 OpenSSH 客户端**（部分网关会丢掉 `SSH-2.0-OpenSSH_for_Windows_9.5` 这条 ident）：

```powershell
wsl ssh -vvv USER@EVAL_HOST
```

若已装 Git Bash，也可用 `"$env:ProgramFiles\Git\usr\bin\ssh.exe" USER@EVAL_HOST`。

2. **强制 IPv4**：`ssh -4 USER@EVAL_HOST`

3. **算法不兼容**（旧 sshd）再试：

```powershell
ssh -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedAlgorithms=+ssh-rsa USER@EVAL_HOST
```

4. 仍在 ident 阶段被掐：本机改不了账号白名单。请导师查该次连接的 `sshd` 日志（`/var/log/secure` 或 `journalctl -u sshd`），常见是 **IP 未放行、MaxStartups、hosts.deny、或 22 上不是 sshd**。Windows 自带 ssh 与 WSL/Ubuntu ssh 若都停在 `kex_exchange_identification`，即可排除「仅 Windows ident 被拒」，需要服务器侧排查。

密码不要发到聊天。

## 2. 登录后：建目录并保存探测

当前提示符若是 `USER@eval-host:/home/USER$`，先确认**自己的家目录和数据盘**，不要把大数据写进别人的 `/home/USER`。

```bash
whoami
echo "$HOME"
pwd
df -h
```

看 `df -h` 里哪一块盘空间大、且你有写权限（常见 `/data`、`/ssd`、`/mnt`、自己的 `$HOME`）。系统盘（`/` 或很小的 `/home`）不要当数据根。

选定后（把路径换成你的，下面以 `$HOME` 为例；若导师指定了 `/data/USER` 就用那个）：

```bash
export DATA="$HOME"          # 或 export DATA=/data/USER
mkdir -p "$DATA/deepfake-bench"/{datasets,models,envs,weights,results,code}
ls -ld "$DATA/deepfake-bench"/*
```

探测并写进 `results`（仓库还没拷上去时，直接用这段；有仓库后可改跑 `bash scripts/probe_server.sh "$DATA/deepfake-bench/results"`）：

```bash
STAMP=$(date +%Y-%m-%d)
OUT="$DATA/deepfake-bench/results/probe-$STAMP.txt"
{
  echo "=== date ==="; date -Is 2>/dev/null || date
  echo; echo "=== whoami / home / pwd ==="
  whoami; echo "HOME=$HOME"; pwd
  echo; echo "=== uname ==="; uname -a
  echo; echo "=== nvidia-smi ==="
  nvidia-smi 2>/dev/null || echo "nvidia-smi not found"
  echo; echo "=== df -h ==="; df -h
  echo; echo "=== free -h ==="
  free -h 2>/dev/null || echo "free not found"
  echo; echo "=== python ==="
  python3 --version 2>/dev/null || echo "python3 not found"
  which python3 2>/dev/null || true
  echo; echo "=== conda ==="
  which conda 2>/dev/null || echo "conda not found"
} | tee "$OUT"
echo "Wrote $OUT"
ls -l "$OUT"
```

把 `df -h` 和 `nvidia-smi` 那两段保存下来，用来决定一次下多少数据。磁盘紧则 DFDC 只用 preview，结果里必须写 `dfdc_preview`。

本仓库稍后放到 `$DATA/deepfake-bench/code/`。评测 JSON 也写在 `$DATA/deepfake-bench/results/`（`cross_dataset.json` 等），与探测文件分开即可。

## 3. 目录含义

```text
$DATA/deepfake-bench/
  datasets/   # FF++、Celeb-DF 等（官方申请后再放）
  models/     # 各官方仓库 clone
  envs/       # 每模型独立 conda/venv
  weights/    # 预训练权重
  results/    # probe-日期.txt 与评测 JSON
  code/       # 本仓库
```

配置里用绝对路径指向上述目录，不要写死别人的盘符。创建命令见上一节。

## 4. 把本仓库和配置放到服务器

本机（不要用密码写进命令历史之外的文件）：

```powershell
scp -r path\to\deepfake-video-research USER@HOST:/path/to/deepfake-bench/code/
```

服务器上复制配置：

```bash
cp configs/video_eval.example.yaml configs/video_eval.yaml
cp configs/datasets.manifest.example.json configs/datasets.manifest.json
# 编辑上述两个文件中的绝对路径
```

`configs/video_eval.yaml` 和 `configs/datasets.manifest.json` 已列入 `.gitignore` 的本地覆盖约定：只提交 `*.example.*`。

## 5. 一模型一环境

不要把四家依赖装进同一个 conda。示例：

```bash
conda create -n lipforensics python=3.8 -y
conda activate lipforensics
# 再按该仓库 README 安装 PyTorch 与 requirements
```

各模型 clone 到 `$DATA/deepfake-bench/models/<name>`，权重放到 `$DATA/deepfake-bench/weights/<name>`。固定 `git rev-parse HEAD`，评测 JSON 会记录 commit。

## 6. 下一步

1. 探测硬件并记下 GPU 名、显存、磁盘。
2. 申请 FF++ / Celeb-DF 等，见 [video-eval-protocol.md](video-eval-protocol.md)。
3. 申请等待期间 clone 代码、建环境、下官方权重。
4. `bash scripts/smoke_one_model.sh lipforensics` 能出分数后再全量。
