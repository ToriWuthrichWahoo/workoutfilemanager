# %%
# The next two lines take care of auto-reloading modules that are included.
#! %load_ext autoreload
#! %autoreload 2
import sys

sys.path.insert(0, "../../")

# %%
from workoutfilemanager.WorkoutFileManager import WorkoutFileManager
manager = WorkoutFileManager()
manager.add("/Users/toriwuthrich/Documents/data/bolt/backup_ascent_descent_logs/20211002_TW_hilly_gravel_ride/2021-10-02-144309-ELEMNT_BOLT_981E-29-0.fit")

