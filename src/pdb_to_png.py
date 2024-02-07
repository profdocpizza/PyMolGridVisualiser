from pymol import cmd
import os
import time

def configure_pymol_cmd(SETTINGS):
    cmd.set("ray_opaque_background", SETTINGS["pymol_settings"]["ray_opaque_background"]) # Tansparency of the image
    cmd.bg_color(SETTINGS["pymol_settings"]["background_colour"]) # Background color. Overrided by ray_opaque_background
    cmd.set("ray_trace_frames", SETTINGS["pymol_settings"]["ray_trace_frames"])
    cmd.set("ray_shadows", SETTINGS["pymol_settings"]["ray_shadows"])
    cmd.set("antialias", SETTINGS["pymol_settings"]["antialias"])
    cmd.set("orthoscopic", SETTINGS["pymol_settings"]["orthoscopic"])
    cmd.set("ray_trace_mode", SETTINGS["pymol_settings"]["ray_trace_mode"])


def default_pymol_script(SETTINGS):
    cmd.show(SETTINGS["pymol_settings"]["representation"], "all")
    if SETTINGS["pymol_settings"]["colour_spectrum"]:
        cmd.spectrum("count", selection="all")
    else:
        cmd.color(SETTINGS["pymol_settings"]["colour"], "all")

def cofactor_binder_pymol_script(SETTINGS):
    # This script works for proteins bound to FMN or FAD only.
    # Modify to use with other cofactors.

    # Select residues FAD or FMN
    cmd.select("cofactor", "resn FAD or resn FMN")
    cmd.unbond("cofactor and elem H", "cofactor and elem C")
    
    # Show selected residues as sticks with orange C-alpha atoms
    cmd.show("sticks", "cofactor")
    cmd.color("magenta", "cofactor and name CA")


    cmd.set("line_width", 5.0)

    # Set cartoon representation to grey_70 with 60% transparency
    cmd.show("cartoon")  # Show the whole protein as a cartoon
    cmd.set("cartoon_color", "gray70")
    # cmd.color("gray70")  # Apply a base color to the protein
    cmd.set("cartoon_transparency", 0.6)
    
    # Select residues within 4 Å of the cofactor
    cmd.select("near_cofactor", "byres (cofactor around 4)")
    
    # Show selected nearby residues as lines
    cmd.show("lines", "near_cofactor")
    
    # Label CA atoms of nearby residues
    cmd.select("near_cofactor_CA", "near_cofactor and name CA")
    cmd.label("near_cofactor_CA", "''+resn+'-'+resi+''")

    removeTags = ["near_cofactor", "near_cofactor_CA", "cofactor"]
    allSele = cmd.get_names("selections")
    for sele in allSele:
        if any(tag in sele for tag in removeTags):
            cmd.delete(sele)


# def your_custom_pymol_script(SETTINGS):
    # cmd.show("cartoon")
    #
    #

def generate_image_from_pdb(pdb_path, output_path, SETTINGS):
    # Load the file
    cmd.delete("all")

    cmd.load(pdb_path,quiet=1)
    cmd.hide("all")

    #### DEFAULT SCRIPT #########
    default_pymol_script(SETTINGS)


    ####FAD/FMN BINDER SCRIPT ####
    # cofactor_binder_pymol_script(SETTINGS)


    ####YOUR CUSTOM SCRIPT ########
    # If SETTINGS parameters are not enough, write your own custom pymol script.
    # your_custom_pymol_script(SETTINGS)


    # New functionality to save PyMOL session
    session_path = output_path.replace('.png', '.pse')  # Assuming output_path ends with .png
    cmd.save(session_path)
    while not os.path.exists(session_path):
        time.sleep(0.02)

    # Save file and ensure it is written. Otherwise can write an empty file.
    cmd.png(output_path, width=SETTINGS["image_dimensions"]["width"], height=SETTINGS["image_dimensions"]["height"], ray=SETTINGS["pymol_settings"]["ray_tracing"], quiet=1)
    while not os.path.exists(output_path):
        time.sleep(0.02)



    cmd.delete("all")