import os
import random
from multiprocessing import Pool
import shutil
import pymol
import json

    
# Import helper functions
from helpers import (
    process_pdb_file,
    generate_pdf_for_pages,
    split_images_for_pages,
    merge_temp_pdfs,
    list_all_pdb_files,
    wait_until_all_files_are_present,
    remove_files,
    create_arg_parser,
    load_settings
    
)

pymol.licensing.check_license_file("./pymolLicenseFile.lic")
print(pymol.licensing.get_info())



def main(pdb_directory, output_directory, filename_pattern="", num_files=48, output_pdf_name=None, grid=(3, 4), write_filenames=True):
    parser = create_arg_parser()
    args = parser.parse_args()

    # Load settings
    SETTINGS = load_settings(args.config)
    
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

if __name__ == "__main__":
    main("/scratch/deltaProteins/collabFoldResults/outputs", "/home/tadas/bin/ProteinVisualiser/outputs","b3ii",num_files=SETTINGS["num_files"], grid=(SETTINGS["grid"]["columns"], SETTINGS["grid"]["rows"]))

# main("/scratch/deltaProteins/collabFoldResults/outputs", "/home/tadas/bin/ProteinVisualiser","b3ii",num_files=600,grid=(20, 10)) # grid = (cols,rows)
# main("/scratch/deltaProteins/downloads", "/home/tadas/bin/ProteinVisualiser","b",num_files=60,grid=(6,4))