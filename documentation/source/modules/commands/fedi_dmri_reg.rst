.. _fedi_dmri_reg:

fedi_dmri_reg
=============

.. rubric:: Synopsis
Perform volume-by-volume registration of 4D diffusion MRI data using ANTs.

.. rubric:: Usage
::

    fedi_dmri_reg [-h] --input_dmri INPUT_DMRI --target_dmri TARGET_DMRI
                  --output_dir OUTPUT_DIR --output_dmri OUTPUT_DMRI

.. rubric:: Options
-  **-h, --help**  
   Show this help message and exit

-  **--input_dmri INPUT_DMRI**  
   Path to the 4D input diffusion MRI file

-  **--target_dmri TARGET_DMRI**  
   Path to the 4D target diffusion MRI file

-  **--output_dir OUTPUT_DIR**  
   Directory for intermediate and output files

-  **--output_dmri OUTPUT_DMRI**  
   Filename for the registered diffusion MRI output

.. rubric:: References
Snoussi, H., Karimi, D., Afacan, O., Utkur, M. and Gholipour, A., 2025.  
*Haitch: A framework for distortion and motion correction in fetal multi-shell diffusion-weighted MRI.*  
Imaging Neuroscience.
