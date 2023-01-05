#!/usr/bin/python3
# Warning: works only on unix-like systems, not windows where "python animaAnatomicalRegisterImage.py ..." has to be run

import argparse
import os
import subprocess
import sys
# from subprocess import run
import shutil
from typing import Optional

if sys.version_info[0] > 2:
    import configparser as ConfParser
else:
    import ConfigParser as ConfParser

import animaRegistrationArguments as regArgs

configFilePath = os.path.join(os.path.expanduser("~"), ".anima", "config.txt")
if not os.path.exists(configFilePath):
    print('Please create a configuration file for Anima python scripts. Refer to the README')
    quit()

configParser = ConfParser.RawConfigParser()
configParser.read(configFilePath)

animaDir = configParser.get("anima-scripts", 'anima')

# Argument parsing
parser = argparse.ArgumentParser(
    description="Runs the registration of an image onto a current reference (to be used from build anatomical atlas).")
parser.add_argument('-d', '--ref-dir', type=str, required=True, help='Reference (working) folder')
parser.add_argument('-r', '--ref-image', type=str, required=True, help='Reference image')
parser.add_argument('-B', '--prefix-base', type=str, required=True, help='Prefix base')
parser.add_argument('-p', '--prefix', type=str, required=True, help='Prefix')
parser.add_argument('-b', '--bch-order', type=int, default=2,
                    help='BCH order when composing transformations in rigid unbiased (default: 2)')
parser.add_argument('-i', '--num-iter', type=int, required=True, help='Iteration number of atlas creation')
parser.add_argument('-c', '--num-cores', type=int, default=40, help='Number of cores to run on')
parser.add_argument('--rigid', action='store_true', help="Unbiased atlas up to a rigid transformation")
parser.add_argument('-t', '--reg-toml', type=str, help="TOML file containing the registration parameters")

args = parser.parse_args()

print("Arguments passed to registration:", args)

# args.ref_dir = args.ref_dir.strip()
# args.ref_image = args.ref_image.strip()
# args.prefix_base = args.prefix_base.strip()
# args.prefix = args.prefix.strip()

os.chdir(args.ref_dir)
basePrefBase = os.path.dirname(args.prefix_base.strip())

temp_dir = os.path.join(args.prefix_base, "tempDir")
residual_dir = os.path.join(args.prefix_base, "residualDir")

k = args.num_iter

animaPyramidalBMRegistration = os.path.join(animaDir, "animaPyramidalBMRegistration")
animaDenseSVFBMRegistration = os.path.join(animaDir, "animaDenseSVFBMRegistration")
animaTransformSerieXmlGenerator = os.path.join(animaDir, "animaTransformSerieXmlGenerator")
animaLinearTransformArithmetic = os.path.join(animaDir, "animaLinearTransformArithmetic")
animaLinearTransformToSVF = os.path.join(animaDir, "animaLinearTransformToSVF")
animaDenseTransformArithmetic = os.path.join(animaDir, "animaDenseTransformArithmetic")
animaImageArithmetic = os.path.join(animaDir, "animaImageArithmetic")
animaCreateImage = os.path.join(animaDir, "animaCreateImage")

registration_parameter_file: Optional[str] = args.reg_toml

default_rigid_registration_parameters = regArgs.AnimaPyramidalBMRegistrationArguments(
    number_of_pyramid_levels=3,
    last_pyramid_level=0,
    initialisation_type=regArgs.InitialisationType.GRAVITY_PCA_CLOSEST_TRANSFORM,
    symmetry_type=regArgs.SymmetryType.KISSING
)

default_non_rigid_registration_parameters = regArgs.AnimaDenseSVFBMRegistrationArguments(
    bobyqa_translate_upper_bound=2,
    elastic_regularisation_sigma=3,
    extrapolation_sigma=2,
    symmetry_type=regArgs.SymmetryType.KISSING,
    similarity_metric=regArgs.SimilarityMetric.CORRELATION_COEFFICIENT
)

if registration_parameter_file is not None:
    rigid_parameters, non_rigid_parameters = regArgs.parse_registration_parameters(
        registration_parameter_file,
        default_rigid_parameters=default_rigid_registration_parameters,
        default_non_rigid_parameters=default_non_rigid_registration_parameters
    )
else:
    rigid_parameters = default_rigid_registration_parameters
    non_rigid_parameters = default_non_rigid_registration_parameters

print(f"Registration Parameters:\n\tRigid:{rigid_parameters}\n\tNon Rigid:{non_rigid_parameters}\n")

# Rigid / affine registration
command = [
    animaPyramidalBMRegistration,
    "-r", args.ref_image,
    "-m", os.path.join(args.prefix_base, args.prefix + "_" + str(k) + ".nii.gz"),
    "-o", os.path.join(temp_dir, args.prefix + "_" + str(k) + "_aff.nrrd"),
    "-O", os.path.join(temp_dir, args.prefix + "_" + str(k) + "_aff_tr.txt"),
    "--out-rigid", os.path.join(temp_dir, args.prefix + "_" + str(k) + "_aff_nr_tr.txt"),
    "--ot", "2",
    # "-p", "3",
    # "-l", "0",
    # "-I", "2",
    "-T", str(args.num_cores),
    # "--sym-reg", "2"
]

command.extend(rigid_parameters.get_command_args())

rigid_output = subprocess.run(command, text=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

print("Ran the rigid registration. Obtained result:")
print("*"*10 + " STDOUT " + "*"*10)
print(rigid_output.stdout)

print("*"*10 + " STDERR " + "*"*10)
print(rigid_output.stderr)
print("*" * 28)

# Non-Rigid registration

# For basic atlases
command = [
    animaDenseSVFBMRegistration,
    "-r", args.ref_image,
    "-m", os.path.join(temp_dir, args.prefix + "_" + str(k) + "_aff.nrrd"),
    "-o", os.path.join(temp_dir, args.prefix + "_" + str(k) + "_bal.nrrd"),
    "-O", os.path.join(temp_dir, args.prefix + "_" + str(k) + "_bal_tr.nrrd"),
    # "--tub", "2",
    # "--es", "3",
    # "--fs", "2",
    "-T", str(args.num_cores),
    # "--sym-reg", "2",
    # "--metric", "1"
]

command.extend(non_rigid_parameters.get_command_args())

non_rigid_output = subprocess.run(command, text=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

print("Ran the non-rigid registration. Obtained result:")
print("*"*10 + " STDOUT " + "*"*10)
print(non_rigid_output.stdout)

print("*"*10 + " STDERR " + "*"*10)
print(non_rigid_output.stderr)
print("*" * 28)

if args.rigid:

    # command = [
    #     animaLinearTransformArithmetic, "-i", os.path.join(
    #         # temp_dir, args.prefix + "_" + str(k) + "_linear_tr.txt"
    #         temp_dir, args.prefix + "_" + str(k) + "_aff_nr_tr.txt"
    #     ),
    #     "-M", "-1",
    #     "-o", os.path.join(
    #         temp_dir, args.prefix + "_" + str(k) + "_linear_tr.txt"
    #     )
    # ]
    # run(command)

    shutil.move(os.path.join(temp_dir, args.prefix + "_" + str(k) + "_aff_nr_tr.txt"),
                os.path.join(temp_dir, args.prefix + "_" + str(k) + "_linear_tr.txt"))

    command = [
        animaLinearTransformToSVF,
        "-i", os.path.join(
            temp_dir, args.prefix + "_" + str(k) + "_linear_tr.txt"
        ),
        "-o", os.path.join(temp_dir, args.prefix + "_" + str(k) + "_linearaddon_tr.nrrd"),
        "-g", args.ref_image
    ]
    subprocess.run(command, text=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    command = [
        animaDenseTransformArithmetic,
        "-i", os.path.join(temp_dir, args.prefix + "_" + str(k) + "_linearaddon_tr.nrrd"),
        "-c", os.path.join(temp_dir, args.prefix + "_" + str(k) + "_bal_tr.nrrd"),
        "-b", str(args.bch_order),
        "-o", os.path.join(temp_dir, args.prefix + "_" + str(k) + "_nonlinear_tr.nrrd")
    ]
    subprocess.run(command, text=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
else:
    shutil.move(os.path.join(temp_dir, args.prefix + "_" + str(k) + "_aff_tr.txt"),
                os.path.join(temp_dir, args.prefix + "_" + str(k) + "_linear_tr.txt"))

    shutil.move(os.path.join(temp_dir, args.prefix + "_" + str(k) + "_bal_tr.nrrd"),
                os.path.join(temp_dir, args.prefix + "_" + str(k) + "_nonlinear_tr.nrrd"))

if os.path.exists(os.path.join(residual_dir, args.prefix + "_" + str(k) + "_nonlinear_tr.nrrd")):
    os.remove(os.path.join(residual_dir, args.prefix + "_" + str(k) + "_nonlinear_tr.nrrd"))

os.symlink(os.path.join(temp_dir, args.prefix + "_" + str(k) + "_nonlinear_tr.nrrd"),
           os.path.join(residual_dir, args.prefix + "_" + str(k) + "_nonlinear_tr.nrrd"))

if os.path.exists(os.path.join(temp_dir, args.prefix + "_" + str(k) + "_nonlinear_tr.nrrd")):
    open(os.path.join(residual_dir, args.prefix + "_" + str(k) + "_flag"), 'a').close()

if os.path.exists(os.path.join(temp_dir, args.prefix + "_" + str(k) + "_bal_tr.nrrd")):
    os.remove(os.path.join(temp_dir, args.prefix + "_" + str(k) + "_bal_tr.nrrd"))

if os.path.exists(os.path.join(temp_dir, args.prefix + "_" + str(k) + "_linearaddon_tr.nrrd")):
    os.remove(os.path.join(temp_dir, args.prefix + "_" + str(k) + "_linearaddon_tr.nrrd"))

wk = -1.0 / k
command = [animaImageArithmetic, "-i", os.path.join(temp_dir, args.prefix + "_" + str(k) + "_nonlinear_tr.nrrd"),
           "-M", str(wk), "-o", os.path.join(temp_dir, "Tk.nrrd")]
subprocess.run(command, text=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

wkk = (k - 1.0) / k
command = [animaImageArithmetic, "-i", os.path.join(temp_dir, args.prefix + "_" + str(k) + "_nonlinear_tr.nrrd"),
           "-M", str(wkk), "-o", os.path.join(temp_dir, "thetak_" + str(k) + ".nrrd")]
subprocess.run(command, text=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
