# -*- coding: utf-8 -*-
"""
Created on Wed May 15 09:23:01 2019

@author: thoma
"""
import sys

import xarray as xr

#Currently not working with SLP files from 2010 - 2018; rHum files from 2000 - 2018; sHum files from 2010 - 2018
#AttributeError: 'DataArray' object has no attribute 'lat'

class EOF:
    def __init__(self, datapath):
        
        #Define lat/lon subset
        lat_boundaries = slice(67.5, 32.5)
        lon_boundaries = slice(10, 25)
        
        #read .nc files
        self.datapath = datapath
        self.ds = xr.open_mfdataset(self.datapath, chunks={'time': 500}).sel(lat=lat_boundaries).sel(lon=lon_boundaries)
        
        #read all available variables
        self.vars = list(self.ds.data_vars)
        for var in self.vars:
            if var != 'time_bnds':
                print(var)
                self.ds[var]
                
                #for the variables on vertical levels we need to squeeze this dimension
                if var == 'rhum' or var == 'shum':
                    self.ds[var] = self.ds[var].squeeze(dim='level')
        
        
    def rolling_window_mean(self,window_size=21):
        
        self.rw_mean = {}

        #for every variable        
        for i, var in enumerate(self.vars):
            #Calculate mean for every rolling window.
            self.rw_mean[var] = self.ds[var].rolling(time=window_size, center=True).mean()

            #remove leap days
            #self.rw_mean[var] = self.rw_mean[var].sel(time=~((self.rw_mean[var].time.dt.month == 2) & (self.rw_mean[var].time.dt.day == 29)))
            
            #rearrange Dataset by day of year. Calc mean for days of year
            self.rw_mean[var] = self.rw_mean[var].dropna('time').groupby('time.dayofyear').mean('time')
            
            #remove leap days
            #self.rw_mean[var] = self.rw_mean[var].drop([60], dim='dayofyear')
            
            if self.rw_mean[var].shape != (366, self.ds[var].lat.shape[0] ,self.ds[var].lon.shape[0]):
                sys.exit("Dimension of rw_mean not correct: EXIT")
        
    def rolling_window_std(self,window_size=21):
        self.rw_std = {}
        
        #for every variable        
        for i, var in enumerate(self.vars):
            #Calc std: (1) cunstruct rolling dataset (2) remove NaN (3) sort by day of year (4) calculate std
            self.rw_std[var] = self.ds[var].rolling(time=window_size, center=True).construct('rolling_dim').dropna('time').groupby('time.dayofyear').std(dim=xr.ALL_DIMS)
            
            #remove leap days
            #self.rw_std[var] = self.rw_std[var].drop([60], dim='dayofyear')
            
            if self.rw_std[var].shape[0] != (366):
                sys.exit("Dimension of rw_std not correct: EXIT")
    
    
    def get_anomaly(self):
        #calculate mean values
        self.rolling_window_mean()
        #calculate standard deviation
        self.rolling_window_std()
        
        self.anomaly = {}
        
        #for every variable        
        for i, var in enumerate(self.vars):
            
            #calculate anomalies: values - means
            anomaly_unnormalized = self.ds[var].groupby('time.dayofyear') - self.rw_mean[var]

            #Norm anomalies with std
            self.anomaly[var] = anomaly_unnormalized.groupby('time.dayofyear') / self.rw_std[var]

        
        
        
        
EOF("./*.nc").get_anomaly()
            
#EOF("./SLP/slp.194*.nc").get_anomaly()