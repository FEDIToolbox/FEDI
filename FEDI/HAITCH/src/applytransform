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

# Function to display script usage
usage() {
    echo "Register Weights nii data using Transformation Matrix."
    echo "Usage: $0 --weights4D <weights_data> --workpath <directory_working_path> --transformspath <directory_transforms_path> --weights4Dreg <outfilename_weights_data_registered>"
    exit 1
}

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --weights4D)
            WEIGHTS4D="$2"
            shift
            ;;
        --workpath)
            WORKPATH="$2"
            shift
            ;;
        --transformspath)
            TRANSFORMSPATH="$2"
            shift
            ;;
        --weights4Dreg)
            WEIGHTS4DREG="$2"
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



# Check if required arguments are provided
if [[ -z "$WEIGHTS4D" || -z "$WORKPATH" || -z "$TRANSFORMSPATH" || -z "$WEIGHTS4DREG" ]]; then
    echo "Please provide all required arguments."
    usage
fi

# Validate input files
if [[ ! -f "$WEIGHTS4D" ]]; then
    echo "Input files do not exist. Please check the file paths."
    exit 1
fi

# Inside dwiregistration script
echo "Received arguments:"
echo "--weights4D: $WEIGHTS4D"
echo "--WORKpath: $WORKPATH"
echo "--Transformspath: $TRANSFORMSPATH"
echo "--WEIGHTS4Dreg: $WEIGHTS4DREG"

mkdir -p "${WORKPATH}"

NVOLUMES=$(mrinfo -size "$WEIGHTS4D" -quiet | awk '{print $4}')

echo "Splitting 4D volume into 3D volumes"

for ((VIDX=0; VIDX<${NVOLUMES}; VIDX++)); do
    mrconvert -coord 3 $VIDX "$WEIGHTS4D" "$WORKPATH/weightsGMM_v${VIDX}.nii.gz" -force
done

WEIGHTSLIST_WARPED=""


for ((VIDX=0; VIDX<${NVOLUMES}; VIDX++)); do
    echo "Performing antsApplyTransforms for volume : $VIDX"

    antsApplyTransforms \
    --dimensionality 3 \
    --input-image-type 0 \
    --input "$WORKPATH/weightsGMM_v${VIDX}.nii.gz" \
    --output "$WORKPATH/weightsGMM_v${VIDX}_warped.nii.gz" \
    --interpolation BSpline \
    --transform "${TRANSFORMSPATH}/Transform_v${VIDX}_0GenericAffine.mat" \
    --reference-image "${TRANSFORMSPATH}/working_v${VIDX}_warped.nii.gz" \
    --default-value 0

    echo "Transformation of volume $VIDX completed successfully."
    WEIGHTSLIST_WARPED+="$WORKPATH/weightsGMM_v${VIDX}_warped.nii.gz "

done


echo "All registrations completed successfully."

mrcat -axis 3 $WEIGHTSLIST_WARPED "$WEIGHTS4DREG"