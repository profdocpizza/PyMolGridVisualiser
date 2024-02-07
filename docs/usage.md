# Usage Instructions & Examples

## Basic Usage

You will always need to run this script from PyMolGridVisualiser directory.

### Using PDB Directory
To convert a directory containing PDB files into a grid-based PDF visualization, use the `--input_folder` argument:
```bash
python PATH/TO/protein_visualiser.py --input_folder PATH/TO/YOUR/PDBS/DIRECTORY/
```


### Using Text File
To convert a list of PDB files specified in a .txt file into a grid-based PDF visualization, use the `--input_txt` argument:
```bash
python PATH/TO/protein_visualiser.py --input_txt PATH/TO/YOUR/PDBS_LIST.txt
```

Refer to [`/examples/example_pdb_list.txt`](/examples/example_pdb_list.txt) for the structure and format of the text file.

### Outputs
Visualisation PDF file will be saved in `/outputs` directory. If you dont like the layout, you can play with Command-line Options above.

## Command-line Options
- `--input_folder INPUT_FOLDER`: Specify the path to the parent folder containing PDB files.
- `--input_txt INPUT_TXT`: Specify the path to a .txt file with paths to PDBs.
- `--sort_pdbs_in_pdf`: Sort PDB files alphabetically in the PDF. Enabled by default. Set to `False` to disable.
- `--output_directory OUTPUT_DIRECTORY`: Specify the directory where the resulting PDF will be saved.
- `--filename_pattern FILENAME_PATTERN`: Specify a pattern to match specific PDB files within the directory.
- `--num_files NUM_FILES`: Specify the number of PDB files to process from the directory.
- `--output_pdf_name OUTPUT_PDF_NAME`: Specify the name of the output PDF file.
- `--grid COLUMNS ROWS`: Define the grid layout for the visualisations in the PDF.
- `--write_filenames`: Add this flag if you want filenames to be included in the PDF.
- `--config CONFIG`: Path to a custom configuration file (by default it uses [`config/default_settings.json`](config/default_settings.json)).

## Default settings 
Default settings are located in the [`config/default_settings.json`](config/default_settings.json) file. Command-line options override the default settings.

## Custom PyMol scripting
If default settings in the [`config/default_settings.json`](config/default_settings.json) does not provide required flexibility, go and modify [`pdb_to_png.py`](src/pdb_to_png.py). 

- You need to modify `generate_image_from_pdb()` function by replacing `default_pymol_script()` with `your_custom_pymol_script()`.

- There is an optional `cofactor_binder_pymol_script()` function as an example. It can be used instead `default_pymol_script()`.