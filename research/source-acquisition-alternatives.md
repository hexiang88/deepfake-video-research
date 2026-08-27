# GitHub 替代来源与证据获取方案

## 目标

GitHub 仅作为代码入口之一，不再作为音视频调研的单点依赖。所有模型、论文、仓库、指标和数据集仍必须满足作者或机构官方来源要求；替代来源不能降低证据标准。

## 来源优先级

| 优先级 | 来源 | 可核验内容 | 使用边界 |
|---|---|---|---|
| 1 | 作者论文页、机构项目页、实验室服务器 | 论文、作者归属、项目说明、结果表、代码/权重链接 | 项目页中的数字仍需绑定数据集、划分、生成器和退化条件 |
| 2 | arXiv、OpenReview、ACL Anthology、CVF、ISCA/Interspeech、ACM/IEEE 作者论文页 | 原始论文、附录、实验表、补充材料 | 论文没有官方实现时只能作为论文证据，不能声明开源实现 |
| 3 | Zenodo、机构数据仓库、作者维护的 Hugging Face 组织/模型页 | 代码压缩包、权重、配置、结果文件、版本 DOI | 必须确认上传者与作者/机构对应；记录 DOI、版本和文件清单 |
| 4 | GitLab、Bitbucket、Gitee、机构自建 Git 服务 | 官方代码和 issue/release | 必须从论文、机构页或作者主页确认官方归属；第三方镜像不计入官方实现 |
| 5 | Papers with Code、CatalyzeX、Hugging Face Papers、搜索引擎结果 | 发现线索、论文与代码的候选关联 | 只作索引，不能作为最终证据或指标来源 |

## 证据分层

- `完全核验`：能从论文/机构页确认作者归属；能获取官方代码或权重；能确认许可证或明确开放类型；指标绑定数据集、划分、伪造类型/生成器和压缩、扰动、跨域或零样本条件。
- `官方部分核验`：作者归属和实现入口可信，但缺许可证、完整代码、权重、实验表或条件字段之一。
- `论文已核验、实现未核验`：论文和实验数字可靠，但没有作者/机构原始实现入口。
- `仅发现线索`：来自搜索摘要、第三方列表或未确认镜像，不进入候选统计。

## 推荐检索顺序

1. 先用论文标题、作者和机构检索官方项目页或机构域名。
2. 从论文实验表提取数据集、攻击家族、压缩/扰动和划分字段。
3. 沿官方项目页的代码、权重、Zenodo、Hugging Face 或机构服务器链接获取实现。
4. 对模型文件、结果文件和配置记录版本、SHA256/DOI、下载日期和来源 URL。
5. 只有在官方来源无法访问时，才用作者确认的 GitLab/Gitee/机构镜像替代 GitHub。
6. 将原始页面、API JSON 或下载文件清单保存为日期快照；不把搜索摘要保存为指标证据。

## PowerShell 只读命令模板

以下命令不访问 GitHub，可在用户终端执行。请勿把令牌写入命令行或快照。

### 论文页和机构页

```powershell
$u = 'https://arxiv.org/abs/2411.10193'
$r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 30
"HTTP=$([int]$r.StatusCode)"
$r.Content | Set-Content -Encoding utf8 "$env:TEMP\paper-page.html"
```

### Zenodo API

```powershell
$q = [uri]::EscapeDataString('title:"audio deepfake"')
$r = Invoke-RestMethod -Uri "https://zenodo.org/api/records?q=$q&size=10" -TimeoutSec 30
$r.hits.hits | Select-Object id,doi,title,created,updated,links | ConvertTo-Json -Depth 6
```

### Hugging Face API

```powershell
$r = Invoke-RestMethod -Uri 'https://huggingface.co/api/models?search=audio%20deepfake&limit=20' -TimeoutSec 30
$r | Select-Object id,author,likes,lastModified,license | ConvertTo-Json -Depth 4
```

Hugging Face 搜索结果只作发现线索。正式采信前必须确认模型卡作者、论文、组织归属、权重文件和评测条件。

### GitLab 公共 API

```powershell
$q = [uri]::EscapeDataString('audio deepfake detection')
$r = Invoke-RestMethod -Uri "https://gitlab.com/api/v4/projects?search=$q&per_page=20" -TimeoutSec 30
$r | Select-Object id,path_with_namespace,web_url,namespace,license,last_activity_at | ConvertTo-Json -Depth 5
```

GitLab 搜索结果同样不能直接证明官方归属，必须回到论文或机构项目页交叉确认。

## 快照字段

每个替代来源快照至少记录：

`访问日期；来源类型；原始 URL；HTTP 状态；标题/作者/机构；论文 DOI 或 arXiv；代码/权重下载 URL；版本、commit、DOI 或 SHA256；许可证；数据集与划分；生成器/伪造类型；压缩/扰动/跨域条件；指标原始单位；证据等级；未确认字段。`

## 当前策略

- 本地已有 GitHub 快照继续使用，不重复审计。
- 新增候选优先通过论文页、机构页、Zenodo、Hugging Face 作者组织和 GitLab 获取。
- 没有官方实现时，候选可以写入“论文已核验、实现未核验”，但不计入开源模型数量。
- 本策略不改变当前覆盖矩阵的完成状态；稀缺方向仍使用已记录的降级门槛。
