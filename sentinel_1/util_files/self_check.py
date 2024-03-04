def self_check(self, crs, polarization, denoise_mode):
    # maybe this entire section shouldnt be here
    assert denoise_mode in [
        "SAR2SAR",
        "mean",
    ], f"## {denoise_mode} must match SAR2SAR or mean"
    assert Utils.is_valid_epsg(crs.replace("EPSG:", "")), "## CRS is not valid"
    assert polarization != None, (
        "## Polarization cannot be none"
        "## Polarization must be either VV, VH, HV or HH"
    )
    if not isinstance(polarization, list):
        polarization = [polarization]
    for pol in polarization:
        assert pol in [
            "VV",
            "VH",
            "HV",
            "HH",
        ], "## Polarization must be either VV, VH, HV or HH"
    return
