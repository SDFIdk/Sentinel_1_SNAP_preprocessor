def main(threads = 1, netcdf_dir = None, geotiff_dir = None, polarization = None, dataset_name = None, denoise_mode = None):
    Tool.threads = threads

    NetCDFToGeoTiff(
        input_dir = netcdf_dir,
        output_dir = geotiff_dir,
        polarization = polarization
    ).run()

    RemoveEmptyGeoTiff(
        input_dir = geotiff_dir
    ).run()

    ChangeResolution(
        input_dir = geotiff_dir,
        x_size = 10,
        y_size = 10
    ).run()

    AlignRaster(
        input_dir = geotiff_dir
    ).run()

    SortOutput(
        input_dir = geotiff_dir,
        output_dir = f'{dataset_name}_{denoise_mode}_denoised_geotiffs_decibel_10m/',
        polarization = polarization
    ).run()


if __name__ == '__main__':
    main()
