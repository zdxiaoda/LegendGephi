# LegendGephi

一个用于解析 GEXF（Graph Exchange XML Format）文件并向 SVG 网络可视化添加图例的 Python 工具。LegendGephi 从 GEXF 节点中提取图层和颜色信息，并自动在 SVG 文件的右上角生成图例。

## 功能特性

- **GEXF 解析**：从 GEXF 网络文件中提取节点的 layer 和 color 属性
- **自动图例生成**：在 SVG 可视化中添加颜色编码的图例，显示图层-颜色映射关系
- **文本自动换行**：自动调整节点标签使其适应节点直径
- **SVG 转 PNG**：支持可选的 SVG 文件转换为高分辨率 PNG 图像

## 系统要求

- Python 3.10 或更高版本
- `cairosvg`（可选，仅在进行 PNG 转换时需要）

## 安装

### 先决条件

- Python 3.10 或更高版本
- uv 包管理器

### 设置

克隆仓库并运行：

```bash
uv sync
```

这将安装所有依赖项，包括可选的 PNG 转换支持（cairosvg）。

## 使用方法

### 基本用法

根据 GEXF 文件中的图层-颜色映射关系，向 SVG 文件添加图例：

```bash
python LegendGephi.py <gexf_file> <svg_file>
```

### 参数

- `gexf_file`: 包含网络数据（具有图层和颜色信息）的 GEXF 文件路径
- `svg_file`: 要添加图例的 SVG 文件路径

### 选项

- `-o, --output`: 指定输出 SVG 文件路径（默认：自动生成 `<basename>_with_legend.svg`；永不覆盖源文件）
- `-p, --png`: 将输出的 SVG 转换为 PNG 格式
- `--png-output`: 指定 PNG 输出文件路径（默认：从 SVG 文件名自动生成）
- `--dpi`: 设置 PNG 输出分辨率（默认：300 DPI）

### 示例

**向 SVG 添加图例：**

```bash
python LegendGephi.py demo/Untitled.gexf demo/Untitled.svg
```

**添加图例并保存为新文件：**

```bash
python LegendGephi.py demo/Untitled.gexf demo/Untitled.svg -o demo/Untitled_with_legend.svg
```

**添加图例并转换为 PNG：**

```bash
python LegendGephi.py demo/Untitled.gexf demo/Untitled.svg -p --dpi 300
```

**添加图例、保存为新文件并转换为 PNG：**

```bash
python LegendGephi.py demo/Untitled.gexf demo/Untitled.svg -o demo/output.svg -p --png-output demo/output.png --dpi 300
```

## 工作原理

1. **GEXF 解析**：该工具解析 GEXF 文件并提取：

   - 节点 `layer` 属性（来自 `attvalue[@for="layer"]`）
   - 节点颜色信息（来自具有 RGB 值的 `viz:color` 元素）

2. **图例生成**：在 SVG 文件的右上角创建图例，包括：

   - 标题（"Layer"）
   - 代表每个图层的颜色方块
   - 每个颜色方块旁的图层标签
   - 带边框的半透明白色背景

3. **文本换行**（如需要）：自动换行长节点标签使其适应节点圆形

4. **PNG 转换**（可选）：以指定的 DPI 将最终的 SVG 转换为 PNG 格式

## GEXF 文件格式

该工具期望 GEXF 文件具有以下特征的节点：

- 在 `attvalue[@for="layer"]` 中定义的 `layer` 属性
- 在 `viz:color` 元素中具有 `r`、`g` 和 `b` 属性的颜色信息

示例 GEXF 节点结构：

```xml
<node id="1">
  <attvalue for="layer" value="Layer1"/>
  <viz:color r="255" g="0" b="0"/>
</node>
```

## SVG 文件格式

该工具期望 SVG 文件具有：

- `viewBox` 属性（或 `width` 和 `height` 属性）
- 包含 circle 元素的 `id="nodes"` 节点组
- 包含 text 元素的 `id="node-labels"` 标签组（可选，用于文本换行）

## 输出

图例被添加到 SVG 文件中，具有以下特征：

- **位置**：右上角，边距 50px
- **大小**：300px 宽度，根据图层数量自动调整高度
- **样式**：半透明白色背景（90% 不透明度）、黑色边框（2px）、Times New Roman 字体
- **布局**：颜色方块（24×24px）和图层标签（16px 字体）
- **标题**："Layer" 标题（20px 字体，加粗）

### 生成的文件

- **SVG 输出**：`<basename>_with_legend.svg`（包括文本换行调整和图例）
- **PNG 输出**（如果使用 `-p` 标记）：`<basename>.png` 或通过 `--png-output` 指定

## 日志输出

该工具使用 Python 的 logging 模块提供详细的处理信息：

- **INFO**：正常操作消息（解析进度、文件保存、转换状态）
- **WARNING**：非关键问题（同一图层的颜色不匹配、文件路径冲突）
- **ERROR**：关键错误（文件缺失、解析失败、转换错误）

## 故障排查

### PNG 转换失败

如果您收到关于 `cairosvg` 未找到的错误，请确保您已运行 `uv sync` 来安装所有依赖项：

```bash
uv sync
```

### 长节点标签未换行

确保您的 SVG 文件具有：

- 包含 circle 元素的 `id="nodes"` 组
- 包含具有与节点 ID 匹配的 `class` 属性的 text 元素的 `id="node-labels"` 组

### 图例位置错误

该工具使用 SVG 的 `viewBox` 属性来计算图例位置。如果位置错误：

- 验证您的 SVG 是否具有有效的 `viewBox` 属性
- 或确保在根 SVG 元素上设置了 `width` 和 `height` 属性

## 项目结构

```
LegendGephi/
├── LegendGephi.py          # 主脚本
├── README.md               # 英文文档
├── README_zh.md            # 中文文档（本文件）
├── pyproject.toml          # 项目配置
├── requirements.txt        # Python 依赖项
└── demo/                   # 示例文件
    ├── Untitled.gexf       # 示例 GEXF 文件
    ├── Untitled.svg        # 示例 SVG 文件
    └── Untitled_with_legend.svg  # 示例输出
```

## 许可证

本项目是开源的，可在 MIT 许可证下自由使用。


## 贡献

欢迎贡献！请随时提交 issue 或 pull request。对于主要更改，请先打开 issue 讨论您想要进行的更改。
