# I have two csv files from SSP output for a each Lawton lake for a bulletin17c using inflow data
# each files contains the UH timeseries for the frequency events
# lets convert these to a DSS file

# %%
import pandas as pd
from pydsstools.heclib.dss import HecDss
from pydsstools.core import TimeSeriesContainer, UNDEFINED
import os

# %%
lawtonka_uh_file = r"C:\Users\MBMcManus\OneDrive - Garver\Documents\Work\Lawton\SSP\B17c_Lawtonka_Inflow.xlsx"
ellsworth_uh_file = r"C:\Users\MBMcManus\OneDrive - Garver\Documents\Work\Lawton\SSP\B17c_Ellsworth_Inflow.xlsx"

df_lawtonka = pd.read_excel(lawtonka_uh_file, sheet_name="UH")
df_ellsworth = pd.read_excel(ellsworth_uh_file, sheet_name="UH")

# drop after the 3rd column
df_lawtonka = df_lawtonka.iloc[:, :3]
df_ellsworth = df_ellsworth.iloc[:, :3]

df_lawtonka
# %%
# in a single DSS file for all lakes and years, 
# for each unique Return Year, create UH timeseries and put it in the DSS file
dss_file = "lake_inflow_frequency_events.dss"
# create the list of times starting at 01JAN2000 00:00 for 14 days, adding zeros after the first 24 values
times = pd.date_range(start="01JAN2000 00:00", periods=24*14, freq="H").tolist()
# %%
with HecDss.Open(dss_file) as dss:
    for year in df_lawtonka["Return Year"].unique():
        # filter the dataframe for the current year
        lawtonka_year_df = df_lawtonka[df_lawtonka["Return Year"] == year]
        ellsworth_year_df = df_ellsworth[df_ellsworth["Return Year"] == year]

        # create the values list for each lake, add zeros the end of the Q (cfs) values 
        # until the length matches the times list
        lawtonka_values = lawtonka_year_df["Q (cfs)"].to_list()
        lawtonka_values.extend([0] * (len(times) - len(lawtonka_values)))

        ellsworth_values = ellsworth_year_df["Q (cfs)"].to_list()
        ellsworth_values.extend([0] * (len(times) - len(ellsworth_values)))

        # create a TimeSeriesContainer for Lawtonka
        tsc_lawtonka = TimeSeriesContainer()
        tsc_lawtonka.startDateTime = "01JAN2000 00:00:00"  # start time for the time series
        tsc_lawtonka.pathname = f"/Lake Lawtonka near Lawton, OK/07309500/RES FLOW-IN//1HOUR/SSP {year}yr/"
        tsc_lawtonka.numberValues = len(times)
        # tsc_lawtonka.times = times
        tsc_lawtonka.values = lawtonka_values
        tsc_lawtonka.units = "cfs"
        tsc_lawtonka.type = "INST"
        tsc_lawtonka.interval = 1  # irregular time series

        # delete the pathname if it exists
        dss.deletePathname(tsc_lawtonka.pathname)
        # write the TimeSeriesContainer to the DSS file
        dss.put_ts(tsc_lawtonka)

        # create a TimeSeriesContainer for Ellsworth
        tsc_ellsworth = TimeSeriesContainer()
        tsc_ellsworth.pathname = f"/Lake Ellsworth near Elgin, OK/07308990/RES FLOW-IN//1HOUR/SSP {year}yr//"
        tsc_ellsworth.numberValues = len(times)
        tsc_ellsworth.startDateTime = "01JAN2000 00:00:00"
        # tsc_ellsworth.times = ellsworth_year_df["Time"].to_list()
        tsc_ellsworth.values = ellsworth_values
        tsc_ellsworth.units = "cfs"
        tsc_ellsworth.type = "INST"
        tsc_ellsworth.interval = 1

        # delete the pathname if it exists
        dss.deletePathname(tsc_ellsworth.pathname)
        # write the TimeSeriesContainer to the DSS file
        dss.put_ts(tsc_ellsworth)
# %%
