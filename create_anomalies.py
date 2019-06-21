#!/usr/bin/env python
import xarray as xr
#from eofs.iris import Eof
from my_utils import calc_normalized_anomalies

from eofs.multivariate.standard import MultivariateEof


import matplotlib.pyplot as plt


# "era", "ncep" or "jra"
rea_selection = "ncep"

# TODO maybe choose variable combination for validation later in this dict
rea_info = {
    "era": {'path':'../data/ERA5/*',
            'vars':['r', 'q']},
    "ncep": {'path':'./NCEP/*/*',
            'vars':['slp', 'rhum', 'shum']},
    "jra": {'path':'../data/JRA55/*/*.nc',
            'vars':['PRMSL_GDS0_MSL', 'RH_GDS0_ISBL', 'SPFH_GDS0_ISBL']},
}


try:
    ds_rea = xr.open_mfdataset(rea_info[rea_selection]['path'], decode_cf=True)
except KeyError:
    print("Choose a valid reanalysis from these options: {}".format(', '.join(rea_info.keys())))
    raise
except:
    print("Unexpected error")
    raise

# Prepare NCEP1 -------------------------------------------------------------------------------------
if rea_selection == 'ncep':
    #ds_rea = xr.open_mfdataset("../data/NCEP1/slp.*", decode_cf=True)
    # Rotate longitude to be able to use slice (0 - 360  ->  -180 - 180)
    ds_rea.coords['lon'].data = (ds_rea.coords['lon'] + 180) % 360 - 180
    ds_rea = ds_rea.sortby(ds_rea.lon)
    ds_rea = ds_rea.sel(lon=slice(-10, 25), lat=slice(67.5, 32.5))
    
    #remove unused voordinate level    
    ds_rea['rhum'] = ds_rea['rhum'].squeeze(dim='level')
    ds_rea['shum'] = ds_rea['shum'].squeeze(dim='level')
    ds_rea = ds_rea.drop('level')
    
    #In some later files there is a variable time_bnds. Needs to be removed!!
    try:
        ds_rea = ds_rea.drop('time_bnds')
    except:
        pass


# Prepare ERA   -------------------------------------------------------------------------------------
if rea_selection == 'era':
    #ds_rea = xr.open_mfdataset("../data/ERA5/*", decode_cf=True).chunk({'time':-1})
    ds_rea = ds_rea.rename({'latitude': 'lat', 'longitude': 'lon'})
    pass

# Prepare JRA-55  -----------------------------------------------------------------------------------
if rea_selection == 'jra':
    #ds_rea = xr.open_mfdataset(rea_info[rea_selection]['path'], decode_cf=True)
    ds_rea = ds_rea.rename({'initial_time0_hours': 'time',
                            'g0_lat_1': 'lat',
                            'g0_lon_2': 'lon'}).drop(['initial_time0_encoded','initial_time0'])

    # Rotate longitude to be able to use slice (0 - 360  ->  -180 - 180)
    ds_rea.coords['lon'].data = (ds_rea.coords['lon'] + 180) % 360 - 180
    ds_rea = ds_rea.sortby(ds_rea.lon)


# Calculate normalized anomalies and construct rolled dimension
ds_rea = calc_normalized_anomalies(ds_rea)

print(ds_rea)

ds_rea.to_netcdf(path="normalized_animaliies_NCEP.nc")
