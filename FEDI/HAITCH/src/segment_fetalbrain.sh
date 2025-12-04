#!/bin/bash -e



# Function to display script usage
usage() {
    echo -e "Segmentation of Fetal Brain from Diffusion-Weighted data.\nUsage: $0 --dmri <input_dmri_data> --seg_tmp_dir <segmentation_work_dir> --dmriskpervolume <output_dmri_skull_stripped_per_volume> --dmrisk <output_dmri_skull_stripped> --mask <output_mask>"
    exit 1
}

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --dmri)
            DMRI="$2"
            shift
            ;;
        --dmriskpervolume)
            DMRISKPERVOLUME="$2"
            shift
            ;;
        --dmrisk)
            DMRISK="$2"
            shift
            ;;
        --mask)
            MASK="$2"
            shift
            ;;
        --seg_tmp_dir)
	    SEG_TMP_DIR="$2"
	    shift
	    ;;
        --help)
            usage
            ;;
        *)
            echo "Unknown parameter: $1"
            usage
            ;;
    esac
    shift
done

rm ${SEG_TMP_DIR}/* -f
mkdir -pv ${SEG_TMP_DIR}

echo -e "\n|---> Fetal Brain extraction II---"
NUMBER_ECHOTIME=1

NVOLUMES_PER_TE=$(mrinfo -size $DMRI -quiet | awk '{print $4}')

echo $NVOLUMES_PER_TE
# cp "$DMRI" "$OUTPATHSUB/extra/working_TE${NUMBER_ECHOTIME}.nii.gz"

# Split the 4D volume(s) into 3D volumes
echo -e "n\Split 4D volume into 3D volumes"
for ((VNUM=0; VNUM<${NVOLUMES_PER_TE}; VNUM++)); do

    mrconvert -coord 3 $VNUM "$DMRI" "${SEG_TMP_DIR}/working_TE${NUMBER_ECHOTIME}_v${VNUM}.nii.gz"

done


# Fetal brain segmentation
SEGMENTATION_METHOD="RAZIEH"

# Both scripts segment all 3D volumes in the input path
if [[ ${SEGMENTATION_METHOD}  == "DAVOOD" ]]; then

    DVD_SRC=/local/software/dmri_segmentation_3d
    python ${DVD_SRC}/dMRI_volume_segmentation.py ${SEG_TMP_DIR} \
                                                  ${DVD_SRC}/model_checkpoint \
                                                  gpu_num=1 \
                                                  dilation_radius=1

elif [[ ${SEGMENTATION_METHOD}  == "RAZIEH" ]]; then
    mkdir -v ${SEG_TMP_DIR}/{fetal-bet,inputs}
    chmod -R 777 ${SEG_TMP_DIR}/{fetal-bet,inputs}
    find ${SEG_TMP_DIR} -maxdepth 1 -name working_TE\*z -a ! -name \*mask\* -exec cp {} -vup ${SEG_TMP_DIR}/inputs/ \;
    mpath=`readlink -f $OUTPATHSUB`
    # Estimate Fetal-Bet field
    docker run -v --rm --mount type=bind,source=${mpath},target=/workspace arfentul/fetalbet-model:first /bin/bash -c \
    "python /app/src/codes/inference.py --data_path /workspace/fod_tracts/seg_tmp/inputs --save_path /workspace/fod_tracts/seg_tmp/fetal-bet --saved_model_path /app/src/model/AttUNet.pth ; chmod 666 /workspace/fod_tracts/seg_tmp/fetal-bet/*"
    echo

    # rename output files
    echo "moving dwi brain masks to ${SEG_TMP_DIR}"
    for mask in ${SEG_TMP_DIR}/fetal-bet/*predicted_mask.nii.gz ; do
        maskbase=`basename $mask`
        cp $mask ${SEG_TMP_DIR}/${maskbase%_predicted*}_mask.nii.gz
    done
    rmdir -v ${SEG_TMP_DIR}/fetal-bet 
fi


# # Skull Stripping data
DWI_LIST1=""
VNUM=0
echo -e "\nSkull-Strip data"

for ((VNUM=0; VNUM<${NVOLUMES_PER_TE}; VNUM++)); do
    mrcalc "${SEG_TMP_DIR}/working_TE${NUMBER_ECHOTIME}_v${VNUM}.nii.gz" "${SEG_TMP_DIR}/working_TE${NUMBER_ECHOTIME}_v${VNUM}_mask.nii.gz" -multiply "${SEG_TMP_DIR}/workingsk_TE${NUMBER_ECHOTIME}_v${VNUM}.nii.gz" -force -quiet
    DWI_LIST1+="${SEG_TMP_DIR}/workingsk_TE${NUMBER_ECHOTIME}_v${VNUM}.nii.gz "
done

mrcat -axis 3 $DWI_LIST1 "$DMRISKPERVOLUME" -force -quiet


# Create Union_mask
echo -e "\nCreate Union Mask"
mrconvert "${SEG_TMP_DIR}/working_TE${NUMBER_ECHOTIME}_v0_mask.nii.gz" "${SEG_TMP_DIR}/union_mask_TE${NUMBER_ECHOTIME}.mif" -force -quiet

for ((VNUM=0; VNUM<${NVOLUMES_PER_TE}; VNUM++)); do
    # Keep the largest connected segmented region
    maskfilter -largest "${SEG_TMP_DIR}/working_TE${NUMBER_ECHOTIME}_v${VNUM}_mask.nii.gz" connect "${SEG_TMP_DIR}/working_TE${NUMBER_ECHOTIME}_v${VNUM}_mask.nii.gz" -force -quiet

    mrcalc "${SEG_TMP_DIR}/union_mask_TE${NUMBER_ECHOTIME}.mif" "${SEG_TMP_DIR}/working_TE${NUMBER_ECHOTIME}_v${VNUM}_mask.nii.gz" -max "${SEG_TMP_DIR}/union_mask_TE${NUMBER_ECHOTIME}.mif" -force  -quiet
done





mrconvert "${SEG_TMP_DIR}/union_mask_TE${NUMBER_ECHOTIME}.mif" "$MASK" -force -quiet


mrcalc "$DMRI" "$MASK" -multiply "$DMRISK" -force -quiet
