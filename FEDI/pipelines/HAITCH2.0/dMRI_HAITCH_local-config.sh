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

# Default values for options
PROTOCOL=""
MODALITY=""
SESSION=""
RUNNUMBER=""
SUBJECTID=""
CONFIG_FILE=""

# Function to display usage information
usage() {
    echo "Usage: $0 -d PROJDIR -p PROTOCOL -i SUBJECTID -m MODALITY -r RUNNUMBER -o CONFIG_FILE -l 0,1 -s SESSION"
    echo "Options:"
    echo "  -d PROJDIR      PROJDIR i.e, /local/projects/suny, without / at the end"
    echo "  -p PROTOCOL     Protocol i.e, haykel, SHARD, SVRTK"
    echo "  -i SUBJECTID    SUBJECT ID i.e, sub-f1357"
    echo "  -s SESSION      Session identifier i.e, s1, s2"
    echo "  -m MODALITY     MODALITY i.e, dwi, dwiME, dwi_hardi"
    echo "  -r RUNNUMBER    RUNNUMBER i.e, run_21"
<<<<<<< HEAD:FEDI/pipelines/HAITCH/dMRI_HAITCH_local-config.sh
    echo "  -g REGSTRAT	    Registration strategy i.e, flirt, ants, manual"
    echo "  -l OPTION       Ignore locks? 0=NO; 1=YES"
=======
    echo "  -g REGSTRAT  Registration strategy i.e, flirt, ants, manual"
>>>>>>> 933b4dc (Add files via upload):FEDI/HAITCH/dMRI_HAITCH_local-config.sh
    echo "  -o CONFIG_FILE  Output file name"
    exit 1
}

# Parse command-line options
<<<<<<< HEAD:FEDI/pipelines/HAITCH/dMRI_HAITCH_local-config.sh
while getopts "d:p:i:m:r:o:s:g:l:" opt; do
=======
while getopts "d:p:i:m:r:o:s:g:" opt; do
>>>>>>> 933b4dc (Add files via upload):FEDI/HAITCH/dMRI_HAITCH_local-config.sh
    case $opt in
        d)
            PROJDIR="$OPTARG"
        ;;

        p)
            PROTOCOL="$OPTARG"
            ;;
        i)
            SUBJECTID="$OPTARG"
            ;;
        m)
            MODALITY="$OPTARG"
            ;;
        r)
            RUNNUMBER="$OPTARG"
            ;;
        o)
            CONFIG_FILE="$OPTARG"
            ;;
        s)
            SESSION="$OPTARG"
            ;;
<<<<<<< HEAD:FEDI/pipelines/HAITCH/dMRI_HAITCH_local-config.sh
        g)
	    REGSTRAT="$OPTARG"
	    ;;
	l)
	    NOLOCKS="$OPTARG"
	    ;;
=======
	g)
	    REGSTRAT="$OPTARG"
	    ;;
>>>>>>> 933b4dc (Add files via upload):FEDI/HAITCH/dMRI_HAITCH_local-config.sh
        \?)
            echo "Invalid option: -$OPTARG" >&2
            usage
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            usage
            ;;
    esac
done



# Check for mandatory options
if [[ -z "${PROJDIR}" || -z "${SUBJECTID}" || -z "${SESSION}" || -z "${MODALITY}" || -z "${RUNNUMBER}" || -z "${PROTOCOL}" || -z "${CONFIG_FILE}" ]]; then
    echo "Error: Missing required options." >&2
    usage
fi

FULLSUBJECTID="${SUBJECTID}_${SESSION}_${MODALITY}_${RUNNUMBER}"

# Generate the configuration content
cat > "${CONFIG_FILE}" <<EOL

#!/bin/bash -e


##########################################################################
##                                                                      ##
##  Part of Fetal and Neonatal Development Imaging toolbox (FEDI)       ##
##                                                                      ##
##                                                                      ##
##  Author:    Haykel Snoussi, PhD (dr.haykel.snoussi@gmail.com)        ##
##             IMAGINE Group | Computational Radiology Laboratory       ##
##             Boston Children's Hospital | Harvard Medical School      ##
##                                                                      ##
##########################################################################



# Set project-specific variables
export PROJNAME="BCH" # Name of project dHCP or BCH

export SUBJECTID="${SUBJECTID}"
export DWIMODALITY="${MODALITY}"
export DWISESSION="${SESSION}"
export RUNNUM="${RUNNUMBER}"
export MCMETHOD="${PROTOCOL}"

export FULLSUBJECTID="${SUBJECTID}_${SESSION}_${MODALITY}_${RUNNUMBER}"

export PROJDIR="${PROJDIR}"

export SRC="\${PROJDIR}/pipelines/HAITCH/src"
export REFS="\${PROJDIR}/pipelines/HAITCH/refs"
export TMPDIR="\${PROJDIR}/tmp"
export INPATH="\${PROJDIR}/data"
export OUTPATH="\${PROJDIR}/protocols"

export INPATHSUB="\${INPATH}/${SUBJECTID}/${SESSION}/${MODALITY}/${RUNNUMBER}"
export OUTPATHSUB="\${OUTPATH}/${PROTOCOL}/${SUBJECTID}/${SESSION}/${MODALITY}_${RUNNUMBER}"

export REGSTRAT="${REGSTRAT}"
<<<<<<< HEAD:FEDI/pipelines/HAITCH/dMRI_HAITCH_local-config.sh
export NOLOCKS="${NOLOCKS}"
=======

>>>>>>> 933b4dc (Add files via upload):FEDI/HAITCH/dMRI_HAITCH_local-config.sh
export BVALS="\${INPATHSUB}/${FULLSUBJECTID}.bvals"
export BVECS="\${INPATHSUB}/${FULLSUBJECTID}.bvecs"
export BVALSTE="\${INPATHSUB}/${FULLSUBJECTID}_TE.bvals"
export BVECSTE="\${INPATHSUB}/${FULLSUBJECTID}_TE.bvecs"
export GRAD4CLS="\${INPATHSUB}/${FULLSUBJECTID}_grad_mrtrix.txt"
export GRAD4CLSTE="\${INPATHSUB}/${FULLSUBJECTID}_grad_mrtrix_TE.txt"
export GRAD5CLS="\${INPATHSUB}/${FULLSUBJECTID}_grad5cls_mrtrix.txt"
export INDX="\${INPATHSUB}/${FULLSUBJECTID}_index_mrtrix.txt"
export JSONF="\${INPATHSUB}/${FULLSUBJECTID}_info.json"

export T2W_DATA

export ACQPARAM="\${REFS}/acqp_Ali_scans.txt"


# dStripe Docker image setup
export dstripe_docker_image=maxpietsch/dstripe:1.1

# Batch size
export NBATCH=8
MRTRIX_NTHREADS=24
export device=cpu # comma separated for multi-GPU or "cpu"
export batch_size=1 # 30 is fine for use on Tesla V100 (32GB), reduce if using the CPU or if GPU is out of memory

EOL

# Make the configuration file executable
chmod +x "${CONFIG_FILE}"

# Print a message indicating the configuration file has been created
#echo "Configuration file created: ${CONFIG_FILE}"
