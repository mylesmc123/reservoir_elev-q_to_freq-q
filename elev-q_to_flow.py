"""
This script is used to convert the Elevation data from USGS gages in the DSS format to Flow data using a Elevation-Discharge relationship.
"""
# %%
from pydsstools.heclib.dss import HecDss
from pydsstools.core import TimeSeriesContainer,UNDEFINED

# DSS Elevation data has been reieved for the following locations:
# Lake Lawtonka and Lake Ellsworth, upstream of lawton Oklahoma.
dss_file = "gages.dss"
excel_file = "LAKE DISCHARGE CALCULATOR.xlsx"

# %%
# List all paths in the DSS file
with HecDss.Open(dss_file) as dss:
    paths = dss.getPathnameList("*")
    # remove D-part by slicing the path. The D-part is at path.split("/")[4]
    before_D_paths = [path.split("/")[0:4] for path in paths]
    after_D_paths = [path.split("/")[5:] for path in paths]
    # join and add 2 forward slashes to the end of the before_D_paths to represent the blank dpart
    before_D_paths = ["/".join(path) + "//" for path in before_D_paths]
    # join the after_D_paths with a forward slash
    after_D_paths = ["/".join(path) for path in after_D_paths]
    # use list comprhension to join the before_D_paths and after_D_paths to create the full path
    noDpaths = [before + after for before, after in zip(before_D_paths, after_D_paths)]
    # for before, after in zip(before_D_paths, after_D_paths):
    #     print(before, after)
    # remove duplicates by converting to a set and back to a list
    noDpaths = list(set(noDpaths))

    for path in noDpaths:
        print(path)
    
    # lawtonka_path = "/Lake Lawtonka near Lawton, OK/07309500/ELEVATION//IR-CENTURY/USGS/"
    # ellsworth_path = "/Lake Ellsworth near Lawton, OK/07310000/STAGE//15Minute/USGS/"
    lawtonka_path = "/Lake Lawtonka near Lawton, OK/07309500/ELEVATION/01Oct2007 - 25Jun2025/IR-CENTURY/USGS/"
    ellsworth_path = "/Lake Ellsworth near Elgin, OK/07308990/ELEVATION/01Oct2007 - 18Jun2025/15Minute/USGS/"

    # # get the data for the two paths
    lawtonka_data = dss.read_ts(lawtonka_path)
    ellsworth_data = dss.read_ts(ellsworth_path)


# %%

# get times and values
import numpy as np
import pandas as pd
#  create a pandas dataframe using np.array(lawtonka_data.pytimes) & lawtonka_data.values
# has a noData value of -3.4028235e+38
lawtonka_df = pd.DataFrame({
    "time": np.array(lawtonka_data.pytimes),
    "value": lawtonka_data.values
})

ellsworth_df = pd.DataFrame({
    "time": np.array(ellsworth_data.pytimes),
    "value": ellsworth_data.values
})

# %%
# get the length of the dataframes
print(f"Lake Lawtonka data length: {len(lawtonka_df)}")
print(f"Lake Ellsworth data length: {len(ellsworth_df)}")

# %%
# remove noData values
lawtonka_df = lawtonka_df[lawtonka_df["value"] > -3.4e+38]
ellsworth_df = ellsworth_df[ellsworth_df["value"] > -3.4e+38]
# convert time to datetime
lawtonka_df["time"] = pd.to_datetime(lawtonka_df["time"], unit='s', utc=True)
ellsworth_df["time"] = pd.to_datetime(ellsworth_df["time"], unit='s', utc=True)
# # set time as index
lawtonka_df.set_index("time", inplace=True)
ellsworth_df.set_index("time", inplace=True)

lawtonka_df

# %%
# get the length of the dataframes again
print(f"Lake Lawtonka data length after removing noData values: {len(lawtonka_df)}")
print(f"Lake Ellsworth data length after removing noData values: {len(ellsworth_df)}")

print(f"\nBecause the data has missing values that have been removed, when writing to DSS, \
the data should be written as 'irregular' data,\nwhich means that the time intervals are not constant.")

# %%
# plot the data
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 5))
plt.plot(lawtonka_df.index, lawtonka_df["value"], label="Lake Lawtonka Elevation (NAVD88)")
plt.title("Lake Lawtonka Elevation (NAVD88)")
plt.xlabel("Time")
plt.ylabel("Elevation (ft NAVD88)")
plt.legend()
plt.grid()
plt.show()

# %%
# plot ellsworth data
plt.figure(figsize=(10, 5))
plt.plot(ellsworth_df.index, ellsworth_df["value"], label="Lake Ellsworth Elevation (NAVD88)")
plt.title("Lake Ellsworth Elevation (NAVD88)")
plt.xlabel("Time")
plt.ylabel("Elevation (ft NAVD88)")
plt.legend()
plt.grid()
plt.show()

#%%
# read the elevation-discharge relationships from a excel file

lawtonka_excel = pd.read_excel(excel_file, sheet_name="LAWTONKA DISCHARGE RATES")
ellsworth_excel = pd.read_excel(excel_file, sheet_name="ELLSWORTH DISCHARGE RATES")

# remove the first 12 rows
lawtonka_excel = lawtonka_excel.iloc[11:]
ellsworth_excel = ellsworth_excel.iloc[11:]
# set the first row as the header
lawtonka_excel.columns = lawtonka_excel.iloc[0]
# remove any columns after the 11th
lawtonka_excel = lawtonka_excel.iloc[:, :10]
ellsworth_excel = ellsworth_excel.iloc[:, :10]
# remove the first two rows
lawtonka_excel = lawtonka_excel.iloc[2:]
ellsworth_excel = ellsworth_excel.iloc[2:]
# drop all columns except the 2nd and the last column
lawtonka_excel = lawtonka_excel.iloc[:, [1, -1]]
ellsworth_excel = ellsworth_excel.iloc[:, [1, -1]]
# rename the columns to Elevation (ft NAVd88) and Q (CFS)
lawtonka_excel.columns = ["Elevation (ft NAVD88)", "Q (CFS)"]
ellsworth_excel.columns = ["Elevation (ft NAVD88)", "Q (CFS)"]

lawtonka_excel
# %%
ellsworth_excel

# %%
# for each elevation in the timeseries dataframes, 
# find the corresponding discharge value in the excel dataframe by looking for the closest elevation value
# and then use that value to create a new column named Flow (cfs) in the timeseries dataframe.
def get_flow_from_elevation(df, excel_df):
    # create a new column for flow
    df["Outflow (cfs)"] = np.nan
    for i, row in df.iterrows():
        elevation = row["value"]
        # find the closest elevation in the excel dataframe
        closest_elevation = excel_df["Elevation (ft NAVD88)"].iloc[(excel_df["Elevation (ft NAVD88)"] - elevation).abs().argsort()[:1]]
        # get the corresponding flow value
        flow_value = excel_df.loc[excel_df["Elevation (ft NAVD88)"] == closest_elevation.values[0], "Q (CFS)"].values[0]
        df.at[i, "Outflow (cfs)"] = flow_value
    return df

lawtonka_df = get_flow_from_elevation(lawtonka_df, lawtonka_excel)
ellsworth_df = get_flow_from_elevation(ellsworth_df, ellsworth_excel)

lawtonka_df
# %%
# plot the flow data for Lake Lawtonka
plt.figure(figsize=(10, 5))
plt.plot(lawtonka_df.index, lawtonka_df["Outflow (cfs)"], label="Lake Lawtonka Outlow (cfs)")
plt.title("Lake Lawtonka Flow (cfs)")
plt.xlabel("Time")
plt.ylabel("Outlow (cfs)")
plt.legend()
plt.grid()
plt.show()

# %%
# plot the flow data for Lake Ellsworth
plt.figure(figsize=(10, 5))
plt.plot(ellsworth_df.index, ellsworth_df["Outflow (cfs)"], label="Lake Ellsworth Outflow (cfs)")
plt.title("Lake Ellsworth Outflow (cfs)")
plt.xlabel("Time")
plt.ylabel("Outflow (cfs)")
plt.legend()
plt.grid()
plt.show()

# %%
lawtonka_df

# %%
# save the dataframes to dss
lawtonka_path_outflow = lawtonka_path.replace("ELEVATION", "RES FLOW-OUT")
# lawtonka_path_outflow = lawtonka_path_outflow.replace("15Minute", "IR-Month")
ellsworth_path_outflow = ellsworth_path.replace("ELEVATION", "RES FLOW-OUT")
ellsworth_path_outflow = ellsworth_path_outflow.replace("15Minute", "IR-CENTURY")

for (pathname, df) in zip([lawtonka_path_outflow, ellsworth_path_outflow], [lawtonka_df, ellsworth_df]):
    # convert the dataframe to a timeseries container
    tsc = TimeSeriesContainer()
    tsc.pathname = pathname
    tsc.startDateTime = df.index.min().strftime("%d%b%Y %H:%M:%S")
    tsc.numberValues = len(df)
    tsc.units = "cfs"
    tsc.type = "INST"
    tsc.interval = -1
    tsc.values = df["Outflow (cfs)"].values.tolist()
    tsc.times = df.index.to_pydatetime().tolist()  # list of datetime objects
    with HecDss.Open(dss_file) as fid:
        # delete the existing path if it exists
        fid.deletePathname(tsc.pathname)
        # print(f"Writing data to {pathname}...")
        # put the timeseries container into the dss file
        fid.put_ts(tsc)

# %%
# check the data types of the time column
print("Data type of the time column in Lake Lawtonka DataFrame:", lawtonka_df.index.dtype)
print("Data type of the time column in Lake Ellsworth DataFrame:", ellsworth_df.index.dtype)

# %%
