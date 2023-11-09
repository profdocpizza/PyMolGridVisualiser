import os
import random
from multiprocessing import Pool
import shutil
import time
from helpers import (
    process_pdb_file,
    generate_pdf_for_pages,
    split_images_for_pages,
    merge_temp_pdfs,
    list_all_pdb_files,
    wait_until_all_files_are_present,
    create_arg_parser,
    load_settings,
    check_license_in_directory,
    get_pdb_paths_from_file,
    create_unique_temp_directory,
)


def main():
    # activate pymol license
    license_info = check_license_in_directory()
    print(license_info)

    parser = create_arg_parser()
    args = parser.parse_args()
    
    # If the script is run without specifying a config, use the default settings
    if args.config is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print(script_dir)
        args.config = os.path.join(script_dir, 'config', 'default_settings.json')


    # Load settings from the default or provided JSON config
    SETTINGS = load_settings(args.config)

    # Adjust default SETTINGS only if parameters were passed
    if args.grid:
        print(f'changing grid {SETTINGS["grid"]["columns"], SETTINGS["grid"]["rows"]} to {args.grid}')
        SETTINGS["grid"]["columns"], SETTINGS["grid"]["rows"] = args.grid
    if args.num_files is not None:
        print(f'changing num_files {SETTINGS["num_files"]} to {args.num_files}')
        SETTINGS["num_files"] = args.num_files
    if args.write_filenames is not None:
        print(f'changing  write_filenames{SETTINGS["write_filenames"]} to {args.write_filenames}')
        SETTINGS["write_filenames"] = args.write_filenames
    if args.output_directory is not None:
        print(f'changing output_directory {SETTINGS["output_directory"]} to {args.output_directory}')
        SETTINGS["output_directory"] = args.output_directory
    if args.output_pdf_name is not None:
        print(f'changing output_pdf_name {SETTINGS["output_pdf_name"]} to {args.output_pdf_name}')
        SETTINGS["output_pdf_name"] = args.output_pdf_name
    if args.filename_pattern is not None:
        print(f'changing filename_pattern {SETTINGS["filename_pattern"]} to {args.filename_pattern}')
        SETTINGS["filename_pattern"] = args.filename_pattern
    if args.sort_pdbs_in_pdf is not None:
        print(f'changing sort_pdbs_in_pdf {SETTINGS["sort_pdbs_in_pdf"]} to {args.sort_pdbs_in_pdf}')
        SETTINGS["sort_pdbs_in_pdf"] = args.sort_pdbs_in_pdf

    # Check if the input was provided as a folder
    if args.input_folder:
        print(f"Processing PDB files in folder: {args.input_folder}")
        # Handle the folder input
        all_files = list_all_pdb_files(args.input_folder, SETTINGS["filename_pattern"])
        path_name = os.path.basename(args.input_folder).replace('/', '_').strip('_')

    # Check if the input was provided as a text file
    elif args.input_txt:
        print(f"Processing PDB files listed in: {args.input_txt}")
        all_files = get_pdb_paths_from_file(args.input_txt)
        path_name = os.path.basename(args.input_txt).replace('/', '_').replace('.txt', '').strip('_')


    # Create a unique temporary directory
    temp_directory = create_unique_temp_directory(SETTINGS["output_directory"], path_name, SETTINGS["filename_pattern"])

    # Define the name and path to the output PDF
    if SETTINGS["output_pdf_name"] is not None:
        output_pdf_path = os.path.join(SETTINGS["output_directory"], f"{SETTINGS['output_pdf_name'].replace('.pdf','')}.pdf")
    else:
        if SETTINGS["filename_pattern"] == "":
            output_pdf_path = os.path.join(SETTINGS["output_directory"], f"{path_name}_all.pdf")
        else:
            output_pdf_path = os.path.join(SETTINGS["output_directory"], f"{path_name}_containing_{SETTINGS['filename_pattern']}.pdf")
            
    print(f"Found {len(all_files)} .pdb files containing '{SETTINGS['filename_pattern']}'")
    matching_files = [f for f in all_files if SETTINGS["filename_pattern"] in os.path.basename(f)]
    if len(matching_files)<1:
        raise ValueError(f"No PDB files found matching pattern: '{SETTINGS['filename_pattern']}' in '{args.input_folder or args.input_txt}'")

    # Select files at random
    selected_files = random.sample(matching_files, min(SETTINGS["num_files"], len(matching_files)))
    print(f"Selected {len(selected_files)} files at random")

    if SETTINGS["sort_pdbs_in_pdf"]:
        selected_files = sorted(selected_files)
    
    # Create and save the images with multiprocessing
    print(f"Generating {len(selected_files)} images with pymol")
    with Pool() as pool:
        image_paths = pool.starmap(process_pdb_file, [(pdb_file, temp_directory, SETTINGS) for pdb_file in selected_files])

    # Check if all images are present
    wait_until_all_files_are_present(image_paths)

    # Create and save the PDF pages 
    print("Creating PDF pages...")
    image_splits = split_images_for_pages(image_paths, (SETTINGS["grid"]["columns"], SETTINGS["grid"]["rows"]))
    with Pool() as pool:
        temp_pdf_paths = pool.starmap(generate_pdf_for_pages, [(start, end, image_subset, temp_directory, SETTINGS) for start, end, image_subset in image_splits])
    
    # Assemble PDF pages to a multi-page PDF
    print("Assembling PDF...")
    merge_temp_pdfs(temp_pdf_paths, output_pdf_path)

    # Remove temporaty directory with all images and pdf pages.
    shutil.rmtree(temp_directory)

if __name__ == "__main__":
    main()