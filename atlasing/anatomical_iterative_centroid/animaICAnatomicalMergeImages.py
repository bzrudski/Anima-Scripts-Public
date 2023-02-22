#!/usr/bin/python3
# Warning: works only on unix-like systems, not windows where "python animaAnatomicalMergeImages.py ..." has to be run

import argparse
import os
import sys
import subprocess

if sys.version_info.major > 2:
    import configparser as ConfParser
else:
    import ConfigParser as ConfParser

configFilePath = os.path.join(os.path.expanduser("~"), ".anima",  "config.txt")
if not os.path.exists(configFilePath):
    print('Please create a configuration file for Anima python scripts. Refer to the README')
    quit(code=1)

configParser = ConfParser.RawConfigParser()
configParser.read(configFilePath)

animaDir = configParser.get("anima-scripts", 'anima')

# Argument parsing
parser = argparse.ArgumentParser(
    description="Builds a new average anatomical form from previously registered images.")
parser.add_argument('-d', '--ref-dir', type=str, required=True, help='Reference (working) folder')
parser.add_argument('-B', '--prefix-base', type=str, required=True, help='Prefix base (image folder)')
parser.add_argument('-p', '--prefix', type=str, required=True, help='Prefix of the image files')
parser.add_argument('-i', '--num-iter', type=int, required=True, help='Iteration number of atlas creation')
parser.add_argument('-c', '--num-cores', type=int, default=40, help='Number of cores to run on')
parser.add_argument('-x', '--auxiliary-image-path', type=str,
                    help="Path to auxiliary images, if these are to be merged as well. Must follow the same naming "
                         "convention as the original images (same prefix and same numbering).")

args = parser.parse_args()
os.chdir(args.ref_dir)

temp_dir = os.path.join(args.prefix_base, "tempDir")

animaAverageImages = os.path.join(animaDir, "animaAverageImages")

# Open the files used for keeping track of the atlas construction
mask_list_file = "masksIms.txt"
image_list_file = "avgImg.txt"
auxiliary_image_list_file = "auxImg.txt"

avg_image_file = open(image_list_file, "w")
masks_file = open(mask_list_file, "w")
aux_image_file = open(auxiliary_image_list_file, "w")

for a in range(1, args.num_iter + 1):
    avg_image_file.write(f"{os.path.join(temp_dir, f'{args.prefix}_{a}_at.nii.gz')}\n")

    if os.path.exists(os.path.join("Masks", f"Mask_{a}.nii.gz")):
        masks_file.write(f"{os.path.join(temp_dir, f'Mask_{a}_at.nii.gz')}\n")

    if args.auxiliary_image_path is not None:
        aux_image_file.write(f"{os.path.join(temp_dir, f'AUX_{a}.nii.gz')}\n")

avg_image_file.close()
masks_file.close()
aux_image_file.close()

# Average the images
command = [
    animaAverageImages,
    "-i", image_list_file,
    "-o", f"averageForm{args.num_iter}.nii.gz"
]

if os.path.exists(os.path.join("Masks", "Mask_1.nii.gz")):
    command += ["-m", mask_list_file]

subprocess.run(command)

# Average the auxiliary images, if present
if args.auxiliary_image_path is not None:
    command = [
        animaAverageImages,
        "-i", auxiliary_image_list_file,
        "-o", f"auxAverageForm{args.num_iter}.nii.gz"
    ]

    if os.path.exists(os.path.join("Masks", "Mask_1.nii.gz")):
        command += ["-m", mask_list_file]

    subprocess.run(command)

