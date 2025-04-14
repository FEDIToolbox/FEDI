import nibabel as nib
import numpy as np
import argparse
from scipy.ndimage import binary_erosion
from FEDI.utils.common import FEDI_ArgumentParser, Metavar


def compute_snr_diff_method(dmri_file, bval_file, mask_file, b0_threshold=50):
    print(f"Loading dMRI: {dmri_file}")
    img = nib.load(dmri_file)
    data = img.get_fdata()
    print(f"dMRI shape: {data.shape}")

    print(f"Loading bvals: {bval_file}")
    bvals = np.loadtxt(bval_file)
    print(f"bvals shape: {bvals.shape}, unique: {np.unique(bvals)}")

    print(f"Loading mask: {mask_file}")
    mask_img = nib.load(mask_file)
    mask = binary_erosion(mask_img.get_fdata().astype(bool), iterations=1)
    print(f"Mask shape: {mask.shape}, num True voxels: {np.sum(mask)}")

    b0_indices = np.where(bvals <= b0_threshold)[0]
    print(f"b=0 indices: {b0_indices}")
    if len(b0_indices) < 2:
        raise ValueError("At least two b=0 volumes are required for SNR estimation.")

    vol1 = data[..., b0_indices[0]]
    vol2 = data[..., b0_indices[1]]
    print(f"vol1/2 shape: {vol1.shape}, dtype: {vol1.dtype}")

    mean_img = (vol1 + vol2) / 2.0
    diff_img = (vol1 - vol2) / np.sqrt(2)

    mean_vals = mean_img[mask]
    noise_vals = diff_img[mask]
    print(f"mean_vals.shape: {mean_vals.shape}, noise_vals.shape: {noise_vals.shape}")
    print(f"mean_vals stats -> mean: {mean_vals.mean()}, std: {mean_vals.std()}")
    print(f"noise_vals stats -> mean: {noise_vals.mean()}, std: {noise_vals.std()}")

    if mean_vals.size == 0 or noise_vals.size == 0:
        raise ValueError("No valid voxels found within mask.")

    signal = np.mean(mean_vals)
    noise_std = np.std(noise_vals, ddof=1)
    print(f"Signal (mean of mean_vals): {signal}")
    print(f"Noise std (std of diff_img): {noise_std}")

    snr = signal / (noise_std + 1e-8)
    print(f"Final SNR = {snr}")
    return np.round(snr, 1), 0.0





def main():
    parser = argparse.ArgumentParser(
        description=(
            "\033[1mDESCRIPTION:\033[0m\n\n    "
            "Compute the Signal-to-Noise Ratio (SNR) for diffusion MRI using the subtraction-based method described in Dietrich et al., JMRI 2007. "
            "Signal is estimated from the mean of two b=0 volumes and noise from their difference."
        ),
        epilog=(
            "\033[1mREFERENCES:\033[0m\n  "
            "Dietrich, O., et al. Measurement of signal-to-noise ratios in MR images. JMRI 2007."
        ),
        formatter_class=FEDI_ArgumentParser
    )

    mandatory = parser.add_argument_group('\033[1mMANDATORY OPTIONS\033[0m')
    mandatory.add_argument('-d', '--dmri', required=True, metavar=Metavar.file, help='4D dMRI file')
    mandatory.add_argument('-a', '--bval', required=True, metavar=Metavar.file, help='bval file')
    mandatory.add_argument('-m', '--mask', required=True, metavar=Metavar.file, help='Binary mask file')

    args = parser.parse_args()

    try:
        snr_mean, snr_std = compute_snr_diff_method(args.dmri, args.bval, args.mask)
        print(f"SNR = {snr_mean} ± {snr_std}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
