from typing import Union

import numpy as np
import pandas as pd
from gpx_converter import Converter as GPXConverter

from .WorkoutFile import WorkoutFile


class WorkoutGpxFile(WorkoutFile):
    """Derived class to hold gpx workouts."""

    def __init__(self, path: str):
        super().__init__(path)

    def dataframe(self, *args, **kwargs) -> Union[None, pd.DataFrame]:
        return self.dfdict.get("gpx")

    def parse(self, rename_df_cols: bool = True, *args, **kwargs) -> None:
        df = GPXConverter(input_file=self.path).gpx_to_dataframe()
        self.dfdict["gpx"] = df
        if rename_df_cols:
            for key, df in self.dfdict.items():
                self._force_consistent_df_column_names(df)
                self.dfdict.update({key: df})

    def time(self, *args, **kwargs) -> np.ndarray:
        return self.idx(*args, **kwargs)
