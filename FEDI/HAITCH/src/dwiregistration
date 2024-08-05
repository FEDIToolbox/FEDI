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
    echo -e "Register Diffusion-Weighted data, volume to volume.\nUsage: $0 --rdmri <raw_dmri_data> --spred <shore_predicted_data> --workingpath <directory_working_path> --rdmrireg <outfilename_raw_dmri_data_registered>"
    exit 1
}

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --rdmri)
            RDMRI="$2"
            shift
            ;;
        --spred)
            SPRED="$2"
            shift
            ;;
        --workingpath)
            WORKINGPATH="$2"
            shift
            ;;
        --rdmrireg)
            RDMRIREG="$2"
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

# Inside dwiregistration script
echo "Received arguments:"
echo "--rdmri: $RDMRI"
echo "--spred: $SPRED"
echo "--workingpath: $WORKINGPATH"
echo "--rdmrireg: $RDMRIREG"


# Check if required arguments are provided
if [[ -z "$RDMRI" || -z "$SPRED" || -z "$WORKINGPATH" || -z "$RDMRIREG" ]]; then
    echo "Please provide all required arguments."
    usage
fi

# Validate input files
if [[ ! -f "$RDMRI" || ! -f "$SPRED" ]]; then
    echo "Input files do not exist. Please check the file paths."
    exit 1
fi

mkdir -p "$WORKINGPATH"

NVOLUMES=$(mrinfo -size "$RDMRI" -quiet | awk '{print $4}')

echo "Splitting 4D volume into 3D volumes"

for ((VIDX=0; VIDX<${NVOLUMES}; VIDX++)); do
    mrconvert -coord 3 $VIDX "$RDMRI" "$WORKINGPATH/working_v${VIDX}.nii.gz" -force -quiet
    mrconvert -coord 3 $VIDX "$SPRED" "$WORKINGPATH/spred_v${VIDX}.nii.gz" -force -quiet
done

DWILIST_WARPED=""

REGISTRATION_TYPE="THREE"

if [[ ${REGISTRATION_TYPE}  == "ONE" ]]; then
    echo "REGISTRATION_TYPE is: $REGISTRATION_TYPE"
    for ((VIDX=0; VIDX<${NVOLUMES}; VIDX++)); do
        echo "Performing antsRegistration for volume : $VIDX"
        antsRegistration \
        --collapse-output-transforms 1 \
        --dimensionality 3 \
        --initialize-transforms-per-stage 0 \
        --interpolation BSpline \
        --output [ $WORKINGPATH/Transform_v${VIDX}_, "$WORKINGPATH/working_v${VIDX}_warped.nii.gz" ] \
        --transform Rigid[ 0.1 ] \
        --metric GC[ "$WORKINGPATH/spred_v${VIDX}.nii.gz", "$WORKINGPATH/working_v${VIDX}.nii.gz", 1, 32, Regular, 0.25 ] \
        --convergence [ 1000x500x250, 1e-06, 10 ] \
        --smoothing-sigmas 1x1x1vox \
        --shrink-factors 8x4x2 \
        --use-histogram-matching 1 \
        --winsorize-image-intensities [0.005,0.995]

        echo "Registration for volume $VIDX completed successfully."
        DWILIST_WARPED+="$WORKINGPATH/working_v${VIDX}_warped.nii.gz "

    done

elif [[ ${REGISTRATION_TYPE}  == "TWO" ]]; then
    echo "REGISTRATION_TYPE is: $REGISTRATION_TYPE"
    for ((VIDX=0; VIDX<${NVOLUMES}; VIDX++)); do
        echo "Performing antsRegistration for volume : $VIDX"
        antsRegistration \
        --collapse-output-transforms 1 \
        --dimensionality 3 \
        --initialize-transforms-per-stage 0 \
        --interpolation BSpline \
        --output [ $WORKINGPATH/Transform_v${VIDX}_, "$WORKINGPATH/working_v${VIDX}_warped.nii.gz" ] \
        --transform Rigid[ 0.1 ] \
        --metric GC[ "$WORKINGPATH/spred_v${VIDX}.nii.gz", "$WORKINGPATH/working_v${VIDX}.nii.gz", 1, 32, Regular, 0.25 ] \
        --convergence [ 2000x1000x500, 1e-06, 10 ] \
        --smoothing-sigmas 1x1x1vox \
        --shrink-factors 4x2x1 \
        --use-histogram-matching 1 \
        --winsorize-image-intensities [0.005,0.995]

        echo "Registration for volume $VIDX completed successfully."
        DWILIST_WARPED+="$WORKINGPATH/working_v${VIDX}_warped.nii.gz "

    done



elif [[ ${REGISTRATION_TYPE}  == "THREE" ]]; then
    echo "REGISTRATION_TYPE is: $REGISTRATION_TYPE"
    for ((VIDX=0; VIDX<${NVOLUMES}; VIDX++)); do
        echo "Performing antsRegistration for volume : $VIDX"
        antsRegistration \
        --collapse-output-transforms 1 \
        --dimensionality 3 \
        --initialize-transforms-per-stage 0 \
        --interpolation BSpline \
        --output [ $WORKINGPATH/Transform_v${VIDX}_, "$WORKINGPATH/working_v${VIDX}_warped.nii.gz" ] \
        --transform Rigid[ 0.01 ] \
        --metric GC[ "$WORKINGPATH/spred_v${VIDX}.nii.gz", "$WORKINGPATH/working_v${VIDX}.nii.gz", 1, 32, Regular, 0.25 ] \
        --convergence [ 2000x1000x500, 1e-07, 10 ] \
        --smoothing-sigmas 1x1x1vox \
        --shrink-factors 4x2x1 \
        --use-histogram-matching 1 \
        --winsorize-image-intensities [0.01,0.99]

        echo "Registration for volume $VIDX completed successfully."
        DWILIST_WARPED+="$WORKINGPATH/working_v${VIDX}_warped.nii.gz "

    done


fi



echo "All registrations completed successfully."

mrcat -axis 3 $DWILIST_WARPED "$RDMRIREG" -quiet