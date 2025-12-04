#!/bin/bash -e

##########################################################################
##                                                                      ##
##  Part of Fetal and Neonatal Development Imaging Toolbox (FEDI)       ##
##                                                                      ##
##                                                                      ##
##  Author:    Haykel Snoussi, PhD (dr.haykel.snoussi@gmail.com)        ##
##             IMAGINE Group | Computational Radiology Laboratory       ##
##             Boston Children's Hospital | Harvard Medical School      ##
##                                                                      ##
##########################################################################




source "$1"
CONFIG_FILE="$1"

# Ensure a config file path is provided
if [ -z "$CONFIG_FILE" ]; then
    echo "Error: No config file provided."
    exit 1
fi

# # Setup file directories and Lock for processing
if [[ -e ${OUTPATHSUB}/lock && ! $NOLOCKS = 1 ]] ; then
        echo "----------------------------------"
        echo "@ $SUBJECTID $OUTPATHSUB Locked"
	echo "@ ${OUTPATHSUB}/lock"
        echo "----------------------------------"
        exit
else
    echo "--"
    #touch ${OUTPATHSUB}/lock
fi



# # # Display Toolbox name
sh ${SRC}/display_name.sh
sleep 1

echo "host: $(hostname), date: $(date)"
echo "----------------------------------"
echo "--------- HAITCH PIPELINE --------"
echo "----------------------------------"


# Define the PP dictionary steps
source ${SRC}/../user_config.sh

# # # Identify the next step marked as "TODO"
TODO_STEP=""
 for STEP in "${!FEDI_DMRI_PIPELINE_STEPS[@]}"; do
  if [[ "${FEDI_DMRI_PIPELINE_STEPS[$STEP]}" == "TODO" ]]; then
    TODO_STEP="${TODO_STEP}_${STEP}"
  fi
 done

# Check if a TODO step was found and set up logging
LOGFILE_TODO="NO" # can disable logging here
if [[ ${LOGFILE_TODO} == "YES" ]] && [[ -n "$TODO_STEP" ]]; then
  echo "Setting up logging"
  if (( ${#TODO_STEP} < 255 )); then
    mkdir -p "${OUTPATHSUB}/logfiles"
    LOGFILE="${OUTPATHSUB}/logfiles/log_${TODO_STEP}.txt"
    > "$LOGFILE"
    exec &>> "$LOGFILE"
    set -x
  else
    TODO_STEP="MANY_STEPS"
    mkdir -p "${OUTPATHSUB}/logfiles"
    LOGFILE="${OUTPATHSUB}/logfiles/log_${TODO_STEP}.txt"
    > "$LOGFILE"
    exec &>> "$LOGFILE"
    set -x
  fi
else
  echo "LOGFILE disabled or no TODO steps found."
fi

mkdir -vp tmp # dwiextract requires a folder named "tmp"

# Find input data
INPUT=""
PHASE=""
CHI2E=""

if [ -d "$INPATHSUB" ]; then
    # Search for the input and phase files based on DWIMODALITY
    case "$DWIMODALITY" in
        dMRI6[1-9]|dMRI8[0-2])
            INPUT=$(find "$INPATHSUB" -type f -name "*_dMRI*.nii.gz")
            ;;
        "dwiME")
            INPUT=$(find "$INPATHSUB" -type f -name "*_dwiME*.nii.gz")
            ;;
        "dwi")
            #INPUT=$(find "$INPATHSUB" -type f -name "*_dwi_*.nii.gz")
            # Data missing DICOM tags is being named differently, this is a concession to catch those cases
	    INPUT=$(find "$INPATHSUB" -type f -name "*_dwi_*.nii.gz" -o -name "*_dwi.nii.gz")
            ;;
        *)
            echo "Invalid DWIMODALITY: $DWIMODALITY"
            exit 1
            ;;
    esac


    if [ -z "$INPUT" ]; then
        echo "Warning: input data not found for $1 !"
        exit 1
    fi
fi




echo "_mrinfo_________________________________"
mrinfo -size $INPUT
echo "________________________________________"

# STEP 0: SOMEPARAMETERS_SETTING
NSIZE1=$(mrinfo -size $INPUT -quiet | awk '{print $1}')
NSIZE2=$(mrinfo -size $INPUT -quiet | awk '{print $2}')
NSIZE3=$(mrinfo -size $INPUT -quiet | awk '{print $3}')

# Determine the number of slices : the minimum dimension size in dir 1, 2 and 3
NSLICES=$NSIZE1
if [ $NSIZE2 -lt $NSLICES ]; then NSLICES=$NSIZE2; fi
if [ $NSIZE3 -lt $NSLICES ]; then NSLICES=$NSIZE3; fi

# Define  the Z-axis number
if [[ $NSLICES == $NSIZE1 ]]; then AXSLICES="0";
elif [[ $NSLICES == $NSIZE2 ]]; then AXSLICES="1";
elif [[ $NSLICES == $NSIZE3 ]]; then AXSLICES="2"; fi

if [ $((NSLICES % 2)) -ne 0 ]; then
    NSLICESCROP=$((NSLICES - 1))
else
   NSLICESCROP=$NSLICES
fi

# Define number of volumes
NVOLUMES=$(mrinfo -size $INPUT -quiet | awk '{print $4}')


# Retrieve strides information
RawSTRIDES=$(mrinfo -strides $INPUT)
IFS=' ' read -ra stride_array <<< "$RawSTRIDES"
STRIDES=""
STRIDES3D=""
stridescount=0
for stride in "${stride_array[@]}"; do
    if [[ $stride -gt 0 ]]; then
        STRIDES+="+$stride,"
    else
        STRIDES+="$stride,"
    fi

    let stridescount+=1
    if [[ $stridescount -le 3 ]]; then
        STRIDES3D="${STRIDES}"
    fi

done

STRIDES="${STRIDES%,}"
STRIDES3D="${STRIDES3D%,}"

echo $STRIDES
echo $STRIDES3D

# Define and create folder
PRPROCESSING_DIR=${OUTPATHSUB}/preprocessing
SEGMENTATION_DIR=${OUTPATHSUB}/segmentation
SEGM_POST_DC_DIR=${OUTPATHSUB}/segmentation/PostDC
DISTORTIONCO_DIR=${OUTPATHSUB}/distortion
MOTIONCORREC_DIR=${OUTPATHSUB}/motion
REGISTRATION_DIR=${OUTPATHSUB}/registrationtoT2w
T2WXFM_FILES_DIR=${OUTPATHSUB}/T2WXFM


SLICEWEIGHTS_DIR=${OUTPATHSUB}/sliceweights
TENFOD_TRACT_DIR=${OUTPATHSUB}/fod_tracts
OUTPUT_FILES_DIR=${OUTPATHSUB}/output
QUAL_CONTROL_DIR=${OUTPATHSUB}/qualitycontrol
RESULTS_SATS_DIR=${OUTPATHSUB}/results
LOCKED_STEPS_DIR=${OUTPATHSUB}/locks

LOCK1=${LOCKED_STEPS_DIR}/lock_STEP1_DWI_DENOISE_USING_GSVS
LOCK2=${LOCKED_STEPS_DIR}/lock_STEP2_MRDEGIBBS_RINGING_ARTI
LOCK3=${LOCKED_STEPS_DIR}/lock_STEP3_RICIAN_BIAS_CORRECTION
LOCK4=${LOCKED_STEPS_DIR}/lock_STEP4_FETAL_BRAIN_EXTRACTION
LOCK5=${LOCKED_STEPS_DIR}/lock_STEP5_SPLIT_CROP_SKDATA_MASK
LOCK6=${LOCKED_STEPS_DIR}/lock_STEP6_SLICECORRECTDISTORTION
LOCK7=${LOCKED_STEPS_DIR}/lock_STEP7_B1FIELDBIAS_CORRECTION
LOCK8=${LOCKED_STEPS_DIR}/lock_STEP8_3DSHORE_RECONSTRUCTION
LOCK9=${LOCKED_STEPS_DIR}/lock_STEP9_REGISTRATION_T2W_ATLAS
LOCK10=${LOCKED_STEPS_DIR}/lock_STEP10_TENSORFOD_TRACTOGRAPHY

TMP_WORK_DIR=${OUTPATHSUB}/tmp


mkdir -p ${OUTPATHSUB}
mkdir -p ${PRPROCESSING_DIR}
mkdir -p ${SEGMENTATION_DIR}
mkdir -p ${SEGM_POST_DC_DIR}

mkdir -p ${DISTORTIONCO_DIR}/BM
mkdir -p ${DISTORTIONCO_DIR}/EPIC
mkdir -p ${DISTORTIONCO_DIR}/TOPUP
mkdir -p ${DISTORTIONCO_DIR}/VOSS
mkdir -p ${REGISTRATION_DIR}
mkdir -p ${T2WXFM_FILES_DIR}


mkdir -p ${MOTIONCORREC_DIR}
mkdir -p ${SLICEWEIGHTS_DIR}
mkdir -p ${TENFOD_TRACT_DIR}
mkdir -p ${OUTPUT_FILES_DIR}
mkdir -p ${QUAL_CONTROL_DIR}
mkdir -p ${RESULTS_SATS_DIR}
mkdir -p ${LOCKED_STEPS_DIR}
mkdir -p ${TMP_WORK_DIR}


WAY_TO_DETERMINE_NECHOTIME="FROM_BVECS_FILE" # Best way is FROM_JSON_FILE
if [[ $WAY_TO_DETERMINE_NECHOTIME == "FROM_BVECS_FILE" ]]; then
    # ! It is not an accurate way of determining of ehotime numner, it fails many times
    # Check how many Echo Time do we have in the data
    read -r line < "$BVECS"
    # Count occurrences of each word (column)
    declare -A counts
    for word in $line; do
        ((counts[$word]++))
    done

    declare -A frequencyOfCounts
    for count in "${counts[@]}"; do
        ((frequencyOfCounts[$count]++))
    done

    maxFreq=0
    commonCount=0
    for count in "${!frequencyOfCounts[@]}"; do
        if [[ "${frequencyOfCounts[$count]}" -gt "$maxFreq" ]]; then
            maxFreq="${frequencyOfCounts[$count]}"
            NUMBER_ECHOTIME=$count
        fi
    done

elif [[ $WAY_TO_DETERMINE_NECHOTIME == "FROM_JSON_FILE" ]]; then
    # Check if EchoTime is an array or a single value and count unique values
    NUMBER_ECHOTIME=$(jq '
      if .EchoTime | type == "array" then
        .EchoTime | unique | length
      else
        1
      end' "$JSONF")
fi

NUMBER_ECHOTIME=1
if [[ ${NUMBER_ECHOTIME} -eq 1 ]]; then
    BVALSTE="${BVALS}"
    BVECSTE="${BVECS}"
    GRAD4CLSTE="${GRAD4CLS}"
fi

echo "----------------------------------"
echo "INPATHSUB   :  $INPATHSUB"
echo "OUTPATHSUB  :  ${OUTPATHSUB}"
echo "INPUT       :  $INPUT"
echo "----------------------------------"
echo "NSLICES  (NUMB OF SLICES) : $NSLICES"
echo "AXSLICES (SLICE-AXIS NUM) : $AXSLICES"
echo "NVOLUMES (NUMB VOLUMES)   : $NVOLUMES"
echo "STRIDES  (STRIDES INFO)   : $STRIDES"
if [[ -n $NUMBER_ECHOTIME ]] ; then
    echo "ECHOTIME (NUMBER_ECHOTIME): $NUMBER_ECHOTIME"
else
    echo "Echo Time info missing -- Check JSON: $JSONF"
fi

echo "----------------------------------"
printf "FEDI_DMRI_PIPELINE_STEPS Details:\n\n"
ranlist="tmp/${RANDOM}.tmp"
for step in "${!FEDI_DMRI_PIPELINE_STEPS[@]}"; do
  printf "%s: %s\n" "$step" "${FEDI_DMRI_PIPELINE_STEPS[$step]}" >> $ranlist
done
sort -V $ranlist
rm $ranlist
echo "----------------------------------"



echo "----------------------------------"
echo "---- LAUNCHING HAITCH PIPELINE ---"
echo "----------------------------------"



let STEPX=1
echo "---------------------------------------------------------------------------------"
# STEP 1: STEP1_DWI_DENOISE_USING_GSVS
if [[ $NOLOCKS = 1 && -e ${LOCK1} && ${FEDI_DMRI_PIPELINE_STEPS["STEP1_DWI_DENOISE_USING_GSVS"]} == "TODO" ]] ; then rm ${LOCK1} ; fi
if [[ ${FEDI_DMRI_PIPELINE_STEPS["STEP1_DWI_DENOISE_USING_GSVS"]} == "TODO" ]] && [[ ! -e ${LOCK1} ]] ; then

    touch ${LOCK1}

    if [ -n "$PHASE" ]; then
        echo "To be done later"
        # Good for better pipeline, but not important right now. To do it later
        # if there is phase, we will not have to apply rician correction
        # mrcalc DICOM_DWI_mag/ DICOM_DWI_phase/ pi 4096 -div -mult -polar complex.mif
        # dwidenoise complex.mif complex_dn.mif -noise noisemap.mif
        # mrcalc complex.mif complex_dn.mif complex_dn.mif -abs -div -conj -mult complex_pc.mif
        # dwidenoise complex_pc.mif denoised_pc_dn.mif -noise noisemap_pc.mif
        # mrcalc denoised_pc_dn.mif -abs denoised_pc_dn_mag.mif

    else

        echo -e "\n ${STEPX}.|--->  dMRI noise level estimation and denoising using GSVS  ---"
        # Exp2 option : the improved estimator GSVS introduced in Cordero-Grande et al. (2019).
        mrconvert $INPUT -set_property comments "FEDI Pipeline" $INPUT -force
        dwidenoise -noise ${PRPROCESSING_DIR}/fullnoisemap.mif -estimator Exp2 $INPUT ${PRPROCESSING_DIR}/dwide.mif -nthreads $MRTRIX_NTHREADS -force
        # Eyeballing the residuals
        mrcalc $INPUT ${PRPROCESSING_DIR}/dwide.mif -subtract ${PRPROCESSING_DIR}/dwidenoise_residuals.mif -force

    fi
else
    echo "Step $STEPX locked or not set to TODO. Moving on."
fi

((STEPX++))
echo "---------------------------------------------------------------------------------"
# STEP 2: STEP2_MRDEGIBBS_RINGING_ARTI
if [[ $NOLOCKS = 1 && -e ${LOCK2} && ${FEDI_DMRI_PIPELINE_STEPS["STEP2_MRDEGIBBS_RINGING_ARTI"]}  == "TODO" ]] ; then rm ${LOCK2} ; fi
if [[ ${FEDI_DMRI_PIPELINE_STEPS["STEP2_MRDEGIBBS_RINGING_ARTI"]}  == "TODO" ]] && [[ ! -e ${LOCK2} ]] ; then

    touch ${LOCK2}

    # Kellner et al., 2016
    echo -e "\n ${STEPX}.|--->  Remove Gibbs Ringing Artifacts  ---"
    echo "GRAD4CLS: $GRAD4CLS"
    echo "GRAD5CLS: $GRAD5CLS"
    if [[ ${PROJNAME} == "BCH" ]]; then
        echo "Calculating GRAD5CLS"
        python ${SRC}/create_grad5cls_index.py $GRAD4CLS $GRAD5CLS $INDX
    fi
    # mrtrix syntax allows piping of output/inputs using dashes "-". A dash in the output argument slot will pipe the output to the next command, a dash in the input argument slot will take the piped data from the previous command
    # some mrtrix binaries including mrdegibbs require a folder named exactly "tmp" in the directory. As of this writing, a mkdir has been added earlier in the script.
    mrdegibbs ${PRPROCESSING_DIR}/dwide.mif - | mrconvert - - -stride "$STRIDES" | mrconvert - -grad $GRAD5CLS -import_pe_eddy $ACQPARAM $INDX ${PRPROCESSING_DIR}/dwigb.mif -force

else
    echo "Step $STEPX locked or not set to TODO. Moving on."
fi

((STEPX++))
echo "---------------------------------------------------------------------------------"
# STEP 3: STEP3_RICIAN_BIAS_CORRECTION
if [[ $NOLOCKS = 1 && -e ${LOCK3} && ${FEDI_DMRI_PIPELINE_STEPS["STEP3_RICIAN_BIAS_CORRECTION"]}  == "TODO" ]] ; then rm ${LOCK3} ; fi
if [[ ${FEDI_DMRI_PIPELINE_STEPS["STEP3_RICIAN_BIAS_CORRECTION"]}  == "TODO" ]] && [[ ! -e ${LOCK3} ]] ; then

    touch ${LOCK3}

    RICIAN_WAY="LOWSNR"

    # Ades-Aron et al., 2019
    echo -e "\n ${STEPX}.|--->  Rician Bias Correction   ---"

    if [[ ${RICIAN_WAY} == "LOWSNR" ]]; then

        # Noise map estimated from low bvalue images only
        # Determine the loweste b-values
        LOWBvalue=$(awk '{for (i=1; i<=NF; i++) if ($i > 0 && (!min || $i < min)) min=$i} END {print min}' "$BVALS")

        dwiextract -grad $GRAD5CLS -shell $LOWBvalue $INPUT ${PRPROCESSING_DIR}/dwiLowBval.mif -force
        dwidenoise -noise ${PRPROCESSING_DIR}/lowbvalnoisemap.mif -estimator Exp2 ${PRPROCESSING_DIR}/dwiLowBval.mif ${PRPROCESSING_DIR}/dwitmp.mif -nthreads $MRTRIX_NTHREADS -force

        NOISE_MAP=${PRPROCESSING_DIR}/lowbvalnoisemap.mif
    fi

    if [[ ! -e $NOISE_MAP  ]] || [[ ${RICIAN_WAY} == "STANDARD" ]]; then

         # Noise map estimated from full volumes
        NOISE_MAP=${PRPROCESSING_DIR}/fullnoisemap.mif

    fi

    mrcalc ${NOISE_MAP} -finite ${NOISE_MAP} 0 -if ${PRPROCESSING_DIR}/finitenoisemap.mif -force
    mrcalc ${PRPROCESSING_DIR}/dwigb.mif 2 -pow ${PRPROCESSING_DIR}/finitenoisemap.mif 2 -pow -sub -abs -sqrt - | mrcalc - -finite - 0 -if ${PRPROCESSING_DIR}/dwirc.mif -force

    mrconvert ${PRPROCESSING_DIR}/dwirc.mif -grad $GRAD5CLS -import_pe_eddy $ACQPARAM $INDX ${PRPROCESSING_DIR}/dwirc.mif -force

else
    echo "Step $STEPX locked or not set to TODO. Moving on."
fi

((STEPX++))
echo "---------------------------------------------------------------------------------"
# STEP 4: STEP4_FETAL_BRAIN_EXTRACTION
if [[ $NOLOCKS = 1 && -e ${LOCK4} && ${FEDI_DMRI_PIPELINE_STEPS["STEP4_FETAL_BRAIN_EXTRACTION"]}  == "TODO" ]] ; then rm ${LOCK4} ; fi
if [[ ${FEDI_DMRI_PIPELINE_STEPS["STEP4_FETAL_BRAIN_EXTRACTION"]}  == "TODO" ]] && [[ ! -e ${LOCK4} ]] ; then

    touch ${LOCK4}

    echo -e "\n${STEPX}.|---> Brain extraction ---"

    SPLIT_INTO_ODDEVEN="NO"
    if [[ $SPLIT_INTO_ODDEVEN == "YES" ]]; then
        # create odd and even 4D volumes. 4D-Odd/even contains all odd/even slices for all directions
        # I am considering i=0 (slice number 1) as odd
        NSLICES_ODD=$(seq 0 2 $((NSLICES - 1)) | tr '\n' ',')
        NSLICES_EVEN=$(seq 1 2 $((NSLICES - 1)) | tr '\n' ',')
        NSLICES_ODD=${NSLICES_ODD%,}
        NSLICES_EVEN=${NSLICES_EVEN%,}
        mrconvert -coord $AXSLICES $NSLICES_ODD "${PRPROCESSING_DIR}/dwirc.mif" "${OUTPATHSUB}/working_odd.mif" -force
        mrconvert -coord $AXSLICES $NSLICES_EVEN "${PRPROCESSING_DIR}/dwirc.mif" "${OUTPATHSUB}/working_even.mif" -force
        echo "Split 4D volume into 3D volumes"
        for ((VIDX=0; VIDX<${NVOLUMES}; VIDX++)); do
            TE=$((VIDX % NUMBER_ECHOTIME + 1))
            VNUM=$((VIDX / NUMBER_ECHOTIME))
            mrconvert -coord 3 $VIDX "${OUTPATHSUB}/working_odd.mif"   "${SEGMENTATION_DIR}/working_odd_TE${TE}_v${VNUM}.nii.gz"
            mrconvert -coord 3 $VIDX "${OUTPATHSUB}/working_even.mif" "${SEGMENTATION_DIR}/working_even_TE${TE}_v${VNUM}.nii.gz"
        done
    fi

    # Split the 4D volume(s) into 3D volumes
    echo "Split 4D volume into 3D volumes"
    for ((VIDX=0; VIDX<${NVOLUMES}; VIDX++)); do
        TE=$((VIDX % NUMBER_ECHOTIME + 1))
        VNUM=$((VIDX / NUMBER_ECHOTIME))
        mrconvert -coord 3 $VIDX "${PRPROCESSING_DIR}/dwirc.mif" "${SEGMENTATION_DIR}/working_TE${TE}_v${VNUM}.nii.gz" -force

    done

    # Fetal brain segmentation
    echo
    echo "============ dMRI Segmentation ============"
    echo "Segmentation Method: $SEGMENTATION_METHOD"
    # if [[ $SEGMENTATION_METHOD == "DAVOOD" ]] ; then
    #     segin="dmri3d" ; segout="dmri3d"
    # elif [[ $SEGMENTATION_METHOD == "RAZIEH" ]] ; then
    #     segin="inputs" ; segout="fetal-bet"
    # else echo SEGMENTATION_METHOD supplied in config is invalid
    #     exit
    # fi 

    # make a subdirectory to feed into segmentation code and copy images there
    mkdir -vp ${OUTPATHSUB}/segmentation/{$segin,$segout}
    chmod 777 ${OUTPATHSUB}/segmentation/{$segin,$segout}
    mpath=`readlink -f ${OUTPATHSUB}` # mount path for container
    find ${OUTPATHSUB}/segmentation -maxdepth 1 -regex '.*working_TE.*v[0-9]+.nii.gz' -a ! -name \*mask\* -exec cp {} -v ${OUTPATHSUB}/segmentation/${segin}/ \;

    # Both scripts segment all 3D volumes in the input path
    if [[ ${SEGMENTATION_METHOD}  == "DAVOOD" ]]; then

        DVD_SRC=/home/ch244310/software/dmri_segmentation_3d
        python ${DVD_SRC}/dMRI_volume_segmentation.py ${SEGMENTATION_DIR} \
                                                      ${DVD_SRC}/model_checkpoint \
                                                      gpu_num=1
                                                      # dilation_radius=1 # option not used



    elif [[ ${SEGMENTATION_METHOD}  == "DAVOODotherway" ]]; then
            #statements    

        if [[ $SING = 1 ]] ; then
            echo "Running dmri3d container with singularity"
            singularity exec docker://arfentul/dmri3d /bin/bash -c "python /src/dMRI_volume_segmentation.py ${OUTPATHSUB}/segmentation/${segin}/ /src/ gpu_num=0 dilation_radius=-1"
        else

            echo "Pulling dmri3d docker container"
            docker pull arfentul/dmri3d # pull docker image
    
            # Mask dwi with dMRI3d
            docker run -v --rm --mount type=bind,source=${mpath},target=/workspace arfentul/dmri3d /bin/bash -c \
            "python /src/dMRI_volume_segmentation.py /workspace/segmentation/${segin}/ /src/ gpu_num=0 dilation_radius=-1 ; chmod 666 /workspace/segmentation/${segin}/*mask.nii.gz"
            echo
        fi




    elif [[ ${SEGMENTATION_METHOD}  == "RAZIEH" ]]; then

        if [[ $SING = 1 ]] ; then
            echo Running dmri3d container with singularity
            singularity exec docker://fetalbet-model /bin/bash -c "python /app/src/codes/inference.py --data_path ${OUTPATHSUB}/segmentation/${segin}/ --save_path ${OUTPATHSUB}/segmentation/${segout}/ --saved_model_path /app/src/model/AttUNet.pth"
        else

            echo "Pulling fetal-bet docker container"
            docker pull arfentul/fetalbet-model # pull docker image

            # Mask dwi with Fetal-BET
            docker run -v --rm --mount type=bind,source=${mpath},target=/workspace arfentul/fetalbet-model:first /bin/bash -c \
            "python /app/src/codes/inference.py --data_path /workspace/segmentation/${segin} --save_path /workspace/segmentation/${segout} --saved_model_path /app/src/model/AttUNet.pth ; chmod 666 /workspace/segmentation/${segout}/*mask.nii.gz"
            echo
        fi

    else
        echo "SEGMENTATION_METHOD specified in $0 is invalid"
        exit
    fi

    # rename output files
    # echo "moving dwi brain masks to ${SEGMENTATION_DIR}"
    # for outmask in ${OUTPATHSUB}/segmentation/${segout}/*mask.nii.gz ; do
    #     maskbase=`basename $outmask`
    #     baseim=`echo $maskbase | sed -e 's,\(v[0-9]\+\)_.*mask.nii.gz,\1,g'`
    #     mv -v ${outmask} ${SEGMENTATION_DIR}/${baseim}_mask.nii.gz
    # done

    # if [[ -d ${OUTPATHSUB}/segmentation/${segin} ]] ; then rm -f ${OUTPATHSUB}/segmentation/${segin}/* ; fi # remove the input image copies

    # Plot segmentation outliers
    for ((TE=1; TE<$((NUMBER_ECHOTIME+1)); TE++)); do
        python ${SRC}/segm_outliers.py -d "${SEGMENTATION_DIR}" -s "working_TE${TE}" -e "_mask.nii.gz" -o "${QUAL_CONTROL_DIR}/${SUBJECTID}_SegmStep4"
    done

else
    echo "Step $STEPX locked or not set to TODO. Moving on."
fi

((STEPX++))
echo "---------------------------------------------------------------------------------"
# STEP 5: STEP5_SPLIT_CROP_SKDATA_MASK
if [[ $NOLOCKS = 1 && -e ${LOCK5} && ${FEDI_DMRI_PIPELINE_STEPS["STEP5_SPLIT_CROP_SKDATA_MASK"]}  == "TODO" ]] ; then rm ${LOCK5} ; fi
if [[ ${FEDI_DMRI_PIPELINE_STEPS["STEP5_SPLIT_CROP_SKDATA_MASK"]}  == "TODO" ]] && [[ ! -e ${LOCK5} ]] ; then

    touch ${LOCK5}

    echo "${STEPX}.|---> Split, crop and skull strip data ---"

    echo "---------------------"
    echo "5.1. Create Union_mask"
    # Create Union_mask
    mrconvert "${SEGMENTATION_DIR}/working_TE1_v0_mask.nii.gz" "${SEGMENTATION_DIR}/union_mask.mif" -force -quiet # just initlialization

    for ((VIDX=0; VIDX<${NVOLUMES}; VIDX++)); do
        TE=$((VIDX % NUMBER_ECHOTIME + 1))
        VNUM=$((VIDX / NUMBER_ECHOTIME))

        # Keep the largest connected segmented region
        maskfilter -largest "${SEGMENTATION_DIR}/working_TE${TE}_v${VNUM}_mask.nii.gz" connect "${SEGMENTATION_DIR}/working_TE${TE}_v${VNUM}_mask.nii.gz" -force -quiet
        # Create union_mask
        mrcalc "${SEGMENTATION_DIR}/union_mask.mif" "${SEGMENTATION_DIR}/working_TE${TE}_v${VNUM}_mask.nii.gz" -max "${SEGMENTATION_DIR}/union_mask.mif" -force  -quiet

    done
    mrconvert "${SEGMENTATION_DIR}/union_mask.mif" "${SEGMENTATION_DIR}/union_mask.nii.gz" -force


    echo "---------------------"
    echo "5.2. Dilate union_mask"
    # Create union_mask_dilated from union_mask
    maskfilter -largest ${SEGMENTATION_DIR}/union_mask.mif connect - | maskfilter -npass 3 - dilate "${SEGMENTATION_DIR}/union_mask_dilated.mif" -force -quiet

    echo "5.3. Crop 4D-dMRI using union_mask_dilated"
    mrgrid -all_axes "${PRPROCESSING_DIR}/dwirc.mif" crop -mask "${SEGMENTATION_DIR}/union_mask_dilated.mif" "${PRPROCESSING_DIR}/dwicrop.mif" -force -quiet

    echo "5.4. Crop union mask"
    mrgrid -all_axes "${SEGMENTATION_DIR}/union_mask.mif" crop -mask "${SEGMENTATION_DIR}/union_mask_dilated.mif" "${PRPROCESSING_DIR}/union_maskcrop.nii.gz" -force -quiet

    # Todo : create an independant script for that with input and output
    echo "5.5. Ensure even dimension to avoid issues"
    NSIZE1TMP=$(mrinfo -size "${PRPROCESSING_DIR}/dwicrop.mif" -quiet | awk '{print $1}')
    NSIZE2TMP=$(mrinfo -size "${PRPROCESSING_DIR}/dwicrop.mif" -quiet | awk '{print $2}')
    NSIZE3TMP=$(mrinfo -size "${PRPROCESSING_DIR}/dwicrop.mif" -quiet | awk '{print $3}')
    if [ $((NSIZE1TMP % 2)) -ne 0 ]; then  mrconvert -coord 0 0:$((NSIZE1TMP-2)) "${PRPROCESSING_DIR}/dwicrop.mif" "${PRPROCESSING_DIR}/dwicrop.mif" -force -quiet; fi
    if [ $((NSIZE2TMP % 2)) -ne 0 ]; then  mrconvert -coord 1 0:$((NSIZE2TMP-2)) "${PRPROCESSING_DIR}/dwicrop.mif" "${PRPROCESSING_DIR}/dwicrop.mif" -force -quiet; fi
    if [ $((NSIZE3TMP % 2)) -ne 0 ]; then  mrconvert -coord 2 0:$((NSIZE3TMP-2)) "${PRPROCESSING_DIR}/dwicrop.mif" "${PRPROCESSING_DIR}/dwicrop.mif" -force -quiet; fi

    if [ $((NSIZE1TMP % 2)) -ne 0 ]; then  mrconvert -coord 0 0:$((NSIZE1TMP-2)) "${PRPROCESSING_DIR}/union_maskcrop.nii.gz" "${PRPROCESSING_DIR}/union_maskcrop.nii.gz" -force -quiet; fi
    if [ $((NSIZE2TMP % 2)) -ne 0 ]; then  mrconvert -coord 1 0:$((NSIZE2TMP-2)) "${PRPROCESSING_DIR}/union_maskcrop.nii.gz" "${PRPROCESSING_DIR}/union_maskcrop.nii.gz" -force -quiet; fi
    if [ $((NSIZE3TMP % 2)) -ne 0 ]; then  mrconvert -coord 2 0:$((NSIZE3TMP-2)) "${PRPROCESSING_DIR}/union_maskcrop.nii.gz" "${PRPROCESSING_DIR}/union_maskcrop.nii.gz" -force -quiet; fi


    echo "5.6. Get 3D volumes croppped and Skull-stripped"
    # 3D volumes croppped and Skull-stripped
    for ((VIDX=0; VIDX<${NVOLUMES}; VIDX++)); do
        TE=$((VIDX % NUMBER_ECHOTIME + 1))
        VNUM=$((VIDX / NUMBER_ECHOTIME))
        #echo "5.6.I. Crop masks"
        mrgrid -all_axes "${SEGMENTATION_DIR}/working_TE${TE}_v${VNUM}_mask.nii.gz" crop -mask "${SEGMENTATION_DIR}/union_mask_dilated.mif" "${SEGMENTATION_DIR}/working_TE${TE}_v${VNUM}_maskcrop.nii.gz" -force -quiet

        #echo "5.6.I.1. Ensure even dimension to avoid issues"
        NSIZE1TMP=$(mrinfo -size "${SEGMENTATION_DIR}/working_TE${TE}_v${VNUM}_maskcrop.nii.gz" -quiet | awk '{print $1}')
        NSIZE2TMP=$(mrinfo -size "${SEGMENTATION_DIR}/working_TE${TE}_v${VNUM}_maskcrop.nii.gz" -quiet | awk '{print $2}')
        NSIZE3TMP=$(mrinfo -size "${SEGMENTATION_DIR}/working_TE${TE}_v${VNUM}_maskcrop.nii.gz" -quiet | awk '{print $3}')
        if [ $((NSIZE1TMP % 2)) -ne 0 ]; then  mrconvert -coord 0 0:$((NSIZE1TMP-2)) "${SEGMENTATION_DIR}/working_TE${TE}_v${VNUM}_maskcrop.nii.gz" "${SEGMENTATION_DIR}/working_TE${TE}_v${VNUM}_maskcrop.nii.gz" -force -quiet; fi
        if [ $((NSIZE2TMP % 2)) -ne 0 ]; then  mrconvert -coord 1 0:$((NSIZE2TMP-2)) "${SEGMENTATION_DIR}/working_TE${TE}_v${VNUM}_maskcrop.nii.gz" "${SEGMENTATION_DIR}/working_TE${TE}_v${VNUM}_maskcrop.nii.gz" -force -quiet; fi
        if [ $((NSIZE3TMP % 2)) -ne 0 ]; then  mrconvert -coord 2 0:$((NSIZE3TMP-2)) "${SEGMENTATION_DIR}/working_TE${TE}_v${VNUM}_maskcrop.nii.gz" "${SEGMENTATION_DIR}/working_TE${TE}_v${VNUM}_maskcrop.nii.gz" -force -quiet; fi


        #echo "5.6.I.2. Split cropped 4D into 3Ds"
        mrconvert -coord 3 $VIDX "${PRPROCESSING_DIR}/dwicrop.mif" - -quiet | mrconvert - "${SEGMENTATION_DIR}/dwicrop_TE${TE}_v${VNUM}.nii.gz" -axes 0,1,2 -force -quiet

        #echo "5.6.I.3. Skull-strip"
        mrcalc "${SEGMENTATION_DIR}/dwicrop_TE${TE}_v${VNUM}.nii.gz" "${SEGMENTATION_DIR}/working_TE${TE}_v${VNUM}_maskcrop.nii.gz" -multiply "${SEGMENTATION_DIR}/dwicropsk_TE${TE}_v${VNUM}.nii.gz" -force -quiet

        DWI_CROPSK_LIST+="${SEGMENTATION_DIR}/dwicropsk_TE${TE}_v${VNUM}.nii.gz "

        #echo "5.6.I.4. Split cropped 4D into 2D (slices)"
        SPLITING_INTO_SLICES="YES"
        if [[ $SPLITING_INTO_SLICES  == "YES" && $NUMBER_ECHOTIME -gt 1 ]]; then
            for ((SIDX=0; SIDX<${NSLICESCROP}; SIDX++)); do
                # echo "mrconvert -coord 3  $VIDX  "${PRPROCESSING_DIR}/dwicrop.mif" - -quiet | mrconvert -coord $AXSLICES $SIDX - "${SEGMENTATION_DIR}/dwicrop_TE${TE}_v${VNUM}_s${SIDX}.nii.gz" -force -quiet"
                mrconvert -coord 3  $VIDX  "${PRPROCESSING_DIR}/dwicrop.mif" - -quiet | mrconvert -coord $AXSLICES $SIDX - "${SEGMENTATION_DIR}/dwicrop_TE${TE}_v${VNUM}_s${SIDX}.nii.gz" -force -quiet
                mrconvert -coord $AXSLICES $SIDX "${SEGMENTATION_DIR}/dwicropsk_TE${TE}_v${VNUM}.nii.gz" "${SEGMENTATION_DIR}/dwicropsk_TE${TE}_v${VNUM}_s${SIDX}.nii.gz" -force -quiet
            done
        fi
    done

    mrcat -axis 3 $DWI_CROPSK_LIST "${PRPROCESSING_DIR}/dwicropsk.nii.gz" -force
else
    echo "Step $STEPX locked or not set to TODO. Moving on."
fi

((STEPX++))
echo "---------------------------------------------------------------------------------"
# STEP 6: STEP6_SLICECORRECTDISTORTION
if [[ $NOLOCKS = 1 && -e ${LOCK6} && ${FEDI_DMRI_PIPELINE_STEPS["STEP6_SLICECORRECTDISTORTION"]} == "TODO" ]] ; then rm ${LOCK6} ; fi
if [[ ${FEDI_DMRI_PIPELINE_STEPS["STEP6_SLICECORRECTDISTORTION"]} == "TODO" ]] && [[ $DWIMODALITY == "dwiME" ]] && [[ $NUMBER_ECHOTIME -gt 1 ]] && [[ ! -e ${LOCK6} ]] ; then

    # Check if VOLUME TO VOLUME DISOTRITON CORRECTION IS SIMILAR to SLICE TO SLICE
    # TO ADD NORMALIZATION SLICE PER SLICE AND normialization of the backgound
    # Masked data worked better for distortion correction for EPIC and TOPUP
    # epiwunarp works only with nifti data
    # reduce smoothness
    # Distortion Correction per slice: to check if we should do TE1-TE2 or TE2-TE1
    # Distortion correction slice-based doesn't work using TOPUP, may be try BM later

    # #  Lock this scan in order to not be processed with other
    # touch ${DISTORTIONCO_DIR}/lock_TOPUP_CLASSIC
    touch ${LOCK6}

    # Fix the DCPREFIX first, meaning which data will be used for the following steps. "dwicrop" or "dwicropsk"
    DCPREFIX="dwicrop"
    DISTORTIONCORRECTION_METHOD="TOPUP"
    DISTORTIONCORRECTION_WAY="CLASSIC"
    # DISTORTIONCORRECTION_WAY="VOLUMETOPUPONLY"

    DISTORTIONCO_TMP="${OUTPATHSUB}/distortion/tmp_${DISTORTIONCORRECTION_METHOD}_${DISTORTIONCORRECTION_WAY}"

    echo "DISTORTION CORRECTION TE1 VOLUME/SLICE to TE2 VOLUME/SLICE"
    echo "Used Distortion Correction Method is     : $DISTORTIONCORRECTION_METHOD"
    echo "Way of Applying Distortion Correction is : $DISTORTIONCORRECTION_WAY"

    ##########################################################################################################################################################
    ##########################################################################################################################################################
    if [[ $DISTORTIONCORRECTION_METHOD == "EPIC" ]]; then
        mkdir -p ${DISTORTIONCO_TMP}
        if [[ $DISTORTIONCORRECTION_WAY == "VOLUME" ]]; then

            DWI_VOLUME_List=""
            NVOLUMES_PER_TE=$((NVOLUMES / NUMBER_ECHOTIME))
            for ((VNUM=0; VNUM<${NVOLUMES_PER_TE}; VNUM++)); do
                echo "Start EPIC distortion correction per volume, volume: $VNUM"
                    epiunwarp --phase-encode-lr --no-flip \
                    --write-jacobian-fwd "${DISTORTIONCO_TMP}/epic_jacfwd_v${VNUM}.nii.gz" \
                    "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}.nii.gz" \
                    "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}.nii.gz" \
                    "${DISTORTIONCO_TMP}/${DCPREFIX}_TE1_v${VNUM}_dcepic.nii.gz" \
                    "${DISTORTIONCO_TMP}/${DCPREFIX}_TE2_v${VNUM}_dcepic.nii.gz" \
                    "${DISTORTIONCO_TMP}/epic_dfield_v${VNUM}.nii.gz"
                    DWI_VOLUME_List+="${DISTORTIONCO_TMP}/${DCPREFIX}_TE1_v${VNUM}_dcepic.nii.gz "
            done
            mrcat -axis 3 $DWI_VOLUME_List "${DISTORTIONCO_DIR}/EPIC/${DCPREFIX}_TE1_dcEPIC_perVolume.nii.gz"

        elif [[ $DISTORTIONCORRECTION_WAY == "SLICE_NODUPLICATION" ]]; then

            # This option is better than the one with duplication because the second one change qform and sform.
            # This option gives an ouput with correct size
            # Correct sform and qform
            DWI_VOLUME_List=""
            NVOLUMES_PER_TE=$((NVOLUMES / NUMBER_ECHOTIME))
            for ((VNUM=0; VNUM<${NVOLUMES_PER_TE}; VNUM++)); do
                DWI_SLICE_List=""
                echo "Start EPIC distortion correction with $DISTORTIONCORRECTION_WAY, volume: $VNUM"
                for ((SIDX=0; SIDX<${NSLICESCROP}; SIDX++)); do
                    # echo "Start EPIC distortion correction per slice, volume-Slice: $VNUM-$SIDX"
                    DIRSORDER="LR"
                    epiunwarp --phase-encode-lr --no-flip  --smooth-sigma-max 2 \
                    --write-jacobian-fwd "${DISTORTIONCO_TMP}/epic_jac_v${VNUM}_s${SIDX}.nii.gz" \
                    "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                    "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                    "${DISTORTIONCO_TMP}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}_dcepic.nii.gz" \
                    "${DISTORTIONCO_TMP}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}_dcepic.nii.gz" \
                    "${DISTORTIONCO_TMP}/epic_dfield_v${VNUM}_s${SIDX}.nii.gz"
                    DWI_SLICE_List+="${DISTORTIONCO_TMP}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}_dcepic.nii.gz "
                done
                mrcat -axis $AXSLICES $DWI_SLICE_List "${DISTORTIONCO_TMP}/${DCPREFIX}_TE1_v${VNUM}_dcepic.nii.gz" -force -quiet
                DWI_VOLUME_List+="${DISTORTIONCO_TMP}/${DCPREFIX}_TE1_v${VNUM}_dcepic.nii.gz "
            done
            mrcat -axis 3 $DWI_VOLUME_List "${DISTORTIONCO_DIR}/EPIC/${DCPREFIX}_TE1_SliceNoDupEpic_${DIRSORDER}.nii.gz"

        elif [[ $DISTORTIONCORRECTION_WAY == "SLICE_WITHDUPLICATION" ]]; then

            # This option gives an ouput with correct size
            # But give warning in the sform and qform
            DWI_VOLUME_List=""
            NVOLUMES_PER_TE=$((NVOLUMES / NUMBER_ECHOTIME))
            for ((VNUM=0; VNUM<${NVOLUMES_PER_TE}; VNUM++)); do
                DWI_SLICE_List=""
                echo "Start EPIC distortion correction with $DISTORTIONCORRECTION_WAY, volume: $VNUM"
                for ((SIDX=0; SIDX<${NSLICESCROP}; SIDX++)); do

                    mrcat -axis $AXSLICES "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                  "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                  "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                  "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                  "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                  "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}_dup.nii.gz" -force -quiet

                    mrcat -axis $AXSLICES "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                  "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                  "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                  "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                  "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                  "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}_dup.nii.gz" -force -quiet

                    DIRSORDER="LR"
                    epiunwarp --phase-encode-lr --no-flip  --smooth-sigma-max 2 \
                    --write-jacobian-fwd "${DISTORTIONCO_TMP}/epic_jac_v${VNUM}_s${SIDX}.nii.gz" \
                    "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}_dup.nii.gz" \
                    "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}_dup.nii.gz" \
                    "${DISTORTIONCO_TMP}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}_dup_dcepic.nii.gz" \
                    "${DISTORTIONCO_TMP}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}_dup_dcepic.nii.gz" \
                    "${DISTORTIONCO_TMP}/epic_dfield_v${VNUM}_s${SIDX}_dup.nii.gz"

                    mrconvert -coord $AXSLICES 3 "${DISTORTIONCO_TMP}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}_dup_dcepic.nii.gz" "${DISTORTIONCO_TMP}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}_DupExt_dcepic.nii.gz" -force -quiet

                    DWI_SLICE_List+="${DISTORTIONCO_TMP}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}_DupExt_dcepic.nii.gz "
                done
                mrcat -axis $AXSLICES $DWI_SLICE_List "${DISTORTIONCO_TMP}/${DCPREFIX}_TE1_v${VNUM}_DupExt_dcepic.nii.gz" -force -quiet
                DWI_VOLUME_List+="${DISTORTIONCO_TMP}/${DCPREFIX}_TE1_v${VNUM}_DupExt_dcepic.nii.gz "
            done
            mrcat -axis 3 $DWI_VOLUME_List "${DISTORTIONCO_DIR}/EPIC/${DCPREFIX}_TE1_SliceDupEpic_${DIRSORDER}.nii.gz"

        fi

    ##########################################################################################################################################################
    ##########################################################################################################################################################
    elif [[ $DISTORTIONCORRECTION_METHOD == "TOPUP" ]]; then

        for DIRSORDER in "APPA"; do

            DISTORTIONCO_TMP="${OUTPATHSUB}/distortion/tmp_${DISTORTIONCORRECTION_METHOD}_${DISTORTIONCORRECTION_WAY}_${DIRSORDER}"
            mkdir -p ${DISTORTIONCO_TMP}
            echo "/////////////////////////////// - ${DIRSORDER} - ///////////////////////////////////////////"
            if [[ $DIRSORDER == "APPA" ]]; then
                echo "0 1 0 0.0431799" > "${DISTORTIONCO_TMP}/TEs_acq_param.txt"
                echo "0 -1 0 0.0431799" >> "${DISTORTIONCO_TMP}/TEs_acq_param.txt"
            elif [[ $DIRSORDER == "PAAP" ]]; then
                echo "0 -1 0 0.0431799" > "${DISTORTIONCO_TMP}/TEs_acq_param.txt"
                echo "0 1 0 0.0431799" >> "${DISTORTIONCO_TMP}/TEs_acq_param.txt"
            fi

            if [[ $DISTORTIONCORRECTION_WAY == "CLASSIC" ]]; then

                echo "Start TOPUP distortion correction per slice, volume-Slice: $VNUM-$SIDX"

                # EVEN ODD ?
                dwiextract -bzero "${PRPROCESSING_DIR}/dwicrop.mif" "${PRPROCESSING_DIR}/dwicrop_allb0.mif" -force
                NALLB0S=$(mrinfo -size "${PRPROCESSING_DIR}/dwicrop_allb0.mif" -quiet | awk '{print $4}')
                LAST_B0_INDEX=$((NALLB0S - NUMBER_ECHOTIME + 1))
                # LAST_B0_INDEX=$((NALLB0S - 1))
                mrconvert -coord 3 0,${LAST_B0_INDEX} "${PRPROCESSING_DIR}/dwicrop_allb0.mif" "${DISTORTIONCO_TMP}/${DCPREFIX}_bothTE_1st_b0s.nii.gz"  -force


                even_sequence=""
                for ((i=0; i<NVOLUMES; i+=2)); do
                    if [[ -z $even_sequence ]]; then
                        even_sequence="$i"
                    else
                        even_sequence="$even_sequence,$i"
                    fi
                done
                echo $even_sequence

                # Sequence for odd numbers (1:3:5:...)
                odd_sequence=""
                for ((i=1; i<NVOLUMES; i+=2)); do
                    if [[ -z $odd_sequence ]]; then
                        odd_sequence="$i"
                    else
                        odd_sequence="$odd_sequence,$i"
                    fi
                done
                echo $odd_sequence


                mrconvert -coord 3 "$even_sequence" "${PRPROCESSING_DIR}/dwicrop.mif"  - | mrconvert - -stride -1,2,3,4 "${PRPROCESSING_DIR}/dwicrop_FSLTE1.nii.gz" -force
                mrconvert -coord 3 "$odd_sequence" "${PRPROCESSING_DIR}/dwicrop.mif" - | mrconvert - -stride -1,2,3,4 "${PRPROCESSING_DIR}/dwicrop_FSLTE2.nii.gz" -force


                topup --imain="${DISTORTIONCO_TMP}/${DCPREFIX}_bothTE_1st_b0s.nii.gz" \
                      --datain="${DISTORTIONCO_TMP}/TEs_acq_param.txt" \
                      --config=b02b0.cnf \
                      --scale=1 \
                      --out="${DISTORTIONCO_TMP}/TEs_topup_results_v${VNUM}" \
                      --fout="${DISTORTIONCO_TMP}/fout_TEs_topup_results_v${VNUM}" \
                      --iout="${DISTORTIONCO_TMP}/iout_TEs_topup_results_v${VNUM}"

                applytopup --imain="${PRPROCESSING_DIR}/dwicrop_FSLTE1.nii.gz" --inindex=1 \
                    --datain="${DISTORTIONCO_TMP}/TEs_acq_param.txt" \
                    --topup="${DISTORTIONCO_TMP}/TEs_topup_results_v${VNUM}" \
                    --out="${DISTORTIONCO_DIR}/TOPUP/dwidc_TOPUP_CLASSIC_TE1_$DIRSORDER.nii.gz" \
                    --method=jac

                applytopup --imain="${PRPROCESSING_DIR}/dwicrop_FSLTE2.nii.gz" --inindex=2 \
                    --datain="${DISTORTIONCO_TMP}/TEs_acq_param.txt" \
                    --topup="${DISTORTIONCO_TMP}/TEs_topup_results_v${VNUM}" \
                    --out="${DISTORTIONCO_DIR}/TOPUP/dwidc_TOPUP_CLASSIC_TE2_$DIRSORDER.nii.gz" \
                    --method=jac

            elif [[ $DISTORTIONCORRECTION_WAY == "VOLUME" ]]; then

                DWIList=""
                NVOLUMES_PER_TE=$((NVOLUMES / NUMBER_ECHOTIME))
                for ((VNUM=0; VNUM<${NVOLUMES_PER_TE}; VNUM++)); do

                    echo "Start TOPUP distortion correction per slice, volume-Slice: $VNUM-$SIDX"
                    # topup parameters to update :--fwhm --miter --scale=1
                    # applytopup parameters to update : --method
                    mrcat -axis 3 "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}.nii.gz" "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}.nii.gz" \
                        "${DISTORTIONCO_TMP}/${DCPREFIX}_bothTEs_v${VNUM}.nii.gz" -force

                    topup --imain="${DISTORTIONCO_TMP}/${DCPREFIX}_bothTEs_v${VNUM}.nii.gz" \
                          --datain="${DISTORTIONCO_TMP}/TEs_acq_param.txt" \
                          --config=b02b0.cnf \
                          --out="${DISTORTIONCO_TMP}/TEs_topup_results_v${VNUM}" \
                          --fout="${DISTORTIONCO_TMP}/fout_TEs_topup_results_v${VNUM}" \
                          --iout="${DISTORTIONCO_TMP}/iout_TEs_topup_results_v${VNUM}"

                    applytopup --imain="${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}.nii.gz","${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}.nii.gz" --inindex=1,2 \
                        --datain="${DISTORTIONCO_TMP}/TEs_acq_param.txt" \
                        --topup="${DISTORTIONCO_TMP}/TEs_topup_results_v${VNUM}" \
                        --out="${DISTORTIONCO_TMP}/dwidc_v${VNUM}.nii.gz"

                    DWIList+="${DISTORTIONCO_TMP}/dwidc_v${VNUM}.nii.gz "
                done

                mrcat -axis 3 $DWIList "${DISTORTIONCO_DIR}/TOPUP/dwidc.nii.gz"

            elif [[ $DISTORTIONCORRECTION_WAY == "VOLUMETOPUPONLY" ]]; then

                DWIList1=""
                DWIList2=""
                NVOLUMES_PER_TE=$((NVOLUMES / NUMBER_ECHOTIME))
                for ((VNUM=0; VNUM<${NVOLUMES_PER_TE}; VNUM++)); do

                    echo "Start VOLUME TOPUP ONLY distortion correction per volume: $VNUM"
                    # topup parameters to update :--fwhm --miter --scale=1
                    # applytopup parameters to update : --method
                    mrcat -axis 3 "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}.nii.gz" "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}.nii.gz" \
                        "${DISTORTIONCO_TMP}/${DCPREFIX}_bothTEs_v${VNUM}.nii.gz" -force

                    topup --imain="${DISTORTIONCO_TMP}/${DCPREFIX}_bothTEs_v${VNUM}.nii.gz" \
                          --datain="${DISTORTIONCO_TMP}/TEs_acq_param.txt" \
                          --config=b02b0.cnf \
                          --scale=1 \
                          --out="${DISTORTIONCO_TMP}/TEs_topup_results_v${VNUM}" \
                          --fout="${DISTORTIONCO_TMP}/fout_TEs_topup_results_v${VNUM}" \
                          --iout="${DISTORTIONCO_TMP}/iout_TEs_topup_results_v${VNUM}"

                    mrconvert -coord 3 0 "${DISTORTIONCO_TMP}/iout_TEs_topup_results_v${VNUM}.nii.gz" - -quiet | mrconvert - "${DISTORTIONCO_TMP}/dwidc_TE1_topup_v${VNUM}.nii.gz" -axes 0,1,2 -force -quiet
                    mrconvert -coord 3 1 "${DISTORTIONCO_TMP}/iout_TEs_topup_results_v${VNUM}.nii.gz" - -quiet | mrconvert - "${DISTORTIONCO_TMP}/dwidc_TE2_topup_v${VNUM}.nii.gz" -axes 0,1,2 -force -quiet

                    DWIList1+="${DISTORTIONCO_TMP}/dwidc_TE1_topup_v${VNUM}.nii.gz "
                    DWIList2+="${DISTORTIONCO_TMP}/dwidc_TE2_topup_v${VNUM}.nii.gz "
                done

                mrcat -axis 3 $DWIList1 "${DISTORTIONCO_DIR}/TOPUP/dwidcTE1_${DISTORTIONCORRECTION_WAY}_${DIRSORDER}.nii.gz"
                mrcat -axis 3 $DWIList2 "${DISTORTIONCO_DIR}/TOPUP/dwidcTE2_${DISTORTIONCORRECTION_WAY}_${DIRSORDER}.nii.gz"

            elif [[ $DISTORTIONCORRECTION_WAY == "SLICE" ]]; then

                DWI_VOLUME_List=""
                NVOLUMES_PER_TE=$((NVOLUMES / NUMBER_ECHOTIME))
                for ((VNUM=0; VNUM<${NVOLUMES_PER_TE}; VNUM++)); do
                    DWI_SLICE_List=""
                    for ((SIDX=0; SIDX<${NSLICESCROP}; SIDX++)); do
                        # This way of distortion correction is not working
                        echo -e "\n |--------------->"
                        echo "--------Start TOPUP distortion correction per slice, volume-Slice: ${VNUM}-${SIDX}"
                        # topup parameters to update :--fwhm --miter --scale=1
                        # applytopup parameters to update : --method

                        mrcat -axis $AXSLICES "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}_dup.nii.gz" -force # -quiet

                        mrcat -axis $AXSLICES "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}_dup.nii.gz" -force # -quiet


                        mrcat -axis 3 "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}_dup.nii.gz" "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}_dup.nii.gz" \
                            "${DISTORTIONCO_TMP}/${DCPREFIX}_bothTEs_v${VNUM}_s${SIDX}.nii.gz" -force

                        topup --imain="${DISTORTIONCO_TMP}/${DCPREFIX}_bothTEs_v${VNUM}_s${SIDX}.nii.gz" \
                              --datain="${DISTORTIONCO_TMP}/TEs_acq_param.txt" \
                              --config=b02b0_1.cnf \
                              --scale=1 \
                              --out="${DISTORTIONCO_TMP}/TEs_topup_results_v${VNUM}_s${SIDX}" \
                              --nthr=24

                        applytopup --imain="${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz","${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" --inindex=1,2 \
                            --datain="${DISTORTIONCO_TMP}/TEs_acq_param.txt" \
                            --topup="${DISTORTIONCO_TMP}/TEs_topup_results_v${VNUM}_s${SIDX}" \
                            --out="${DISTORTIONCO_TMP}/dwidc_v${VNUM}_s${SIDX}.nii.gz"

                        mrconvert -coord 2 3 "${DISTORTIONCO_TMP}/dwidc_v${VNUM}_s${SIDX}.nii.gz" "${DISTORTIONCO_TMP}/dwidcS_v${VNUM}_s${SIDX}.nii.gz" -force -quiet
                        DWI_SLICE_List+="${DISTORTIONCO_TMP}/dwidcS_v${VNUM}_s${SIDX}.nii.gz "

                        echo -e "\n ======================================================================================="
                    done
                    mrcat -axis 2 $DWI_SLICE_List "${DISTORTIONCO_TMP}/dwidcS_v${VNUM}_perSlice.nii.gz" -force -quiet
                    DWI_VOLUME_List+="${DISTORTIONCO_TMP}/dwidcS_v${VNUM}_perSlice.nii.gz "
                done
                mrcat -axis 3 $DWI_VOLUME_List "${DISTORTIONCO_TMP}/dwidcTOPUPs_perSlice.nii.gz" -quiet

            elif [[ $DISTORTIONCORRECTION_WAY == "SLICE_NEW" ]]; then

                DWI_VOLUME_List1=""
                DWI_VOLUME_List2=""
                NVOLUMES_PER_TE=$((NVOLUMES / NUMBER_ECHOTIME))
                for ((VNUM=0; VNUM<${NVOLUMES_PER_TE}; VNUM++)); do
                    DWI_SLICE_List1=""
                    DWI_SLICE_List2=""
                    for ((SIDX=0; SIDX<${NSLICESCROP}; SIDX++)); do
                        echo -e "\n |--------Start TOPUP distortion correction per slice, volume($VNUM)-Slice($SIDX)"
                        # topup parameters to update :--fwhm --miter --scale=1, ## applytopup parameters to update : --method

                        mrcat -axis $AXSLICES "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}_dup.nii.gz" -force -quiet

                        mrcat -axis $AXSLICES "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}_dup.nii.gz" -force -quiet

                        mrcat -axis 3 "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}_dup.nii.gz" "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}_dup.nii.gz" \
                            "${DISTORTIONCO_TMP}/${DCPREFIX}_bothTEs_v${VNUM}_s${SIDX}.nii.gz" -force -quiet


                        topup --imain="${DISTORTIONCO_TMP}/${DCPREFIX}_bothTEs_v${VNUM}_s${SIDX}.nii.gz" \
                              --datain="${DISTORTIONCO_TMP}/TEs_acq_param.txt" \
                              --config=b02b0.cnf \
                              --out="${DISTORTIONCO_TMP}/TEs_SliceDupTopup_results_v${VNUM}_s${SIDX}" \
                              --fout="${DISTORTIONCO_TMP}/fout_TEs_SliceDupTopup_results_v${VNUM}_s${SIDX}" \
                              --iout="${DISTORTIONCO_TMP}/iout_TEs_SliceDupTopup_results_v${VNUM}_s${SIDX}" \
                              --estmov=0 \
                              --scale=1
                              # --nthr=12

                        applytopup --imain="${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}_dup.nii.gz" --inindex=1 \
                            --datain="${DISTORTIONCO_TMP}/TEs_acq_param.txt" \
                            --topup="${DISTORTIONCO_TMP}/TEs_SliceDupTopup_results_v${VNUM}_s${SIDX}" \
                            --out="${DISTORTIONCO_TMP}/iout_TE1_SliceDupTopup_resultsApplyTopup_v${VNUM}_s${SIDX}" \
                            --method=jac

                        applytopup --imain="${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}_dup.nii.gz" --inindex=2 \
                            --datain="${DISTORTIONCO_TMP}/TEs_acq_param.txt" \
                            --topup="${DISTORTIONCO_TMP}/TEs_SliceDupTopup_results_v${VNUM}_s${SIDX}" \
                            --out="${DISTORTIONCO_TMP}/iout_TE2_SliceDupTopup_resultsApplyTopup_v${VNUM}_s${SIDX}" \
                            --method=jac

                        mrconvert -coord $AXSLICES 3 "${DISTORTIONCO_TMP}/iout_TE1_SliceDupTopup_resultsApplyTopup_v${VNUM}_s${SIDX}.nii.gz" "${DISTORTIONCO_TMP}/iout_TE1_SliceDupTopup_v${VNUM}_s${SIDX}_APPLYTOPUP.nii.gz" -force -quiet
                        mrconvert -coord $AXSLICES 3 "${DISTORTIONCO_TMP}/iout_TE2_SliceDupTopup_resultsApplyTopup_v${VNUM}_s${SIDX}.nii.gz" "${DISTORTIONCO_TMP}/iout_TE2_SliceDupTopup_v${VNUM}_s${SIDX}_APPLYTOPUP.nii.gz" -force -quiet

                        DWI_SLICE_List1+="${DISTORTIONCO_TMP}/iout_TE1_SliceDupTopup_v${VNUM}_s${SIDX}_APPLYTOPUP.nii.gz "
                        DWI_SLICE_List2+="${DISTORTIONCO_TMP}/iout_TE2_SliceDupTopup_v${VNUM}_s${SIDX}_APPLYTOPUP.nii.gz "

                        echo -e "\n ======================================================================================="
                    done

                    mrcat -axis $AXSLICES $DWI_SLICE_List1 "${DISTORTIONCO_TMP}/iout_TE1_SliceDupTopup_v${VNUM}_APPLYTOPUP.nii.gz" -force -quiet
                    mrcat -axis $AXSLICES $DWI_SLICE_List2 "${DISTORTIONCO_TMP}/iout_TE2_SliceDupTopup_v${VNUM}_APPLYTOPUP.nii.gz" -force -quiet

                    DWI_VOLUME_List1+="${DISTORTIONCO_TMP}/iout_TE1_SliceDupTopup_v${VNUM}_APPLYTOPUP.nii.gz "
                    DWI_VOLUME_List2+="${DISTORTIONCO_TMP}/iout_TE2_SliceDupTopup_v${VNUM}_APPLYTOPUP.nii.gz "
                done

                mrcat -axis 3 $DWI_VOLUME_List1 "${DISTORTIONCO_DIR}/TOPUP/dwidc_TE1_SliceDupTopup_${DIRSORDER}_APPLYTOPUP.nii.gz" -force -quiet
                mrcat -axis 3 $DWI_VOLUME_List2 "${DISTORTIONCO_DIR}/TOPUP/dwidc_TE2_SliceDupTopup_${DIRSORDER}_APPLYTOPUP.nii.gz" -force -quiet

                # topup (and utilisation of its field estimate in eddy) can indeed produce negative output values despite non-negative input values.
                # This occurs if the estimated susceptibility field is non-diffeomorphic (whether or not the actual distortions are diffeomorphic),
                # which leads to negative values of the Jacobian. The other corrections performed within eddy are pretty much guaranteed to not
                # produce this effect as the spatial frequencies involved are far lower and the basis in which they are represented is different.
                # While it makes perfect sense to use e.g. “mrcalc DWI.mif 0.0 -max” to clamp negative DWI intensities at zero, that doesn’t actually resolve this specific issue
                # As I am fitting with SHORE, this issue will be resolved.

                mrconvert "${DISTORTIONCO_DIR}/TOPUP/dwidc_TE1_SliceDupTopup_${DIRSORDER}_APPLYTOPUP.nii.gz" - -stride "$STRIDES" | mrcalc - 0.0 -max "${DISTORTIONCO_DIR}/TOPUP/dwidc_TE1_SliceDupTopup_${DIRSORDER}_APPLYTOPUP.nii.gz"  -force
                mrconvert "${DISTORTIONCO_DIR}/TOPUP/dwidc_TE2_SliceDupTopup_${DIRSORDER}_APPLYTOPUP.nii.gz" - -stride "$STRIDES" | mrcalc - 0.0 -max "${DISTORTIONCO_DIR}/TOPUP/dwidc_TE2_SliceDupTopup_${DIRSORDER}_APPLYTOPUP.nii.gz"  -force

            elif [[ $DISTORTIONCORRECTION_WAY == "SLICETOPUPONLY" ]]; then

                DWI_VOLUME_List1=""
                DWI_VOLUME_List2=""
                NVOLUMES_PER_TE=$((NVOLUMES / NUMBER_ECHOTIME))
                for ((VNUM=0; VNUM<${NVOLUMES_PER_TE}; VNUM++)); do
                    DWI_SLICE_List1=""
                    DWI_SLICE_List2=""
                    for ((SIDX=0; SIDX<${NSLICESCROP}; SIDX++)); do
                        echo -e "\n |--------Start TOPUP distortion correction per slice, volume($VNUM)-Slice($SIDX)"
                        ## topup parameters to update :--fwhm --miter --scale=1, ## applytopup parameters to update : --method

                        mrcat -axis $AXSLICES "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}_dup.nii.gz" -force -quiet

                        mrcat -axis $AXSLICES "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                      "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}_dup.nii.gz" -force -quiet


                        mrcat -axis 3 "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}_dup.nii.gz" "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}_dup.nii.gz" \
                            "${DISTORTIONCO_TMP}/${DCPREFIX}_bothTEs_v${VNUM}_s${SIDX}.nii.gz" -force -quiet


                        topup --imain="${DISTORTIONCO_TMP}/${DCPREFIX}_bothTEs_v${VNUM}_s${SIDX}.nii.gz" \
                              --datain="${DISTORTIONCO_TMP}/TEs_acq_param.txt" \
                              --config=b02b0.cnf \
                              --out="${DISTORTIONCO_TMP}/TEs_SliceDupTopup_results_v${VNUM}_s${SIDX}" \
                              --fout="${DISTORTIONCO_TMP}/fout_TEs_SliceDupTopup_results_v${VNUM}_s${SIDX}" \
                              --iout="${DISTORTIONCO_TMP}/iout_TEs_SliceDupTopup_results_v${VNUM}_s${SIDX}" \
                              --estmov=0 \
                              --scale=1
                              # --nthr=12

                        mrconvert -coord 3 0 "${DISTORTIONCO_TMP}/iout_TEs_SliceDupTopup_results_v${VNUM}_s${SIDX}.nii.gz" - -quiet | mrconvert - "${DISTORTIONCO_TMP}/iout_TE1_SliceDupTopup_v${VNUM}_s${SIDX}_dup.nii.gz" -axes 0,1,2 -force -quiet
                        mrconvert -coord 3 1 "${DISTORTIONCO_TMP}/iout_TEs_SliceDupTopup_results_v${VNUM}_s${SIDX}.nii.gz" - -quiet | mrconvert - "${DISTORTIONCO_TMP}/iout_TE2_SliceDupTopup_v${VNUM}_s${SIDX}_dup.nii.gz" -axes 0,1,2 -force -quiet

                        mrconvert -coord $AXSLICES 3 "${DISTORTIONCO_TMP}/iout_TE1_SliceDupTopup_v${VNUM}_s${SIDX}_dup.nii.gz" "${DISTORTIONCO_TMP}/iout_TE1_SliceDupTopup_v${VNUM}_s${SIDX}.nii.gz" -force -quiet
                        mrconvert -coord $AXSLICES 3 "${DISTORTIONCO_TMP}/iout_TE2_SliceDupTopup_v${VNUM}_s${SIDX}_dup.nii.gz" "${DISTORTIONCO_TMP}/iout_TE2_SliceDupTopup_v${VNUM}_s${SIDX}.nii.gz" -force -quiet

                        DWI_SLICE_List1+="${DISTORTIONCO_TMP}/iout_TE1_SliceDupTopup_v${VNUM}_s${SIDX}.nii.gz "
                        DWI_SLICE_List2+="${DISTORTIONCO_TMP}/iout_TE2_SliceDupTopup_v${VNUM}_s${SIDX}.nii.gz "

                        echo -e "\n ======================================================================================="
                    done

                    mrcat -axis $AXSLICES $DWI_SLICE_List1 "${DISTORTIONCO_TMP}/iout_TE1_SliceDupTopup_v${VNUM}.nii.gz" -force -quiet
                    mrcat -axis $AXSLICES $DWI_SLICE_List2 "${DISTORTIONCO_TMP}/iout_TE2_SliceDupTopup_v${VNUM}.nii.gz" -force -quiet

                    DWI_VOLUME_List1+="${DISTORTIONCO_TMP}/iout_TE1_SliceDupTopup_v${VNUM}.nii.gz "
                    DWI_VOLUME_List2+="${DISTORTIONCO_TMP}/iout_TE2_SliceDupTopup_v${VNUM}.nii.gz "
                done

                mrcat -axis 3 $DWI_VOLUME_List1 "${DISTORTIONCO_DIR}/TOPUP/dwidc_TE1_SliceDupTopup_${DIRSORDER}.nii.gz" -force -quiet
                mrcat -axis 3 $DWI_VOLUME_List2 "${DISTORTIONCO_DIR}/TOPUP/dwidc_TE2_SliceDupTopup_${DIRSORDER}.nii.gz" -force -quiet

                # topup (and utilisation of its field estimate in eddy) can indeed produce negative output values despite non-negative input values.
                # This occurs if the estimated susceptibility field is non-diffeomorphic (whether or not the actual distortions are diffeomorphic),
                # which leads to negative values of the Jacobian. The other corrections performed within eddy are pretty much guaranteed to not
                # produce this effect as the spatial frequencies involved are far lower and the basis in which they are represented is different.
                # While it makes perfect sense to use e.g. “mrcalc DWI.mif 0.0 -max” to clamp negative DWI intensities at zero, that doesn’t actually resolve this specific issue
                # As I am fitting with SHORE, this issue will be resolved.

                mrconvert "${DISTORTIONCO_DIR}/TOPUP/dwidc_TE1_SliceDupTopup_${DIRSORDER}.nii.gz" - -stride "$STRIDES" | mrcalc - 0.0 -max "${DISTORTIONCO_DIR}/TOPUP/dwidc_TE1_SliceDupTopup_${DIRSORDER}.nii.gz"  -force
                mrconvert "${DISTORTIONCO_DIR}/TOPUP/dwidc_TE2_SliceDupTopup_${DIRSORDER}.nii.gz" - -stride "$STRIDES" | mrcalc - 0.0 -max "${DISTORTIONCO_DIR}/TOPUP/dwidc_TE2_SliceDupTopup_${DIRSORDER}.nii.gz"  -force

            fi
        done

    ##########################################################################################################################################################
    ##########################################################################################################################################################
    elif [[ $DISTORTIONCORRECTION_METHOD == "BM" ]]; then


        for GradientPhaseDirection in "0" "2"; do # By experience, "1" results in transformation field empty.
            for Forward in "1" "2"; do
                if [ "$Forward" == "1" ]; then
                    Backward="2"
                elif [ "$Forward" == "2" ]; then
                    Backward="1"
                fi

                DISTORTIONCO_TMP="${OUTPATHSUB}/distortion/tmp_${DISTORTIONCORRECTION_METHOD}_${DISTORTIONCORRECTION_WAY}"
                DISTORTIONCO_TMP="${DISTORTIONCO_TMP}_DIR${GradientPhaseDirection}_Fte${Forward}_Bte${Backward}"
                mkdir -p "${DISTORTIONCO_TMP}"

                if [[ $DISTORTIONCORRECTION_WAY == "VOLUME" ]]; then

                    DWIList=""
                    NVOLUMES_PER_TE=$((NVOLUMES / NUMBER_ECHOTIME))
                    for ((VNUM=0; VNUM<${NVOLUMES_PER_TE}; VNUM++)); do

                        echo "Start BM Distortion Correction per volume: $VNUM"
                        echo "---> Compute the Initial Transformation"
                        animaDistortionCorrection -f "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}.nii.gz" -b "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}.nii.gz" \
                                                  -o "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}.nii.gz" -s 2 --dir $GradientPhaseDirection


                        echo "---> Transformation Block-Matching"
                        animaBMDistortionCorrection -f "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}.nii.gz" -b "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}.nii.gz" \
                                                    -i "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}.nii.gz" -o "${DISTORTIONCO_TMP}/BM_v${VNUM}.nii.gz" \
                                                    -O "${DISTORTIONCO_TMP}/Trsf_BM_v${VNUM}.nii.gz" --dir $GradientPhaseDirection

                        DWIList+="${DISTORTIONCO_TMP}/BM_v${VNUM}.nii.gz "
                    done
                    echo "---> Concatenate BM corrected 3D volumes"
                    mrcat -axis 3 $DWIList "${DISTORTIONCO_TMP}/dwidcBM.nii.gz"

                elif [[ $DISTORTIONCORRECTION_WAY == "SECONDCLASSICSLICE" ]]; then

                    DWI_VOLUME_List=""
                    DWI_TRSFSV_List=""
                    NVOLUMES_PER_TE=$((NVOLUMES / NUMBER_ECHOTIME))
                    for ((VNUM=0; VNUM<${NVOLUMES_PER_TE}; VNUM++)); do
                        DWI_SLICE_List=""
                        DWI_TRSFS_List=""
                        echo "Start BM Distortion Correction per volume: $VNUM"
                        for ((SIDX=0; SIDX<${NSLICESCROP}; SIDX++)); do
                            echo "======================================================================================="
                            echo "======================================================================================="
                            echo "Start BM Distortion Correction per slice, volume-Slice: $VNUM-$SIDX"

                            mrcat -axis $AXSLICES "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}_dup.nii.gz" -force  -quiet

                            mrcat -axis $AXSLICES "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}_dup.nii.gz" -force  -quiet


                            echo "---> Compute the Initial Transformation"
                            animaDistortionCorrection -f "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Forward}_v${VNUM}_s${SIDX}_dup.nii.gz" \
                                                      -b "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Backward}_v${VNUM}_s${SIDX}_dup.nii.gz" \
                                                      -o "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}_s${SIDX}.nii.gz" \
                                                      -s 2 --dir $GradientPhaseDirection

                            echo "---> Transformation Block-Matching"
                            animaBMDistortionCorrection -f "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Forward}_v${VNUM}_s${SIDX}_dup.nii.gz" \
                                                        -b "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Backward}_v${VNUM}_s${SIDX}_dup.nii.gz" \
                                                        -i "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}_s${SIDX}.nii.gz" \
                                                        -o "${DISTORTIONCO_TMP}/BMsliceDup_v${VNUM}_s${SIDX}.nii.gz" \
                                                        -O "${DISTORTIONCO_TMP}/Trsf_BM_v${VNUM}_s${SIDX}.nii.gz" \
                                                        --bs 5 --sp 3 --dir $GradientPhaseDirection
                            # #Check if animaBMDistortionCorrection was successful
                            if [ $? -ne 0 ]; then
                            echo "animaBMDistortionCorrection failed, performing fallback operation by reapplying BM without initialization..."
                            animaBMDistortionCorrection -f "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Forward}_v${VNUM}_s${SIDX}_dup.nii.gz" \
                                                        -b "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Backward}_v${VNUM}_s${SIDX}_dup.nii.gz" \
                                                        -o "${DISTORTIONCO_TMP}/BMsliceDup_v${VNUM}_s${SIDX}.nii.gz" \
                                                        -O "${DISTORTIONCO_TMP}/Trsf_BM_v${VNUM}_s${SIDX}.nii.gz" \
                                                        --bs 5 --sp 3 --dir $GradientPhaseDirection
                                if [ $? -ne 0 ]; then
                                    echo "animaBMDistortionCorrection failed even without initialization, performing fallback operation ..."
                                    cp "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Forward}_v${VNUM}_s${SIDX}_dup.nii.gz" "${DISTORTIONCO_TMP}/BMsliceDup_v${VNUM}_s${SIDX}.nii.gz"
                                    cp "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}_s${SIDX}.nii.gz" "${DISTORTIONCO_TMP}/Trsf_BM_v${VNUM}_s${SIDX}.nii.gz"
                                else
                                    echo "animaBMDistortionCorrection completed successfully without initialization."
                                fi
                            else
                                echo "animaBMDistortionCorrection completed successfully with initialization."
                            fi


                            mrconvert -coord $AXSLICES 3 "${DISTORTIONCO_TMP}/BMsliceDup_v${VNUM}_s${SIDX}.nii.gz" "${DISTORTIONCO_TMP}/BMslice_v${VNUM}_s${SIDX}.nii.gz" -force -quiet
                            mrconvert -coord $AXSLICES 3 "${DISTORTIONCO_TMP}/Trsf_BM_v${VNUM}_s${SIDX}.nii.gz" "${DISTORTIONCO_TMP}/Trsf_BMSlice_v${VNUM}_s${SIDX}.nii.gz" -force -quiet
                            DWI_SLICE_List+="${DISTORTIONCO_TMP}/BMslice_v${VNUM}_s${SIDX}.nii.gz "
                            DWI_TRSFS_List+="${DISTORTIONCO_TMP}/Trsf_BMSlice_v${VNUM}_s${SIDX}.nii.gz "

                            echo -e "\n ======================================================================================="
                        done
                        mrcat -axis $AXSLICES $DWI_SLICE_List "${DISTORTIONCO_TMP}/BM_v${VNUM}_perSlice.nii.gz" -force -quiet
                        mrcat -axis $AXSLICES $DWI_TRSFS_List "${DISTORTIONCO_TMP}/Trsf_BMSlice_v${VNUM}_perSlice.nii.gz" -force -quiet
                        DWI_VOLUME_List+="${DISTORTIONCO_TMP}/BM_v${VNUM}_perSlice.nii.gz "
                        DWI_TRSFSV_List+="${DISTORTIONCO_TMP}/Trsf_BMSlice_v${VNUM}_perSlice.nii.gz "
                    done
                    mrcat -axis 3 $DWI_VOLUME_List "${DISTORTIONCO_DIR}/BM/dwidc_SliceDupBM_Dir${GradientPhaseDirection}_Fte${Forward}_Bte${Backward}.nii.gz" -quiet
                    mrcat -axis 3 $DWI_TRSFSV_List "${DISTORTIONCO_DIR}/BM/TRSF_SliceDupBM_Dir${GradientPhaseDirection}_Fte${Forward}_Bte${Backward}.nii.gz" -quiet

                elif [[ $DISTORTIONCORRECTION_WAY == "VINITSLICE" ]]; then

                    DWI_VOLUME_List=""
                    DWI_TRSFSV_List=""
                    NVOLUMES_PER_TE=$((NVOLUMES / NUMBER_ECHOTIME))
                    for ((VNUM=0; VNUM<${NVOLUMES_PER_TE}; VNUM++)); do
                        DWI_SLICE_List=""
                        DWI_TRSFS_List=""
                        echo "Start BM Distortion Correction per volume: $VNUM"
                        echo "---> Compute the Initial Transformation"
                        animaDistortionCorrection -f "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Forward}_v${VNUM}.nii.gz" \
                                                  -b "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Backward}_v${VNUM}.nii.gz" \
                                                  -o "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}.nii.gz" \
                                                  -s 2 --dir $GradientPhaseDirection



                        for ((SIDX=0; SIDX<${NSLICESCROP}; SIDX++)); do
                            echo "======================================================================================="
                            echo "======================================================================================="
                            echo "Start BM Distortion Correction per slice, volume-Slice: $VNUM-$SIDX"

                            mrconvert -coord $AXSLICES $SIDX "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}.nii.gz" "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}_s${SIDX}.nii.gz" -force -quiet

                            mrcat -axis $AXSLICES "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}_s${SIDX}_dup.nii.gz" -force  -quiet

                            mrcat -axis $AXSLICES "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}_dup.nii.gz" -force  -quiet

                            mrcat -axis $AXSLICES "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}_dup.nii.gz" -force  -quiet


                            echo "---> Transformation Block-Matching"
                            animaBMDistortionCorrection -f "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Forward}_v${VNUM}_s${SIDX}_dup.nii.gz" \
                                                        -b "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Backward}_v${VNUM}_s${SIDX}_dup.nii.gz" \
                                                        -i "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}_s${SIDX}_dup.nii.gz" \
                                                        -o "${DISTORTIONCO_TMP}/BMsliceDup_v${VNUM}_s${SIDX}.nii.gz" \
                                                        -O "${DISTORTIONCO_TMP}/Trsf_BM_v${VNUM}_s${SIDX}.nii.gz" \
                                                        --bs 5 --sp 3 --dir $GradientPhaseDirection
                            # #Check if animaBMDistortionCorrection was successful
                            if [ $? -ne 0 ]; then
                                echo "animaBMDistortionCorrection failed, performing fallback operation..."
                                cp "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Forward}_v${VNUM}_s${SIDX}_dup.nii.gz" "${DISTORTIONCO_TMP}/BMsliceDup_v${VNUM}_s${SIDX}.nii.gz"
                                cp "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}_s${SIDX}_dup.nii.gz" "${DISTORTIONCO_TMP}/Trsf_BM_v${VNUM}_s${SIDX}.nii.gz"
                            else
                                echo "animaBMDistortionCorrection completed successfully."
                            fi


                            mrconvert -coord $AXSLICES 3 "${DISTORTIONCO_TMP}/BMsliceDup_v${VNUM}_s${SIDX}.nii.gz" "${DISTORTIONCO_TMP}/BMslice_v${VNUM}_s${SIDX}.nii.gz" -force -quiet
                            mrconvert -coord $AXSLICES 3 "${DISTORTIONCO_TMP}/Trsf_BM_v${VNUM}_s${SIDX}.nii.gz" "${DISTORTIONCO_TMP}/Trsf_BMSlice_v${VNUM}_s${SIDX}.nii.gz" -force -quiet
                            DWI_SLICE_List+="${DISTORTIONCO_TMP}/BMslice_v${VNUM}_s${SIDX}.nii.gz "
                            DWI_TRSFS_List+="${DISTORTIONCO_TMP}/Trsf_BMSlice_v${VNUM}_s${SIDX}.nii.gz "

                            echo -e "\n ======================================================================================="
                        done
                        mrcat -axis $AXSLICES $DWI_SLICE_List "${DISTORTIONCO_TMP}/BM_v${VNUM}_perSlice.nii.gz" -force -quiet
                        mrcat -axis $AXSLICES $DWI_TRSFS_List "${DISTORTIONCO_TMP}/Trsf_BMSlice_v${VNUM}_perSlice.nii.gz" -force -quiet
                        DWI_VOLUME_List+="${DISTORTIONCO_TMP}/BM_v${VNUM}_perSlice.nii.gz "
                        DWI_TRSFSV_List+="${DISTORTIONCO_TMP}/Trsf_BMSlice_v${VNUM}_perSlice.nii.gz "
                    done

                    mrcat -axis 3 $DWI_VOLUME_List "${DISTORTIONCO_DIR}/BM/dwidc_VinitSliceDupBM_Dir${GradientPhaseDirection}_Fte${Forward}_Bte${Backward}.nii.gz" -quiet
                    mrcat -axis 3 $DWI_TRSFSV_List "${DISTORTIONCO_DIR}/BM/TRSF_VinitSliceDupBM_Dir${GradientPhaseDirection}_Fte${Forward}_Bte${Backward}.nii.gz" -quiet

                # This option gives an error :"Description: ITK ERROR: ImageToImageFilter(0x7fdd400035f0): Inputs do not occupy the same physical space! "
                elif [[ $DISTORTIONCORRECTION_WAY == "VBMINITSLICE" ]]; then

                    DWI_VOLUME_List=""
                    DWI_TRSFSV_List=""
                    NVOLUMES_PER_TE=$((NVOLUMES / NUMBER_ECHOTIME))
                    for ((VNUM=0; VNUM<${NVOLUMES_PER_TE}; VNUM++)); do
                        DWI_SLICE_List=""
                        DWI_TRSFS_List=""
                        echo "Start BM Distortion Correction per volume: $VNUM"
                        echo "---> Compute the Initial Transformation"
                        animaBMDistortionCorrection -f "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Forward}_v${VNUM}.nii.gz" \
                                                    -b "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Backward}_v${VNUM}.nii.gz" \
                                                    -o "${DISTORTIONCO_TMP}/Initial_BMsliceDup_v${VNUM}.nii.gz" \
                                                    -O "${DISTORTIONCO_TMP}/Initial_Trsf_BM_v${VNUM}.nii.gz" \
                                                    --bs 5 --sp 2 --dir $GradientPhaseDirection


                        for ((SIDX=0; SIDX<${NSLICESCROP}; SIDX++)); do
                            echo "======================================================================================="
                            echo "======================================================================================="
                            echo "Start BM Distortion Correction per slice, volume-Slice: $VNUM-$SIDX"

                            mrconvert -coord $AXSLICES $SIDX "${DISTORTIONCO_TMP}/Initial_Trsf_BM_v${VNUM}.nii.gz" "${DISTORTIONCO_TMP}/Initial_Trsf_BM_v${VNUM}_s${SIDX}.nii.gz" -force -quiet

                            mrcat -axis $AXSLICES "${DISTORTIONCO_TMP}/Initial_Trsf_BM_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${DISTORTIONCO_TMP}/Initial_Trsf_BM_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${DISTORTIONCO_TMP}/Initial_Trsf_BM_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${DISTORTIONCO_TMP}/Initial_Trsf_BM_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${DISTORTIONCO_TMP}/Initial_Trsf_BM_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${DISTORTIONCO_TMP}/Initial_Trsf_BM_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${DISTORTIONCO_TMP}/Initial_Trsf_BM_v${VNUM}_s${SIDX}_dup.nii.gz" -force  -quiet

                            mrcat -axis $AXSLICES "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}_dup.nii.gz" -force  -quiet

                            mrcat -axis $AXSLICES "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}_dup.nii.gz" -force  -quiet


                            echo "---> Transformation Block-Matching"
                            animaBMDistortionCorrection -f "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Forward}_v${VNUM}_s${SIDX}_dup.nii.gz" \
                                                        -b "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Backward}_v${VNUM}_s${SIDX}_dup.nii.gz" \
                                                        -i "${DISTORTIONCO_TMP}/Initial_Trsf_BM_v${VNUM}_s${SIDX}_dup.nii.gz" \
                                                        -o "${DISTORTIONCO_TMP}/BMsliceDup_v${VNUM}_s${SIDX}.nii.gz" \
                                                        -O "${DISTORTIONCO_TMP}/Trsf_BM_v${VNUM}_s${SIDX}.nii.gz" \
                                                        --bs 3 --sp 2 --dir $GradientPhaseDirection
                            # #Check if animaBMDistortionCorrection was successful
                            if [ $? -ne 0 ]; then
                                echo "animaBMDistortionCorrection failed, performing fallback operation..."
                                cp "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Forward}_v${VNUM}_s${SIDX}_dup.nii.gz" "${DISTORTIONCO_TMP}/BMsliceDup_v${VNUM}_s${SIDX}.nii.gz"
                                cp "${DISTORTIONCO_TMP}/Initial_Trsf_BM_v${VNUM}_s${SIDX}_dup.nii.gz" "${DISTORTIONCO_TMP}/Trsf_BM_v${VNUM}_s${SIDX}.nii.gz"
                            else
                                echo "animaBMDistortionCorrection completed successfully."
                            fi


                            mrconvert -coord $AXSLICES 3 "${DISTORTIONCO_TMP}/BMsliceDup_v${VNUM}_s${SIDX}.nii.gz" "${DISTORTIONCO_TMP}/BMslice_v${VNUM}_s${SIDX}.nii.gz" -force -quiet
                            mrconvert -coord $AXSLICES 3 "${DISTORTIONCO_TMP}/Trsf_BM_v${VNUM}_s${SIDX}.nii.gz" "${DISTORTIONCO_TMP}/Trsf_BMSlice_v${VNUM}_s${SIDX}.nii.gz" -force -quiet
                            DWI_SLICE_List+="${DISTORTIONCO_TMP}/BMslice_v${VNUM}_s${SIDX}.nii.gz "
                            DWI_TRSFS_List+="${DISTORTIONCO_TMP}/Trsf_BMSlice_v${VNUM}_s${SIDX}.nii.gz "

                            echo -e "\n ======================================================================================="
                        done
                        mrcat -axis $AXSLICES $DWI_SLICE_List "${DISTORTIONCO_TMP}/BM_v${VNUM}_perSlice.nii.gz" -force -quiet
                        mrcat -axis $AXSLICES $DWI_TRSFS_List "${DISTORTIONCO_TMP}/Trsf_BMSlice_v${VNUM}_perSlice.nii.gz" -force -quiet
                        DWI_VOLUME_List+="${DISTORTIONCO_TMP}/BM_v${VNUM}_perSlice.nii.gz "
                        DWI_TRSFSV_List+="${DISTORTIONCO_TMP}/Trsf_BMSlice_v${VNUM}_perSlice.nii.gz "
                    done
                    mrcat -axis 3 $DWI_VOLUME_List "${DISTORTIONCO_DIR}/BM/dwidc_VBMinitSliceDupBM_Dir${GradientPhaseDirection}_Fte${Forward}_Bte${Backward}.nii.gz" -quiet
                    mrcat -axis 3 $DWI_TRSFSV_List "${DISTORTIONCO_DIR}/BM/TRSF_VBMinitSliceDupBM_Dir${GradientPhaseDirection}_Fte${Forward}_Bte${Backward}.nii.gz" -quiet

                fi
            done
        done

    ##########################################################################################################################################################
    ##########################################################################################################################################################
    elif [[ $DISTORTIONCORRECTION_METHOD == "VOSS" ]]; then


        for GradientPhaseDirection in "1" "2"; do # By experience, "1" results in transformation field empty.
            for Forward in "1" "2"; do
                if [ "$Forward" == "1" ]; then
                    Backward="2"
                elif [ "$Forward" == "2" ]; then
                    Backward="1"
                fi
                DISTORTIONCO_TMP="${OUTPATHSUB}/distortion/tmp_${DISTORTIONCORRECTION_METHOD}_${DISTORTIONCORRECTION_WAY}"
                DISTORTIONCO_TMP="${DISTORTIONCO_TMP}_DIR${GradientPhaseDirection}_Fte${Forward}_Bte${Backward}"
                mkdir -p "${DISTORTIONCO_TMP}"

                if [[ $DISTORTIONCORRECTION_WAY == "VOLUME" ]]; then

                    echo "To do later"
                    # DWIList=""
                    # NVOLUMES_PER_TE=$((NVOLUMES / NUMBER_ECHOTIME))
                    # for ((VNUM=0; VNUM<${NVOLUMES_PER_TE}; VNUM++)); do

                    #     echo "Start BM Distortion Correction per volume: $VNUM"
                    #     echo "---> Compute the Initial Transformation"
                    #     animaDistortionCorrection -f "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}.nii.gz" -b "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}.nii.gz" \
                    #                               -o "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}.nii.gz" -s 2 --dir $GradientPhaseDirection


                    #     echo "---> Transformation Block-Matching"
                    #     animaBMDistortionCorrection -f "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}.nii.gz" -b "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}.nii.gz" \
                    #                                 -i "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}.nii.gz" -o "${DISTORTIONCO_TMP}/VOSS_v${VNUM}.nii.gz" \
                    #                                 -O "${DISTORTIONCO_TMP}/Trsf_VOSS_v${VNUM}.nii.gz" --dir $GradientPhaseDirection

                    #     DWIList+="${DISTORTIONCO_TMP}/VOSS_v${VNUM}.nii.gz "
                    # done
                    # echo "---> Concatenate BM corrected 3D volumes"
                    # mrcat -axis 3 $DWIList "${DISTORTIONCO_TMP}/dwidcBM.nii.gz"

                elif [[ $DISTORTIONCORRECTION_WAY == "SLICE" ]]; then

                    DWI_VOLUME_List=""
                    DWI_TRSFSV_List=""
                    NVOLUMES_PER_TE=$((NVOLUMES / NUMBER_ECHOTIME))
                    for ((VNUM=0; VNUM<${NVOLUMES_PER_TE}; VNUM++)); do
                        DWI_SLICE_List=""
                        DWI_TRSFS_List=""
                        echo "Start BM Distortion Correction per volume: $VNUM"
                        for ((SIDX=0; SIDX<${NSLICESCROP}; SIDX++)); do
                            echo "======================================================================================="
                            echo "======================================================================================="
                            echo "Start BM Distortion Correction per slice, volume-Slice: $VNUM-$SIDX"

                            mrcat -axis $AXSLICES "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE1_v${VNUM}_s${SIDX}_dup.nii.gz" -force  -quiet

                            mrcat -axis $AXSLICES "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}.nii.gz" \
                                          "${SEGMENTATION_DIR}/${DCPREFIX}_TE2_v${VNUM}_s${SIDX}_dup.nii.gz" -force  -quiet


                            echo "---> Compute the Initial Transformation"
                            animaDistortionCorrection -f "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Forward}_v${VNUM}_s${SIDX}_dup.nii.gz" \
                                                      -b "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Backward}_v${VNUM}_s${SIDX}_dup.nii.gz" \
                                                      -o "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}_s${SIDX}.nii.gz" \
                                                      -s 2 --dir $GradientPhaseDirection


                            animaApplyDistortionCorrection -f "${SEGMENTATION_DIR}/${DCPREFIX}_TE${Forward}_v${VNUM}_s${SIDX}_dup.nii.gz" \
                                                           -t "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}_s${SIDX}.nii.gz" \
                                                           -o "${DISTORTIONCO_TMP}/VOSSsliceDup_v${VNUM}_s${SIDX}.nii.gz" \


                            mrconvert -coord $AXSLICES 3 "${DISTORTIONCO_TMP}/VOSSsliceDup_v${VNUM}_s${SIDX}.nii.gz" "${DISTORTIONCO_TMP}/VOSSslice_v${VNUM}_s${SIDX}.nii.gz" -force -quiet
                            mrconvert -coord $AXSLICES 3 "${DISTORTIONCO_TMP}/Initial_Trsf_Voss_v${VNUM}_s${SIDX}.nii.gz" "${DISTORTIONCO_TMP}/Trsf_VOSSSlice_v${VNUM}_s${SIDX}.nii.gz" -force -quiet
                            DWI_SLICE_List+="${DISTORTIONCO_TMP}/VOSSslice_v${VNUM}_s${SIDX}.nii.gz "
                            DWI_TRSFS_List+="${DISTORTIONCO_TMP}/Trsf_VOSSSlice_v${VNUM}_s${SIDX}.nii.gz "

                            echo -e "\n ======================================================================================="
                        done
                        mrcat -axis $AXSLICES $DWI_SLICE_List "${DISTORTIONCO_TMP}/VOSS_v${VNUM}_perSlice.nii.gz" -force -quiet
                        mrcat -axis $AXSLICES $DWI_TRSFS_List "${DISTORTIONCO_TMP}/Trsf_VOSSSlice_v${VNUM}_perSlice.nii.gz" -force -quiet
                        DWI_VOLUME_List+="${DISTORTIONCO_TMP}/VOSS_v${VNUM}_perSlice.nii.gz "
                        DWI_TRSFSV_List+="${DISTORTIONCO_TMP}/Trsf_VOSSSlice_v${VNUM}_perSlice.nii.gz "
                    done
                    mrcat -axis 3 $DWI_VOLUME_List "${DISTORTIONCO_DIR}/VOSS/dwidc_SliceDupVOSS_Dir${GradientPhaseDirection}_Fte${Forward}_Bte${Backward}.nii.gz" -quiet
                    mrcat -axis 3 $DWI_TRSFSV_List "${DISTORTIONCO_DIR}/VOSS/TRSF_SliceDupVOSS_Dir${GradientPhaseDirection}_Fte${Forward}_Bte${Backward}.nii.gz" -quiet

                fi
            done
        done
    fi


elif [[ ${FEDI_DMRI_PIPELINE_STEPS["STEP6_SLICECORRECTDISTORTION"]} == "TODO" ]] && [[ $NUMBER_ECHOTIME -eq 1 ]] && [[ ! -e ${LOCK6} ]]; then

    #touch ${DISTORTIONCO_DIR}/lock
    touch ${LOCK6}
    echo "${STEPX}.|---> Distortion Correction   ---"
    echo -e "\nNo 2nd TE is available ==> No Distortion Correction will be done."
    # mrconvert "${OUTPATHSUB}/${DCPREFIX}.mif" "${OUTPATHSUB}/dwiprebc_TE1.mif" -force
    # mrconvert "${PRPROCESSING_DIR}/union_maskcrop.nii.gz" "${OUTPATHSUB}/dwiprebc_mask_TE1.nii.gz" -force

elif [[ ${FEDI_DMRI_PIPELINE_STEPS["STEP6_SLICECORRECTDISTORTION"]} == "TODO" ]] && [[ -e ${LOCK6} ]]; then

    echo "\nScan is Already processed/checked for distortion."

else
    echo "Step $STEPX locked or not set to TODO. Moving on."
fi


((STEPX++))
echo "---------------------------------------------------------------------------------"
# STEP 7: STEP7_B1FIELDBIAS_CORRECTION
if [[ $NOLOCKS = 1 && -e ${LOCK7} && ${FEDI_DMRI_PIPELINE_STEPS["STEP7_B1FIELDBIAS_CORRECTION"]} == "TODO" ]] ; then rm ${LOCK7} ; fi
if [[ ${FEDI_DMRI_PIPELINE_STEPS["STEP7_B1FIELDBIAS_CORRECTION"]} == "TODO" ]] && [[ ! -e ${LOCK7} ]] ; then

    touch ${LOCK7}
    echo -e "\n${STEPX}.|--->  B1 Field Bias Correction   ---"

    B1CORRECTIONWAY="Using_B0"
    echo "EchoTime number is ${NUMBER_ECHOTIME}"


    ############################################################
    if [[ ${NUMBER_ECHOTIME} -eq 1 ]]; then
        BVALSTE="${BVALS}"
        BVECSTE="${BVECS}"
        GRAD4CLSTE="${GRAD4CLS}"

        # Define the method for B1 correction. Options: "Using_B0", "Individually", "using_mask"
        B1CORRECTIONWAY="Using_B0"

        mrconvert "${PRPROCESSING_DIR}/dwicrop.mif" "${PRPROCESSING_DIR}/dwicrop.mif" -stride "$STRIDES" -force
        # Make sure that ANTS's Inputs occupy the same physical space!
        mrconvert "${PRPROCESSING_DIR}/union_maskcrop.nii.gz" - -stride "$STRIDES3D" | mrtransform - -template "${PRPROCESSING_DIR}/dwicrop.mif" -interp nearest "${PRPROCESSING_DIR}/dwibcmask_TE1.nii.gz" -force

        mrcalc "${PRPROCESSING_DIR}/dwicrop.mif" "${PRPROCESSING_DIR}/dwibcmask_TE1.nii.gz" -mult  "${PRPROCESSING_DIR}/dwibc_sk_TE1.mif" -force

        if [[ $B1CORRECTIONWAY == "Using_B0" ]]; then
            dwibiascorrect ants -mask "${PRPROCESSING_DIR}/dwibcmask_TE1.nii.gz" -bias "${PRPROCESSING_DIR}/b1N4BiasField_TE1.mif" "${PRPROCESSING_DIR}/dwicrop.mif" "${PRPROCESSING_DIR}/dwibc_TE1.mif" -force
            if [[ ! -e ${PRPROCESSING_DIR}/dwibc_TE1.mif ]]; then
                dwibiascorrect ants -bias "${PRPROCESSING_DIR}/b1N4BiasField_TE1.mif" "${PRPROCESSING_DIR}/dwicrop.mif" "${PRPROCESSING_DIR}/dwibc_TE1.mif" -force
            fi
        elif [[ $B1CORRECTIONWAY == "Individually" ]]; then
            echo "To be implemented/improved later"
            # this option is not working : raise MRtrixError('DW gradient scheme contains different number of entries (' + str(len(dwi_header.keyval()['dw_scheme']))
            # + ' to number of volumes in DWIs (' + dwi_header.size()[3] + ')'). Soome efforts should be done here to improve it. Read Maria Derpez and DESIGNER papers.
                # DWImif=""
                # mkdir -p "${PRPROCESSING_DIR}/tmp_bc"
                # for ((VIDX=0; VIDX<${NVOLUMES}; VIDX++)); do
                #     mrconvert -coord 3  $VIDX  "${PRPROCESSING_DIR}/dwirc.mif"  "${PRPROCESSING_DIR}/tmp_bc/dwiprebc_${VIDX}.mif"
                #     dwibiascorrect ants -bias "${PRPROCESSING_DIR}/tmp_bc/b1biasfield_${VIDX}.mif" "${PRPROCESSING_DIR}/tmp_bc/dwiprebc_${VIDX}.mif" "${PRPROCESSING_DIR}/tmp_bc/dwibc_${VIDX}.mif"
                #     DWImif+="${PRPROCESSING_DIR}/tmp_bc/dwibc_${VIDX}.mif "
                # done
                # mrcat -axis 3 $DWImif ${PRPROCESSING_DIR}/dwibc.mif

        elif [[ $B1CORRECTIONWAY == "using_mask" ]] ; then
            echo "To be implemented soon"
        fi

    ############################################################
    elif [[ ${NUMBER_ECHOTIME} -gt 1 ]] && [[ -e "${DISTORTIONCO_DIR}/TOPUP/dwidcTE1_VOLUMETOPUPONLY_APPA.nii.gz" ]]; then


        WORKING_DMRI_BC1="${DISTORTIONCO_DIR}/TOPUP/dwidcTE1_VOLUMETOPUPONLY_APPA"
        # "${DISTORTIONCO_DIR}/BM/dwidc_SliceDupBM_Dir0_Fte1_Bte2"
        #WORKING_DMRI_BC2=${DISTORTIONCO_DIR}/BM/dwidc_TE2_TOPUPONLY_perSlice

        python "${SRC}/update_bvecs_bvals.py"  --dmri "${WORKING_DMRI_BC1}.nii.gz" \
                                        --bvals "${BVALS}" \
                                        --bvecs "${BVECS}" \
                                        --grads "${GRAD4CLS}" \
                                        --ntecho "${NUMBER_ECHOTIME}" \
                                        --bvalsnew "${BVALSTE}" \
                                        --bvecsnew "${BVECSTE}" \
                                        --gradsnew  "${GRAD4CLSTE}"



        mrconvert "${WORKING_DMRI_BC1}.nii.gz" "${WORKING_DMRI_BC1}.mif" -stride "$STRIDES" -force
        #mrconvert "${WORKING_DMRI_BC2}.nii.gz" "${WORKING_DMRI_BC2}.mif" -stride "$STRIDES" -force

        mrconvert "${WORKING_DMRI_BC1}.mif" "${WORKING_DMRI_BC1}.mif" -grad $GRAD4CLSTE -force
        #mrconvert "${WORKING_DMRI_BC2}.mif" "${WORKING_DMRI_BC2}.mif" -grad $GRAD4CLSTE -force


        if [[ ! -e ${PRPROCESSING_DIR}/dwiTopupVolumemask_TE1.nii.gz ]] && [[ ! -e ${PRPROCESSING_DIR}/dwiTopupVolume_sk_TE1.mif ]]; then

            bash ${SRC}/segment_fetalbrain.sh --dmri "${WORKING_DMRI_BC1}.mif" \
                                         --seg_tmp_dir ${PRPROCESSING_DIR}/seg_tmp \
                                         --dmrisk ${PRPROCESSING_DIR}/dwibc_sk_TE1.mif \
                                         --mask ${PRPROCESSING_DIR}/dwibcmask_TE1.nii.gz
        else

            cp ${PRPROCESSING_DIR}/dwiTopupVolumemask_TE1.nii.gz ${PRPROCESSING_DIR}/dwibcmask_TE1.nii.gz
            cp ${PRPROCESSING_DIR}/dwiTopupVolume_sk_TE1.mif ${PRPROCESSING_DIR}/dwibc_sk_TE1.mif

        fi

        # Make sure that ANTS's Inputs occupy the same physical space!
        mrconvert "${PRPROCESSING_DIR}/dwibcmask_TE1.nii.gz" - -stride "$STRIDES3D" | mrtransform - -template "${WORKING_DMRI_BC1}.mif" -interp nearest "${PRPROCESSING_DIR}/dwibcmask_TE1.nii.gz" -force

        if [[ $B1CORRECTIONWAY == "Using_B0" ]]; then

            dwibiascorrect ants -mask "${PRPROCESSING_DIR}/dwibcmask_TE1.nii.gz" -bias "${PRPROCESSING_DIR}/b1N4BiasField_TE1.mif" "${WORKING_DMRI_BC1}.mif" "${PRPROCESSING_DIR}/dwibc_TE1.mif" -force
            #dwibiascorrect ants -bias ${OUTPATHSUB}/b1biasfieldTE2.mif "${WORKING_DMRI_BC2}.mif" "${OUTPATHSUB}/dwibc_TE2.mif"
            if [[ ! -e ${PRPROCESSING_DIR}/dwibc_TE1.mif ]]; then
                dwibiascorrect ants -bias "${PRPROCESSING_DIR}/b1N4BiasField_TE1.mif" "${WORKING_DMRI_BC1}.mif" "${PRPROCESSING_DIR}/dwibc_TE1.mif" -force
            fi

        elif [[ $B1CORRECTIONWAY == "Individually" ]]; then
            echo "To be implemented/improved later"
            # this option is not working : raise MRtrixError('DW gradient scheme contains different number of entries (' + str(len(dwi_header.keyval()['dw_scheme']))
            # + ' to number of volumes in DWIs (' + dwi_header.size()[3] + ')'). Some efforts should be done here to improve it. Read Maria Derpez and DESIGNER papers.
            # DWImif=""
            # for ((VIDX=0; VIDX<${NVOLUMES}; VIDX++)); do
            #     mrconvert -coord 3  $VIDX  ${OUTPATHSUB}/dwirc.mif  ${OUTPATHSUB}/dwiprebc_${VIDX}.mif
            #     dwibiascorrect ants -bias "${OUTPATHSUB}/b1biasfield_${VIDX}.mif" "${OUTPATHSUB}/dwiprebc_${VIDX}.mif" "${OUTPATHSUB}/dwibc_${VIDX}.mif"
            #     DWImif+="dwibc_${VIDX}.mif "
            # done
            # mrcat -axis 3 $DWImif ${OUTPATHSUB}/dwibc.mif

        elif [[ $B1CORRECTIONWAY == "using_mask" ]]; then
            echo "To be implemented soon"
        fi

    else
        echo "Error: Unexpected value for NUMBER_ECHOTIME."
        exit
    fi

else
    echo "Step $STEPX locked or not set to TODO. Moving on."
fi

((STEPX++))
echo "---------------------------------------------------------------------------------"
# STEP 8: STEP8_3DSHORE_RECONSTRUCTION
if [[ $NOLOCKS = 1 && -e ${LOCK8} && ${FEDI_DMRI_PIPELINE_STEPS["STEP8_3DSHORE_RECONSTRUCTION"]}  == "TODO" && ! -e ${MOTIONCORREC_DIR}/spred5.nii.gz ]] ; then rm ${LOCK8} ; fi
if [[ ${FEDI_DMRI_PIPELINE_STEPS["STEP8_3DSHORE_RECONSTRUCTION"]}  == "TODO" ]] && [[ ! -e ${LOCK8} ]]; then

    echo -e "\n ${STEPX}.|--->  3D SHORE RECONSTRUCTION   ---"
    touch ${LOCK8}

    ########### mrconvert dwicrop.mif -axes 0,2,1,3 dwicropOK.mif -force
    WORKING_DMRI="${MOTIONCORREC_DIR}/working_TE1.nii.gz"
    WORKING_DMRIMASK="${MOTIONCORREC_DIR}/working_mask_TE1.nii.gz"

    WORKING_DMRI_GMM="${MOTIONCORREC_DIR}/working_TE1_GMM.nii.gz"
    WORKING_DMRIMASK_GMM="${MOTIONCORREC_DIR}/working_mask_TE1_GMM.nii.gz"

    # copy necessary data and make sure that strides are correct
    mrconvert "${PRPROCESSING_DIR}/dwibc_TE1.mif" "${WORKING_DMRI}" -stride "$STRIDES" -force

    maskfilter -npass 1 "${PRPROCESSING_DIR}/dwibcmask_TE1.nii.gz" dilate - | mrconvert - "${WORKING_DMRIMASK}" -stride "$STRIDES3D" -force

    # bvals and bvecs for different TE
    if [[ ${NUMBER_ECHOTIME} -eq 1 ]]; then
        BVALSTE="${BVALS}"
        BVECSTE="${BVECS}"

    elif [[ ${NUMBER_ECHOTIME} -gt 1 ]]; then

        python "${SRC}/update_bvecs_bvals.py"  --dmri "${WORKING_DMRI}" \
                                        --bvals "${BVALS}" \
                                        --bvecs "${BVECS}" \
                                        --grads "${GRAD4CLS}" \
                                        --ntecho "${NUMBER_ECHOTIME}" \
                                        --bvalsnew "${BVALSTE}" \
                                        --bvecsnew "${BVECSTE}" \
                                        --gradsnew  "${GRAD4CLSTE}"
    else
        echo "Error: Unexpected value for NUMBER_ECHOTIME."
        exit 1
    fi


    #
    RAWWORKING_DMRI="$WORKING_DMRI"

    EPOCHS=6 # Set number of reconstruction iterations here
    ITER_REG="1 2 3 4"
    REG_UPDATE=0
    REG_COUNTER=0
    BVECSTEIN=$BVECSTE

    for ((ITER=0; ITER<$EPOCHS; ITER++)); do
        ITERM=$((ITER-1))


        # AXIS SLICE is number 0 or 1.
        echo "=================================================================================================================="
        echo "Reorient data for GMM slice weighting : $ITER"
        echo "=================================================================================================================="



        if [[ $AXSLICES -eq "0" ]]; then

            echo "Applying Transformation Axis as Slice's Axis = $AXSLICES"

            echo "0 0  1 0
            1 0 0 0
            0 1  0 0
            0 0  0 1" > "${PRPROCESSING_DIR}/trans_axis0.txt"

            mrtransform -linear  "${PRPROCESSING_DIR}/trans_axis0.txt" "${WORKING_DMRI}" "${WORKING_DMRI_GMM}" -force
            mrtransform -linear  "${PRPROCESSING_DIR}/trans_axis0.txt" "${WORKING_DMRIMASK}" "${WORKING_DMRIMASK_GMM}" -force

            if [[ -e "${MOTIONCORREC_DIR}/spred${ITERM}.nii.gz" ]]; then

                SPRED_GMM="${MOTIONCORREC_DIR}/spred${ITERM}_GMM.nii.gz"
                mrtransform -linear  "${PRPROCESSING_DIR}/trans_axis0.txt" "${MOTIONCORREC_DIR}/spred${ITERM}.nii.gz" "${SPRED_GMM}" -force
            fi
        elif [[ $AXSLICES -eq "1" ]]; then
            echo "Applying Transformation Axis as Slice's Axis = $AXSLICES"
            echo "1 0  0 0
            0 0 -1 0
            0 1  0 0
            0 0  0 1" > "${PRPROCESSING_DIR}/trans_axis1.txt"

            mrtransform -linear  "${PRPROCESSING_DIR}/trans_axis1.txt" "${WORKING_DMRI}" "${WORKING_DMRI_GMM}" -force
            mrtransform -linear  "${PRPROCESSING_DIR}/trans_axis1.txt" "${WORKING_DMRIMASK}" "${WORKING_DMRIMASK_GMM}" -force
            if [[ -e "${MOTIONCORREC_DIR}/spred${ITERM}.nii.gz" ]]; then

                SPRED_GMM="${MOTIONCORREC_DIR}/spred${ITERM}_GMM.nii.gz"
                mrtransform -linear  "${PRPROCESSING_DIR}/trans_axis1.txt" "${MOTIONCORREC_DIR}/spred${ITERM}.nii.gz" "${SPRED_GMM}" -force
            fi

        elif [[ $AXSLICES -eq "2" ]]; then
            WORKING_DMRI_GMM=${WORKING_DMRI}
            WORKING_DMRIMASK_GMM=${WORKING_DMRIMASK}
            SPRED_GMM="${MOTIONCORREC_DIR}/spred${ITERM}.nii.gz"

        fi


        echo "=================================================================================================================="
        echo "Start Reconstruction Iteration : $ITER"
        echo "=================================================================================================================="
        # # Outlier Detection

        echo " -dmri $WORKING_DMRI"
        echo " -dmrigmm $WORKING_DMRI_GMM"
        echo " -bval$BVALSTE"
        echo " -bvec$BVECSTE"
        echo " -outpath${SLICEWEIGHTS_DIR}"
        echo " -fsliceweights_mzscore fsliceweights_mzscore_${ITER}.txt"
        echo " -fsliceweights_angle_neighborsfsliceweights_angle_neighbors_${ITER}.txt"
        echo " -fsliceweights_corre_neighborsfsliceweights_corre_neighbors_${ITER}.txt"
        echo " -fsliceweights_gmmodelfsliceweights_gmmodel_${ITER}.txt"
        echo " -fvoxelweights_shorebasedfvoxelweights_shore_${ITER}.nii.gz"
        echo " -spred${MOTIONCORREC_DIR}/spred${ITERM}.nii.gz"
        echo " -spredgmm${SPRED_GMM}"
        echo " -mask$WORKING_DMRIMASK"
        echo " -maskgmm$WORKING_DMRIMASK_GM"

        python ${SRC}/outlierdetection.py --dmri  "$WORKING_DMRI" \
                                   --dmrigmm  "$WORKING_DMRI_GMM" \
                                   --bval "$BVALSTE" \
                                   --bvec "$BVECSTE" \
                                   --outpath "${SLICEWEIGHTS_DIR}" \
                                   --fsliceweights_mzscore  "fsliceweights_mzscore_${ITER}.txt" \
                                   --fsliceweights_angle_neighbors "fsliceweights_angle_neighbors_${ITER}.txt" \
                                   --fsliceweights_corre_neighbors "fsliceweights_corre_neighbors_${ITER}.txt" \
                                   --fsliceweights_gmmodel "fsliceweights_gmmodel_${ITER}.txt" \
                                   --fvoxelweights_shorebased "fvoxelweights_shore_${ITER}.nii.gz" \
                                   --spred "${MOTIONCORREC_DIR}/spred${ITERM}.nii.gz" \
                                   --spredgmm "${SPRED_GMM}" \
                                   --mask "$WORKING_DMRIMASK" \
                                   --maskgmm "$WORKING_DMRIMASK_GMM"




        echo "=================================================================================================================="
        # Select weighting method
        if [ $ITER -eq 0 ]; then # Initialization

            SHOREWEIGHTING="${SLICEWEIGHTS_DIR}/fsliceweights_mzscore_${ITER}.txt"
            echo "Modfied Zscore (slice-wise) weights will be used."
        elif [[ $ITER -eq 98 ]]; then # Final iteration - alternative option for final weighting
        #elif [[ $ITER -eq $((EPOCHS - 1)) ]]; then # This would replace the final iteration weighting method

            ITERSPECIAL=1
            bash ${SRC}/applytransform.sh --weights4D "${SLICEWEIGHTS_DIR}/fsliceweights_gmmodel_${ITERSPECIAL}.nii.gz"  \
                                  --workpath "${MOTIONCORREC_DIR}/registration_gmm" \
                                  --transformspath "${REG_WORKINGPATH}" \
                                  --weights4Dreg "${SLICEWEIGHTS_DIR}/fsliceweights_gmmodel_${ITERSPECIAL}_reg.nii.gz"

            SHOREWEIGHTING="${SLICEWEIGHTS_DIR}/fsliceweights_gmmodel_${ITERSPECIAL}_reg.nii.gz"
            echo "Shore-based (voxel-wise) weights will be used."

        elif [[ $ITER -eq 99 ]]; then # # not used - alternative option for final weighting

            SHOREWEIGHTING="${SLICEWEIGHTS_DIR}/fvoxelweights_shore_${ITER}.nii.gz"
                echo "Shore-based (voxel-wise) weights will be used."

        else # default weighting after the initial step

            SHOREWEIGHTING="${SLICEWEIGHTS_DIR}/fsliceweights_gmmodel_${ITER}.txt"
            echo "GMM (slice-wise) weights will be used."

        fi
        echo "=================================================================================================================="
        # SHORE Fitting
        python ${SRC}/shorerecon.py --dmri "$WORKING_DMRI" --bval "$BVALSTE" --bvec_in "$BVECSTEIN" --bvec_out "$BVECSTE" \
                             --mask "$WORKING_DMRIMASK" \
                             --weights  "${SHOREWEIGHTING}" \
                             --fspred "${MOTIONCORREC_DIR}/spred${ITER}.nii.gz" \
                             -do_not_use_mask

        # Make sure that the bvec_in is bvec_out after the reconstruction done
        BVECSTEIN=$BVECSTE

        echo "=================================================================================================================="
        # Registration of original data to SHORE predicted data after specific number of iterations
        if [[ "$ITER_REG" == *"$ITER"* ]]; then
            echo "Start Registration : $ITER"

            ((REG_COUNTER++))
            REG_WORKINGPATH="${MOTIONCORREC_DIR}/registration_iter${REG_COUNTER}"
            # v2v registration
            bash ${SRC}/dwiregistration.sh  --rdmri "$RAWWORKING_DMRI" \
                                    --spred "${MOTIONCORREC_DIR}/spred${ITER}.nii.gz" \
                                    --workingpath "${REG_WORKINGPATH}" \
                                    --rdmrireg "${MOTIONCORREC_DIR}/working_updated${REG_UPDATE}.nii.gz"

            # Rotate bvecs per volume
            # Check if the rotation component should be inversed or not
            BVECSTEROT="${MOTIONCORREC_DIR}/rotated_bvecs$REG_UPDATE"
            python ${SRC}/rotate_bvecs_ants.py --bvecs "$BVECSTE" \
                                        --bvecsnew "$BVECSTEROT" \
                                        --pathofmatfile "${REG_WORKINGPATH}" \
                                        --startprefix "Transform_v" \
                                        --endprefix "_0GenericAffine.mat"

            WORKING_DMRI="${MOTIONCORREC_DIR}/working_updated${REG_UPDATE}.nii.gz"
            BVECSTEIN=$BVECSTEROT
            REG_UPDATE=$((REG_UPDATE+1))
        fi
    done


    #cp "${MOTIONCORREC_DIR}/spred$((EPOCHS - 1)).nii.gz" "${MOTIONCORREC_DIR}/sprediction.nii.gz"
else
    echo "Step $STEPX locked or not set to TODO. Moving on."
fi

((STEPX++))
echo "---------------------------------------------------------------------------------"
# STEP 9: STEP9_REGISTRATION_T2W_ATLAS
if [[ $NOLOCKS = 1 && -e ${LOCK9} && ${FEDI_DMRI_PIPELINE_STEPS["STEP9_REGISTRATION_T2W_ATLAS"]}  == "TODO" ]] ; then rm ${LOCK9} ; fi
if [[ ${FEDI_DMRI_PIPELINE_STEPS["STEP9_REGISTRATION_T2W_ATLAS"]}  == "TODO" ]] && [[ ! -e ${LOCK9} ]]; then

    echo " ${STEPX}.|---> Registration to T2W and Atlas"
    touch ${LOCK9}

    # bvals and bvecs for different TE
    if [[ ${NUMBER_ECHOTIME} -eq 1 ]]; then
        BVALSTE="${BVALS}"
        BVECSTE="${BVECS}"
    fi

    FILES=(${T2W_DATA}/${SUBJECTID}/${DWISESSION}/xfm/*.tfm)

    if [[ -e ${FILES[0]} ]] && [[ -e "${BVALSTE}" ]]; then

        T2W_ORIGIN_SPACE="${T2W_DATA}/${SUBJECTID}/${DWISESSION}/xfm/${SUBJECTID}_${DWISESSION}_rec-${T2W_RECON_METHOD}_t2w-t2space.nii.gz"
        T2W_ATLAS_SPACE="${T2W_DATA}/${SUBJECTID}/${DWISESSION}/struct/${SUBJECTID}_${DWISESSION}_rec-${T2W_RECON_METHOD}_t2w.nii.gz"
        XFM="${T2W_DATA}/${SUBJECTID}/${DWISESSION}/xfm/${SUBJECTID}_${DWISESSION}_rec-${T2W_RECON_METHOD}_from-t2space_to-atlas.tfm"

        cp ${T2W_ORIGIN_SPACE} ${T2WXFM_FILES_DIR}/.
        cp ${T2W_ATLAS_SPACE} ${T2WXFM_FILES_DIR}/.
        cp ${XFM} ${T2WXFM_FILES_DIR}/.

        if [[ ! -f ${T2WXFM_FILES_DIR}/`basename ${T2W_ORIGIN_SPACE}` ]] ; then echo "t2w origin space not found" ; continue ; fi
        if [[ ! -f ${T2WXFM_FILES_DIR}/`basename ${T2W_ATLAS_SPACE}` ]] ; then echo "t2w atlas space not found" ; continue ; fi
        if [[ ! -f ${T2WXFM_FILES_DIR}/`basename ${XFM}` ]] ; then echo "t2w origin-to-atlas space transform not found" ; continue ; fi

        lastspred=`find ${MOTIONCORREC_DIR} -maxdepth 1 -name spred\*.nii.gz | sort | tail -n1`
        # mrconvert "${MOTIONCORREC_DIR}/spred5.nii.gz" "${MOTIONCORREC_DIR}/spred5STRIDES.nii.gz" -stride "$STRIDES" -force
        mrconvert -fslgrad ${MOTIONCORREC_DIR}/rotated_bvecs3 $BVALSTE ${lastspred} ${PRPROCESSING_DIR}/spredraw.mif -force

        mrgrid ${PRPROCESSING_DIR}/spredraw.mif regrid -vox 1.25 ${PRPROCESSING_DIR}/spred.mif -force # upsamled

        echo "Register DWI to T2"
        if [[ $REGSTRAT == "manual" ]]; then
            echo method: manual

            # Start by SLICER OR ITKSNAP to get MANUAL_REG_MATRIX ... preprocessing/spred_0.nii.gz to T2WXFM/*_t2w-t2space.nii.gz
            transformconvert ${REGISTRATION_DIR}/MANUAL_REG_MATRIX.txt itk_import ${REGISTRATION_DIR}/itk_mrtrixslicer.mat -force
            transformcalc  ${REGISTRATION_DIR}/itk_mrtrixslicer.mat rigid  ${REGISTRATION_DIR}/linear_mrtrix_rigid.mat -force

        elif [[ $REGSTRAT == "ants" ]] ; then

            echo method: ANTS
  	        OUTANTS="${REGISTRATION_DIR}/ANTSrigid_to_t2"
  	        ANTSXFM=${OUTANTS}Affine.txt
  	        mrconvert "${PRPROCESSING_DIR}/spred.mif" "${PRPROCESSING_DIR}/spred.nii.gz"

  	        if [[ ! -f ${OUTANTS}/ANTSrigid_to_t2.nii.gz ]] ; then
  		          echo "Running ANTS"
  		          ANTS 3 -m PR[${T2W_ORIGIN_SPACE},${PRPROCESSING_DIR}/spred.nii.gz,1,2] -o ${OUTANTS} -r Gauss[3,0] --do-rigid
  		          WarpImageMultiTransform 3 ${PRPROCESSING_DIR}/spred.nii.gz ${OUTANTS}.nii.gz -R ${T2W_ORIGIN_SPACE} ${OUTANTS}Warp.nii.gz ${ANTSXFM}
  	        else
  	            echo "ANTS output found"
  	        fi

  	    # c3d_affine_tool used to convert ANTS output to FSL (readable by mrtrix)
  	    c3d_affine_tool -ref ${T2W_ORIGIN_SPACE} -src ${PRPROCESSING_DIR}/spred.nii.gz -itk ${ANTSXFM} -ras2fsl -o ${REGISTRATION_DIR}/c3d_ants_dwi-to-t2.mat
        transformconvert ${REGISTRATION_DIR}/c3d_ants_dwi-to-t2.mat ${PRPROCESSING_DIR}/spred.mif ${T2W_ORIGIN_SPACE} flirt_import ${REGISTRATION_DIR}/itk_ants.mat -force
        transformcalc  ${REGISTRATION_DIR}/itk_ants.mat rigid  ${REGISTRATION_DIR}/linear_mrtrix_rigid.mat -force
        else

            echo method: FLIRT
            mrconvert -coord 3 0 "${PRPROCESSING_DIR}/spred.mif" "${PRPROCESSING_DIR}/spred_0.nii.gz" -force
            flirt -in  ${PRPROCESSING_DIR}/spred_0.nii.gz -ref  $T2W_ORIGIN_SPACE -dof 6  -cost corratio -omat ${REGISTRATION_DIR}/flirt.mat
            transformconvert ${REGISTRATION_DIR}/flirt.mat "${PRPROCESSING_DIR}/spred.mif" $T2W_ORIGIN_SPACE flirt_import ${REGISTRATION_DIR}/flirt_mrtrix.mat -force
            transformcalc ${REGISTRATION_DIR}/flirt_mrtrix.mat rigid ${REGISTRATION_DIR}/linear_mrtrix_rigid.mat -force

        fi


        # just for QC
        mrtransform  -linear ${REGISTRATION_DIR}/linear_mrtrix_rigid.mat "${PRPROCESSING_DIR}/spred.mif" "${REGISTRATION_DIR}/spred_reg2T2W.mif"  -inverse -force



        echo "Apply atlas transform to DWI [T2 space]"
        echo "T2-to-atlas transform: ${XFM}"
        transformconvert ${XFM} itk_import ${REGISTRATION_DIR}/itk_mrtrix.mat -force
        transformcalc ${REGISTRATION_DIR}/itk_mrtrix.mat rigid ${REGISTRATION_DIR}/itk_mrtrix_rigid.mat -force

        # combination of the 2 matrices 
        transformcompose  ${REGISTRATION_DIR}/linear_mrtrix_rigid.mat ${REGISTRATION_DIR}/itk_mrtrix_rigid.mat ${REGISTRATION_DIR}/combination_rigid.mat -force
        mrtransform -template ${T2W_ATLAS_SPACE} -linear ${REGISTRATION_DIR}/combination_rigid.mat "${PRPROCESSING_DIR}/spred.mif" "${PRPROCESSING_DIR}/spred_xfm.mif" -force



        # Haykel, March 28th, 2024: I recommend to add a registeration step "${PRPROCESSING_DIR}/spred_xfm.mif" to ${T2W_ATLAS_SPACE}


	echo "Segment fetal brain script"
        bash ${SRC}/segment_fetalbrain.sh --dmri ${PRPROCESSING_DIR}/spred_xfm.mif \
         --seg_tmp_dir ${TENFOD_TRACT_DIR}/seg_tmp \
         --dmriskpervolume ${PRPROCESSING_DIR}/spred_xfm_sk_pervolume.mif \
         --dmrisk ${PRPROCESSING_DIR}/spred_xfm_sk.mif \
         --mask ${PRPROCESSING_DIR}/spred_xfm_mask.nii.gz

    else
        echo "Something is missing T2W scans (or may be BVALSTE)"
        echo "Looked for T2W in: ${T2W_DATA}"
    fi

else
    echo "Step $STEPX locked or not set to TODO. Moving on."
fi

((STEPX++))
echo "---------------------------------------------------------------------------------"
# STEP 10: STEP10_TSOR_RESP_FOD_TRACTOG
if [[ $NOLOCKS = 1 && -e ${LOCK10} && ${FEDI_DMRI_PIPELINE_STEPS["STEP10_TSOR_RESP_FOD_TRACTOG"]}  == "TODO" ]] ; then rm ${LOCK10} ; fi
if [[ ${FEDI_DMRI_PIPELINE_STEPS["STEP10_TSOR_RESP_FOD_TRACTOG"]}  == "TODO" ]] && [[ -e "${PRPROCESSING_DIR}/spred_xfm_sk.mif"  ]]  && [[ ! -e ${LOCK10} ]] ; then

        echo "${STEPX}.|---> Tensor FOD Tractography"
        touch ${LOCK10}
        dwi2tensor \
            -mask "${PRPROCESSING_DIR}/spred_xfm_mask.nii.gz" \
            "${PRPROCESSING_DIR}/spred_xfm_sk.mif"  \
            "${TENFOD_TRACT_DIR}/tensor.mif" -force
            # -dkt "${TENFOD_TRACT_DIR}/dkt_tensor.nii.gz" \


        tensor2metric "${TENFOD_TRACT_DIR}/tensor.mif" -vector  "${TENFOD_TRACT_DIR}/dec.mif" -force

        mrcalc "${TENFOD_TRACT_DIR}/dec.mif" -abs "${TENFOD_TRACT_DIR}/fac.nii"  -force


        mrconvert "${TENFOD_TRACT_DIR}/tensor.mif" "${TENFOD_TRACT_DIR}/tensor.nii.gz" -force


        # # # Visulization:
        # mrview "${TENFOD_TRACT_DIR}/fac.nii" \
        # -odf.load_tensor "${TENFOD_TRACT_DIR}/tensor.nii.gz"


        # Read b-values, sort, and remove duplicates considering a tolerance (e.g., b-values within 50 are considered the same shell)
        tolerance=50
        unique_bvals=$(awk -v tol=$tolerance '{for (i=1; i<=NF; i++) if($i > tol) printf "%.0f\n", ($i+tol/2)/tol*tol}' $BVALSTE | sort -n | uniq)

        # Count the unique non-zero b-values
        NUM_SHELLS=$(echo "$unique_bvals" | wc -l)



        # TRACTOGRAPHY_WAY=""
        if [ "$NUM_SHELLS" -gt 1 ]; then
            echo "Multi-shell data"
            # FOD
            dwi2response dhollander -mask "${PRPROCESSING_DIR}/spred_xfm_mask.nii.gz" \
            "${PRPROCESSING_DIR}/spred_xfm_sk.mif" \
            ${TENFOD_TRACT_DIR}/wm_response.txt \
            ${TENFOD_TRACT_DIR}/gm_response.txt \
            ${TENFOD_TRACT_DIR}/csf_response.txt -force

            #  Perform CSD (Constrained Spherical Deconvolution) to estimate fiber orientation distributions (FODs):
            # to add if loop, if it is multi-shell or HARDI
            dwi2fod msmt_csd "${PRPROCESSING_DIR}/spred_xfm_sk.mif" \
                "${TENFOD_TRACT_DIR}/wm_response.txt" "${TENFOD_TRACT_DIR}/wmfod.mif" \
                "${TENFOD_TRACT_DIR}/gm_response.txt" "${TENFOD_TRACT_DIR}/gm.mif" \
                "${TENFOD_TRACT_DIR}/csf_response.txt" "${TENFOD_TRACT_DIR}/csf.mif" \
                -mask "${PRPROCESSING_DIR}/spred_xfm_mask.nii.gz" -force

            # mrview "${TENFOD_TRACT_DIR}/fac.nii" -odf.load_sh "${TENFOD_TRACT_DIR}/wmfod.mif"

            # dhollander_tracts ??
            tckgen "${TENFOD_TRACT_DIR}/wmfod.mif" "${TENFOD_TRACT_DIR}/tractography.tck" \
                    -backtrack \
                    -mask "${PRPROCESSING_DIR}/spred_xfm_mask.nii.gz" \
                    -seed_dynamic "${TENFOD_TRACT_DIR}/wmfod.mif" \
                    -select 100000 \
                    -minlength 10 \
                    -maxlength 120 \
                    -cutoff 0.01 -power 6 -force
            date

            # ${SRC}/convert_tck_trk.py -o tck_2_trk -t "${TENFOD_TRACT_DIR}/dhollander_tracts.tck" -a "${TENFOD_TRACT_DIR}/tensor.nii.gz"

        else

		echo "Single-shell data"
		    mkdir -v tmp

            # FOD
            dwi2response tournier -mask "${PRPROCESSING_DIR}/spred_xfm_mask.nii.gz" \
            "${PRPROCESSING_DIR}/spred_xfm_sk.mif" \
            ${TENFOD_TRACT_DIR}/response_single_shell.txt -force

            #  Perform CSD (Constrained Spherical Deconvolution) to estimate fiber orientation distributions (FODs):
            # to add if loop, if it is multi-shell or HARDI
            dwiextract "${PRPROCESSING_DIR}/spred_xfm_sk.mif" - | dwi2fod msmt_csd - \
                "${TENFOD_TRACT_DIR}/response_single_shell.txt" "${TENFOD_TRACT_DIR}/wmfod_single_shell.mif" \
                -mask "${PRPROCESSING_DIR}/spred_xfm_mask.nii.gz" -force

		    #  Perform CSD (Constrained Spherical Deconvolution) to estimate fiber orientation distributions (FODs):
		    # to add if loop, if it is multi-shell or HARDI
		    dwiextract "${PRPROCESSING_DIR}/spred_xfm_sk.mif" - | dwi2fod csd - \
			"${TENFOD_TRACT_DIR}/response_single_shell.txt" "${TENFOD_TRACT_DIR}/wmfod_single_shell.mif" \
			-mask "${PRPROCESSING_DIR}/spred_xfm_mask.nii.gz" -force

		    # mrview "${TENFOD_TRACT_DIR}/fac.nii" \
			# -odf.load_sh "${TENFOD_TRACT_DIR}/wmfod.mif"


            tckgen "${TENFOD_TRACT_DIR}/wmfod_single_shell.mif" "${TENFOD_TRACT_DIR}/tractography.tck" \
                    -backtrack \
                    -mask "${PRPROCESSING_DIR}/spred_xfm_mask.nii.gz" \
                    -seed_dynamic "${TENFOD_TRACT_DIR}/wmfod_single_shell.mif" \
                    -select 100000 \
                    -minlength 10 \
                    -maxlength 120 \
                    -cutoff 0.01 -power 1.0 -force
            date

		    # ${SRC}/convert_tck_trk.py -o tck_2_trk -t "${TENFOD_TRACT_DIR}/tractography.tck" -a "${TENFOD_TRACT_DIR}/tensor.nii.gz"

        fi


((STEPX++))
echo "---------------------------------------------------------------------------------"
# STEP 11: STEP11_ADVANCED_FETAL_TRACTO


if [[ ${FEDI_DMRI_PIPELINE_STEPS["STEP11_ADVANCED_FETAL_TRACTO"]}  == "TODO" ]]; then

    python fetal_tract/advanced_fetal_tractography.py \
      --basename GA23 \
      --work_dir /my/data \
      --subject_dir example \
      --tensor_path /my/data/example/GA23.nii.gz \
      --md_path /my/data/example/GA23_md.nii.gz \
      --tissue_path /my/data/example/GA23_tissue.nii.gz \
      --parcellation_path /my/data/example/GA23_regional.nii.gz

fi


else
    echo "Step $STEPX locked or not set to TODO. Moving on."
fi

# echo "Exporting pipeline outputs"
# for output in ${TENFOD_TRACT_DIR}/tensor.nii.gz ${TENFOD_TRACT_DIR}/fac.nii ${PRPROCESSING_DIR}/spred_xfm_sk.mif ; do
#     if [[ ! -f $output ]] ; then
#         echo "Pipeline product file ${output} not found"
#     fi
# done

# cp "${TENFOD_TRACT_DIR}/tensor.nii.gz" -v ${OUTPUT_FILES_DIR}/${FULLSUBJECTID}_desc-tensor.nii.gz
# cp "${TENFOD_TRACT_DIR}/fac.nii" -v ${OUTPUT_FILES_DIR}/${FULLSUBJECTID}_desc-fac.nii.gz
# mrconvert "${PRPROCESSING_DIR}/spred_xfm_sk.mif" -stride -1,2,3,4 -export_grad_fsl \
#     ${OUTPUT_FILES_DIR}/${FULLSUBJECTID}.bvecs \
#     ${OUTPUT_FILES_DIR}/${FULLSUBJECTID}.bvals \
#     ${OUTPUT_FILES_DIR}/${FULLSUBJECTID}_desc-spred.nii.gz -force

# echo "Pipleine script complete!"
