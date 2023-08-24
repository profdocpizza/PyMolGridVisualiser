# Usage Instructions & Examples

## Basic Usage

To convert a directory containing PDB files into a grid-based PDF visualization:

python src/protein_visualiser.py path/to/your/directory/


By default, this will generate a PDF in your current directory.

### Command-line Options

- `--output_directory OUTPUT_DIRECTORY`: Specify the directory where the resulting PDF will be saved.
  
- `--filename_pattern FILENAME_PATTERN`: Specify a pattern to match specific PDB files within the directory.

- `--num_files NUM_FILES`: Specify the number of PDB files to process from the directory.

- `--output_pdf_name OUTPUT_PDF_NAME`: Specify the name of the output PDF file.

- `--grid COLUMNS ROWS`: Define the grid layout for the visualizations in the PDF.

- `--write_filenames`: Add this flag if you want filenames to be included in the PDF.

- `--config CONFIG`: Path to a custom configuration file (by default it uses `config/default_settings.json`).

## Default Configuration

You can modify the default configuration file to adjust various settings. Default settings file is found in `config/default_settings.json`.


## Examples

Example PDB files are located in the `examples/` directory. You can use these to test the functionality:

python src/protein_visualiser.py examples/

