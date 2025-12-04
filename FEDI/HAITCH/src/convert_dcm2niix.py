#!/usr/bin/env python3.10

##########################################################################
##                                                                      ##
##  Preparation part of the Fetal Diffusion MRI pipeline                ##
##  dcm2niix version                                                    ##
##                                                                      ##
##                                                                      ##
##  Author:    Haykel Snoussi, PhD (dr.haykel.snoussi@gmail.com)        ##
##             IMAGINE Group | Computational Radiology Laboratory       ##
##             Boston Children's Hospital | Harvard Medical School      ##
##                                                                      ##
##########################################################################


import argparse
import os
import subprocess
import pydicom
import json

def main():
    parser = argparse.ArgumentParser(description='DICOM Conversion to NIFTII using mrconvert')
    parser.add_argument('-i', '--input_directory', type=str, help='Specify the input dicom directory path')
    parser.add_argument('-o', '--output_directory', type=str, help='Specify the output directory path')
    parser.add_argument('-s', '--subjectid', type=str, help='Provide a study subject ID')
    parser.add_argument('-v', '--visitid', type=str, help='Provide a study visit ID')
    args = parser.parse_args()

    # Check if all required options are provided
    if not all([args.input_directory, args.output_directory, args.subjectid, args.visitid]):
        parser.print_help()
        return

    first_dcm_file = os.listdir(args.input_directory)[0]

    ds = pydicom.dcmread(os.path.join(args.input_directory, first_dcm_file))

    # Explore the attributes and methods of the ds object
    all_atributes=dir(ds)

    # ds_modality
    Series_Description = ds[0x0008, 0x103e].value
    if (0x0018, 0x1030) in ds:
        protocol_name = ds[0x0018, 0x1030].value
        ds_modality = protocol_name
    elif (0x0008, 0x9209) in ds:
        acquisition_contrast = ds[0x0008, 0x9209].value
        ds_modality = acquisition_contrast
    elif (0x0008, 0x103e) in ds:
        ds_modality = Series_Description
    else:
        ds_modality = None

    # SET ID NAMES
    print("DS_modality          : ", ds_modality)
    patient_id = args.subjectid
    visit_id = args.visitid
    print("Subject ID           : ", patient_id)
    print("Visit ID             : ", visit_id)
    print("Series Description   : ", Series_Description)
    subject_id = f"{patient_id}"
    serie_number = ds[0x0020, 0x0011].value
    s_number=f"run_{serie_number}"

    # SET SEQUENCES MATCHES
    diffusion_matches = ["dti", "DIFFUSION", "DIFF", "diff", "dwi", "DTI", "EPI_highres_with_distortion", "epi_me_128", "dual"]
    derivative_matches = ["_FA", "_ColFA", "_ADC", "_TENSOR_B0", "_TENSOR", "_TRACEW", "_DFC"]
    fieldmap_matches = ["fieldmap", "field_map"]
    T2W_matches = ["HASTE", "haste", "T2MATCH", "AX_T2_FS"]
    T1W_matches = ["VIBE", "vibe"]
    fmri_matches = ["fmri", "fMRI", "FMRI"]
    Multi_EchoTime=["_me", "echo", "cho" ]

    # CHECK FOR SEQUENCE MATCHES
    foldername = os.path.basename(args.input_directory) # also check for matches with folder name
    mri_modality="unknown"
    seq_name="other"
    # This if statement is supposed to filter out matches for derivative diffusion matches based on the protocol name or series description
    if any([x in ds_modality for x in diffusion_matches]) and not any([y in ds_modality for y in derivative_matches]) and not any([z in Series_Description for z in derivative_matches]):
        if any([x in ds_modality for x in Multi_EchoTime]):
            mri_modality = "dwi_me"
            seq_name = "dwi_me"
        else:
            mri_modality = "dwi"
            seq_name = "dwi"
    elif any([x in ds_modality for x in diffusion_matches]):
        mri_modality = "fieldmap"
        seq_name = "fieldmap"
    elif any([x in ds_modality for x in T2W_matches]):
        mri_modality="anat"
        seq_name="t2w"
    elif any([x in ds_modality for x in T1W_matches]):
        mri_modality="anat"
        seq_name="vibe"
    elif any([x in ds_modality for x in fmri_matches]):
        mri_modality="func"
        seq_name="func"

    fullid = f"{subject_id}_{visit_id}_{seq_name}_{s_number}"
    dcm2niix_outputname=f'{subject_id}_{mri_modality}'

    output_directory_dcm2niix = os.path.join(args.output_directory, mri_modality, s_number)

    tmp_directory = os.path.join(output_directory_dcm2niix, "tmp")
    os.makedirs(output_directory_dcm2niix, exist_ok=True)
    os.makedirs(tmp_directory, exist_ok=True)


    info_source_dir = os.path.join(output_directory_dcm2niix, 'info_source_dir.txt' )

    with open(info_source_dir, "w") as file:
        file.write(args.input_directory)


    # Loop through files in the input directory
    for file in os.listdir(args.input_directory):
        filename = os.fsdecode(file)
        input_file = os.path.join(args.input_directory, filename)
        #base_name = os.path.splitext(filename)[0]
        base_name = os.path.basename(filename)
        new_file = os.path.join(tmp_directory, f'{base_name}_jpeg')

        # Perform the conversion using dcmdjpeg
        subprocess.run(['dcmdjpeg', input_file, new_file])


    if mri_modality.startswith('dwi'):
        print("MRI Modality is :", mri_modality)
        # Convert DWI modality with gradient information
        json_export = os.path.join(output_directory_dcm2niix, f'{fullid}_info.json')
        #pydicom_header = os.path.join(output_directory_dcm2niix, f'{fullid}_pydicom_header.txt')
        #grad_mrtrix = os.path.join(output_directory_dcm2niix, f'{fullid}_grad_mrtrix.txt')
        #pe_table = os.path.join(output_directory_dcm2niix, f'{fullid}_pe_table.txt')
        #pe_eddy = os.path.join(output_directory_dcm2niix, f'{fullid}_pe_eddy.txt')


        cmd_dcm2niix = [
        'dcm2niix', '-z', 'o' , '-w', '0', '-v', '0', dcm2niix_outputname, '-f', fullid, '.nii.gz', '-o', output_directory_dcm2niix, args.input_directory
        ]
        
    else:
        # Convert other modalities without gradient information
        cmd_dcm2niix = [
        'dcm2niix', '-z', 'o' , '-w', '0', '-v', '0', dcm2niix_outputname, '-f', fullid, '.nii.gz', '-o', output_directory_dcm2niix, args.input_directory
        ]
       

    print(' '.join(cmd_dcm2niix))
    subprocess.run(cmd_dcm2niix)


    # Remove dmcdjpeg temporary directory
    subprocess.run(['rm', '-rf', tmp_directory])

print(' ')
        
if __name__ == '__main__':
    main()


exit()
###############
# acpparams.txt for topup and eddy
acq_file_dcm2niix = os.path.join(output_directory_dcm2niix, f'{fullid}_acqparams_dcm2niix.txt')

# assuming 4 echoes
echoes = [1 ,2, 3, 4]

for echo in echoes:
    json_file = subprocess.check_output(
    f'find "{output_directory_dcm2niix}" -type f -name "*echo-{echo}*.json"',
        shell=True, text=True).strip()
                
    if not json_file:
        print(f"No json file found for echo {echo}, skipping")
        continue

    with open(json_file, "r") as f:
                json_data = json.load(f)
                
    phase_dir = json_data["PhaseEncodingDirection"]
    readout_time = json_data["TotalReadoutTime"]
    direction = pow(-1, int(echo) - 1)
                

    if "j" in phase_dir:
        with open(acq_file_dcm2niix, "a") as acq_file:
            acq_file.write(f"0 {direction} 0 {readout_time}\n")
    elif "i" in phase_dir:
        with open(acq_file_dcm2niix, "a") as acq_file:
            acq_file.write(f"{direction} 0 0 {readout_time}\n")
    elif "k" in phase_dir:
        with open(acq_file_dcm2niix, "a") as acq_file:
            acq_file.write(f"0 0 {direction} {readout_time}\n")
    else:
        print("Phase encoding direction not recognized")
        exit(1)