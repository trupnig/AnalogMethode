#!/usr/bin/env python

"""utils.py: Utility methods for AnalogMethod"""

__author__ = "Georg Seyerl"
__copyright__ = "Copyright 2019"
__license__ = "MIT"
__maintainer__ = "Georg Seyerl"
__email__ = "g.seyerl@posteo.net"
__status__ = "Development"

import xarray as xr
import pandas as pd

def calc_normalized_anomalies(ds_prep, window_size=21):
    """
    This method prepares the input Dataset. It calculates the normalized anomalies with means
    and std calculated with a centered window of size window_size
    """

    # Resample with mean over data if temporal resolution is higher than daily (Lower resolution not supported here)
    if pd.infer_freq(ds_prep.time.data) not in 'D':
        ds_prep = ds_prep.resample(time='1D').mean()
        ds_prep = ds_prep.chunk({'time':-1})

    # calculates the climatology and the standard deviation for further anomaly calculation
    ds_prep_roll = ds_prep.rolling(time=window_size, center=True).construct('window_dim') # creates the rolling window as a new dimension

    # calculate climatology (dayofyear mean) for rolling window over Target Day ± 10days (pool)
    # IMPORTANT DIFFERENCE:
    # mean rolling window before meaning time: all windows where at least one timestep is missing are dropped
    # ds_prep_clim_alt = ds_prep.rolling(time=window_size, center=True).mean().groupby('time.dayofyear').mean('time')

    # mean after construct with dropna: same as above (all windows, where at least one timestep is missing are dropped)
    # ds_prep_clim = ds_prep_roll.dropna('time').groupby('time.dayofyear').mean(dim=['window_dim','time'])

    # mean after construct without dropna: first and last windows are considered, even if there are timesteps with missing values
    ds_prep_clim = ds_prep_roll.groupby('time.dayofyear').mean(dim=['window_dim','time'])

    # calculate standard deviation (dayofyear std) for rolling window over Target Day ± 10days (pool)
    ds_prep_std = ds_prep_roll.groupby('time.dayofyear').std(dim=xr.ALL_DIMS) # Calculates the std for dayofyear of TD + pool, shape(365,)

    # calculate daily normalized anomalies with mean and std from TD + pool
    ds_prep = ds_prep.groupby('time.dayofyear') - ds_prep_clim
    ds_prep = ds_prep.groupby('time.dayofyear') / ds_prep_std

    # Rechunking necessary after groupby
    ds_prep = ds_prep.chunk({'time': -1})

    return ds_prep
