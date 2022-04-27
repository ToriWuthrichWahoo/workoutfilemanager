# %%
# The next two lines take care of auto-reloading modules that are included.
#! %load_ext autoreload
#! %autoreload 2
import sys

sys.path.insert(0, "../../")

# %% Example of how to run the workout file manager
from workoutfilemanager.WorkoutFileManager import WorkoutFileManager
manager = WorkoutFileManager()
data = manager.run("/Users/toriwuthrich/Documents/data/bolt/backup_ascent_descent_logs/20211002_TW_hilly_gravel_ride_test")

# %% Example of how to access data frames
data[0].print()
df = data[0].dataframe()
print(df)
