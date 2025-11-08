# LegendGephi

A Python tool for parsing GEXF (Graph Exchange XML Format) files and adding interactive legends to SVG network visualizations. LegendGephi extracts layer and color information from GEXF nodes and automatically generates a legend in the top-right corner of SVG files.

## Features

- **GEXF Parsing**: Extracts layer and color attributes from GEXF network files
- **Automatic Legend Generation**: Adds a color-coded legend to SVG visualizations showing layer-color mappings
- **Text Wrapping**: Automatically adjusts node labels to fit within node diameters
- **SVG to PNG Conversion**: Optional conversion of SVG files to high-resolution PNG images

## Requirements

- Python 3.10 or higher
- `cairosvg` (optional, only required for PNG conversion)

## Installation

### Using uv (Recommended)

```bash
uv pip install -e .
```

### Using pip

```bash
pip install cairosvg
```

## Usage

### Basic Usage

Add a legend to an SVG file based on layer-color mappings from a GEXF file:

```bash
python LegendGephi.py <gexf_file> <svg_file>
```

### Options

- `-o, --output`: Specify output SVG file path (default: overwrites input file)
- `-p, --png`: Convert the output SVG to PNG format
- `--png-output`: Specify PNG output file path (default: auto-generated from SVG filename)
- `--dpi`: Set PNG output resolution (default: 300)

### Examples

**Add legend to SVG:**

```bash
python LegendGephi.py demo/Untitled.gexf demo/Untitled.svg
```

**Add legend and save to new file:**

```bash
python LegendGephi.py demo/Untitled.gexf demo/Untitled.svg -o demo/Untitled_with_legend.svg
```

**Add legend and convert to PNG:**

```bash
python LegendGephi.py demo/Untitled.gexf demo/Untitled.svg -p --dpi 300
```

**Add legend, save to new file, and convert to PNG:**

```bash
python LegendGephi.py demo/Untitled.gexf demo/Untitled.svg -o demo/output.svg -p --png-output demo/output.png --dpi 300
```

## How It Works

1. **GEXF Parsing**: The tool parses the GEXF file and extracts:

   - Node `layer` attributes (from `attvalue[@for="layer"]`)
   - Node color information (from `viz:color` elements with RGB values)

2. **Legend Generation**: Creates a legend in the top-right corner of the SVG file with:

   - A title ("Layer")
   - Color boxes representing each layer
   - Layer labels next to each color box
   - Semi-transparent white background with border

3. **Text Wrapping** (if needed): Automatically wraps long node labels to fit within node circles

4. **PNG Conversion** (optional): Converts the final SVG to PNG format at specified DPI

## GEXF File Format

The tool expects GEXF files with nodes that have:

- A `layer` attribute defined in `attvalue[@for="layer"]`
- Color information in `viz:color` elements with `r`, `g`, and `b` attributes

Example GEXF node structure:

```xml
<node id="1">
  <attvalue for="layer" value="Layer1"/>
  <viz:color r="255" g="0" b="0"/>
</node>
```

## SVG File Format

The tool expects SVG files with:

- A `viewBox` attribute (or `width` and `height` attributes)
- Node groups with `id="nodes"` containing circle elements
- Label groups with `id="node-labels"` containing text elements (optional, for text wrapping)

## Output

The legend is added to the SVG file with:

- Position: Top-right corner with 50px margin
- Size: 300px width, auto height based on number of layers
- Style: Semi-transparent white background, black border, Times New Roman font
- Layout: Color boxes (24×24px) with layer labels (16px font)

## License

This project is open source and available for use.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
