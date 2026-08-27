# 图片模态官方仓库初筛快照

核验日期：2026-08-12。此处仅记录仓库页面存在及页面标题表达的项目身份；许可证、Star、论文实验表和数据下载条件仍需逐项补核。

| 项目 | 官方仓库 | 页面核验结果 | 初步方向 |
|---|---|---|---|
| DIRE | [ZhendongWang6/DIRE](https://github.com/ZhendongWang6/DIRE) | HTTP 200；页面标题明确为 ICCV 2023、扩散生成图像检测官方实现 | 扩散模型生成图检测 |
| DeepfakeBench | [SCLBD/DeepfakeBench](https://github.com/SCLBD/DeepfakeBench) | HTTP 200；页面标题明确为 comprehensive benchmark of deepfake detection | 换脸/重演及统一基准 |
| FaceForensics | [ondyari/FaceForensics](https://github.com/ondyari/FaceForensics) | HTTP 200；页面标题明确为 FaceForensics 数据集仓库 | 换脸/操纵数据集与基准 |
| UniversalFakeDetect（候选 URL） | [Purdue-M2/UniversalFakeDetect](https://github.com/Purdue-M2/UniversalFakeDetect) | 本次请求连接异常，未据此确认或排除 | GAN/扩散通用生成图检测 |
| UniversalFakeDetect（候选 URL） | [YuhengB/UniversalFakeDetect](https://github.com/YuhengB/UniversalFakeDetect) | 本次请求连接异常，未据此确认或排除 | GAN/扩散通用生成图检测 |
| GenImage（候选 URL） | [ayushmishra95/GenImage](https://github.com/ayushmishra95/GenImage) | 本次请求连接异常，未据此确认或排除 | 扩散/GAN数据集与跨生成器评测 |

## GitHub 官方搜索页发现的候选

官方搜索页（HTTP 200）返回了以下候选入口，但搜索结果本身不证明作者归属、论文对应关系或官方性：

- 通用生成图检测：`WisconsinAIVision/UniversalFakeDetect`
- 扩散图检测：`beibuwandeluori/DRCT`、`luo3300612/LaRE`
- 方向索引：`zju-pi/Awesome-Fully-AI-Generated-Image-Detection`
- 扩散检测相关候选：`WeinanGuan/NASA-Swin`、`huangyingsong/DEUA`、`AnaMVasilcoiu/LATTE-Diffusion-Detector`

后续仓库页面批量访问出现长连接等待，故这些条目全部保持“候选/待核验”，不计入主清单。索引仓库也不计为检测算法。

## 处理规则

- `DIRE`、`DeepfakeBench` 和 `FaceForensics` 进入“已发现待深核验”，尚未计入任何方向的 6 个合格方案。
- 仓库页面可访问只证明项目入口存在；还必须补充作者/机构归属、LICENSE、权重/推理代码状态、输入输出、论文指标和官方下载条件。
- 同一仓库可能是数据集、基准框架或检测模型，报告中按角色分栏，不能重复计数。

## 2026-08-12 API/README 深核验结果

以下数据通过 GitHub 官方 API 与官方 README 读取；Star 和更新时间是动态快照。

| 项目 | 论文/项目对应关系 | Stars | LICENSE API 字段 | 代码/权重线索 | 当前分类 |
|---|---|---:|---|---|---|
| [DIRE](https://github.com/ZhendongWang6/DIRE) | ICCV 2023；README 明确作者、论文、DiffusionForensics 数据集和预训练模型 | 403 | 未声明 | 提供代码、数据集和预训练模型下载入口 | 官方代码；归档，需记录维护风险 |
| [UniversalFakeDetect](https://github.com/WisconsinAIVision/UniversalFakeDetect) | CVPR 2023；README 明确论文、项目页和跨生成模型检测目标 | 368 | MIT | 含 Setup 与预训练模型章节 | 官方代码候选，需补权重和指标条件 |
| [DRCT](https://github.com/beibuwandeluori/DRCT) | ICML 2024 Spotlight；README 明确论文与 DRCT-2M | 168 | 未声明 | 提供训练/重建流程，DRCT-2M 指向 ModelScope | 官方代码；数据和权重待补 |
| [LaRE](https://github.com/luo3300612/LaRE) | CVPR 2024；LaRE2 latent reconstruction error | 55 | Apache-2.0 | 指向 GenImage 官方仓库，并依赖 DIFT/LASTED | 官方代码；依赖链较长 |
| [NASA-Swin](https://github.com/WeinanGuan/NASA-Swin) | TIFS 2025；README 给出作者、论文、arXiv 和代码 | 17 | 未声明 | 使用 GenImage，并有预训练模型章节 | 官方代码候选，需补权重/指标 |
| [DEUA](https://github.com/huangyingsong/DEUA) | README 对应扩散检测不确定性与非对称学习 | 3 | Apache-2.0 | 含训练和不确定性估计命令 | 官方代码候选，需论文版本和指标核对 |
| [LATTE](https://github.com/AnaMVasilcoiu/LATTE-Diffusion-Detector) | README 列出阿姆斯特丹大学/NFI 作者团队与 Latent Trajectory Embedding | 9 | 未声明 | 官方代码入口，论文链接版本需核对 | 官方代码候选，需补实验表 |
| [GenImage](https://github.com/GenImage-Dataset/GenImage) | LaRE/NASA-Swin README 指向的官方数据集仓库 | 578 | NOASSERTION；含 `License` 文件 | 数据集角色，不是检测模型 | 数据集/基准，不计入算法数量 |
| [DeepfakeBench](https://github.com/SCLBD/DeepfakeBench) | 官方描述为 comprehensive benchmark of deepfake detection | 1083 | NOASSERTION；含 `LICENSE` | 基准框架/模型集合角色需拆分 | 基准框架，不计入算法数量 |
| [FaceForensics](https://github.com/ondyari/FaceForensics) | 官方描述为 FaceForensics dataset | 2762 | NOASSERTION；含 `LICENSE` | 数据集角色 | 数据集，不计入算法数量 |
