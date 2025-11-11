#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析GEXF文件，提取所有节点的layer和对应的color信息
并在SVG文件的右上方添加图例
"""

import xml.etree.ElementTree as ET
import sys
import argparse
import os
import re
import logging

def parse_gexf(gexf_file):
    """
    解析GEXF文件，提取所有节点的layer和color信息
    
    Args:
        gexf_file: GEXF文件路径
    
    Returns:
        dict: layer到color的映射字典
    """
    # 定义命名空间
    # 根元素有默认命名空间 http://gexf.net/1.3
    # viz元素有命名空间 http://gexf.net/1.3/viz
    gexf_ns = 'http://gexf.net/1.3'
    viz_ns = 'http://gexf.net/1.3/viz'
    
    # 解析XML文件
    tree = ET.parse(gexf_file)
    root = tree.getroot()
    
    # 存储layer到color的映射
    layer_color_map = {}
    
    # 查找所有节点（节点在gexf命名空间下）
    nodes = root.findall(f'.//{{{gexf_ns}}}node')
    
    logging.info(f"Found {len(nodes)} nodes\n")
    
    # 遍历每个节点
    for node in nodes:
        # 提取layer值
        layer = None
        attvalues = node.findall(f'.//{{{gexf_ns}}}attvalue[@for="layer"]')
        if attvalues:
            layer = attvalues[0].get('value')
        
        # 提取color值（viz:color在viz命名空间下）
        color = None
        color_elem = node.find(f'.//{{{viz_ns}}}color')
        
        if color_elem is not None:
            r = color_elem.get('r', '0')
            g = color_elem.get('g', '0')
            b = color_elem.get('b', '0')
            color = f"rgb({r}, {g}, {b})"
        
        # 如果layer和color都存在，添加到映射中
        if layer and color:
            # 如果该layer还没有记录，或者记录的颜色相同，则更新
            if layer not in layer_color_map:
                layer_color_map[layer] = color
            elif layer_color_map[layer] != color:
                # 如果同一个layer有不同的color，打印警告
                logging.warning(f"Warning: layer '{layer}' has different color values!")
                logging.warning(f"  Existing color: {layer_color_map[layer]}")
                logging.warning(f"  New color: {color}\n")
    
    return layer_color_map

def estimate_text_width(text, font_size, font_family='Times New Roman'):
    """
    估算文本宽度
    
    Args:
        text: 文本内容
        font_size: 字体大小
        font_family: 字体族
    
    Returns:
        float: 估算的文本宽度
    """
    # 对于Times New Roman等比例字体，使用0.6作为平均字符宽度系数
    # 这个系数可以根据实际字体调整
    char_width_factor = 0.6
    
    # 计算文本宽度（字符数 × 字体大小 × 系数）
    text_width = len(text) * float(font_size) * char_width_factor
    return text_width

def wrap_text_to_fit_diameter(text, font_size, node_diameter, font_family='Times New Roman'):
    """
    将文本换行以适应节点直径（仅按单词换行）
    
    Args:
        text: 原始文本
        font_size: 字体大小
        node_diameter: 节点直径
        font_family: 字体族
    
    Returns:
        list: 换行后的文本行列表
    """
    # 如果文本宽度小于节点直径，不需要换行
    text_width = estimate_text_width(text, font_size, font_family)
    if text_width <= node_diameter:
        return [text]
    
    # 需要换行，按单词分割文本
    words = text.split()
    if not words:
        return [text]
    
    lines = []
    current_line = []
    current_width = 0
    
    # 单词间距的宽度（大约为字体大小的0.3倍）
    space_width = float(font_size) * 0.3
    
    for word in words:
        word_width = estimate_text_width(word, font_size, font_family)
        
        # 如果当前行加上这个单词会超过节点直径，开始新行
        if current_line and current_width + space_width + word_width > node_diameter:
            lines.append(' '.join(current_line))
            current_line = [word]
            current_width = word_width
        else:
            if current_line:
                current_width += space_width
            current_line.append(word)
            current_width += word_width
    
    # 添加最后一行
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def can_fit_with_wrapping(text, font_size, node_diameter, font_family='Times New Roman'):
    """
    检查通过换行，文本是否能在指定字体大小下适应节点
    
    Args:
        text: 文本内容
        font_size: 字体大小
        node_diameter: 节点直径
        font_family: 字体族
    
    Returns:
        tuple: (是否适应, 换行后的行列表)
    """
    # 尝试换行
    lines = wrap_text_to_fit_diameter(text, font_size, node_diameter, font_family)
    
    # 检查所有行是否都能适应节点宽度
    available_width = node_diameter * 0.95
    for line in lines:
        line_width = estimate_text_width(line, font_size, font_family)
        if line_width > available_width:
            return False, lines
    
    # 检查总高度是否适应节点高度
    available_height = node_diameter * 0.95
    line_height = font_size * 1.2
    total_height = (len(lines) - 1) * line_height + font_size
    
    if total_height > available_height:
        return False, lines
    
    return True, lines

def calculate_optimal_font_size(text, node_diameter, font_family='Times New Roman', min_font_size=4, max_font_size=100):
    """
    根据文本和节点直径计算最优字体大小
    尽量提高字体大小到max_font_size，通过换行单词来适应
    
    Args:
        text: 文本内容
        node_diameter: 节点直径
        font_family: 字体族
        min_font_size: 最小字体大小
        max_font_size: 最大字体大小
    
    Returns:
        float: 计算出的最优字体大小
    """
    # 从最大字体开始，逐步降低，找到能适应的最大字体
    # 使用二分查找加速这个过程
    left, right = min_font_size, max_font_size
    optimal_size = min_font_size
    
    while left <= right:
        mid = (left + right) / 2
        can_fit, _ = can_fit_with_wrapping(text, mid, node_diameter, font_family)
        
        if can_fit:
            # 当前字体大小可以适应，尝试更大的
            optimal_size = mid
            left = mid + 0.5
        else:
            # 当前字体大小不能适应，尝试更小的
            right = mid - 0.5
    
    return max(optimal_size, min_font_size)

def adjust_node_labels_in_tree(tree, root, auto_font_size=False, min_font_size=None, max_font_size=None):
    """
    在内存中调整SVG树中节点标签的文本，使其适应节点直径（不保存文件）
    
    Args:
        tree: ElementTree对象
        root: 根元素
        auto_font_size: 是否自动调整字体大小以适应节点
        min_font_size: 最小字体大小（字体底线）
        max_font_size: 最大字体大小（初始目标，会根据最大节点调整）
    
    Returns:
        int: 修改的节点数量
    """
    svg_ns = 'http://www.w3.org/2000/svg'
    
    # 查找节点组和标签组
    nodes_group = root.find(f'.//{{{svg_ns}}}g[@id="nodes"]')
    labels_group = root.find(f'.//{{{svg_ns}}}g[@id="node-labels"]')
    
    if nodes_group is None or labels_group is None:
        logging.warning("Warning: Nodes or labels group not found, skipping text wrapping")
        return 0
    
    # 创建节点ID到节点信息的映射
    node_map = {}
    max_node_diameter = 0
    for circle in nodes_group.findall(f'.//{{{svg_ns}}}circle'):
        node_class = circle.get('class', '')
        node_r = float(circle.get('r', '0'))
        node_diameter = node_r * 2  # 直径 = 半径 × 2
        node_map[node_class] = node_diameter
        max_node_diameter = max(max_node_diameter, node_diameter)
    
    # 如果启用自动字体大小且指定了max_font_size，先在最大节点上计算目标字体
    actual_max_font_size = max_font_size
    if auto_font_size and max_font_size is not None and max_node_diameter > 0:
        # 第一阶段：找到最大节点对应的文本，在其上计算能达到的最大字体大小
        max_node_class = None
        max_node_text = None
        
        for text_elem in labels_group.findall(f'.//{{{svg_ns}}}text'):
            node_class = text_elem.get('class', '')
            if node_class in node_map and abs(node_map[node_class] - max_node_diameter) < 0.01:
                max_node_class = node_class
                max_node_text = (text_elem.text or '').strip()
                if max_node_text:
                    break
        
        # 在最大节点上计算能达到的最优字体大小
        if max_node_text:
            calc_min_font_size = min_font_size if min_font_size is not None else 4
            achievable_font_size = calculate_optimal_font_size(
                max_node_text, 
                max_node_diameter, 
                'Times New Roman', 
                calc_min_font_size, 
                max_font_size
            )
            actual_max_font_size = achievable_font_size
            logging.info(f"Smart sizing strategy:")
            logging.info(f"  Max node diameter: {max_node_diameter:.1f}px")
            logging.info(f"  Max node text: '{max_node_text[:30]}...' (len={len(max_node_text)})")
            logging.info(f"  Target max font size: {max_font_size:.1f}pt -> Achievable: {actual_max_font_size:.1f}pt")
            logging.info(f"  Using {actual_max_font_size:.1f}pt as ceiling for all nodes\n")
    
    # 处理每个文本标签
    modified_count = 0
    for text_elem in labels_group.findall(f'.//{{{svg_ns}}}text'):
        node_class = text_elem.get('class', '')
        if node_class not in node_map:
            continue
        
        # 获取文本内容和字体大小
        text_content = (text_elem.text or '').strip()
        if not text_content:
            continue
        
        # 首字母大写
        text_content = text_content.capitalize()
        
        font_size = float(text_elem.get('font-size', '12'))
        font_family = text_elem.get('font-family', 'Times New Roman')
        node_diameter = node_map[node_class]
        
        x = text_elem.get('x', '0')
        y = text_elem.get('y', '0')
        
        # 第一步：如果启用自动字体大小调整，计算最优字体大小
        if auto_font_size:
            # 先用原始字体大小检查是否需要换行
            text_width = estimate_text_width(text_content, font_size, font_family)
            if text_width > node_diameter:
                # 需要换行
                lines_initial = wrap_text_to_fit_diameter(text_content, font_size, node_diameter, font_family)
            else:
                lines_initial = [text_content]
            
            # 确定字体大小的范围
            # 使用 actual_max_font_size（由最大节点确定）而不是原始的 max_font_size
            calc_min_font_size = int(min_font_size) if min_font_size is not None else 4
            calc_max_font_size = int(actual_max_font_size) if actual_max_font_size is not None else 100
            
            # 对于多行文本，考虑多行所需的高度空间
            if len(lines_initial) > 1:
                # 多行情况：为每一行计算最优字体大小，取最小值
                optimal_sizes = []
                for line in lines_initial:
                    opt_size = calculate_optimal_font_size(line, node_diameter, font_family, calc_min_font_size, calc_max_font_size)
                    optimal_sizes.append(opt_size)
                optimal_font_size = min(optimal_sizes)
            else:
                # 单行情况：直接计算最优字体大小
                optimal_font_size = calculate_optimal_font_size(text_content, node_diameter, font_family, calc_min_font_size, calc_max_font_size)
            
            if optimal_font_size != font_size:
                text_elem.set('font-size', str(optimal_font_size))
                font_size = optimal_font_size
                modified_count += 1
                constraint_info = ""
                if min_font_size is not None or max_font_size is not None:
                    constraints = []
                    if min_font_size is not None:
                        constraints.append(f"min: {min_font_size:.1f}pt")
                    if max_font_size is not None:
                        constraints.append(f"max: {max_font_size:.1f}pt")
                    constraint_info = f" ({', '.join(constraints)})"
                logging.info(f"  Auto-adjusted font size for node '{node_class}': {text_content[:30]}... -> {optimal_font_size:.1f}pt{constraint_info}")
        
        # 第二步：检查最终字体大小下是否需要换行
        text_width = estimate_text_width(text_content, font_size, font_family)
        if text_width > node_diameter:
            # 需要换行
            lines_to_use = wrap_text_to_fit_diameter(text_content, font_size, node_diameter, font_family)
        else:
            lines_to_use = [text_content]
        
        # 第三步：更新文本内容（应用首字母大写）
        if len(lines_to_use) > 1:
            # 多行情况：使用tspan元素
            # 计算行高（字体大小的1.2倍）
            line_height = font_size * 1.2
            
            # 计算总高度，用于垂直居中
            total_height = (len(lines_to_use) - 1) * line_height
            start_y = float(y) - total_height / 2
            
            # 清除原始文本内容
            text_elem.text = None
            
            # 为每一行创建tspan元素
            for i, line in enumerate(lines_to_use):
                tspan = ET.SubElement(text_elem, f'{{{svg_ns}}}tspan', {
                    'x': x,
                    'y': str(start_y + i * line_height),
                    'text-anchor': 'middle',
                    'dominant-baseline': 'central'
                })
                tspan.text = line
            
            if auto_font_size:
                # 如果启用了自动字体大小，不重复计数
                pass
            else:
                modified_count += 1
            logging.info(f"  Wrapped node '{node_class}': {text_content[:30]}...")
        else:
            # 单行情况：直接更新文本元素
            text_elem.text = text_content
    
    return modified_count

def add_legend_to_svg(svg_file, layer_color_map, output_file=None, auto_font_size=False, min_font_size=None, max_font_size=None):
    """
    在SVG文件的右上方添加图例，同时进行节点标签换行调整
    只保存一个文件，不修改源文件
    
    Args:
        svg_file: SVG文件路径
        layer_color_map: layer到color的映射字典
        output_file: 输出文件路径，如果为None则自动生成新文件名（不覆盖原文件）
        auto_font_size: 是否自动调整节点字体大小以适应节点直径
        min_font_size: 最小字体大小（字体底线）
        max_font_size: 最大字体大小（字体上限）
    """
    # SVG命名空间
    svg_ns = 'http://www.w3.org/2000/svg'
    
    # 解析SVG文件
    tree = ET.parse(svg_file)
    root = tree.getroot()
    
    # 先进行节点标签换行和字体调整
    if auto_font_size:
        constraints = []
        if min_font_size is not None:
            constraints.append(f"min: {min_font_size:.1f}pt")
        if max_font_size is not None:
            constraints.append(f"max: {max_font_size:.1f}pt")
        if constraints:
            logging.info(f"Auto-adjusting node label font sizes ({', '.join(constraints)}) with text wrapping...")
        else:
            logging.info("Auto-adjusting node label font sizes and checking text wrapping...")
    else:
        logging.info("Checking and adjusting node label text...")
    modified_count = adjust_node_labels_in_tree(tree, root, auto_font_size, min_font_size, max_font_size)
    if modified_count > 0:
        if auto_font_size:
            logging.info(f"Adjusted font sizes and/or text wrapping for {modified_count} node labels\n")
        else:
            logging.info(f"Adjusted text wrapping for {modified_count} node labels\n")
    else:
        logging.info("All node label texts already fit within node diameter, no adjustment needed\n")
    
    # 获取SVG的viewBox属性
    viewbox = root.get('viewBox', '').split()
    if len(viewbox) == 4:
        min_x = float(viewbox[0])
        min_y = float(viewbox[1])
        width = float(viewbox[2])
        height = float(viewbox[3])
    else:
        # 如果没有viewBox，使用width和height
        width = float(root.get('width', '2579.6'))
        height = float(root.get('height', '1936.0'))
        min_x = -width / 2
        min_y = -height / 2
    
    # 计算右下角位置（留一些边距）
    margin = 50
    # 增大图例尺寸
    legend_width = 300  # 图例宽度
    legend_x = min_x + width - legend_width - margin
    
    # 图例参数
    title_font_size = 30  # 标题字体大小
    item_font_size = 22   # 项目字体大小
    color_box_size = 28   # 颜色方块大小
    item_spacing = 50     # 项目间距
    padding = 15          # 内边距
    
    # 首先计算图例高度来确定 legend_y
    bg_height_temp = len(layer_color_map) * item_spacing + padding * 2 + title_font_size + 10
    legend_y = min_y + height - bg_height_temp - margin  # 右下角位置
    
    # 创建图例组（使用SVG命名空间）
    legend_group = ET.Element(f'{{{svg_ns}}}g', {'id': 'legend', 'class': 'legend'})
    
    # 图例背景（白色半透明背景）
    bg_height = len(layer_color_map) * item_spacing + padding * 2 + title_font_size + 10
    bg_rect = ET.SubElement(legend_group, f'{{{svg_ns}}}rect', {
        'x': str(legend_x - padding),
        'y': str(legend_y - padding),
        'width': str(legend_width),
        'height': str(bg_height),
        'fill': 'white',
        'fill-opacity': '0.9',
        'stroke': 'black',
        'stroke-width': '2'
    })
    
    # 添加图例标题
    title = ET.SubElement(legend_group, f'{{{svg_ns}}}text', {
        'x': str(legend_x),
        'y': str(legend_y + title_font_size),
        'font-size': str(title_font_size),
        'font-weight': 'bold',
        'fill': '#000000',
        'font-family': 'Times New Roman, serif'
    })
    title.text = 'Layer'
    
    # 为每个layer添加图例项
    y_offset = title_font_size + 15
    for i, (layer, color) in enumerate(sorted(layer_color_map.items())):
        item_y = legend_y + y_offset + i * item_spacing
        
        # 颜色方块（增大）
        color_rect = ET.SubElement(legend_group, f'{{{svg_ns}}}rect', {
            'x': str(legend_x),
            'y': str(item_y - color_box_size // 2 +15),
            'width': str(color_box_size),
            'height': str(color_box_size),
            'fill': color,
            'stroke': '#000000',
            'stroke-width': '1'
        })
        
        # 文本标签（增大字体）
        text = ET.SubElement(legend_group, f'{{{svg_ns}}}text', {
            'x': str(legend_x + color_box_size + 10),
            'y': str(item_y + item_font_size // 3 + 15),
            'font-size': str(item_font_size),
            'fill': '#000000',
            'font-family': 'Times New Roman, serif'
        })
        text.text = layer
    
    # 将图例添加到SVG根元素
    root.append(legend_group)
    
    # 确定输出文件路径（确保不覆盖源文件）
    if output_file is None:
        base_name = os.path.splitext(svg_file)[0]
        output_path = f"{base_name}_with_legend.svg"
    else:
        output_path = output_file
    
    # 确保输出文件路径不等于源文件路径
    if os.path.abspath(output_path) == os.path.abspath(svg_file):
        base_name = os.path.splitext(svg_file)[0]
        output_path = f"{base_name}_with_legend.svg"
        logging.warning(f"Warning: Output file cannot be the same as source file, automatically renamed to: {output_path}")
    
    # 使用原始格式保存，保持DOCTYPE声明
    ET.register_namespace('', svg_ns)
    
    # 美化XML输出
    def indent(elem, level=0):
        """美化XML输出"""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                indent(child, level+1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    # 美化整个文档
    indent(root)
    
    # 保存文件（只保存一次，包含换行调整和图例）
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    logging.info(f"Saved SVG file (with text wrapping and legend): {output_path}")
    
    return output_path

def svg_to_png(svg_file, png_file=None, dpi=300):
    """
    将SVG文件转换为PNG文件
    
    Args:
        svg_file: SVG文件路径
        png_file: PNG输出文件路径，如果为None则自动生成
        dpi: 输出分辨率（默认300）
    """
    try:
        import cairosvg
    except ImportError:
        logging.error("Error: cairosvg library is required to convert PNG")
        logging.error("Please run: uv pip install cairosvg")
        return False
    
    if png_file is None:
        # 自动生成PNG文件名
        base_name = os.path.splitext(svg_file)[0]
        png_file = f"{base_name}.png"
    
    try:
        cairosvg.svg2png(url=svg_file, write_to=png_file, dpi=dpi)
        logging.info(f"SVG converted to PNG: {png_file} (DPI: {dpi})")
        return True
    except Exception as e:
        logging.error(f"Error: SVG to PNG conversion failed - {e}")
        return False

def main():
    """主函数"""
    # 配置logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    parser = argparse.ArgumentParser(description='Parse GEXF file and add legend to SVG file')
    parser.add_argument('gexf_file', help='GEXF file path')
    parser.add_argument('svg_file', help='SVG file path')
    parser.add_argument('-o', '--output', help='Output SVG file path (default: auto-generate new filename, does not overwrite source file)')
    parser.add_argument('-p', '--png', action='store_true', help='Convert SVG to PNG')
    parser.add_argument('--png-output', help='PNG output file path (default: auto-generate)')
    parser.add_argument('--dpi', type=int, default=300, help='PNG output resolution (default: 300)')
    parser.add_argument('--auto-font-size', action='store_true', help='Auto-adjust node label font sizes to fit within node diameter')
    parser.add_argument('--min-font-size', type=float, help='Minimum font size (font size floor, requires --auto-font-size)')
    parser.add_argument('--max-font-size', type=float, help='Maximum font size (font size ceiling, requires --auto-font-size, scales proportionally based on node size)')
    
    args = parser.parse_args()
    
    logging.info("=" * 60)
    logging.info("Parsing GEXF file - Extracting Layer and Color information")
    logging.info("=" * 60)
    logging.info("")
    
    try:
        # 解析GEXF文件
        layer_color_map = parse_gexf(args.gexf_file)
        
        # 输出结果
        logging.info("=" * 60)
        logging.info("Layer and corresponding Color:")
        logging.info("=" * 60)
        logging.info("")
        
        for layer, color in sorted(layer_color_map.items()):
            logging.info(f"Layer: {layer}")
            logging.info(f"Color: {color}")
            logging.info("-" * 60)
        
        logging.info(f"\nFound {len(layer_color_map)} different Layers")
        logging.info("")
        
        # 在SVG文件中添加图例并调整节点标签（只保存一个文件）
        logging.info("=" * 60)
        logging.info("Processing SVG file (text wrapping and legend addition)...")
        logging.info("=" * 60)
        output_svg = add_legend_to_svg(args.svg_file, layer_color_map, args.output, args.auto_font_size, args.min_font_size, args.max_font_size)
        
        # 如果指定了PNG转换，则转换
        if args.png:
            logging.info("")
            logging.info("=" * 60)
            logging.info("Converting SVG to PNG...")
            logging.info("=" * 60)
            svg_to_png(output_svg, args.png_output, args.dpi)
        
    except FileNotFoundError as e:
        logging.error(f"Error: File not found - {e}")
    except ET.ParseError as e:
        logging.error(f"Error: XML parsing failed - {e}")
    except Exception as e:
        logging.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

