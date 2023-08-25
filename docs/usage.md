# Usage Instructions & Examples

## Basic Usage

To convert a directory containing PDB files into a grid-based PDF visualization:
    ```
    python src/protein_visualiser.py path/to/your/directory/
    ```

By default, this will generate a PDF in your /outputs directory. 

### Command-line Options

- `--output_directory OUTPUT_DIRECTORY`: Specify the directory where the resulting PDF will be saved.
  
- `--filename_pattern FILENAME_PATTERN`: Specify a pattern to match specific PDB files within the directory.

- `--num_files NUM_FILES`: Specify the number of PDB files to process from the directory.

- `--output_pdf_name OUTPUT_PDF_NAME`: Specify the name of the output PDF file.

- `--grid COLUMNS ROWS`: Define the grid layout for the visualizations in the PDF.

- `--write_filenames`: Add this flag if you want filenames to be included in the PDF.

- `--config CONFIG`: Path to a custom configuration file (by default it uses `config/default_settings.json`).

## Examples

Example PDB files are located in the `examples/` directory. You can use these to test the functionality.

First you need to unzip the pdb files:
    ```
    unzip examples/pdbs/all_pdbs.zip -d examples/pdbs/
    ```

Then you can run the visualiser with default settings like:
    ```
    python src/protein_visualiser.py examples/pdbs
    ```

Visualisation PDF file will be saved in `/outputs` directory. If you dont like the layout, you can play with Command-line Options above.