DOCUMENTATION FOR SENTINEL 1 PREPROCESSOR
04-03-2024

This script acquires converts, crops and denoises Sentinel-1 and -2

USER INPUTS
    While the script is designied to be run with a data range, shape file, directory SNAP xml and 
    crs, several other parameters can be adjusted in the userscript for which the script has
    default valus otherwise.

    REQUIRED INPUTS

    Working and output folders
        As this script will acquire data from CDSE, only a directory path for the files
        is needed, not the files themselves. This dir will then contain the SAFE files
        and the geotiffs being worked on.
        The output dir will then serve as a destination for the finished 7z file.

    Shape
        Shape must be a path to the .shp file of an unzipped shapedir or a zipped
        shapefile.

        Used for determining extent for product acquisition and clipping images down. 

    CRS
        Must be a string in EPSG:XXXXX format. Reverts to EPSG:4326 if invalid or 'None'
        Used to warp both shape and images.

    Date range
        A start and end date must be specified for the acquisition script. Any data
        availabe in that range over the shape file will be downloaded to the working dir

    Pre process g

    gpt_exe
        Defaults to 'C:/Users/b025527/AppData/Local/snap/bin/gpt.exe'
        Path to SNAPs gpt tool. Required for processing of SAFE files.

    OPTIONAL INPUTS

    Concurrency
        Defaults to 4
        Number of download threads from CDSE. Maximum is 4.

    Land sea mask
        Defaults to "shapes/landpolygon_1000.zip"
        Land sea mask shape file either zipped or unzipped. 
        Currently set to Denmark but can be any shape

    Max cloud pct
        Defaults to 40
        Defines maximum allowed cloud percent within shape value for Sentinel-2 images

    Polarization
        Defaults to [VV, VH]
        Polarizations for Sentinel-1. Either or both modes can be selected and a file will
        be made for either.

    Denoise mode
        Defaults to mean
        Selects which mode to densoise files.
        Mean will use a mean filter on a 3x3 window.
        SAR2SAR will use an ML based denoising method. Incompatible with sigma0.

