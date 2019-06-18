#!/usr/bin/env python
import xarray as xr
#from eofs.iris import Eof
from my_utils import calc_normalized_anomalies

from eofs.multivariate.standard import MultivariateEof


import matplotlib.pyplot as plt




# TODO:
# Add test data
# Comments and tests for anomaly calculation
# Create AnalogMethod class:
#   - prepare method with anomalie calculation function as argument (e.g from utils calc_normalized_anomalies)
#   - loop in new classMethod
#   - EOF loop for explained variance

#           --------------------------------------------
# ----------------------------------------------------------------
#                     VALIDATION SETTINGS
# ----------------------------------------------------------------
#           --------------------------------------------

# "era", "ncep" or "jra"
rea_selection = "ncep"

# TODO maybe choose variable combination for validation later in this dict
rea_info = {
    "era": {'path':'../data/ERA5/*',
            'vars':['r', 'q']},
    "ncep": {'path':'./Test/*',
            'vars':['slp', 'rhum', 'shum']},
    "jra": {'path':'../data/JRA55/*/*.nc',
            'vars':['PRMSL_GDS0_MSL', 'RH_GDS0_ISBL', 'SPFH_GDS0_ISBL']},
}


# Usefull for debugging
# .sel(lat=48, lon=16, method="nearest").plot()

#           --------------------------------------------
# ----------------------------------------------------------------
#                        MAIN TERRITORY
# ----------------------------------------------------------------
#           --------------------------------------------

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
ds_rea_roll = ds_rea.rolling(time=21, center=True).construct('window_dim')

# Loop over dayofyear   ---------------------------------------------------------------------------------------------------------
for _, ds_doy in ds_rea_roll.groupby("time.dayofyear"):

    #Für jeden tag EOFs berechnen
    #Dazu von xarray zu iris gehen
    #Dann multivariate EOFs berechnen
    ds_doy = ds_doy.rename({"time":"time_old"})
    #ds_test = ds_test.stack(time=('time_old', 'window_dim')).transpose('time_eof', 'lat', 'lon', 'nbnds')
    ds_doy = ds_doy.stack(time=('time_old', 'window_dim')).transpose('time', 'lat', 'lon')
    # Add attribute axis for EOF package to find new time dimension
    ds_doy.coords['time'].attrs['axis'] = 'T'

    # Rename time dimension to avoid conflict if pcs are computed

    # Create an EOF solver to do the EOF analysis. Square-root of cosine of
    # latitude weights are applied before the computation of EOFs.
    # coslat = np.cos(np.deg2rad(z_djf.coords['latitude'].values)).clip(0., 1.)
    # wgts = np.sqrt(coslat)[..., np.newaxis]
    #solver = Eof(ds_test.pres.dropna('time'))

    #print(ds_test)
        
    SLP = ds_doy.slp.dropna('time').values
    RHUM = ds_doy.rhum.dropna('time').values
    SHUM = ds_doy.shum.dropna('time').values
    
    msolver = MultivariateEof([SLP, RHUM, SHUM])
    eofs_slp, eofs_rhum, eofs_shum = msolver.eofs(neofs=5)

    pcs = msolver.pcs(npcs=5)
    
    eigenvalues = msolver.eigenvalues(neigs=5)
    
    D=0
    
    pseudo_pcs = msolver.projectField([SLP[D,:,:], RHUM[D,:,:], SHUM[D,:,:]],neofs=5)
    
    variance_fraction = msolver.varianceFraction(neigs=5)
    
    total_variance = msolver.totalAnomalyVariance()

    field = pseudo_pcs[0]*eofs_slp[0]+pseudo_pcs[1]*eofs_slp[1]+pseudo_pcs[2]*eofs_slp[2]+pseudo_pcs[3]*eofs_slp[3]+pseudo_pcs[4]*eofs_slp[4]
    
    
    #--------------- Plotting of EOFs ---------------------------------
    fig, ax = plt.subplots(figsize=(10, 10))
    im = ax.imshow(field, interpolation='nearest')
    fig.colorbar(im, shrink=0.8)
    #fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax)
    plt.show()
    

    break
