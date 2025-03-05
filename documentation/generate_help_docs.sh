#!/bin/bash


TOOLS=("fedi_dmri_moco" "fedi_dmri_reg" "fedi_dmri_recon" "fedi_apply_transform" "fedi_dmri_qweights" "fedi_dmri_rotate_bvecs" "fedi_dmri_outliers" "fedi_dmri_snr")

for tool in "${TOOLS[@]}"; do
    echo "${tool} - Command Help" > source/help_outputs/${tool}.txt
    echo "=================================" >> source/help_outputs/${tool}.txt
    echo "" >> source/help_outputs/${tool}.txt
    echo "**Usage:**" >> source/help_outputs/${tool}.txt
    echo "" >> source/help_outputs/${tool}.txt
    echo ".. code-block:: bash" >> source/help_outputs/${tool}.txt
    echo "" >> source/help_outputs/${tool}.txt
    ${tool} --help | sed 's/\x1B\[[0-9;]*m//g' >> source/help_outputs/${tool}.txt
    echo "" >> source/help_outputs/${tool}.txt
done
