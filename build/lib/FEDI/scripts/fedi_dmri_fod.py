import argparse
import os
import numpy as np
import torch
import nibabel as nib
from collections import OrderedDict
from huggingface_hub import hf_hub_download
from FEDI.utils.common import FEDI_ArgumentParser
from FEDI.models.pytorch.sh import spherical_harmonic
from FEDI.models.pytorch.models import SphericalCNN_FOD_Neonatal

BATCH_SIZE = int(1e4)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "\033[1mDESCRIPTION:\033[0m \n\n    "
            "FOD estimation for neonatal data.\n"
        ),
        epilog=(
            "\033[1mREFERENCES:\033[0m\n  "
            "Snoussi, H. and Karimi, D., 2025. Equivariant Spherical CNNs for Accurate Fiber Orientation Distribution Estimation in Neonatal Diffusion MRI with Reduced Acquisition Time. arXiv preprint arXiv:2504.01925."
        ),
        formatter_class=FEDI_ArgumentParser
    )

    mandatory = parser.add_argument_group('\033[1mMANDATORY OPTIONS\033[0m')
    mandatory.add_argument("-d", "--dmri", required=True, help="Path to the input dMRI file.")
    mandatory.add_argument("-a", "--bval", required=True, help="Path to the bval file.")
    mandatory.add_argument("-e", "--bvec", required=True, help="Path to the bvec file.")
    mandatory.add_argument("-o", "--out", required=True, help="Output filename (NIfTI format).")
    parser.add_argument("-m", "--mask", required=False, help="Path to brain mask file.")

    return parser.parse_args()

def compute_sh_basis(bvecs, l_max=8):
    thetas = np.arccos(np.clip(bvecs[:, 2], -1.0, 1.0))
    phis = np.mod(np.arctan2(bvecs[:, 1], bvecs[:, 0]) + 2 * np.pi, 2 * np.pi)
    degrees = list(range(0, l_max + 1, 2))
    n_coeffs = sum(2 * l + 1 for l in degrees)
    basis = np.zeros((len(bvecs), n_coeffs), dtype=np.float32)

    idx = 0
    for l in degrees:
        for m in range(-l, l + 1):
            basis[:, idx] = spherical_harmonic(l, m, thetas, phis).numpy()
            idx += 1
    return basis

def main():
    args = parse_arguments()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dwi_data = nib.load(args.dmri).get_fdata()
    affine = nib.load(args.dmri).affine
    header = nib.load(args.dmri).header
    bvals = np.loadtxt(args.bval)[:dwi_data.shape[3]]
    bvecs = np.loadtxt(args.bvec)[:, :dwi_data.shape[3]].T

    if args.mask:
        mask = nib.load(args.mask).get_fdata().astype(bool)
        dwi_wm = dwi_data[mask]
    else:
        mask = None
        dwi_wm = dwi_data.reshape(-1, dwi_data.shape[3])

    n_voxels = dwi_wm.shape[0]
    sh_coeffs = np.zeros((n_voxels, 3, 45))
    shells = [400, 1000, 2600]
    shell_indices = {s: np.where(np.isclose(bvals, s, atol=50))[0] for s in shells}

    for shell_idx, shell in enumerate(shells):
        idx = shell_indices[shell]
        B = compute_sh_basis(bvecs[idx], l_max=8)
        S = dwi_wm[:, idx]
        C = np.linalg.lstsq(B, S.T, rcond=None)[0].T
        sh_coeffs[:, shell_idx, :] = C

    sh_tensor = torch.from_numpy(sh_coeffs).float().to(device)

    print("Downloading model from Hugging Face Hub...")
    model_path = hf_hub_download(
        repo_id="feditoolbox/scnn_neonatal_fod_estimation",
        filename="scnn_neonatal_fod_estimation.pth"
    )

    model = SphericalCNN_FOD_Neonatal(c_in=3, n_out=45).to(device)
    state_dict = torch.load(model_path, map_location=device)
    model.load_state_dict({k.replace("module.", ""): v for k, v in state_dict.items()})
    model.eval()

    fod = torch.zeros((n_voxels, 45), dtype=torch.float32, device=device)
    with torch.no_grad():
        for i in range(0, n_voxels, BATCH_SIZE):
            batch = sh_tensor[i:i + BATCH_SIZE]
            if batch.dim() == 2:
                batch = batch.unsqueeze(1)
            out = model(batch)
            fod[i:i + BATCH_SIZE] = out[:, :45]

    fod = fod.cpu().numpy()
    if mask is not None:
        full_shape = mask.shape + (45,)
        out_fod = np.zeros(full_shape, dtype=np.float32)
        out_fod[mask] = fod
    else:
        out_fod = fod.reshape(dwi_data.shape[:3] + (45,))

    nib.save(nib.Nifti1Image(out_fod, affine, header), args.out)
    print(f"FOD map saved: {args.out}")

if __name__ == "__main__":
    main()
