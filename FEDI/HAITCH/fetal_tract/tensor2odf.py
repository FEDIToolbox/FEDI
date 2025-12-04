import sys
import nibabel as nib
from dipy.data import get_sphere
import numpy as np
import dipy.reconst.shm as shm
from dipy.core.geometry import vector_norm


def from_lower_triangular(D):
    tensor_indices = np.array([[0, 3, 4], [3, 1, 5], [4, 5, 2]])
    return D[..., tensor_indices]


def evals_and_evecs_from_tensor(my_tensor):
    try:
        eigenvals, eigenvecs = np.linalg.eigh(my_tensor)
        order = eigenvals.argsort()[::-1]
        eigenvecs = eigenvecs[:, order]
        eigenvals = eigenvals[order]
    except:
        eigenvals = np.zeros(3)
        eigenvecs = np.zeros((3, 3))

    return eigenvals, eigenvecs


def md_from_tensor(my_tensor):
    try:
        eigenvals, eigenvecs = np.linalg.eigh(my_tensor)
        order = eigenvals.argsort()[::-1]
        eigenvals = eigenvals[order]

        ev1, ev2, ev3 = eigenvals
        md = np.abs((ev1 + ev2 + ev3) / 3) * 1000

        all_zero = (eigenvals == 0).all(axis=0)
        fa = np.sqrt(0.5 * ((ev1 - ev2) ** 2 +
                            (ev2 - ev3) ** 2 +
                            (ev3 - ev1) ** 2) /
                     ((eigenvals * eigenvals).sum(0) + all_zero))
    except:
        md = 0
        fa = 0

    return md, fa

def dk_sf_to_sh(sf, sphere, sh_order, basis_type, smooth=0.0):
    sph_harm_basis = shm.sph_harm_lookup.get(basis_type)
    if sph_harm_basis is None:
        raise ValueError("Invalid basis name.")
    B, m, n = sph_harm_basis(sh_order, sphere.theta, sphere.phi)

    L = -n * (n + 1)
    invB = shm.smooth_pinv(B, np.sqrt(smooth) * L)

    if sf.ndim > 2:
        ssx, ssy, ssz, ssn = sf.shape
        sf = np.reshape(sf, [ssx * ssy * ssz, ssn])
        sh = np.dot(sf, invB.T)
        _, ssn = sh.shape
        sh = np.reshape(sh, [ssx, ssy, ssz, ssn])
    else:
        sh = np.dot(sf, invB.T)

    return sh


def dtitk_2_fod(ten, mask, sphere="repulsion724"):
    sphere_odf = get_sphere(sphere)
    v_odf, _ = sphere_odf.vertices, sphere_odf.faces

    tensor = np.squeeze(ten) / 1000
    SX, SY, SZ, _ = tensor.shape

    ten_odf = np.zeros((SX, SY, SZ, len(v_odf)), np.float32)
    MD = np.zeros((SX, SY, SZ), np.float32)
    FA = np.zeros((SX, SY, SZ), np.float32)

    for ix in range(SX):
        for iy in range(SY):
            for iz in range(SZ):
                if mask[ix, iy, iz]:
                    wlls_params = tensor[ix, iy, iz, :]
                    temp = np.zeros(6)
                    temp[0] = wlls_params[0]
                    temp[1] = wlls_params[2]
                    temp[2] = wlls_params[5]
                    temp[3] = wlls_params[1]
                    temp[4] = wlls_params[3]
                    temp[5] = wlls_params[4]

                    wlls_tensor = from_lower_triangular(temp)
                    MD[ix, iy, iz], FA[ix, iy, iz] = md_from_tensor(wlls_tensor)

                    e_vals, e_vecs = evals_and_evecs_from_tensor(wlls_tensor)

                    lower = 4 * np.pi * np.sqrt(np.prod(e_vals[1:], -1))
                    projection = np.dot(v_odf, e_vecs)
                    projection /= np.sqrt(e_vals)
                    projection = ((vector_norm(projection) ** -3) / lower).T
                    projection *= (e_vals[0] / e_vals[1:].mean()) ** 2
                    ten_odf[ix, iy, iz, :] = projection

    return MD, FA, ten_odf


def compute_fod_sh(ten, sh_order=6, sphere="repulsion724"):
    # Compute mask
    mask = ten[:, :, :, 0, 0] > 0.1

    md, fa, fod = dtitk_2_fod(ten, mask, sphere)
    sphere_sh = get_sphere(sphere)
    fod_sh = dk_sf_to_sh(fod, sphere_sh, sh_order, "tournier07", smooth=0.0)

    for channel in range(fod_sh.shape[-1]):
        array = fod_sh[:, :, :, channel].copy()
        array_nz = array[array != 0]
        min_, max_ = np.percentile(array_nz, 0.10), np.percentile(array_nz, 99.90)
        array[array < min_] = min_
        array[array > max_] = max_
        fod_sh[:, :, :, channel] = array.copy()

    fod_sh *= 10
    return fod_sh

def main():
    file_name = sys.argv[1]
    
    # Loading data
    ten_img = nib.load(file_name)
    ten = ten_img.get_fdata()
    affine = ten_img.affine

    # Compute FOD SH
    fod_sh = compute_fod_sh(ten)

    # Save results
    fod_sh_img = nib.Nifti1Image(fod_sh, affine)
    nib.save(fod_sh_img, file_name.replace(".nii.gz", "_odf.nii.gz"))

if __name__ == "__main__":
    main()