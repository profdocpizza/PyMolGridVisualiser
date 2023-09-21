# Usage Instructions & Examples

## Basic Usage

You will always need to run this script from PyMolGridVisualiser directory.

### Using PDB Directory
To convert a directory containing PDB files into a grid-based PDF visualization:
    ```
    python src/protein_visualiser.py path/to/your/directory/
    ```

### Using Text File
To convert a list of PDB files specified in a .txt file into a grid-based PDF visualization:
    ```
    python src/protein_visualiser.py path/to/your/pdb_list.txt
    ```
Refer to `/examples/example_pdb_list.txt` for the structure and format of the text file.

### Outputs
Visualisation PDF file will be saved in `/outputs` directory. If you dont like the layout, you can play with Command-line Options above.

## Command-line Options

- `--output_directory OUTPUT_DIRECTORY`: Specify the directory where the resulting PDF will be saved.
  
- `--filename_pattern FILENAME_PATTERN`: Specify a pattern to match specific PDB files within the directory.

- `--num_files NUM_FILES`: Specify the number of PDB files to process from the directory.

- `--output_pdf_name OUTPUT_PDF_NAME`: Specify the name of the output PDF file.

- `--grid COLUMNS ROWS`: Define the grid layout for the visualisations in the PDF.

- `--write_filenames`: Add this flag if you want filenames to be included in the PDF.

- `--config CONFIG`: Path to a custom configuration file (by default it uses `config/default_settings.json`).

## Default settings 

Default settings are located in `config/default_settings.json` file. Command-line options override the default settings. 