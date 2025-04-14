.. _fedi_dmri_qweights:

fedi_dmri_qweights
==================

.. rubric:: Synopsis
Process diffusion MRI scheme and generate Siemens scanner compatible output.

.. rubric:: Usage
::

    fedi_dmri_qweights [-h] -i <file> -o <file> -b <int> [<int> ...] -d <file>
                       [--interspersed] [-n <int>] [--b0_at_beginning] [--b0_at_end]

.. rubric:: Options
**Help**

-  **-h, --help**  
   Show this help message and exit

**Mandatory**

-  **-i, --unitary_scheme <file>**  
   Path to the input scheme file from http://www.emmanuelcaruyer.com/q-space-sampling.php  
   containing unitary directions and b-values (e.g., `Sample.txt`)

-  **-o, --siemens_scheme <file>**  
   Output file where directions will be saved in Siemens scanner format (`*.dvs`)

-  **-b, --bvalues <int> [<int> ...]**  
   List of b-values corresponding to each shell in the input scheme (e.g., `1000 2000 3000`)

-  **-d, --debug_file <file>**  
   Path to a debug file where detailed info about directions and weights will be logged

**Optional**

-  **--interspersed**  
   Intersperse b=0 volumes among the directions (default: False)

-  **-n, --num_b0_volumes <int>**  
   Number of b=0 volumes to include (only if `--interspersed` is used)

-  **--b0_at_beginning**  
   Include a b=0 volume at the beginning of the acquisition

-  **--b0_at_end**  
   Include a b=0 volume at the end of the acquisition

.. rubric:: References
Snoussi, H., Karimi, D., Afacan, O., Utkur, M. and Gholipour, A., 2025.  
*Haitch: A framework for distortion and motion correction in fetal multi-shell diffusion-weighted MRI.*  
Imaging Neuroscience.

