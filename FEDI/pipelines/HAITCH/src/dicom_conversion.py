#!/usr/bin/env python3.10

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


import argparse
import os
import subprocess
import pydicom
import json

def main():
    parser = argparse.ArgumentParser(description='DICOM Conversion to NIFTII using mrconvert')
    parser.add_argument('-i', '--input_directory', type=str, help='Specify the input dicom directory path')
    parser.add_argument('-o', '--output_directory', type=str, help='Specify the output directory path')
    args = parser.parse_args()

    # Check if all required options are provided
    if not all([args.input_directory, args.output_directory]):
        parser.print_help()
        return

    first_dcm_file = os.listdir(args.input_directory)[0]

    ds = pydicom.dcmread(os.path.join(args.input_directory, first_dcm_file))

    # Explore the attributes and methods of the ds object
    all_atributes=dir(ds)

    # print(ds)



    if (0x0010, 0x0020) in ds:
        patient_id = ds[0x0010, 0x0020].value
    else:
        patient_id ="Unknow_ID"

    # ds_modality
    if (0x0018, 0x1030) in ds:
        protocol_name = ds[0x0018, 0x1030].value
        ds_modality = protocol_name
    elif (0x0008, 0x9209) in ds:
        acquisition_contrast = ds[0x0008, 0x9209].value
        ds_modality = acquisition_contrast
    elif (0x0008, 0x103e) in ds:
        Series_Description = ds[0x0008, 0x103e].value
        ds_modality = Series_Description
    else:
        ds_modality = None



    acquisition_date = "00000000"

    # Check for the presence of acquisition date information
    if (0x0040, 0x2004) in ds and '20' in ds[0x0018, 0x1030].value:
        acquisition_date = ds[0x0018, 0x1030].value
        print("Acquisition date (0x0040, 0x2004)    : ", acquisition_date)

    elif (0x0008, 0x0020) in ds and '20' in ds[0x0008, 0x0020].value:
        acquisition_date = ds[0x0008, 0x0020].value
        print("Acquisition date (0x0008, 0x0020)    : ", acquisition_date)



    serie_number = ds[0x0020, 0x0011].value
    

    print("DS_modality          : ", ds_modality)
    print("Acquisition date     : ", acquisition_date)
    print("Patient ID           : ", patient_id)

    subject_name = f"sub-{patient_id}_{acquisition_date}"
    s_number=f"run_{serie_number}"
    diffusion_matches = ["dti", "DIFFUSION", "DIFF", "diff", "dwi", "DTI", "EPI_highres_with_distortion", "epi_me_128"]
    fieldmap_matches = ["fieldmap"]
    T2W_matches = ["T2 HASTE", "T2haste", "T2MATCH", "AX_T2_FS", "HASTE"]
    Multi_EchoTime=["_me", "echo", "cho" ]





    mri_modality="unknown"
    if any([x in ds_modality for x in diffusion_matches]):
        if any([x in ds_modality for x in Multi_EchoTime]):
            mri_modality = "dwi_me"
        else:
            mri_modality = "dwi"
    elif any([x in ds_modality for x in diffusion_matches]):
        mri_modality = "fieldmap"
    elif any([x in ds_modality for x in T2W_matches]):
        mri_modality="T2W"



    diffusion_matches = ["dti", "DIFFUSION", "DIFF", "diff", "dwi", "DWI", "DTI", "EPI_highres_with_distortion", "epi_me_128", "dual"]
    fieldmap_matches = ["fieldmap"]
    T2W_matches = ["T2 HASTE", "T2haste", "T2MATCH", "AX_T2_FS"]
    Multi_EchoTime = ["_me", "echo", "cho"]

    mri_modality = "unknown"

    if any([x in ds_modality for x in diffusion_matches]):
        if any([x in ds_modality for x in Multi_EchoTime]):
            mri_modality = "dwi_me"
        else:
            mri_modality = "dwi"
    elif any([x in ds_modality for x in fieldmap_matches]):
        mri_modality = "fieldmap"
    elif any([x in ds_modality for x in T2W_matches]):
        mri_modality = "T2W"





    output_directory_mrconvert = os.path.join(args.output_directory, subject_name, mri_modality, s_number, "mrconvert")
    output_directory_dcm2niix = os.path.join(args.output_directory, subject_name, mri_modality, s_number, "dcm2niix")

    tmp_directory = os.path.join(output_directory_mrconvert, "tmp")
    os.makedirs(output_directory_mrconvert, exist_ok=True)
    os.makedirs(output_directory_dcm2niix, exist_ok=True)
    os.makedirs(tmp_directory, exist_ok=True)


    info_source_dir = os.path.join(output_directory_mrconvert, 'info_source_dir.txt' )

    with open(info_source_dir, "w") as file:
        file.write(args.input_directory)



    # Loop through files in the input directory
    for file in os.listdir(args.input_directory):
        filename = os.fsdecode(file)
        input_file = os.path.join(args.input_directory, filename)
        base_name = os.path.splitext(filename)[0]
        new_file = os.path.join(tmp_directory, f'{base_name}_jpeg')

        # Perform the conversion using dcmdjpeg
        subprocess.run(['dcmdjpeg', input_file, new_file])




    
    if mri_modality.startswith('dwi'):
        print("MRI Modality is :", mri_modality)
        # Convert DWI modality with gradient information
        json_export = os.path.join(output_directory_mrconvert, f'{subject_name}_info.json')
        pydicom_header = os.path.join(output_directory_mrconvert, f'{subject_name}_pydicom_header.txt')
        grad_mrtrix = os.path.join(output_directory_mrconvert, f'{subject_name}_grad_mrtrix.txt')
        grad_fsl_bvecs = os.path.join(output_directory_mrconvert, f'{subject_name}_bvecs')
        grad_fsl_bvals = os.path.join(output_directory_mrconvert, f'{subject_name}_bvals')
        pe_table = os.path.join(output_directory_mrconvert, f'{subject_name}_pe_table.txt')
        pe_eddy = os.path.join(output_directory_mrconvert, f'{subject_name}_pe_eddy.txt')
        


        # adding '-export_pe_table', pe_table, '-export_pe_eddy', pe_eddy, doesn't work for some data
        cmd_mrconvert = [
        'mrconvert', '-json_export', json_export, '-export_grad_mrtrix', grad_mrtrix, '-export_grad_fsl',
        grad_fsl_bvecs, grad_fsl_bvals, tmp_directory, os.path.join(output_directory_mrconvert, f'{subject_name}_{mri_modality}.nii.gz'), '-force'
        ]
        
     
        # dcm2niix_outputname=f'{subject_name}_{mri_modality}_run-%s_desc-%p_echo-%e'
        dcm2niix_outputname=f'{subject_name}_{mri_modality}'
        cmd_dcm2niix = [
        'dcm2niix', '-z', 'o' , '-w', '0', '-v', '0', dcm2niix_outputname, '-o', output_directory_dcm2niix, args.input_directory
        ]

        print(' '.join(cmd_mrconvert))  # Print the command
        print(' '.join(cmd_dcm2niix))
        subprocess.run(cmd_mrconvert)
        subprocess.run(cmd_dcm2niix)


            # Goal is creating the following
        json_file_params = os.path.join(output_directory_mrconvert, f'{subject_name}_dMRI_params.json')
        acq_file_dcm2niix = os.path.join(output_directory_dcm2niix, f'{subject_name}_acqparams_dcm2niix.txt')
        acq_file_mrconvert = os.path.join(output_directory_mrconvert, f'{subject_name}_acqparams_mrconvert.txt')


        # Read the MRCONVERT JSON file of mrconvert: 
        with open(json_export) as json_file:
            data = json.load(json_file)


        # Check for the existence of required fields
        if 'MultibandAccelerationFactor' in data:
            mb_factor = data['MultibandAccelerationFactor']
        else:
            mb_factor = None  # Set to None or provide a default value

        if 'SliceEncodingDirection' in data: # Be careful, we don't need this in information : SliceEncodingDirection != PhaseEncodingDirection
            SliceEncodingDirection = data['SliceEncodingDirection']
        else:
            SliceEncodingDirection = None  # Set to None or provide a default value

        if 'SliceTiming' in data:
            slice_timing = data['SliceTiming']
            if slice_timing[0] > slice_timing[1]:
                slice_order = "even-odd"
            else:
                slice_order = "odd-even"
        else:
            slice_timing = None  # Set to None or provide a default value
            slice_order = None   # Set to None or provide a default value

        # Create a dictionary to store the specific information
        specific_info = {
            'mb_factor': mb_factor,
            'SliceEncodingDirection': SliceEncodingDirection,
            'slice_timing': slice_timing,
            'slice_order': slice_order
        }


        # Write the specific information to the JSON file
        with open(json_file_params, 'w') as json_file:
            json.dump(specific_info, json_file)

        with open(pydicom_header, 'w') as f:
                f.write(str(ds))


        ###############
        # acpparams.txt for topup and eddy

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


        # Remove temporary directory
        subprocess.run(['rm', '-rf', tmp_directory])


    else:
        # Convert other modalities without gradient information
        cmd = [
        'mrconvert', tmp_directory, os.path.join(output_directory_mrconvert, f'{subject_name}_{mri_modality}_{ds_modality}.nii.gz'), '-force'
        ]

        print(' '.join(cmd))
        subprocess.run(cmd)


        
if __name__ == '__main__':
    main()