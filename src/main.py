import os
import concurrent.futures
import functools
import random
import pymol
import time
from pymol import cmd
# pymol.pymol_argv = ["pymol", "-qc"]
# pymol.finish_launching()  breaks pymol with Pool() as pool: image generation
from fpdf import FPDF
from PIL import Image
from multiprocessing import Pool
from PyPDF2 import PdfFileMerger
import shutil
pymol.licensing.check_license_file("./pymolLicenseFile.lic")
print(pymol.licensing.get_info())

cmd.set("ray_trace_frames", 0)
cmd.set("ray_shadows", "off")
cmd.set("antialias", 0)
cmd.set("orthoscopic", "on")

def process_pdb_file(args):
    pdb_file, temp_directory = args
    base_name = os.path.basename(pdb_file)
    image_file = os.path.join(temp_directory, os.path.splitext(base_name)[0] + ".png")
    generate_image_from_pdb(pdb_file, image_file)
    return image_file

def generate_image_from_pdb(pdb_path, output_path):
    cmd.delete("all")
    cmd.load(pdb_path,quiet=1)
    cmd.bg_color("white")
    cmd.hide("all")
    cmd.show("cartoon", "all")
    cmd.color("skyblue", "all")
    # Disable ray tracing for faster rendering
    cmd.png(output_path, width=400, height=400, ray=0, quiet=1)
    # print(f"Saved at {output_path}")
    while not os.path.exists(output_path):
        # print("sleeping")
        time.sleep(0.02)
    cmd.delete("all")


def generate_pdf_for_pages(start, end, image_files, grid, temp_directory, write_filenames=False):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    cell_width = (297 - 20) / grid[0]
    cell_height = (210 - 20) / grid[1]
    images_count = 0

    # Calculate the font size based on cell width and clamp between min and max sizes
    font_size = cell_width * 0.12  # Setting font size proportional to cell width
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

def main(pdb_directory, output_directory, filename_pattern="", num_files=48, output_pdf_name=None, grid=(3, 4), write_filenames=True):
    # Create temporary directory for the images and PDF
    path_name = pdb_directory.replace('/','_').strip('_')
    temp_directory = f"{output_directory}/{path_name}_containing_{filename_pattern}"
    if not os.path.exists(temp_directory):
        os.mkdir(temp_directory)

    # give name and path to output pdf
    if output_pdf_name is not None:
        output_pdf_path = os.path.join(output_directory, f"{output_pdf_name.strip('.pdf')}.pdf")
    else:
        if filename_pattern == "":
            output_pdf_path = os.path.join(output_directory, f"{path_name}_all.pdf")
        else:
            output_pdf_path = os.path.join(output_directory, f"{path_name}_containing_{filename_pattern}.pdf")

    # filter pdbs from given directory. look deeply
    print(f"Filtering .pdb files that contain '{filename_pattern}'")
    all_files = list_all_pdb_files(pdb_directory,filename_pattern)
    print(f"Found {len(all_files)} .pdb files containing '{filename_pattern}'")
    matching_files = [f for f in all_files if filename_pattern in os.path.basename(f)]
    if len(matching_files)<1:
        raise ValueError(f"No PDB files found matching pattern: '{filename_pattern}' in the pdb_directory: '{pdb_directory}'")

    # select files at random
    selected_files = random.sample(matching_files, min(num_files, len(matching_files)))
    selected_files = sorted(selected_files)
    print(f"Selected {len(selected_files)} files at random")
    
    # Create and save the images
    print(f"Generating {len(selected_files)} images with pymol")
    with Pool() as pool:
        image_paths = pool.map(process_pdb_file, [(pdb, temp_directory) for pdb in selected_files])

    # Check if all images are present
    wait_until_all_files_are_present(image_paths)


    print("Creating PDF pages...")
    image_splits = split_images_for_pages(image_paths, grid)
    with Pool() as pool:
        temp_pdf_paths = pool.starmap(generate_pdf_for_pages, [(start, end, image_subset, grid, temp_directory, write_filenames) for start, end, image_subset in image_splits])
    print("Assembling PDF...")
    merge_temp_pdfs(temp_pdf_paths,output_pdf_path)

    # clean up temporary files and dir
    # remove_files(set(temp_pdf_paths))
    # remove_files(set(image_paths))
    # os.rmdir(temp_directory)
    shutil.rmtree(temp_directory)

main("/scratch/deltaProteins/collabFoldResults/outputs", "/home/tadas/bin/ProteinVisualiser","b3ii",num_files=600,grid=(20, 10)) # grid = (cols,rows)
# main("/scratch/deltaProteins/downloads", "/home/tadas/bin/ProteinVisualiser","b",num_files=60,grid=(6,4))