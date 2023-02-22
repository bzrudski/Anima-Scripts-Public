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

configFilePath = os.path.join(os.path.expanduser("~"), ".anima", "config.txt")
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
parser.add_argument('-p', '--prefix', type=str, required=True, help='Prefix of image filename')
parser.add_argument('-a', '--num-img', type=int, required=True, help='Image number')
parser.add_argument('-b', '--bch-order', type=int, default=2,
                    help='BCH order when composing transformations in rigid unbiased (default: 2)')
parser.add_argument('-i', '--num-iter', type=int, required=True, help='Iteration number of atlas creation')
parser.add_argument('-c', '--num-cores', type=int, default=40, help='Number of cores to run on')
parser.add_argument('-s', '--start', type=int, default=1, help='Number of images in the starting atlas (default: 1)')
parser.add_argument('-x', '--auxiliary-image-path', type=str,
                    help="Path to auxiliary images, if these are to be transformed as well. Must have same prefix as "
                         "images.")

args = parser.parse_args()
os.chdir(args.ref_dir)

k = args.num_iter
a = args.num_img

temp_dir = os.path.join(args.prefix_base, "tempDir")
residual_dir = os.path.join(args.prefix_base, "residualDir")

animaImageArithmetic = os.path.join(animaDir, "animaImageArithmetic")
animaTransformSerieXmlGenerator = os.path.join(animaDir, "animaTransformSerieXmlGenerator")
animaApplyTransformSerie = os.path.join(animaDir, "animaApplyTransformSerie")
animaDenseTransformArithmetic = os.path.join(animaDir, "animaDenseTransformArithmetic")
animaCreateImage = os.path.join(animaDir, "animaCreateImage")
animaLinearTransformArithmetic = os.path.join(animaDir, "animaLinearTransformArithmetic")

if a == 1 and k == 2:
    # If image number is 1 and this is the second iteration, create a new canvas for the transformations.
    command = [
        animaCreateImage,
        "-g", "averageForm1.nii.gz",
        "-v", "3",
        "-b", "0",
        "-o", f"{temp_dir}/thetak_1.nrrd"
    ]
    subprocess.run(command)

    command = [
        animaLinearTransformArithmetic,
        "-i", os.path.join(temp_dir, f"{args.prefix}_2_linear_tr.txt"),
        "-M", "0",
        "-o", os.path.join(temp_dir, f"{args.prefix}_1_linear_tr.txt")
    ]
    subprocess.run(command)

# Path to the non-rigid transformation
nonrigid_transformation_path = os.path.join(temp_dir, f"thetak_{a}.nrrd")

if a < k:
    # If the image number is less than the number of iterations, perform arithmetic on the dense transformation fields.
    command = [
        animaDenseTransformArithmetic,
        "-i", nonrigid_transformation_path,
        "-c", os.path.join(temp_dir, "Tk.nrrd"),
        "-b", str(args.bch_order),
        "-o", nonrigid_transformation_path
    ]
    subprocess.run(command)

# Generate the series of image transformations using the linear and non-linear transformations.
transform_series_path = os.path.join(temp_dir, f"T_{a}.xml")

command = [
    animaTransformSerieXmlGenerator,
    "-i", os.path.join(temp_dir, f"{args.prefix}_{a}_linear_tr.txt"),
    "-i", nonrigid_transformation_path,
    "-o", transform_series_path
]
subprocess.run(command)

# Apply the transformations
previous_atlas = f"averageForm{k - 1}.nii.gz"

command = [
    animaApplyTransformSerie,
    "-i", os.path.join(args.prefix_base, f"{args.prefix}_{a}.nii.gz"),
    "-t", transform_series_path,
    "-g", previous_atlas,
    "-o", os.path.join(temp_dir, f"{args.prefix}_{a}_at.nii.gz"),
    "-p", str(args.num_cores)
]
subprocess.run(command)

# Transform the masks if they exist
if os.path.exists(os.path.join("Masks", f"Mask_{a}.nii.gz")):
    command = [
        animaApplyTransformSerie,
        "-i", os.path.join("Masks", f"Mask_{a}.nii.gz"),
        "-t", transform_series_path,
        "-g", previous_atlas,
        "-o", os.path.join(temp_dir, f"Mask_{a}_at.nii.gz"),
        "-p", str(args.num_cores),
        "-n", "nearest"
    ]
    subprocess.run(command)

# Apply the transformations to the auxiliary images
if args.auxiliary_image_path is not None:
    auxiliary_image_path = os.path.join(args.auxiliary_image_path, f"{args.prefix}_{a}.nii.gz")
    
    command = [
        animaApplyTransformSerie,
        "-i", auxiliary_image_path,
        "-t", transform_series_path,
        "-g", previous_atlas,
        "-o", os.path.join(temp_dir, f"AUX_{a}.nii.gz"),
        "-p", str(args.num_cores),
        "-n", "nearest"
    ]
    subprocess.run(command)
