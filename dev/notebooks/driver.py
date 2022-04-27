# %%
# The next two lines take care of auto-reloading modules that are included.
#! %load_ext autoreload
#! %autoreload 2
import sys
import os

sys.path.insert(0, "../../")

# %% Example of how to run the workout file manager
from workoutfilemanager.WorkoutFileManager import WorkoutFileManager
manager = WorkoutFileManager()
path = os.path.join(os.getcwd(), "dev/data/20211002_TW_hilly_gravel_ride_fit")
data = manager.run(path)

# %% Example of how to access data frames
data[0].print()
df = data[0].dataframe()
print(df)
