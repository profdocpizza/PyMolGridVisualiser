import os
import concurrent.futures
import functools
from PIL import Image
from fpdf import FPDF
from PyPDF2 import PdfFileMerger
# import pymol
from pymol import cmd
import json
import time
import argparse
import pymol

def check_license_in_directory():
    """Search for a .lic file in the current directory and check its license."""
    license_file = next((file for file in os.listdir() if file.endswith(".lic")), None)

    if license_file:
        pymol.licensing.check_license_file(license_file)
        return pymol.licensing.get_info()
    else:
        return "No .lic file found in the current directory."

def load_settings(path):
    with open(path, 'r') as f:
        return json.load(f)

def create_arg_parser():
    parser = argparse.ArgumentParser(description="A protein visualizer tool that generates PDFs from PDB files.")

    # Required arguments
    parser.add_argument("pdb_directory", type=str, help="Path to the directory containing PDB files.")
    
    # Optional arguments
    parser.add_argument("--output_directory", type=str, default=None, help="Path to the directory where the output PDF will be saved.")
    parser.add_argument("--filename_pattern", type=str, default=None, help="Pattern to match specific PDB files.")
    parser.add_argument("--num_files", type=int, default=None, help="Number of PDB files to visualize.")
    parser.add_argument("--output_pdf_name", type=str, default=None, help="Custom name for the output PDF.")
    parser.add_argument("--grid", type=int, nargs=2, default=None, metavar=("COLUMNS", "ROWS"), help="Grid dimensions for arranging images in the PDF.")
    parser.add_argument("--write_filenames", action="store_true", default=None, help="Include the filenames in the output PDF.")
    parser.add_argument("--config", type=str, default="config/default_settings.json", help="Path to custom configuration settings in JSON format.")
    
    return parser



parser = create_arg_parser()
args = parser.parse_args()

SETTINGS = load_settings(args.config)

cmd.set("ray_trace_frames", SETTINGS["pymol_settings"]["ray_trace_frames"])
cmd.set("ray_shadows", SETTINGS["pymol_settings"]["ray_shadows"])
cmd.set("antialias", SETTINGS["pymol_settings"]["antialias"])
cmd.set("orthoscopic", SETTINGS["pymol_settings"]["orthoscopic"])
cmd.set("ray_trace_mode", SETTINGS["pymol_settings"]["ray_trace_mode"])

def process_pdb_file(args):
    pdb_file, temp_directory = args
    base_name = os.path.basename(pdb_file)
    image_file = os.path.join(temp_directory, os.path.splitext(base_name)[0] + ".png")
    generate_image_from_pdb(pdb_file, image_file)
    return image_file

def generate_image_from_pdb(pdb_path, output_path):
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


def generate_pdf_for_pages(start, end, image_files, grid, temp_directory, write_filenames=False):
    # pdf = FPDF(orientation="L", unit="mm", format="A4")
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
        if write_filenames:
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
    
def list_pdb_files_in_directory(directory, filename_pattern=""):
    """Returns all pdb files in a given directory matching the filename_pattern."""
    return [os.path.join(directory, entry.name) for entry in os.scandir(directory) if entry.name.endswith('.pdb') and filename_pattern in os.path.splitext(entry.name)[0]]

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
