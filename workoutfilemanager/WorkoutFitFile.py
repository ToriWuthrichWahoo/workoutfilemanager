import os
import subprocess
from typing import Any, Dict, Generator, Union

import numpy as np
import pandas as pd

from .WorkoutFile import WorkoutFile
from workoutfilemanager.paths.Paths import Paths


class WorkoutFitFile(WorkoutFile):
    """Derived class to hold .fit file workouts"""

    def __init__(self, path: str):
        super().__init__(path)
        # paths = Paths()
        # self.crFitTool: str = paths.crFitToolPath
        self.crFit_output_files: list[str] = [
            "ant",
            "CLM_WORKOUT_CUSTOM_ALERT",
            "device_infos",
            "laps",
            "lengths",
            "records",
            "sessions",
            "srm_bike_profiles",
            "wahoo_custom_nums",
            "wahoo_pedal_monitor",
        ]
        self.csv_output_name = os.path.join(
            self.dirname, "." + self.basename.strip(".fit")
        )

    def print(self) -> None:
        super().print()
        self.console.print(f"""crFitTool: {self.pathfinder.get("crFitTool")}""")

    def dataframe(self, *args, **kwargs) -> Union[None, pd.DataFrame]:
        return self.dfdict.get("records")

    def time(self, *args, **kwargs) -> np.ndarray:
        return self.get("seconds", *args, **kwargs)

    def hovertext(self, *args, **kwargs) -> list[str]:
        superhovertext = super().hovertext(*args, **kwargs)
        return [
            info + f" <br>time: {t :.4f}"
            for t, info in zip(self.time(), superhovertext)
        ]

    def parse(
        self,
        mute: bool = True,
        remove_created_files: bool = False,
        remove_df_nan_cols: bool = True,
        rename_df_cols: bool = True,
        *args,
        **kwargs,
    ) -> None:

        self._run_crFitTool(mute)
        self._check_created_files_successfully()
        self._read_csvs_and_add_to_dict(remove_df_nan_cols)
        if remove_created_files:
            self._remove_created_files()
        if rename_df_cols:
            for key, df in self.dfdict.items():
                self._force_consistent_df_column_names(df)
                self.dfdict.update({key: df})

        self._fill_missing_with_nan()

    def _run_crFitTool(self, mute: bool) -> None:
        input = self.path
        # Output is the filename minus the .fit ending but with a dot in front
        # to hide the generated files.
        output = self.csv_output_name

        command = (
            f"""{self.pathfinder.get("crFitTool")} --in "{input}" --csv "{output}" """
        )
        kwargs = {"shell": True}  # type: Dict[str, Any]
        if mute:
            kwargs["stderr"] = subprocess.DEVNULL
            kwargs["stdout"] = subprocess.DEVNULL
        subprocess.call(command, **kwargs)

    def _csv_file_generator(self) -> Generator:
        for ending in self.crFit_output_files:
            file = self.csv_output_name + f".{ending}.csv"
            yield file, ending

    def _check_created_files_successfully(self) -> None:
        for file, _ in self._csv_file_generator():
            if not os.path.isfile(file):
                self.console.print(
                    f"Could not create file {file}",
                    style="bold red",
                    highlight=False,
                )

    def _read_csvs_and_add_to_dict(self, remove_df_nan_cols: bool) -> None:
        for file, ending in self._csv_file_generator():
            if os.path.isfile(file):
                df = pd.read_csv(file)
                if remove_df_nan_cols:
                    df.dropna(axis=1, how="all", inplace=True)
                if not df.empty:
                    self.dfdict[ending] = df

    def _fill_missing_with_nan(self) -> None:
        df = self.dataframe()
        if df is not None:
            df = (
                df.set_index("seconds")
                .reindex(
                    np.arange(df["seconds"].min(), df["seconds"].max() + 1),
                    fill_value=np.nan,
                )
                .reset_index()
            )
            self.dfdict["records"] = df

    def _remove_created_files(self) -> None:
        for file, _ in self._csv_file_generator():
            if os.path.isfile(file):
                os.remove(file)
