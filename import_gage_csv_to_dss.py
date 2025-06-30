# Use pydsstools to import gage data from a CSV file into a DSS file.
# %%
import pandas as pd
from pydsstools.heclib.dss import HecDss
from pydsstools.core import TimeSeriesContainer, UNDEFINED

# open the csv file and read it into a pandas dataframe
df = pd.read_csv("07309500 - Lake Lawtonka near Lawton, OK.csv")

# %%
# drop columns except datetime and Gage height, feet
df = df[["datetime", "Gage height, feet"]]
df
# %%
# convert the datetime column to a pandas datetime object
df["datetime"] = pd.to_datetime(df["datetime"], format="%Y-%m-%d %H:%M:%S+00:00")
df
# %%
# write the dataframe to a DSS file
dss_file = "gages.dss"
# assume the dss file already exists
with HecDss.Open(dss_file) as dss:
    # create a TimeSeriesContainer object
    tsc = TimeSeriesContainer()
    tsc.pathname = "/Lake Lawtonka near Lawton, OK/07309500/ELEVATION/01Oct2007 - 18Jun2025/IR-CENTURY/USGS/"
    tsc.numberValues = len(df)
    tsc.times = df["datetime"].to_list()
    tsc.values = df["Gage height, feet"].to_list()
    tsc.units = "feet"
    tsc.type = "INST"
    tsc.interval = -1 # -1 indicates irregular time series
    
    # write the TimeSeriesContainer to the DSS file
    dss.put_ts(tsc)
# %%
