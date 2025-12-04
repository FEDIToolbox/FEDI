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
# ./dMRI_conversion.sh

show_help () {
cat << EOF
    USAGE: sh ${0##*/} [project directory]
    This script starts the FEDI pipeline. Supply the project directory.
    data, protocols, and scripts directories specified in script.

    -i LIST.txt	Specify an input text list of input data folder run paths (data/sub-x/sx/dwi/runx)
    --reg STRAT	Specify registration strategy (flirt, manual, ants; default=flirt)
    -l		Ignore any existing locks		

EOF
}

die() {
    printf '%s\n' "$1" >&2
    exit 1
}

while :; do
    case $1 in
        -h|-\?|--help)
            show_help # help message
            exit
            ;;
        -i|--inputs)
            if [[ -f "$2" ]] ; then
                INLIST=$2 # Specify input scan list
                shift
            else
                die 'error: input scan list not found'
            fi
            ;;
	--reg)
	   if [[ -n "$2" ]] ; then
	   	REGSTRAT=$2 # specify registration strategy
		shift
	   else
	   	die 'error: invalid registration strategy'
	   fi
	   ;;
	-l|--ignore-locks)
	    let NOLOCKS=1
	    ;;
        --) # end of optionals
            shift
            break
            ;;
        -)?*
            printf 'warning: unknown option (ignored: %s\m' "$1" >&2
            ;;
        *) # default case, no optionals
            break
    esac
    shift
done

if [ $# -ne 1 ]; then
    show_help
    exit
fi

if [ ! -d $1 ] ; then
	die "error: $1 is not a directory"
fi

# Set project-specific variables
PROTOCOL="HAITCH"
PROJDIR=`readlink -f $1`
# PROJDIR="/home/ch244310/projects/chd"

INPATH="${PROJDIR}/data" # path of data
export DMRISCRIPTS="${PROJDIR}/scripts/dmri_codes/HAITCH" # path of scripts
OUTPATH="${PROJDIR}/data" # path of output

# Set Defaults for optionals
if [[ ! -n $REGSTRAT ]] ; then REGSTRAT="flirt" ; fi
export REGSTRAT
if [[ ! $NOLOCKS = 1 ]] ; then let NOLOCKS=0 ; fi

# MODALITY=dwi # ie, "*" , "dwi", "dwiHARDI" or "dwiME" # HARDI only (at least 2 bvalues, we can go by any number of directions) or dMRI_ME

# Assign all run directories to processing list, or use the supplied input text file
# INPATH is the "data" folder with converted data
if [[ ! -n $INLIST ]] ; then
  echo "Locating runs"
	ALLRUNS=`find ${INPATH} -mindepth 3 -maxdepth 3 -type d -name dMRI\*`
else
	ALLRUNS=$(cat $INLIST)
fi

echo $INLIST

for RUNDIR in $ALLRUNS ; do
	echo $RUNDIR
	if [ -d $RUNDIR ] ; then

		# Set the scan data paths and identifiers
		NOTRAILSLASH=${RUNDIR%/}
		RUNNUMBER=${NOTRAILSLASH##*/}

		MODALITYDIR=${NOTRAILSLASH}
		MODALITY=${RUNNUMBER}

		SESSIONDIR=${RUNDIR%/*}
		SESSION=${SESSIONDIR##*/}
		SESSION=${SESSION#*_}
		SUBJECTDIR=${SESSIONDIR%/*}
		SUBJECTID=${SUBJECTDIR##*/}


		echo "NOTRAILSLASH : $NOTRAILSLASH"
		echo "RUNNUMBER : $RUNNUMBER"
		echo "MODALITYDIR : $MODALITYDIR"
		echo "MODALITY : $MODALITY"
		echo "SESSIONDIR : $SESSIONDIR"
		echo "SESSION : $SESSION"
		echo "SUBJECTDIR : $SUBJECTDIR"
		echo "SUBJECTID : $SUBJECTID"


		# echo "Protocol   : $PROTOCOL"
		# echo "SubjectID  : $SUBJECTID"
		# echo "Session    : $SESSION"
		# echo "Modality   : $MODALITY"
		# echo "Run Number : $RUNNUMBER"
		echo ""


		case $MODALITY in
			dMRI6[1-9]|dMRI8[0-2]) # dwi|dwiHARDI|dwiME (only processing diffusion)
				if [[ -e $RUNDIR/lock && ! $NOLOCKS = 1 ]] ; then

				  echo "====================================================="
				  echo "@ $SUBJECTID $RUNDIR Locked (lock in data folder)"
				  echo "@ $RUNDIR/lock"
				  echo "====================================================="

				else

					echo -e "\n\n\n"
					echo "====================================================="
					echo "====================================================="

					echo "Protocol   : $PROTOCOL"
					echo "SubjectID  : $SUBJECTID"
					echo "Session    : $SESSION" 
					echo "Modality   : $MODALITY"
					echo "Run Number : $RUNNUMBER"
					echo ""

					# Creation of configuration file
					OUTPATHSUB="${NOTRAILSLASH}"
					# mkdir -p ${OUTPATHSUB}
					FULLSUBJECTID="${SUBJECTID}_${SESSION}_${MODALITY}"
					CONFIG_FILE="${OUTPATHSUB}/${PROTOCOL}_local-config_${FULLSUBJECTID}.sh"

					# rename files

					# for file in "$NOTRAILSLASH"/*; do
					#     case "$file" in
					#         *.nii.gz) mv -f "$file" "$NOTRAILSLASH/$FULLSUBJECTID.nii.gz" ;;
					#         *.bval)   mv -f "$file" "$NOTRAILSLASH/$FULLSUBJECTID.bval"   ;;
					#         *.bvec)   mv -f "$file" "$NOTRAILSLASH/$FULLSUBJECTID.bvec"   ;;
					#         *.json)   mv -f "$file" "$NOTRAILSLASH/$FULLSUBJECTID.json"   ;;
					# 		*.txt)    mv -f "$file" "$NOTRAILSLASH/$FULLSUBJECTID.txt"   ;;
					#     esac
					# done

					# for file in "$NOTRAILSLASH"/*; do
					#     case "$file" in
					#         # *.nii.gz) dest="$NOTRAILSLASH/$FULLSUBJECTID.nii.gz" ;;
					#         # *.bval)   dest="$NOTRAILSLASH/$FULLSUBJECTID.bval"   ;;
					#         # *.bvec)   dest="$NOTRAILSLASH/$FULLSUBJECTID.bvec"   ;;
					#         # *.json)   dest="$NOTRAILSLASH/$FULLSUBJECTID.json"   ;;
					#         *.txt)    dest="$NOTRAILSLASH/$FULLSUBJECTID.txt"    ;;
					#         *)        continue ;;
					#     esac

					#     # Skip if source and destination are the same
					#     if [[ "$file" != "$dest" ]]; then
					#         cp -f "$file" "$dest"
					#     fi
					# done



					# # Create config file
					bash ${DMRISCRIPTS}/dMRI_HAITCH_local-config.sh -d "$PROJDIR" -p "$PROTOCOL" -i "$SUBJECTID" -s "$SESSION" -m $MODALITY -r "$RUNNUMBER" -g "$REGSTRAT" -l "$NOLOCKS" -o "$CONFIG_FILE"

					# Processing data
					bash ${DMRISCRIPTS}/dMRI_HAITCH.sh "${CONFIG_FILE}"

					echo "====================================================="
					echo "====================================================="
				fi
				;;
			*)
				echo "$RUNDIR is not a diffusion data directory"
				;;
		esac

	else
		echo "$RUNDIR is not a directory"
		if [[ -n $INLIST ]] ; then echo "are the paths in $INLIST correct?" ; fi	
	fi
done
