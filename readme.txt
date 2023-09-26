DOCUMENTATION FOR SENTINEL 1 PREPROCESSOR
31-08-2023

This script downloads, crops and denoises Sentinel-1 SAFE files.

The denoising component is an implementation of SAR2SAR
SAR2SAR: https://doi.org/10.1109/JSTARS.2021.3071864

USER INPUTS
    Date range

        The date range must be a tuple with a start and end date formatted in DDMMYYYY.
        The script will fail if not provided.

    Input and output folders

        Path to folders. If not present, will be created as 'input/' and 'output/'.
        Output folder will contain, unprocessed geotiffs and sorted denoised geotiffs

    Shape
        Shape must be a path to the .shp file of an unzipped shapedir.
        If 'None', entire product will be processed without clipping to shape.
        This will also skip product acquisition.

        Used for determining extent for product acquisition and clipping images down. 

    CRS
        Must be a string in EPSG:XXXXX format. Reverts to EPSG:4326 if invalid or 'None'
        Used to warp both shape and images.

    Polarization
        Polarization of the radar product. Must be either VV, VH, HV or HH.
        Can be either a single string or a list of strings, in any combination of the four.

        A geotiff will be created for each polarization specified, tagged in filename.

    Unit
        If 'decibel', the unti will be converted from the linar measurements provided by 
        Sentinel-1 to decibel using the formula 10*log10(x).
        Reverts to linear if not 'decibel'.

    Denoise mode
        If 'SAR2SAR', the denoising module will use a tensorflow based denoising method. 
        Otherwise a mean filter with a 3x3 pixel window will be applied.

MODULES
    The main script (flood_main) calls submodules from the flood_preprocessing script.
    These can diabled in the main script to skip unneeded steps.

    Acquisition
        The script will use the sentinelsat API to download data for date range and shape.
        If files are already present in input, these files will not be redownloaded.

        Acquisition requires a copernicus login (https://scihub.copernicus.eu/apihub), 
        provided either in the script itself or via a .netrc file in the root dir.
        See https://sentinelsat.readthedocs.io/en/stable/api_overview.html#authentication.
        If neither are present, script will fail.

        Module can be disabled if only data already present in input folder should be 
        processed

    SAFE to geotiff
        Module converts the SAFE file into one geotiff per polarization specified. 
        Along with tagging the filenames with the polarization, the orbital diraction'
        will also be tagged be either ASC or DSC.

    Warp to CRS 
        The geotiffs will be set to the CRS specified

        If disabled, the CRS og the SAFE files as provided (EPSG:4326) will be used

    Clip to shape
        The shape files will be warped to specified CRS and used to clip geotiffs to its extent.

        If disabled, the entire extent of the image will be denoised.

    Denoise and convert unit
        Module will use either SAR2SAR or mean filter to denoise, depending on specification.
        If 'decibel' is specified as unit, the default linear units will be converted.

        Unit can be skipped if no denoising is needed.

    Sort output
        Sorts denoised output into folder based on orbital direction and polarization.

        Can be skipped to leave all outputs in single directory.

OUTPUTS
    The designated output folder (or 'output/' if none designated) will contain both 
    the final and intermediate outputs.
    
    unprocessed_geotiffs
        This folder will contain georeferenced geotiffs cut to the input shape without denoising.
        These are used to recreate CRS after denoising.

    denoised_geotiffs
        Will contain denoised, georeferrenced and clipped geotiffs. Final destination if 
        'sort output' is not enabled. 

    sorted_denoised_geotiffs
        If 'sort output' is enabled, this folder will contain a number of subfolders in which 
        the denoised geotiffs are sorted by orbital direction and polarization.
