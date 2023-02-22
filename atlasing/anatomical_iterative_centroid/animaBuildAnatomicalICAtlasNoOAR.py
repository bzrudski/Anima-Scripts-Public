#!/usr/bin/python3
# Warning: works only on unix-like systems, not windows where "python animaBuildAnatomicalAtlas.py ..." has to be run

import argparse
import os
import glob
import sys
import subprocess
import shutil

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
animaScriptsDir = configParser.get("anima-scripts", 'anima-scripts-public-root')

# Argument parsing
parser = argparse.ArgumentParser(
    description="Builds and runs a series of scripts to construct an anatomical atlas (unbiased up to an affine"
                " or rigid transform, with different or equal weights)."
)

# Maybe change the prefix to a list of files
parser.add_argument('-p', '--data-prefix', type=str, required=True, help='Data prefix (including folder)')
parser.add_argument('-n', '--num-images', type=int, required=True, help='Number of images in the atlas')
parser.add_argument('-c', '--num-cores', type=int, default=8, help='Number of cores to run on (default: 8)')
parser.add_argument('-b', '--bch-order', type=int, default=2,
                    help='BCH order when composing transformations (default: 2)')
parser.add_argument('-s', '--start', type=int, default=1, help='number of images in the starting atlas (default: 1)')
parser.add_argument('--rigid', action='store_true', help="Unbiased atlas up to a rigid transformation")
parser.add_argument('-t', '--reg-toml', type=str, help="TOML file containing the registration parameters")
parser.add_argument('-x', '--auxiliary-image-path', type=str,
                    help="Path to auxiliary images, if these are to be transformed as well. Must have same prefix as "
                         "images.")

args = parser.parse_args()

print("Arguments given:", args)

print("Beginning atlas construction...")

prefixBase = os.path.dirname(args.data_prefix)
prefix = os.path.basename(args.data_prefix)

auxiliary_image_output_prefix = "auxImage"

temp_dir = os.path.join(prefixBase, "tempDir")
residual_dir = os.path.join(prefixBase, "residualDir")

os.chdir(prefixBase)

# if not os.path.exists("tempDir"):
#     os.makedirs("tempDir")
#
# if os.path.exists("residualDir"):
#     shutil.rmtree("residualDir")
#
# os.makedirs("residualDir")

if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

if os.path.exists(residual_dir):
    shutil.rmtree(residual_dir)

os.makedirs(residual_dir)


if args.start == 1 or args.start == 0:
    shutil.copyfile(os.path.join(prefixBase, f"{prefix}_1.nii.gz"), "averageForm1.nii.gz")
    args.start = 1 

previousMergeId = 0


for k in range(args.start + 1, args.num_images + 1):
    print(f"Starting with image {k}...")
    if os.path.exists('it_' + str(k) + '_done'):
        firstImage = 1
        continue
    ref = "averageForm" + str(k-1)

    print("*************Incorporating image: " + str(k) + " in atlas: " + ref)

    for f in glob.glob("residualDir/" + prefix + '_*_nl_tr.nrrd') + glob.glob("residualDir/" + prefix + '_*_flag'):
        os.remove(f)

    nCoresPhysical = int(args.num_cores / 2)

    # REPLACE ALL THE OAR COMMANDS HERE WITH THE ABILITY TO RUN LOCALLY... WE HAVE 24 CORES...
    # Maybe try replacing with calls to `os.system`, as per this answer on SO:
    # https://stackoverflow.com/questions/3781851/run-a-python-script-from-another-python-script-passing-in-arguments
    # Regrettably, there doesn't seem to be a better way, although the code is already written to not deal with
    # return values...
    # Update: using subprocess.run, since they were already using it for their OAR calls

    # Register the new image against the reference
    registration_command = [
        "python",
        os.path.join(animaScriptsDir,
                     "atlasing/anatomical_iterative_centroid/animaICAnatomicalRegisterImage.py"),
        "-d", os.getcwd(),
        "-r", f"{ref}.nii.gz",
        "-B", prefixBase,
        "-p", prefix,
        "-i", str(k),
        "-b", str(args.bch_order),
        "-c", str(args.num_cores),
    ]

    # Pass in the registration arguments file
    if args.reg_toml is not None:
        registration_command.extend(["-t", args.reg_toml])

    if args.rigid:
        registration_command.append("--rigid")

    registration_process = subprocess.run(registration_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                          text=True)

    if registration_process.returncode != 0:
        print("********** STDOUT **********")
        print(registration_process.stdout)
        print("****************************")
        print("********** STDERR **********")
        print(registration_process.stderr)
        print("****************************")
        raise Exception(f"Registration process returned with non-zero code {registration_process.returncode}!")

    print("Registration against reference completed for image", k)

    # Use the BCH approximation to update the deformation fields
    numJobs = k

    for i in range(1, numJobs + 1):
        bch_command = [
            "python",
            os.path.join(animaScriptsDir,
                         "atlasing/anatomical_iterative_centroid/animaICAnatomicalComposeTransformations.py"),
            "-d", os.getcwd(),
            "-B", prefixBase,
            "-p", prefix,
            "-i", str(k),
            "-c", str(args.num_cores),
            "-s", str(args.start),
            "-b", str(args.bch_order),
            "-a", str(i),
        ]

        if args.auxiliary_image_path is not None:
            bch_command += ["-x", args.auxiliary_image_path]

        bch_process = subprocess.run(bch_command, stdout=subprocess.PIPE, text=True)

        if bch_process.returncode != 0:
            print(bch_process.stderr)
            raise Exception(f"BCH process for image {i} in iteration {k} returned with non-zero code {bch_process.returncode}!")

        print(f"BCH completed for image {k} and image {i}")

    # Merge the new image into the atlas
    merge_command = [
        "python",
        os.path.join(animaScriptsDir,
                     "atlasing/anatomical_iterative_centroid/animaICAnatomicalMergeImages.py"),
        "-d", os.getcwd(),
        "-B", prefixBase,
        "-p", prefix,
        "-i", str(k),
        "-c", str(args.num_cores),
    ]

    if args.auxiliary_image_path is not None:
        merge_command += ["-x", args.auxiliary_image_path]

    merge_process = subprocess.run(merge_command, stdout=subprocess.PIPE, text=True)

    if merge_process.returncode != 0:
        print(merge_process.stderr)
        raise Exception(f"Merge process for iteration {k} returned with non-zero code {merge_process.returncode}!")

    print(f"Merge completed for image {k}")

    print(f"************* Finished adding image {k} to atlas {ref}\n")

if args.auxiliary_image_path is not None:
    # Copy final auxiliary images, if available, to the parent directory:
    aux_file_list = sorted(glob.glob(os.path.join(temp_dir, "AUX_*.nii.gz")))

    for i, transformed_aux_image in enumerate(aux_file_list):
        j = i + 1
        shutil.copy2(transformed_aux_image, os.path.join(prefixBase, f"{auxiliary_image_output_prefix}{j}.nii.gz"))

    print("Copied the final transformed auxiliary images to the parent directory.")

print("Finished atlas construction! Exiting now...")
