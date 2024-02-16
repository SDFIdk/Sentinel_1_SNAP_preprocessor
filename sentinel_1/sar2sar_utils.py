import numpy as np
import tensorflow as tf
from PIL import Image
import scipy.ndimage
from scipy import special

# SAR2SAR: https://doi.org/10.1109/JSTARS.2021.3071864

# DEFINE PARAMETERS OF SPECKLE AND NORMALIZATION FACTOR
M = 10.089038980848645
m = -1.429329123112601
L = 1
c = (1 / 2) * (special.psi(L) - np.log(L))
cn = c / (M - m)  # normalized (0,1) mean of log speckle


def normalize_sar(im):
    return ((np.log(np.clip(im, 0.24, np.max(im))) - m) * 255 / (M - m)).astype(
        "float32"
    )

    # EXPERIMENTAL
    # return ((np.log(np.clip(im,0.24,np.max(im))) - m) * (M - m)).astype('float32')


def denormalize_sar(im):
    return np.exp((M - m) * (np.squeeze(im)).astype("float32") + m)


def load_sar_images(file):
    numpy_raster = np.load(file)
    numpy_raster = normalize_sar(
        numpy_raster[0, :, :]
    )  # hardcoded to assume data band is first
    return np.array(numpy_raster).reshape(
        1, np.size(numpy_raster, 0), np.size(numpy_raster, 1), 1
    )


def store_data_and_plot(im, threshold, filename):
    im = np.clip(im, 0, threshold)
    im = im / threshold * 255
    im = Image.fromarray(im.astype("float64")).convert("L")
    im.save(filename.replace("npy", "png"))


def save_sar_images(denoised, noisy, imagename, save_dir):
    # threshold = np.mean(noisy)+3*np.std(noisy)

    denoisedfilename = save_dir + imagename.replace(
        "\\", "/"
    )  # BUG had to insert that .replace for windows compatibility
    np.save(denoisedfilename, denoised)
    # store_data_and_plot(denoised, threshold, denoisedfilename)  #saves .pngs

    # noisy does not appear to be needed
    # noisyfilename = save_dir + "/noisy_numpys/" + imagename.replace('\\', '/')
    # np.save(noisyfilename, noisy)
    # store_data_and_plot(noisy, threshold, noisyfilename)
