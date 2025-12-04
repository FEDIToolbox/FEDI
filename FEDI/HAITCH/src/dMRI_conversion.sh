#!/bin/bash -e

##########################################################################
##                                                                      ##
##  Preparation part of the Fetal Diffusion MRI pipeline                ##
##                                                                      ##
##                                                                      ##
##  Author:    Haykel Snoussi, PhD (dr.haykel.snoussi@gmail.com)        ##
##             IMAGINE Group | Computational Radiology Laboratory       ##
##             Boston Children's Hospital | Harvard Medical School      ##
##                                                                      ##
##########################################################################

# importing all required configurations
# source /local/projects/fetal_MEcho_dMRI/scripts/dmri_pipeline/dMRI_local-config.sh

while getopts ":hi:o:s:v:" opt; do
  case $opt in
    h)
      echo "Usage: $0 -i <input_dcm_dir> -o <output_dir> -s <study_id> -v <visit_id>"
      echo
      echo "    <input_dcm_dir> should be the scan folder with multiple DICOM series in subfolders"
      echo "    <output_dir> is the study setup folder, probably 'data'"
      echo "    <study_id> subject identifier - do not include 'sub-', the script will add this string"
      echo "    <visit_id> for example, 's1'"
      exit 0
      ;;
    i)
      input_dcm_dir=$OPTARG
      ;;
    o)
      output_dir=$OPTARG
      ;;
    s)
      study_id=$OPTARG
      ;;
    v)
      visit_id=$OPTARG
      ;;
    \?)
      echo "Invalid option: -$OPTARG. Use -h for help." >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument. Use -h for help." >&2
      exit 1
      ;;
  esac
done

if [ -z "$input_dcm_dir" ] || [ -z "$output_dir" ] || [ -z "$study_id" ] || [ -z "$visit_id" ] ; then
  echo "Incorrect argument supplied. Use -h for help."
  exit 1
fi

SRC=`dirname $0`

function check_dependencies() {
	# check that all dependencies are installed, if not, exit
	local dependencies_list=(find grep mrconvert dcmdjpeg)
	for dependency in "${dependencies_list[@]}"; do
		if ! command -v "$dependency" &>/dev/null; then
			echo "$dependency not found, exiting"
			exit 1
		fi
	done
}

function convert_dcms_conversion() {
	# Converts dicom files in the input directory to nifti format,
	#python $SRC/dicom_conversion.py -i "$SERIES" -o "$output_dir" -s "$study_id" -v "$visit_id"
	python $SRC/dicom_conversion.py -i "$SERIES" -o "${output_dir}/$study_id/$visit_id" -s ${study_id} -v ${visit_id}
}

function main() {
	echo "Start dMRI preparation"
	
	# exec &>> log.txt
	# set -x
	check_dependencies
	for SERIES in ${input_dcm_dir}/* ; do
		if [[ -d $SERIES ]] ; then
            echo INPUT: $SERIES
            convert_dcms_conversion
            # grad5cls_index
        else
            echo "No subfolder, trying to convert this dir directly instead"
            SERIES=`dirname $SERIES`
            echo INPUT: $SERIES
            convert_dcms_conversion
            break
		fi
	done
}

main
