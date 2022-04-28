import pytest
import os
import pandas as pd
import numpy as np

from workoutfilemanager.WorkoutFileManager import WorkoutFileManager

basic_test_data = [
    ("20211002_TW_hilly_gravel_ride_fit"),  # fit file folder
    # ("20211002_TW_hilly_gravel_ride_log"),  # log file folder
    ("20211002_TW_hilly_gravel_ride_gpx"),  # gpx file folder
]


@pytest.mark.parametrize("data_folder", basic_test_data)
def test_basic_fit_parse(data_folder) -> None:
    """Make sure that parsing a file resuls in a non-empty dataframe."""
    manager = WorkoutFileManager()
    path = os.path.join(os.getcwd(), "dev/data/", data_folder)
    data = manager.run(path)
    if data is not None:
        df = data[0].dataframe()
        if df is not None:
            assert df.empty == False


accuracy_test_data = [
    ("20211002_TW_hilly_gravel_ride_fit", 43.7),  # fit file folder
    # (
    #     "20211002_TW_hilly_gravel_ride_log",
    #     43.65,
    # ),  # log file folder (note this number is different as we only use the first 1000 lines of the log file)
    ("20211002_TW_hilly_gravel_ride_gpx", 43.7),  # gpx file folder
]


@pytest.mark.parametrize("data_folder,mean_lat", accuracy_test_data)
def test_accurate_fit_parse(data_folder, mean_lat) -> None:
    """Make sure that we get valid data from the parsed file."""
    manager = WorkoutFileManager()
    path = os.path.join(os.getcwd(), "dev/data/", data_folder)
    data = manager.run(path)
    print(data_folder, data)

    df = data[0].dataframe()
    if df is not None:
        mean_lat_deg = np.mean(df["latitude"])
        # print(mean_lat_deg)
        # print(mean_lat)
        assert np.round(mean_lat_deg, 2) == mean_lat
