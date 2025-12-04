#!/bin/bash

# To disable a step, change the string to "DONE"
# To enable a step, change the string to "TODO"
# Only steps set to TODO will run when dMRI_HAITCH.sh is run
declare -A FEDI_DMRI_PIPELINE_STEPS=(
  [STEP1_DWI_DENOISE_USING_GSVS]="TODO"
  [STEP2_MRDEGIBBS_RINGING_ARTI]="TODO"
  [STEP3_RICIAN_BIAS_CORRECTION]="TODO"
  [STEP4_FETAL_BRAIN_EXTRACTION]="TODO"
  [STEP5_SPLIT_CROP_SKDATA_MASK]="TODO"
  [STEP6_SLICECORRECTDISTORTION]="TODO"
  [STEP7_B1FIELDBIAS_CORRECTION]="TODO"
  [STEP8_3DSHORE_RECONSTRUCTION]="TODO"
  [STEP9_REGISTRATION_T2W_ATLAS]="DONE"
  [STEP10_TSOR_RESP_FOD_TRACTOG]="DONE"
)

# Tell HAITCH where to find processed T2 data including t2 to atlas registrations
# requires $T2W_DATA/subj/scan/struct/subj_scan_rec-SVRTK_t2w.nii.gz
# requires $T2W_DATA/subj/scan/xfm/subj_scan_rec-SVRTK_t2w-t2space.nii.gz
# requires $T2W_DATA/subj/scan/xfm/subj_scan_rec-SVRTK_from-t2space_to-atlas.nii.gz
export T2W_DATA="protocols/t2w"

# Set the T2 reconstruction pipeline output to "niftymic" or "SVRTK"
export T2W_RECON_METHOD="niftymic"
#export T2W_RECON_METHOD="SVRTK"

# Set dwi brain segmentation to use DAVOOD (dmri3d) or RAZIEH (fetal-bet)
export SEGMENTATION_METHOD="DAVOOD"
#export SEGMENTATION_METHOD="RAZIEH"