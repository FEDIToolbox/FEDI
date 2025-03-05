fedi_dmri_qweights - Command Help
=================================

**Usage:**

.. code-block:: bash


     Fetal and Neonatal Development Imaging - FEDI Toolbox


USAGE: 

    fedi_dmri_qweights [-h] -i <file> -o <file> -b <int>
                                         [<int> ...] -d <file>
                                         [--interspersed] [-n <int>]
                                         [--b0_at_beginning] [--b0_at_end]

DESCRIPTION: 

    Process diffusion MRI scheme and generate Siemens scanner compatible output.

HELP:
  -h, --help            show this help message and exit

MANDATORY OPTIONS:
  -i, --unitary_scheme <file>
                        Path to the input scheme file from http://www.emmanuelcaruyer.com/q-space-sampling.php containing unitary directions and b-values. Example: Sample.txt
  -o, --siemens_scheme <file>
                        Path to the output file where directions will be saved in Siemens scanner format (*.dvs).
  -b, --bvalues <int> [<int> ...]
                        List of b-values corresponding to each shell in the input scheme (e.g., 1000 2000 3000).
  -d, --debug_file <file>
                        Path to the debug file where detailed information about the directions and weights will be logged.

OPTINAL OPTIONS:
  --interspersed        Specify whether to intersperse b-value=0 volumes among the directions (default: False).
  -n, --num_b0_volumes <int>
                        Number of b-value=0 volumes to include, if --interspersed was chosen.
  --b0_at_beginning     Include b-value=0 volume at the beginning of the acquisition.
  --b0_at_end           Include b-value=0 volume at the end of the acquisition.

REFERENCES:
  Snoussi, H., Karimi, D., Afacan, O., Utkur, M. and Gholipour, A., 2024. Haitch: A framework for distortion and motion correction in fetal multi-shell diffusion-weighted MRI. arXiv preprint arXiv:2406.20042.

