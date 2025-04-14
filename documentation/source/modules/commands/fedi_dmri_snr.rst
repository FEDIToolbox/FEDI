.. _fedi_dmri_snr:

fedi_dmri_snr
=============

.. rubric:: Synopsis
Compute the Signal-to-Noise Ratio (SNR) for diffusion MRI using the subtraction-based method described in Dietrich et al., JMRI 2007. Signal is estimated from the mean of two b=0 volumes and noise from their difference.

.. rubric:: Usage
::

    fedi_dmri_snr [-h] -d <file> -a <file> -m <file> [-b <file>]


.. rubric:: Description


This tool estimates the Signal-to-Noise Ratio (SNR) from two non-diffusion-weighted (b=0) volumes using the *difference method*,
as described in Dietrich et al., JMRI 2007.

The SNR is computed within the provided binary mask as:

.. math::

    \mathrm{SNR} = \frac{\mu\left(\frac{S_1 + S_2}{2}\right)}{\sigma\left(\frac{S_1 - S_2}{\sqrt{2}}\right)}

where :math:`S_1` and :math:`S_2` are the two b=0 volumes, :math:`\mu(\cdot)` denotes the mean signal, and :math:`\sigma(\cdot)` denotes the standard deviation of the noise within the mask.


This method assumes that the two b=0 volumes are acquired independently and without preprocessing-induced duplication.
It is appropriate when at least two distinct b=0 images are available.


.. rubric:: Options
**Help**

-  **-h, --help**  
   Show this help message and exit

**Mandatory**

-  **-d, --dmri <file>**  
   Input 4D dMRI NIfTI image (e.g., `dmri.nii.gz`)

-  **-a, --bval <file>**  
   Bvals file (e.g., `bvals.txt`)

-  **-m, --mask <file>**  
   Binary mask within which SNR will be averaged (e.g., `brain_mask.nii.gz`)


.. rubric:: References
- Dietrich, O., Heiland, S., Sartor, K., 2007.  
  *Measurement of signal-to-noise ratios in MR images: Influence of multichannel coils, parallel imaging, and reconstruction filters.*  
  Journal of Magnetic Resonance Imaging, 26(2), 375–385.

- Snoussi, H., Karimi, D., Afacan, O., Utkur, M. and Gholipour, A., 2025.  
  *Haitch: A framework for distortion and motion correction in fetal multi-shell diffusion-weighted MRI.*  
  Imaging Neuroscience.
