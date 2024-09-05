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
PROTOCOL="FEDI"
PROJDIR=`readlink -f $1`

INPATH="${PROJDIR}/data" # path of data
DMRISCRIPTS="${PROJDIR}/pipelines/HAITCH" # path of scripts
OUTPATH="${PROJDIR}/protocols" # path of output

# Set Defaults for optionals
if [[ ! -n $REGSTRAT ]] ; then REGSTRAT="flirt" ; fi
export REGSTRAT
if [[ ! $NOLOCKS = 1 ]] ; then let $NOLOCKS = 0 ; fi

export T2W_DATA="/fileserver/alborz/clem/fediANTsreg/share/setup"

# MODALITY=dwi # ie, "*" , "dwi", "dwiHARDI" or "dwiME" # HARDI only (at least 2 bvalues, we can go by any number of directions) or dMRI_ME


# Assign all run directories to processing list, or use the supplied input text file
if [[ ! -n $INLIST ]] ; then
  echo "Locating runs"
	ALLRUNS=`find ${INPATH} -mindepth 4 -maxdepth 4 -type d -name run\*`
else
	ALLRUNS=$(cat $INLIST)
fi

for RUNDIR in $ALLRUNS ; do
	if [ -d $RUNDIR ] ; then

		# Set the scan data paths and identifiers
		RUNNUMBER=${RUNDIR##*/}
		MODALITYDIR=${RUNDIR%/*}
		MODALITY=${MODALITYDIR##*/}
		SESSIONDIR=${MODALITYDIR%/*}
		SESSION=${SESSIONDIR##*/}
		SUBJECTDIR=${SESSIONDIR%/*}
		SUBJECTID=${SUBJECTDIR##*/}

		case $MODALITY in
			dwi|dwiHARDI|dwiME) # dwi|dwiHARDI|dwiME (only processing diffusion)
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
					OUTPATHSUB="${OUTPATH}/${PROTOCOL}/${SUBJECTID}/${SESSION}/${MODALITY}_${RUNNUMBER}"
					mkdir -p ${OUTPATHSUB}
					FULLSUBJECTID="${SUBJECTID}_${SESSION}_${MODALITY}_${RUNNUMBER}"
					CONFIG_FILE="${OUTPATHSUB}/${PROTOCOL}_local-config_${FULLSUBJECTID}.sh"

					# Create config file
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
	fi
done
