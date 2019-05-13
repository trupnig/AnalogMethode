#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 12 16:15:47 2019

@author: thomas
"""
import iris
import numpy as np
from datetime import datetime, timedelta

def lat_boundaries(cell):
    """Return True for values between boundaries"""
    return cell >= 32.5 and cell <= 67.5

def lon_boundaries(cell):
    """Return True for values between boundaries"""
    return cell >= 10 and cell <= 25

#def filter_leap_day(cell):
    

filename = './NCEP_Dayli_Averages/SLP/SLP_01012009-31122018.nc'
cubes = iris.load(filename)


SLP = cubes[0]

#Check if there are full years!!!

#---------- Create a Subset ----------------------------

SLP_subset = SLP.extract(iris.Constraint(latitude=lat_boundaries, longitude=lon_boundaries))

#--------- calculate Anomalies -------------------------

#Calculate Mean values for every Day with rolling window.

#must be odd
window_size = 11

#create a NaN list to fill missing values at beginn and end of list
y = np.zeros(int((window_size-1)/2))
y[:] = np.nan

#get index of 29th of Feb days. Better way?
index=[]
c = 0
for cell in SLP_subset.coord('time').cells():
    if str(cell)[5:10] == "02-29":
        index.append(c)
    
    c+=1
      

#For every gridpoint

  

for lat in range(SLP_subset.coord('latitude').shape[0]):
    for lon in range(SLP_subset.coord('longitude').shape[0]):
        
        gridpoint = SLP_subset[:,lat,lon].data

        #create rolling window
        gp_rw = iris.util.rolling_window(gridpoint, window_size)
    
        #calculate mean of windows
        gp_rw_mean = np.mean(gp_rw,axis=1)    
        
        #Add missing values to beginn and end of list
        gp_rw_mean = np.insert(gp_rw_mean,0,y)
        gp_rw_mean = np.insert(gp_rw_mean,len(gp_rw_mean),y)
        
        #Remove Leap Days
        gp_rw_mean = np.delete(gp_rw_mean, index)
        
        gridpoint = np.delete(gridpoint, index)
    
        #calc mean for years (Only working if we have full years)
        gp_mean = np.nanmean(gp_rw_mean.reshape(-1, 365),axis=0)
        
        new_gp_mean = gp_mean
        for i in range(int(len(gp_rw_mean)/len(gp_mean)-1)):
            new_gp_mean = np.concatenate((new_gp_mean,gp_mean))
            
        anomalie = gridpoint - new_gp_mean
        
#calculate mean value over all years.
        
        
#Remove 29.02!!

#Windowbreite = 10. Ds Bedeutet, wir starten bei tag 6 und enden bei tag 15 von 20
#n/2 am anfang und n/2 am ende fehlen






#-------------- Normalize anomalies ---------------------