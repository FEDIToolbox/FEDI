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

    # print(ds)



#    if (0x0010, 0x0020) in ds:
#        patient_id = ds[0x0010, 0x0020].value
#    else:
#        patient_id ="Unknow_ID"

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



#    acquisition_date = "00000000"

    # Check for the presence of acquisition date information
#    if (0x0040, 0x2004) in ds and '20' in ds[0x0018, 0x1030].value:
#        acquisition_date = ds[0x0018, 0x1030].value
#        print("Acquisition date (0x0040, 0x2004)    : ", acquisition_date)

#    elif (0x0008, 0x0020) in ds and '20' in ds[0x0008, 0x0020].value:
#        acquisition_date = ds[0x0008, 0x0020].value
#        print("Acquisition date (0x0008, 0x0020)    : ", acquisition_date)



    serie_number = ds[0x0020, 0x0011].value
    

    # SET ID NAMES
    print("DS_modality          : ", ds_modality)
#    print("Acquisition date     : ", acquisition_date)
#    print("Patient ID           : ", patient_id)
    patient_id = args.subjectid
    visit_id = args.visitid
    print("Subject ID           : ", patient_id)
    print("Visit ID             : ", visit_id)
    print("Series Description   : ", Series_Description)
#    subject_id = f"sub-{patient_id}_{acquisition_date}"
    subject_id = f"{patient_id}"
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


    output_directory_mrconvert = os.path.join(args.output_directory, mri_modality, s_number)

    tmp_directory = os.path.join(output_directory_mrconvert, "tmp")
    os.makedirs(output_directory_mrconvert, exist_ok=True)
    os.makedirs(tmp_directory, exist_ok=True)


    info_source_dir = os.path.join(output_directory_mrconvert, 'info_source_dir.txt' )

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
        json_export = os.path.join(output_directory_mrconvert, f'{fullid}_info.json')
        pydicom_header = os.path.join(output_directory_mrconvert, f'{fullid}_pydicom_header.txt')
        grad_mrtrix = os.path.join(output_directory_mrconvert, f'{fullid}_grad_mrtrix.txt')
        grad_fsl_bvecs = os.path.join(output_directory_mrconvert, f'{fullid}.bvecs')
        grad_fsl_bvals = os.path.join(output_directory_mrconvert, f'{fullid}.bvals')
        pe_table = os.path.join(output_directory_mrconvert, f'{fullid}_pe_table.txt')
        pe_eddy = os.path.join(output_directory_mrconvert, f'{fullid}_pe_eddy.txt')
        

        # adding '-export_pe_table', pe_table, '-export_pe_eddy', pe_eddy, doesn't work for some data
        cmd_mrconvert = [
        'mrconvert', '-clear_property', 'comments', '-json_export', json_export, '-export_grad_mrtrix', grad_mrtrix, '-export_grad_fsl',
        grad_fsl_bvecs, grad_fsl_bvals, args.input_directory, os.path.join(output_directory_mrconvert, f'{fullid}.nii.gz')#, '-force'
        ]
#        'mrconvert', '-clear_property', 'comments', '-json_export', json_export, '-export_grad_mrtrix', grad_mrtrix, '-export_grad_fsl',
#        grad_fsl_bvecs, grad_fsl_bvals, tmp_directory, os.path.join(output_directory_mrconvert, f'{fullid}.nii.gz')#, '-force'
#        ]

        print(' '.join(cmd_mrconvert))  # Print the command
        subprocess.run(cmd_mrconvert)

        # Goal is creating the following
        json_file_params = os.path.join(output_directory_mrconvert, f'{fullid}_dMRI_params.json')
        acq_file_mrconvert = os.path.join(output_directory_mrconvert, f'{fullid}_acqparams_mrconvert.txt')


        # Read the MRCONVERT JSON file of mrconvert: 
        if not os.path.isfile(json_export):
            print('JSON export for ' + fullid + 'not found')
        else:

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


    else:
        # Convert other modalities without gradient information
        cmd = [
        #'mrconvert', '-clear_property', 'comments', tmp_directory, os.path.join(output_directory_mrconvert, f'{subject_id}_{mri_modality}_{ds_modality}.nii.gz'), '-force'
        'mrconvert', '-clear_property', 'comments', tmp_directory, os.path.join(output_directory_mrconvert, f'{fullid}.nii.gz'), '-force'
        ]

        print(' '.join(cmd))
        subprocess.run(cmd)


    # Remove dmcdjpeg temporary directory
    subprocess.run(['rm', '-rf', tmp_directory])

print(' ')
        
if __name__ == '__main__':
    main()
