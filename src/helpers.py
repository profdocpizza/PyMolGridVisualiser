import os
import concurrent.futures
import functools
from PIL import Image
from fpdf import FPDF
from PyPDF2 import PdfFileMerger
import json
import time
import argparse
import pymol
from pymol import cmd

# Calculate the script directory once at the module level
script_directory = os.path.dirname(os.path.abspath(__file__))


def check_license_in_directory():
    """Search for a .lic file starting one directory up from the helpers.py directory and scanning all subdirectories."""
    start_directory = os.path.abspath(os.path.join(script_directory, os.pardir))
    for root, dirs, files in os.walk(start_directory):
        for file in files:
            if file.endswith(".lic"):
                license_file_path = os.path.join(root, file)
                print(f"Found pymol license at {license_file_path}")
                pymol.licensing.check_license_file(license_file_path)
                return pymol.licensing.get_info()
    return "No .lic file found in the parent directory or its subdirectories."

def load_settings(path):
    with open(path, 'r') as f:
        return json.load(f)

def create_arg_parser():
    parser = argparse.ArgumentParser(description="A protein visualizer tool that generates PDFs from PDB files.")
    
    # Create a mutually exclusive group for --input_folder and --input_txt
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--input_folder", type=str, help="Path to the parent folder containing PDB files.")
    input_group.add_argument("--input_txt", type=str, help="Path to a .txt file with paths to PDBs.")


    # Optional arguments
    parser.add_argument("--filename_pattern", type=str, default=None, help="Pattern to match specific PDB files.")
    parser.add_argument("--num_files", type=int, default=None, help="Number of PDB files to visualize.")
    parser.add_argument("--output_pdf_name", type=str, default=None, help="Custom name for the output PDF.")
    parser.add_argument("--grid", type=int, nargs=2, default=None, metavar=("COLUMNS", "ROWS"), help="Grid dimensions for arranging images in the PDF.")
    parser.add_argument("--write_filenames", action="store_true", default=None, help="Include the filenames in the output PDF.")
    parser.add_argument("--sort_pdbs_in_pdf", action='store_true', default=None, help="Sort PDB files alphabetically before adding to the PDF.")

    default_output_directory = os.path.join(os.path.join(script_directory, os.pardir), 'outputs')
    parser.add_argument("--output_directory", type=str, default=default_output_directory, help="Path to the directory where the output PDF will be saved.")
    default_config_path = os.path.join(os.path.join(script_directory, os.pardir), 'config', 'default_settings.json')
    parser.add_argument("--config", type=str, default=default_config_path, help="Path to custom configuration settings in JSON format.")
    
    return parser


def process_pdb_file( pdb_file, temp_directory, SETTINGS):
    base_name = os.path.basename(pdb_file)
    image_file = os.path.join(temp_directory, os.path.splitext(base_name)[0] + ".png")
    generate_image_from_pdb(pdb_file, image_file, SETTINGS) 
    return image_file

def generate_image_from_pdb(pdb_path, output_path, SETTINGS):
    cmd.delete("all")
    cmd.load(pdb_path,quiet=1)
    cmd.bg_color(SETTINGS["pymol_settings"]["background_colour"])
    cmd.hide("all")
    cmd.show(SETTINGS["pymol_settings"]["representation"], "all")
    if SETTINGS["pymol_settings"]["colour_spectrum"]:
        cmd.spectrum("count", selection="all")
    else:
        cmd.color(SETTINGS["pymol_settings"]["colour"], "all")
    # Disable ray tracing for faster rendering
    cmd.png(output_path, width=SETTINGS["image_dimensions"]["width"], height=SETTINGS["image_dimensions"]["height"], ray=0, quiet=1)
    while not os.path.exists(output_path):
        time.sleep(0.02)
    cmd.delete("all")


def generate_pdf_for_pages(start, end, image_files, temp_directory, SETTINGS):
    grid = (SETTINGS["grid"]["columns"], SETTINGS["grid"]["rows"])
    pdf = FPDF(orientation=SETTINGS["pdf_settings"]["orientation"], 
            unit=SETTINGS["pdf_settings"]["unit"], 
            format=SETTINGS["pdf_settings"]["format"])

    cell_width = (297 - 20) / grid[0]
    cell_height = (210 - 20) / grid[1]
    images_count = 0

    # Calculate the font size based on cell width and clamp between min and max sizes
    font_size = cell_width * 0.15 * SETTINGS["pdf_settings"]["font_size_multiplier"] # Setting font size proportional to cell width
    font_size = max(2, min(font_size, 14))  # Clamping between 4 and 10

    # Set font and determine base height
    pdf.set_font("Helvetica", size=font_size)  # Changed font to Helvetica
    base_height = pdf.get_string_width('A') * 1.5  # Assuming width is a good proxy for height, and we inflate it a bit.

    pdf.set_auto_page_break(auto=True, margin=0)  # reduce line spacing when the text is split

    pdf.add_page()  # Add a new page for the current set of images
    for image_path in image_files:
        # Calculate X and Y position for image placement.
        x = 10 + (images_count % grid[0]) * cell_width
        y = 10 + ((images_count // grid[0]) % grid[1]) * cell_height

        # Calculate width and height for the image to maintain aspect ratio.
        with Image.open(image_path) as img:
            img_width, img_height = img.size
            aspect_ratio = img_width / img_height
            new_width = cell_width
            new_height = cell_width / aspect_ratio
            if new_height > cell_height:
                new_height = cell_height
                new_width = cell_height * aspect_ratio

        # Add the image to the PDF.
        pdf.image(image_path, x, y, new_width, new_height)

        # If write_filenames is True, write the image filename within the image boundaries at the bottom.
        if SETTINGS["write_filenames"]:
            filename_line_spacing = base_height / 1  # Adjust the filename_space dynamically based on the base_height
            filename = os.path.splitext(os.path.basename(image_path))[0]
            text_y = y + new_height - filename_line_spacing
            text_width = new_width
            pdf.set_fill_color(255, 255, 255)  # Set background color to white
            pdf.set_xy(x, text_y)
            pdf.multi_cell(text_width, filename_line_spacing, filename, border=0, align='C', fill=True)


        images_count += 1

    # Save the temporary PDF file with a unique name based on the start index.
    temp_pdf_path = os.path.join(temp_directory, f"temp_{start}.pdf")
    pdf.output(temp_pdf_path, "F")
    return temp_pdf_path


def split_images_for_pages(image_files, grid):
    images_per_page = grid[0] * grid[1]
    num_pages = len(image_files) // images_per_page
    if len(image_files) % images_per_page > 0:
        num_pages += 1  # If there's a remainder, we need an additional page

    image_splits = []
    for i in range(num_pages):
        start = i * images_per_page
        end = start + images_per_page
        image_splits.append((start, end, image_files[start:end]))
    
    return image_splits

def merge_temp_pdfs(temp_pdf_paths,output_pdf_path):      
    # Merge all the temporary PDFs into one
    merger = PdfFileMerger()
    for pdf in temp_pdf_paths:
        merger.append(pdf)

    merger.write(output_pdf_path)
    merger.close()

    print(f"Final PDF saved to {output_pdf_path}")

def remove_files(paths):
    # Cleanup temporary files
    for path in paths:
        os.remove(path)
        
def get_pdb_paths_from_file(file_path):
    """
    Extracts and validates PDB paths from a provided .txt file.

    Args:
    - file_path (str): Path to the .txt file containing paths to PDBs.

    Returns:
    - List[str]: List of validated PDB paths.

    Raises:
    - FileNotFoundError: If the provided file does not exist.
    - ValueError: If a line in the file doesn't point to an existing PDB file.
    """

    # Check if the provided file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The provided file {file_path} does not exist.")

    pdb_paths = []

    # Read the file and extract PDB paths
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith("#"):
                continue
            line = line.strip()  # Remove whitespace and newline characters
            if line:  # Ensure the line is not empty
                # Validate if it's a valid path and points to a .pdb file
                if not os.path.exists(line):
                    raise ValueError(f"The path {line} mentioned in the file does not exist.")
                elif not line.lower().endswith('.pdb'):
                    raise ValueError(f"The path {line} does not point to a .pdb file.")
                else:
                    pdb_paths.append(line)

    return pdb_paths

def list_pdb_files_in_directory(directory, filename_pattern=""):
    """Returns all pdb files in a given directory matching the filename_pattern."""
    # return [os.path.join(directory, entry.name) for entry in os.scandir(directory) if entry.name.endswith('.pdb') and filename_pattern in os.path.splitext(entry.name)[0]]
    return [os.path.join(directory, entry.name) for entry in os.scandir(directory) if entry.name.endswith('.pdb')]

def list_all_pdb_files(root_dir, filename_pattern=""):
    directories = []
    for dirpath, _, _ in os.walk(root_dir):
        directories.append(dirpath)
        
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Pass the same filename_pattern to all worker threads
        partial_func = functools.partial(list_pdb_files_in_directory, filename_pattern=filename_pattern)
        results = list(executor.map(partial_func, directories))
    # Flatten list of lists
    pdbs = [item for sublist in results for item in sublist]
    return pdbs

def wait_until_all_files_are_present(paths):
    all_files_present = False
    while not all_files_present:
        if all([os.path.exists(image) for image in paths]):
            all_files_present = True
        else:
            print("Waiting for all image files to be present...")
            time.sleep(0.1)

def create_unique_temp_directory(output_directory, path_name, filename_pattern):
    # Create a unique identifier for the temporary directory
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    
    # Create temporary directory name
    temp_directory_name = f"{path_name}_containing_{filename_pattern}_{timestamp}"
    temp_directory = os.path.join(output_directory, temp_directory_name)
    
    # Ensure the directory does not exist and then create it
    if not os.path.exists(temp_directory):
        os.makedirs(temp_directory)
        return temp_directory
    else:
        # Raise an error if the directory already exists
        raise FileExistsError(f"The directory {temp_directory} already exists. Please remove it manually or run the script again.")
    
def main():
    parser = create_arg_parser()
    args = parser.parse_args()

    SETTINGS = load_settings(args.config)

    cmd.set("ray_trace_frames", SETTINGS["pymol_settings"]["ray_trace_frames"])
    cmd.set("ray_shadows", SETTINGS["pymol_settings"]["ray_shadows"])
    cmd.set("antialias", SETTINGS["pymol_settings"]["antialias"])
    cmd.set("orthoscopic", SETTINGS["pymol_settings"]["orthoscopic"])
    cmd.set("ray_trace_mode", SETTINGS["pymol_settings"]["ray_trace_mode"])

if __name__ == '__main__':
    main()