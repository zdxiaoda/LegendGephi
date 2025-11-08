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
    
    print(f"找到 {len(nodes)} 个节点\n")
    
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
                print(f"警告: layer '{layer}' 有不同的颜色值!")
                print(f"  已有颜色: {layer_color_map[layer]}")
                print(f"  新颜色: {color}\n")
    
    return layer_color_map

def add_legend_to_svg(svg_file, layer_color_map, output_file=None):
    """
    在SVG文件的右上方添加图例
    
    Args:
        svg_file: SVG文件路径
        layer_color_map: layer到color的映射字典
        output_file: 输出文件路径，如果为None则覆盖原文件
    """
    # SVG命名空间
    svg_ns = 'http://www.w3.org/2000/svg'
    
    # 解析SVG文件
    tree = ET.parse(svg_file)
    root = tree.getroot()
    
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
    
    # 计算右上角位置（留一些边距）
    margin = 50
    # 增大图例尺寸
    legend_width = 300  # 图例宽度增加到300
    legend_x = min_x + width - legend_width - margin
    legend_y = min_y + margin
    
    # 创建图例组（使用SVG命名空间）
    legend_group = ET.Element(f'{{{svg_ns}}}g', {'id': 'legend', 'class': 'legend'})
    
    # 图例参数（增大尺寸）
    title_font_size = 20  # 标题字体大小
    item_font_size = 16   # 项目字体大小
    color_box_size = 24   # 颜色方块大小
    item_spacing = 40     # 项目间距
    padding = 15          # 内边距
    
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
    
    # 保存文件（保持原始格式）
    output_path = output_file if output_file else svg_file
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
    
    # 美化图例组
    indent(legend_group, 1)
    
    # 保存文件
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    print(f"图例已添加到SVG文件: {output_path}")
    
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
        print("错误: 需要安装 cairosvg 库才能转换PNG")
        print("请运行: uv pip install cairosvg")
        return False
    
    if png_file is None:
        # 自动生成PNG文件名
        base_name = os.path.splitext(svg_file)[0]
        png_file = f"{base_name}.png"
    
    try:
        cairosvg.svg2png(url=svg_file, write_to=png_file, dpi=dpi)
        print(f"SVG已转换为PNG: {png_file} (DPI: {dpi})")
        return True
    except Exception as e:
        print(f"错误: SVG转PNG失败 - {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='解析GEXF文件并在SVG文件中添加图例')
    parser.add_argument('gexf_file', help='GEXF文件路径')
    parser.add_argument('svg_file', help='SVG文件路径')
    parser.add_argument('-o', '--output', help='输出SVG文件路径（默认覆盖原文件）')
    parser.add_argument('-p', '--png', action='store_true', help='将SVG转换为PNG')
    parser.add_argument('--png-output', help='PNG输出文件路径（默认自动生成）')
    parser.add_argument('--dpi', type=int, default=300, help='PNG输出分辨率（默认300）')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("解析GEXF文件 - 提取Layer和Color信息")
    print("=" * 60)
    print()
    
    try:
        # 解析GEXF文件
        layer_color_map = parse_gexf(args.gexf_file)
        
        # 输出结果
        print("=" * 60)
        print("Layer 和对应的 Color:")
        print("=" * 60)
        print()
        
        for layer, color in sorted(layer_color_map.items()):
            print(f"Layer: {layer}")
            print(f"Color: {color}")
            print("-" * 60)
        
        print(f"\n总共找到 {len(layer_color_map)} 个不同的Layer")
        print()
        
        # 在SVG文件中添加图例
        print("=" * 60)
        print("在SVG文件中添加图例...")
        print("=" * 60)
        output_svg = add_legend_to_svg(args.svg_file, layer_color_map, args.output)
        
        # 如果指定了PNG转换，则转换
        if args.png:
            print()
            print("=" * 60)
            print("将SVG转换为PNG...")
            print("=" * 60)
            svg_to_png(output_svg, args.png_output, args.dpi)
        
    except FileNotFoundError as e:
        print(f"错误: 找不到文件 - {e}")
    except ET.ParseError as e:
        print(f"错误: XML解析失败 - {e}")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

