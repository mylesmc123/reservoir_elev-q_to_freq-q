# We have Elevation and Storage USGS Data for Lake Lawtonka and Lake Ellsworth.
# We also have an Elevation Discharge Curve from the city
# we Need to create n elevation-storage and storage discharge curve for HMS 

# %%
import pandas as pd
from pydsstools.heclib.dss import HecDss
from pydsstools.core import PairedDataContainer, UNDEFINED

ElevStor_file_lawtonka = "Lawtonka_Elev-Stor_Curve.xlsx"
ElevStor_file_ellsworth = "Ellsworth_Elev-Stor_Curve.xlsx"

ElevQ_file = "LAKE DISCHARGE CALCULATOR.xlsx"

# %%
df_ElevStor_lawtonka = pd.read_excel(ElevStor_file_lawtonka)
df_ElevStor_ellsworth = pd.read_excel(ElevStor_file_ellsworth)

df_ElevQ_lawtonka = pd.read_excel(ElevQ_file, sheet_name="LAWTONKA DISCHARGE RATES")
df_ElevQ_ellsworth = pd.read_excel(ElevQ_file, sheet_name="ELLSWORTH DISCHARGE RATES")

# %%
df_ElevQ_ellsworth
# %%
# remove the first 12 rows
df_ElevQ_lawtonka = df_ElevQ_lawtonka.iloc[11:]
df_ElevQ_ellsworth = df_ElevQ_ellsworth.iloc[11:]
# set the first row as the header
df_ElevQ_lawtonka.columns = df_ElevQ_lawtonka.iloc[0]
# remove any columns after the 11th
df_ElevQ_lawtonka = df_ElevQ_lawtonka.iloc[:, :10]
df_ElevQ_ellsworth = df_ElevQ_ellsworth.iloc[:, :10]
# remove the first two rows
df_ElevQ_lawtonka = df_ElevQ_lawtonka.iloc[2:]
df_ElevQ_ellsworth = df_ElevQ_ellsworth.iloc[2:]
# drop all columns except the 2nd and the last column
df_ElevQ_lawtonka = df_ElevQ_lawtonka.iloc[:, [1, -1]]
df_ElevQ_ellsworth = df_ElevQ_ellsworth.iloc[:, [1, -1]]
# rename the columns to Elevation (ft NAVd88) and Q (CFS)
df_ElevQ_lawtonka.columns = ["Elevation (ft NAVD88)", "Q (CFS)"]
df_ElevQ_ellsworth.columns = ["Elevation (ft NAVD88)", "Q (CFS)"]

# %%
df_ElevQ_ellsworth
# %%
# now we need to clean up the elev-storage dataframes to remove any duplicates
df_ElevStor_lawtonka
# %%
# for any duplicate elevations, keep the first value and drop the rest
df_ElevStor_lawtonka = df_ElevStor_lawtonka.drop_duplicates(subset=["Elevation (ft)"], keep="first")
df_ElevStor_ellsworth = df_ElevStor_ellsworth.drop_duplicates(subset=["Elevation (ft)"], keep="first")
# remove any rows where the elevation is NaN
df_ElevStor_lawtonka = df_ElevStor_lawtonka.dropna(subset=["Elevation (ft)"])
df_ElevStor_ellsworth = df_ElevStor_ellsworth.dropna(subset=["Elevation (ft)"])

# test if the elevation is ascending
if not df_ElevStor_lawtonka["Elevation (ft)"].is_monotonic_increasing:
    print("Elevation (ft) in Lawtonka is not ascending")
if not df_ElevStor_ellsworth["Elevation (ft)"].is_monotonic_increasing:
    print("Elevation (ft) in Ellsworth is not ascending")
# test if the storage is ascending
if not df_ElevStor_lawtonka["Storage (ac-ft)"].is_monotonic_increasing:
    print("Storage (ac-ft) in Lawtonka is not ascending")
if not df_ElevStor_ellsworth["Storage (ac-ft)"].is_monotonic_increasing:
    print("Storage (ac-ft) in Ellsworth is not ascending")
# %%
df_ElevStor_lawtonka

# %%
# we need to extrapolate the elevation-storage curve to cover the full range of elevations in the discharge curve
# to do this lets use the slope of the last two points in the elevation-storage curve
slope_lawtonka = (df_ElevStor_lawtonka["Storage (ac-ft)"].iloc[-1] - df_ElevStor_lawtonka["Storage (ac-ft)"].iloc[-2]) / \
                 (df_ElevStor_lawtonka["Elevation (ft)"].iloc[-1] - df_ElevStor_lawtonka["Elevation (ft)"].iloc[-2])
slope_ellsworth = (df_ElevStor_ellsworth["Storage (ac-ft)"].iloc[-1] - df_ElevStor_ellsworth["Storage (ac-ft)"].iloc[-2]) / \
                 (df_ElevStor_ellsworth["Elevation (ft)"].iloc[-1] - df_ElevStor_ellsworth["Elevation (ft)"].iloc[-2])
# get the max elevation in the discharge curve
max_elev_lawtonka = df_ElevQ_lawtonka["Elevation (ft NAVD88)"].max()
max_elev_ellsworth = df_ElevQ_ellsworth["Elevation (ft NAVD88)"].max()

# %%

# extrapolate the elevation-storage curve to cover the full range of elevations in the discharge curve
def extrapolate_elev_storage(df, slope, max_elev):
    last_elev = df["Elevation (ft)"].iloc[-1]
    last_storage = df["Storage (ac-ft)"].iloc[-1]
    new_rows = []
    while last_elev < max_elev:
        last_elev += 0.1  # increment elevation by 0.1 ft
        last_storage += slope * 0.1  # calculate new storage using the slope
        new_rows.append({"Elevation (ft)": last_elev, "Storage (ac-ft)": last_storage})
    if new_rows:
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    return df
df_ElevStor_lawtonka = extrapolate_elev_storage(df_ElevStor_lawtonka, slope_lawtonka, max_elev_lawtonka)
df_ElevStor_ellsworth = extrapolate_elev_storage(df_ElevStor_ellsworth, slope_ellsworth, max_elev_ellsworth)

# %%
# plot the elevation-storage data for lawtonka
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 5))
plt.plot(df_ElevStor_lawtonka["Storage (ac-ft)"], df_ElevStor_lawtonka["Elevation (ft)"], label="Lake Lawtonka Storage-Elevation")
plt.title("Lake Lawtonka Storage-Elevation Curve")
plt.xlabel("Storage (acre-feet)")
plt.ylabel("Elevation (ft NAVD88)")
plt.legend()
plt.grid()
plt.show()

# %%
# plot the elevation-discharge data for lawtonka
plt.figure(figsize=(10, 5))
plt.plot(df_ElevQ_lawtonka["Q (CFS)"], df_ElevQ_lawtonka["Elevation (ft NAVD88)"], label="Lake Lawtonka Discharge-Elevation")
plt.title("Lake Lawtonka Discharge-Elevation Curve")
plt.xlabel("Discharge (cfs)")
plt.ylabel("Elevation (ft NAVD88)")
plt.legend()
plt.grid()
plt.show()
# %%
# plot the elevation-storage data for ellsworth
plt.figure(figsize=(10, 5))
plt.plot(df_ElevStor_ellsworth["Storage (ac-ft)"], df_ElevStor_ellsworth["Elevation (ft)"], label="Lake Ellsworth Storage-Elevation")
plt.title("Lake Ellsworth Storage-Elevation Curve")
plt.xlabel("Storage (acre-feet)")
plt.ylabel("Elevation (ft NAVD88)")
plt.legend()
plt.grid()
plt.show()

# %%
# plot the elevation-discharge data for ellsworth
plt.figure(figsize=(10, 5))
plt.plot(df_ElevQ_ellsworth["Q (CFS)"], df_ElevQ_ellsworth["Elevation (ft NAVD88)"], label="Lake Ellsworth Discharge-Elevation")
plt.title("Lake Ellsworth Discharge-Elevation Curve")
plt.xlabel("Discharge (cfs)")
plt.ylabel("Elevation (ft NAVD88)")
plt.legend()
plt.grid()
plt.show()
# %%
# now lets create the storage-discharge curve for both lakes
def create_storage_discharge_curve(elev_storage_df, elev_discharge_df):
    # create a list to hold the storage-discharge pairs
    storage_discharge_list = []
    
    # for each elevation in the elev_storage_df, find the corresponding discharge value in the elev_discharge_df
    for i, row in elev_storage_df.iterrows():
        elevation = row["Elevation (ft)"]
        storage = row["Storage (ac-ft)"]
        
        # find the closest elevation in the elev_discharge_df
        closest_elevation = elev_discharge_df["Elevation (ft NAVD88)"].iloc[
            (elev_discharge_df["Elevation (ft NAVD88)"] - elevation).abs().argsort()[:1]]
        
        # get the corresponding discharge value
        discharge_value = elev_discharge_df.loc[
            elev_discharge_df["Elevation (ft NAVD88)"] == closest_elevation.values[0], "Q (CFS)"].values[0]
        
        # append the storage and discharge values to the list
        storage_discharge_list.append({
            "Storage (ac-ft)": storage,
            "Q (CFS)": discharge_value
        })
    
    storage_discharge_df = pd.DataFrame(storage_discharge_list)
    return storage_discharge_df

# create the storage-discharge curve for lawtonka
storage_discharge_lawtonka = create_storage_discharge_curve(df_ElevStor_lawtonka, df_ElevQ_lawtonka)
# create the storage-discharge curve for ellsworth
storage_discharge_ellsworth = create_storage_discharge_curve(df_ElevStor_ellsworth, df_ElevQ_ellsworth)
# %%
# clean up the storage-discharge dataframes to remove any duplicates
storage_discharge_lawtonka = storage_discharge_lawtonka.drop_duplicates(subset=["Storage (ac-ft)"], keep="first")
storage_discharge_ellsworth = storage_discharge_ellsworth.drop_duplicates(subset=["Storage (ac-ft)"], keep="first")

# remove duplicates in the discharge column
storage_discharge_lawtonka = storage_discharge_lawtonka.drop_duplicates(subset=["Q (CFS)"], keep="first")
storage_discharge_ellsworth = storage_discharge_ellsworth.drop_duplicates(subset=["Q (CFS)"], keep="first")

# round the Q (CFS) values to 2 decimal places
storage_discharge_lawtonka["Q (CFS)"] = storage_discharge_lawtonka["Q (CFS)"].round(2)
storage_discharge_ellsworth["Q (CFS)"] = storage_discharge_ellsworth["Q (CFS)"].round(2)
# ensure the storage is ascending
if not storage_discharge_lawtonka["Storage (ac-ft)"].is_monotonic_increasing:
    print("Storage (ac-ft) in Lawtonka is not ascending")
if not storage_discharge_ellsworth["Storage (ac-ft)"].is_monotonic_increasing:
    print("Storage (ac-ft) in Ellsworth is not ascending")
# %%# plot the storage-discharge curve for lawtonka
plt.figure(figsize=(10, 5))
plt.plot(storage_discharge_lawtonka["Q (CFS)"], storage_discharge_lawtonka["Storage (ac-ft)"], label="Lake Lawtonka Storage-Discharge")
plt.title("Lake Lawtonka Storage-Discharge Curve")  
plt.xlabel("Discharge (cfs)")
plt.ylabel("Storage (acre-feet)")
plt.legend()
plt.grid() 
plt.show()
# %%# plot the storage-discharge curve for ellsworth
plt.figure(figsize=(10, 5))
plt.plot(storage_discharge_ellsworth["Q (CFS)"], storage_discharge_ellsworth["Storage (ac-ft)"], label="Lake Ellsworth Storage-Discharge")
plt.title("Lake Ellsworth Storage-Discharge Curve")
plt.xlabel("Discharge (cfs)")
plt.ylabel("Storage (acre-feet)")
plt.legend()
plt.grid()
plt.show()
# %%
# now lets save the elev-stor and the storage-discharge curves to csv files as paired data records
storage_discharge_lawtonka.to_csv("Lawtonka_Storage-Discharge_Curve.csv", index=False)
storage_discharge_ellsworth.to_csv("Ellsworth_Storage-Discharge_Curve.csv", index=False)
df_ElevStor_ellsworth.to_csv("Ellsworth_Elev-Stor_Curve.csv", index=False)
df_ElevStor_lawtonka.to_csv("Lawtonka_Elev-Stor_Curve.csv", index=False)

# %%
