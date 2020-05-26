#!/usr/bin/python3

import sys
import argparse

if sys.version_info[0] > 2:
    import configparser as ConfParser
else:
    import ConfigParser as ConfParser

import tempfile
import glob
import os
import shutil
import numpy as np
from subprocess import call

configFilePath = os.path.expanduser("~") + "/.anima/config.txt"
if not os.path.exists(configFilePath):
    print('Please create a configuration file for Anima python scripts. Refer to the README')
    quit()

configParser = ConfParser.RawConfigParser()
configParser.read(configFilePath)

animaDir = configParser.get("anima-scripts", 'anima')
animaScriptsDir = configParser.get("anima-scripts", 'anima-scripts-public-root')

# Argument parsing
parser = argparse.ArgumentParser(
    description="Given a set of DW images, arranges them for atlas construction: preprocessing, DTI and MCM "
                "computation, tracts start and end regions from tractseg")

parser.add_argument('-n', '--num-subjects', type=int, required=True,
                    help="Number of subjects used for computing the atlas")

parser.add_argument('-i', '--dw-images-prefix', type=str, required=True, help='DW images prefix (folder + basename)')
parser.add_argument('-d', '--dw-dicom-folders-prefix', type=str, default="", help='Dicom folders prefixes (will append '
                                                                                  '_n to them')
parser.add_argument('-t', '--t1-images-prefix', type=str, required=True, help='T1 images prefix (folder + basename)')
parser.add_argument('--type', type=str, default="tensor", help="Type of compartment model for fascicles (stick, zeppelin, tensor, noddi, ddi)")

parser.add_argument('--tractseg-fa-template', type=str, required=True, help="FA template in MNI space from TractSeg. Usually located in the tractseg package well hidden")
parser.add_argument('--dw-without-reversed-b0', action='store_true', help="No reversed B0 provided with the DWIs")

args = parser.parse_args()

# The goal here is to prepare, from DWI data, the creation of an atlas with all data necessary for fiber atlas creation
# What's needed: a DWI folder (with bvecs and bvals attached, if unsure of bvecs: with dicoms attached in
# separated folders), a T13D images folder
# Things done:
# - preprocess using diffusion pre-processing script each DWI -> get tensors from that, brain masks and smooth DWIs
# - estimate MCM from smooth DWIs
# - run tractseg (registration to MNI, run tractseg, get begin and end regions, merge them and put them back on patient)
# - put all data in structure for atlas creation and post-processing. Folders will be:
#    - images: tensors for atlas creation
#    - Masks: DWI brain masks
#    - Tracts_Masks: masks for tractography from tractseg
#    - MCM: MCM estimations from DWI
# And that's it we're done, after that the DTI atlas may be created

animaComputeDTIScalarMaps = os.path.join(animaDir, "animaComputeDTIScalarMaps")
animaPyramidalBMRegistration = os.path.join(animaDir, "animaPyramidalBMRegistration")
animaTransformSerieXmlGenerator = os.path.join(animaDir, "animaTransformSerieXmlGenerator")
animaApplyTransformSerie = os.path.join(animaDir, "animaApplyTransformSerie")
animaImageArithmetic = os.path.join(animaDir, "animaImageArithmetic")
animaThrImage = os.path.join(animaDir, "animaThrImage")

animaMCMApplyTransformSerie = os.path.join(animaDir, "animaMCMApplyTransformSerie")
animaMCMAverageImages = os.path.join(animaDir, "animaMCMApplyTransformSerie")
animaMCMTractography = os.path.join(animaDir, "animaMCMTractography")
animaMajorityLabelVoting = os.path.join(animaDir, "animaMajorityLabelVoting")
animaFibersFilterer = os.path.join(animaDir, "animaFibersFilterer")

os.makedirs('Tensors', exist_ok=True)
os.makedirs('Preprocessed_DWI', exist_ok=True)
os.makedirs('MCM', exist_ok=True)
os.makedirs('Tracts_Masks', exist_ok=True)

# Tracts list imported from tractseg (
tracksLists = ['AF_left', 'AF_right', 'ATR_left', 'ATR_right', 'CA', 'CC_1', 'CC_2', 'CC_3', 'CC_4', 'CC_5', 'CC_6',
               'CC_7', 'CG_left', 'CG_right', 'CST_left', 'CST_right', 'MLF_left', 'MLF_right', 'FPT_left', 'FPT_right',
               'FX_left', 'FX_right', 'ICP_left', 'ICP_right', 'IFO_left', 'IFO_right', 'ILF_left', 'ILF_right', 'MCP',
               'OR_left', 'OR_right', 'POPT_left', 'POPT_right', 'SCP_left', 'SCP_right', 'SLF_I_left', 'SLF_I_right',
               'SLF_II_left', 'SLF_II_right', 'SLF_III_left', 'SLF_III_right', 'STR_left', 'STR_right', 'UF_left',
               'UF_right', 'CC', 'T_PREF_left', 'T_PREF_right', 'T_PREM_left', 'T_PREM_right', 'T_PREC_left',
               'T_PREC_right', 'T_POSTC_left', 'T_POSTC_right', 'T_PAR_left', 'T_PAR_right', 'T_OCC_left',
               'T_OCC_right', 'ST_FO_left', 'ST_FO_right', 'ST_PREF_left', 'ST_PREF_right', 'ST_PREM_left',
               'ST_PREM_right', 'ST_PREC_left', 'ST_PREC_right', 'ST_POSTC_left', 'ST_POSTC_right', 'ST_PAR_left',
               'ST_PAR_right', 'ST_OCC_left', 'ST_OCC_right']

dwiPrefixBase = os.path.dirname(args.dw_images_prefix)
dwiPrefix = os.path.basename(args.dw_images_prefix)
t1PrefixBase = os.path.dirname(args.t1_images_prefix)
t1Prefix = os.path.basename(args.t1_images_prefix)

for dataNum in range(1, args.num_subjects + 1):
    # Preprocess diffusion data
    preprocCommand = ["python3", os.path.join(animaScriptsDir,"diffusion","animaDiffusionImagePreprocessing.py"), "-b", os.path.join(dwiPrefixBase, dwiPrefix + "_" + str(dataNum) + ".bval"),
                      "-t", os.path.join(t1PrefixBase, t1Prefix + "_" + str(dataNum) + ".nii.gz"),
                      "-i", os.path.join(dwiPrefixBase, dwiPrefix + "_" + str(dataNum) + ".nii.gz")]

    if not args.dw_without_reversed_b0:
        preprocCommand = preprocCommand + ["-r", os.path.join(dwiPrefixBase, dwiPrefix + "_" + str(dataNum) + "_reversed_b0.nii.gz")]

    if args.dw_dicom_folders_prefix == "":
        preprocCommand = preprocCommand + ["-g", os.path.join(dwiPrefixBase, dwiPrefix + "_" + str(dataNum) + ".bvec")]
    else:
        dicomPrefixBase = os.path.dirname(args.dw_dicom_folders_prefix)
        dicomPrefix = os.path.basename(args.dw_dicom_folders_prefix)
        preprocCommand = preprocCommand + ["-D", os.path.join(dicomPrefixBase, dicomPrefix + "_" + str(dataNum), "*")]

    call(preprocCommand)

    # Move preprocessed results to output folders
    shutil.move(os.path.join(dwiPrefixBase, dwiPrefix + "_" + str(dataNum) + "_Tensors.nrrd"), os.path.join("Tensors", "DTI_" + str(dataNum) + ".nrrd"))
    shutil.move(os.path.join(dwiPrefixBase, dwiPrefix + "_" + str(dataNum) + "_preprocessed.bvec"), os.path.join("Preprocessed_DWI", "DWI_" + str(dataNum) + "_preprocessed.bvec"))
    shutil.copy(os.path.join(dwiPrefixBase, dwiPrefix + "_" + str(dataNum) + ".bval"), os.path.join("Preprocessed_DWI", "DWI_" + str(dataNum) + "_preprocessed.bval"))
    shutil.move(os.path.join(dwiPrefixBase, dwiPrefix + "_" + str(dataNum) + "_preprocessed.nrrd"), os.path.join("Preprocessed_DWI", "DWI_" + str(dataNum) + "_preprocessed.nrrd"))
    shutil.move(os.path.join(dwiPrefixBase, dwiPrefix + "_" + str(dataNum) + "_brainMask.nrrd"), os.path.join("Preprocessed_DWI", "DWI_" + str(dataNum) + "_preprocessed_brainMask.nrrd"))
    os.remove(os.path.join(dwiPrefixBase, dwiPrefix + "_" + str(dataNum) + "_Tensors_B0.nrrd"))
    os.remove(os.path.join(dwiPrefixBase, dwiPrefix + "_" + str(dataNum) + "_Tensors_NoiseVariance.nrrd"))

    # Now estimate MCMs
    os.chdir("Preprocessed_DWI")
    mcmCommand = ["python3", os.path.join(animaScriptsDir,"diffusion","animaMultiCompartmentModelEstimation.py"), "-i", "DWI_" + str(dataNum) + "_preprocessed.nrrd",
                  "-g", "DWI_" + str(dataNum) + "_preprocessed.bvec", "-b", "DWI_" + str(dataNum) + "_preprocessed.bval", "-n", "3", "-m", "DWI_" + str(dataNum) + "_preprocessed_brainMask.nrrd",
                  "-t", args.type]
    call(mcmCommand)

    # Now move results to MCM folder
    os.chdir("..")
    shutil.move(os.path.join("Preprocessed_DWI","DWI_" + str(dataNum) + "_preprocessed_MCM_avg.mcm"), "MCM")
    shutil.move(os.path.join("Preprocessed_DWI","DWI_" + str(dataNum) + "_preprocessed_MCM_avg"), "MCM")
    for f in glob.glob(os.path.join("Preprocessed_DWI","DWI_" + str(dataNum) + "_preprocessed_MCM*")):
        if os.path.isdir(f):
            shutil.rmtree(f, ignore_errors=True)
        else:
            os.remove(f)

    # Now transform subject FA to MNI reference FA template in tractseg
    tmpFolder = tempfile.mkdtemp()
    extractFACommand = [animaComputeDTIScalarMaps, "-i", os.path.join("Tensors", "DTI_" + str(dataNum) + ".nrrd"), "-f", os.path.join(tmpFolder,"Subject_FA.nrrd")]
    call(extractFACommand)

    regFACommand = [animaPyramidalBMRegistration, "-r", args.tractseg_fa_template, "-m", os.path.join(tmpFolder,"Subject_FA.nrrd"), "-o", os.path.join(tmpFolder,"Subject_FA_OnMNI.nrrd"),
                    "-O", os.path.join(tmpFolder,"Subject_FA_OnMNI_tr.txt"), "-s", "0"]
    call(regFACommand)

    trsfSerieGenCommand = [animaTransformSerieXmlGenerator, "-i", os.path.join(tmpFolder,"Subject_FA_OnMNI_tr.txt"), "-o", os.path.join(tmpFolder,"Subject_FA_OnMNI_tr.xml")]
    call(trsfSerieGenCommand)

    applyTrsfCommand = [animaApplyTransformSerie, "-i", os.path.join("Preprocessed_DWI","DWI_" + str(dataNum) + "_preprocessed.nrrd"), "-t", os.path.join(tmpFolder,"Subject_FA_OnMNI_tr.xml"),
                        "-g", args.tractseg_fa_template, "-o", os.path.join(tmpFolder, "DWI_MNI.nii.gz"), "--grad", os.path.join("Preprocessed_DWI","DWI_" + str(dataNum) + "_preprocessed.bvec"),
                        "-O", os.path.join(tmpFolder, "DWI_MNI.bvec")]
    call(applyTrsfCommand)

    shutil.copy(os.path.join("Preprocessed_DWI","DWI_" + str(dataNum) + "_preprocessed.bval"), os.path.join(tmpFolder, "DWI_MNI.bval"))
    # Trick to get back temporary file to mrtrix ok format (switch y axis)
    tmpData = np.loadtxt(os.path.join(tmpFolder, "DWI_MNI.bvec"))
    tmpData[1] *= -1
    np.savetxt(os.path.join(tmpFolder, "DWI_MNI.bvec"), tmpData)

    applyTrsfCommand = [animaApplyTransformSerie, "-i", os.path.join("Preprocessed_DWI", "DWI_" + str(dataNum) + "_preprocessed_brainMask.nrrd"),
                        "-t", os.path.join(tmpFolder, "Subject_FA_OnMNI_tr.xml"), "-g", args.tractseg_fa_template,
                        "-o", os.path.join(tmpFolder, "DWI_MNI_brainMask.nii.gz"), "-n", "nearest"]
    call(applyTrsfCommand)

    # Finally call tractseg on adapted data
    tractsegCommand = ["TractSeg", "-i", os.path.join(tmpFolder, "DWI_MNI.nii.gz"), "-o", tmpFolder, "--bvals", os.path.join(tmpFolder, "DWI_MNI.bval"),
                       "--bvecs", os.path.join(tmpFolder, "DWI_MNI.bvec"), "--raw_diffusion_input", "--brain_mask",  os.path.join(tmpFolder, "DWI_MNI_brainMask.nii.gz"),
                       "--output_type", "endings_segmentation"]
    call(tractsegCommand)

    for track in tracksLists:
        # Merge begin and end into a single label image
        labelsMergeCommand = [animaImageArithmetic, "-i", os.path.join(tmpFolder, "endings_segmentations", track + "_e.nii.gz"), "-M", "2",
                              "-a", os.path.join(tmpFolder, "endings_segmentations", track + "_b.nii.gz"), "-o", os.path.join(tmpFolder, "endings_segmentations", track + ".nrrd")]
        call(labelsMergeCommand)

        labelsThrCommand = [animaThrImage, "-i", os.path.join(tmpFolder, "endings_segmentations", track + ".nrrd"), "-t", "2.1", "-o", os.path.join(tmpFolder, "tmp.nrrd")]
        call(labelsThrCommand)

        labelFinalizeCommand = [animaImageArithmetic, "-i", os.path.join(tmpFolder, "endings_segmentations", track + ".nrrd"), "-s", os.path.join(tmpFolder, "tmp.nrrd"),
                               "-o", os.path.join(tmpFolder, "endings_segmentations", track + ".nrrd")]
        call(labelFinalizeCommand)

        # Now move back to native space
        applyTrsfCommand = [animaApplyTransformSerie, "-i", os.path.join(tmpFolder, "endings_segmentations", track + ".nrrd"), "-t",
                            os.path.join(tmpFolder, "Subject_FA_OnMNI_tr.xml"), "-g", os.path.join("Preprocessed_DWI","DWI_" + str(dataNum) + "_preprocessed.nrrd"),
                            "-o", os.path.join("Tracts_Masks", track + "_" + str(dataNum) + ".nrrd"), "-I", "-n", "nearest"]
        call(applyTrsfCommand)

    shutil.rmtree(tmpFolder)
