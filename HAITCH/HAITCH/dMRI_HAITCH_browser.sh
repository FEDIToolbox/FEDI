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

# Set project-specific variables 
PROTOCOL="FEDI" 
PROJDIR=/local/projects/sunny

INPATH="${PROJDIR}/data" # path of data
DMRISCRIPTS="$PROJDIR/scripts/fedi" # path of scripts
OUTPATH="${PROJDIR}/protocols" # path of output


# MODALITY=dwi # ie, "*" , "dwi", "dwiHARDI" or "dwiME" # HARDI only (at least 2 bvalues, we can go by any number of directions) or dMRI_ME


for SUBJECTDIR in ${INPATH}/*; do
	SUBJECTID=${SUBJECTDIR#"${INPATH}/"}
	for SESSIONDIR in ${SUBJECTDIR}/*; do
		SESSION=${SESSIONDIR#"${SUBJECTDIR}/"}
		for MODALITYDIR in ${SESSIONDIR}/*; do # $MODALITY
			if [ -d "$MODALITYDIR" ]; then
				MODALITY=${MODALITYDIR#"$SESSIONDIR/"}
				# echo $MODALITYDIR
				# echo "$MODALITY working directory."
				case $MODALITY in
					dwi|dwiHARDI|dwiME) # dwi|dwiHARDI|dwiME
						for RUNDIR in ${MODALITYDIR}/*; do
							RUNNUMBER=${RUNDIR#"$MODALITYDIR/"}
							if [ -d "$RUNDIR" ]; then
								if [ -e $RUNDIR/lock ] ; then

								    echo "====================================================="
								    echo "@ SUBJECTID Locked"
								    echo "====================================================="

								elif [[ -e $RUNDIR/todo.txt ]]; then
									#statements

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
									bash ${DMRISCRIPTS}/dMRI_local-config.sh -d "$PROJDIR" -p "$PROTOCOL" -i "$SUBJECTID" -s "$SESSION" -m $MODALITY -r "$RUNNUMBER" -o "$CONFIG_FILE"

									# Processing data
									bash ${DMRISCRIPTS}/dMRI_HAITCH.sh "${CONFIG_FILE}"

									echo "====================================================="
									echo "====================================================="
								fi
							else
								echo "$RUNDIR directory does not exist."
							fi
						done
						;;
					*)
						echo "It is not a diffusion data directory"
						;;
				esac
			else
    			echo "$MODALITY directory does not exist."
			fi	
		done
	done
done
