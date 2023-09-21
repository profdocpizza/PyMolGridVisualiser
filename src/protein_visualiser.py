import os
import random
from multiprocessing import Pool
import shutil

    
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
    load_settings,
    check_license_in_directory,
    get_pdb_paths_from_file 
)


def main():
    # activate pymol license
    license_info = check_license_in_directory()
    print(license_info)

    parser = create_arg_parser()
    args = parser.parse_args()

    # Load settings from the default or provided JSON config
    SETTINGS = load_settings(args.config)
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
        print(f'changing output_directory {SETTINGS["output_pdf_name"]} to {args.output_pdf_name}')
        SETTINGS["output_pdf_name"] = args.output_pdf_name
    if args.filename_pattern is not None:
        print(f'changing output_directory {SETTINGS["filename_pattern"]} to {args.filename_pattern}')
        SETTINGS["filename_pattern"] = args.filename_pattern

    # Extracting necessary settings into variables for easier use
    output_directory = SETTINGS["output_directory"]
    filename_pattern = SETTINGS["filename_pattern"]
    num_files = SETTINGS["num_files"]
    output_pdf_name = SETTINGS["output_pdf_name"]
    grid = (SETTINGS["grid"]["columns"], SETTINGS["grid"]["rows"])
    write_filenames = SETTINGS["write_filenames"]

    # Determine if the input_path is a directory or a .txt file
    if os.path.isdir(args.input_path):
        print(f"Filtering .pdb files that contain '{filename_pattern}' in provided directory '{args.input_path}'")
        # Filter pdbs from given directory. look deeply
        all_files = list_all_pdb_files(args.input_path)
    elif args.input_path.endswith(".txt"):
        print(f"Getting .pdb files that contain '{filename_pattern}' in provided txt file '{args.input_path}'")
        all_files = get_pdb_paths_from_file(args.input_path)
    else:
        parser.error("The provided input_path is neither a directory nor a .txt file. For example, use 'PATH/TO/YOUR/PDBS' or PATH/TO/YOUR/PATH_LIST.txt ")




    # Create temporary directory for the images and PDF
    path_name = args.input_path.replace('/','_').replace('.txt','').strip('_')
    temp_directory = rf"{output_directory}/{path_name}_containing_{filename_pattern}"
    if not os.path.exists(temp_directory):
        os.mkdir(temp_directory)

    # Define the name and path to the output PDF
    if output_pdf_name is not None:
        output_pdf_path = os.path.join(output_directory, f"{output_pdf_name.replace('.pdf','')}.pdf")
    else:
        if filename_pattern == "":
            output_pdf_path = os.path.join(output_directory, f"{path_name}_all.pdf")
        else:
            output_pdf_path = os.path.join(output_directory, f"{path_name}_containing_{filename_pattern}.pdf")

    
    print(f"Found {len(all_files)} .pdb files containing '{filename_pattern}'")
    matching_files = [f for f in all_files if filename_pattern in os.path.basename(f)]
    if len(matching_files)<1:
        raise ValueError(f"No PDB files found matching pattern: '{filename_pattern}' in '{args.input_path}'")

    # Select files at random
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
    merge_temp_pdfs(temp_pdf_paths, output_pdf_path)

    shutil.rmtree(temp_directory)

if __name__ == "__main__":
    main()