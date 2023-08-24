# Usage Instructions & Examples

## Basic Usage

To convert a PDB file into a PDF:

python -m src.protein_visualizer --input path/to/your/input.pdb

This will generate a PDF in your current directory.

## Configuration

You can use the default configuration file to adjust various settings. Modify the `config/default_settings.json` to adjust according to your needs.

## Examples

Example PDB files are located in the `examples/` directory. You can use these to test the functionality:

python -m src.protein_visualizer --input examples/sample1.pdb
