# 图片检测实验与数据证据快照

来源：各官方仓库 README，通过 GitHub API 读取；核验日期：2026-08-12。README 摘要不是论文实验表的替代品，以下只记录 README 明确写出的条件。

## DIRE

- 官方 README 称 DiffusionForensics benchmark 含 **8 个扩散模型**，并主张对未见扩散模型具有泛化、对多种扰动具有鲁棒性。
- README 提供 DiffusionForensics 数据集、代码和预训练模型下载入口（Baidu/OneDrive/RecDrive）。
- 这些是项目自述，具体 AUC/AP、扰动参数和训练/测试划分需回到 ICCV 2023 论文实验表。

## UniversalFakeDetect

- README 称论文整体研究 **19 个模型**；扩散测试数据说明包含 LDM/Glide，文中还说明论文表格使用 10,000 个随机抽样图像，而发布数据为每个域 1,000 张真实/伪造图。
- 官方验证脚本输出每个测试域的 AP 和以 0.5 为阈值的 Accuracy。
- 训练数据约 72GB、测试数据约 19GB 的描述来自 README；不能将其直接解释为单一数据集规模。

## DRCT

- 官方 README 定义两阶段：扩散重建 + margin-based contrastive training。
- DRCT-2M 指向 ModelScope 官方数据入口；训练示例区分 MSCOCO 真实图、重建图和 Stable Diffusion 生成图。
- README 的 correction note 明确写出：用 DRCT Conv-B 测试 BigGAN 的实际 Accuracy 为 **59.81%**。该数值绑定 BigGAN、Conv-B 和 README correction note，不得泛化为 DRCT 总体准确率。

## LaRE / NASA-Swin / DEUA

- LaRE README 使用 GenImage 训练和评测，并将方法定位为 latent-space reconstruction error；依赖 DIFT/LASTED。
- NASA-Swin README 明确使用 GenImage，并提供 NASA-Swin-Base 权重和 GenImage 子集推理脚本，声称可复现 Table I/II；具体数值待论文表核验。
- DEUA README 明确出现 GenImage 与 DRCT-2M 的路径和评测脚本；具体指标、划分和不确定性校准结果待论文/输出文件核验。

## LATTE

- README 明确建模 Stable Diffusion 去噪过程中的 latent trajectory，并提供 robustness.py。
- README 声称在 GenImage、Chameleon、Diffusion Forensics 上优于 AIDE/LaRE，并提供 GenImage 8 个生成器的 pairwise evaluation 说明。
- 该“优于”表述尚未转录为可比较数字；需要读取论文表格/图、训练子集与测试子集、扰动参数后才能用于基准选型。
