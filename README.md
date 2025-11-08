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

### Prerequisites

- Python 3.10 or higher
- uv package manager

### Setup

Clone the repository and run:

```bash
uv sync
```

This will install all dependencies including optional PNG conversion support (cairosvg).

## Usage

### Basic Usage

Add a legend to an SVG file based on layer-color mappings from a GEXF file:

```bash
python LegendGephi.py <gexf_file> <svg_file>
```

### Arguments

- `gexf_file`: Path to the GEXF file containing network data with layer and color information
- `svg_file`: Path to the SVG file to add the legend to

### Options

- `-o, --output`: Specify output SVG file path (default: auto-generates `<basename>_with_legend.svg`; never overwrites source file)
- `-p, --png`: Convert the output SVG to PNG format
- `--png-output`: Specify PNG output file path (default: auto-generated from SVG filename)
- `--dpi`: Set PNG output resolution (default: 300 DPI)

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

- **Position**: Top-right corner with 50px margin
- **Size**: 300px width, auto height based on number of layers
- **Style**: Semi-transparent white background (90% opacity), black border (2px), Times New Roman font
- **Layout**: Color boxes (24×24px) with layer labels (16px font)
- **Title**: "Layer" header (20px font, bold)

### Generated Files

- **SVG Output**: `<basename>_with_legend.svg` (includes text wrapping adjustments and legend)
- **PNG Output** (if `-p` flag used): `<basename>.png` or as specified with `--png-output`

## Logging

The tool uses Python's logging module to provide detailed information about processing:

- **INFO**: Normal operation messages (parsing progress, file saves, conversion status)
- **WARNING**: Non-critical issues (mismatched colors for same layer, file path conflicts)
- **ERROR**: Critical errors (missing files, parsing failures, conversion errors)

## Troubleshooting

### PNG Conversion Fails

If you get an error about `cairosvg` not being found, ensure you ran `uv sync` to install all dependencies:

```bash
uv sync
```

### Long Node Labels Not Wrapping

Ensure your SVG file has:

- A group with `id="nodes"` containing circle elements
- A group with `id="node-labels"` containing text elements with `class` attributes matching node IDs

### Legend Positioning Issues

The tool uses the SVG's `viewBox` attribute to calculate legend position. If you get incorrect positioning:

- Verify your SVG has a valid `viewBox` attribute
- Or ensure `width` and `height` attributes are set on the root SVG element

## Project Structure

```
LegendGephi/
├── LegendGephi.py          # Main script
├── README.md               # English documentation (this file)
├── README_zh.md            # Chinese documentation
├── pyproject.toml          # Project configuration
├── requirements.txt        # Python dependencies
└── demo/                   # Example files
    ├── Untitled.gexf       # Sample GEXF file
    ├── Untitled.svg        # Sample SVG file
    └── Untitled_with_legend.svg  # Example output
```

## License

This project is open source and available for use under the MIT License.


## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests. For major changes, please open an issue first to discuss what you would like to change.
