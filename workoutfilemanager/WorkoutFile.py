import os
from abc import ABC, abstractmethod
import pandas as pd
from rich.console import Console
from rich.table import Table
from matplotlib.pyplot import cm
import numpy as np
from typing import Union
import shutil


class WorkoutFile(ABC):
    """Abstract class that serves as a superclass for all possible workout
    types. Defines abstractmethods that need to be implemented by all derived
    classes.

    Parameters
    ----------
    ABC : _type_
        Abstract Metaclass
    """

    def __init__(self, path: str, *args, **kwargs) -> None:

        shutil.move(path, path.replace(" ", "__"))
        path = path.replace(" ", "__")

        self.path: str = path
        self.dirname: str = os.path.dirname(path)
        self.basename: str = os.path.basename(path)
        self.console = Console(highlight=False, style="grey58")
        self.dfdict: dict[str, pd.DataFrame] = {}

    def print(self) -> None:
        """Print information about workout."""
        self.console.print(f"path: {self.path}")
        self.console.print(f"dirname: {self.dirname}")
        self.console.print(f"basename: {self.basename}")

    @abstractmethod
    def dataframe(self, *args, **kwargs) -> Union[None, pd.DataFrame]:
        """Returns a dataframe that stores information for a workout. """
        pass

    @abstractmethod
    def parse(self, *args, **kwargs) -> None:
        """Parse a workout file."""
        pass

    @abstractmethod
    def time(self, *args, **kwargs) -> np.ndarray:
        """Return time data.

        Returns
        -------
        np.ndarray
            Numpy array that holds the time data.
        """
        pass

    @staticmethod
    def _printdf(
        df: pd.DataFrame,
        name: str = "",
        to_pager: bool = False,
    ) -> None:
        """Print dataframe in a nice way.

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe to print
        name : str, optional
            Title of plot, by default ""
        to_pager : bool, optional
            Whether or not to write to pager, by default False. Experimental.
        """
        table = Table(title=name)
        colors = iter(cm.tab10(np.linspace(0, 1, len(list(df)))))
        for column in list(df):
            c = next(colors)
            color = f"rgb({int(255*c[0])},{int(255*c[1])},{int(255*c[2])})"
            table.add_column(
                column,
                justify="right",
                style=color,
                header_style=color,
                no_wrap=True,
            )
        for _, row in df.iterrows():
            row_str = [str(v) for v in row.values]
            table.add_row(*row_str)

        console = Console()
        if to_pager:
            with console.pager():
                console.print(table)
        else:
            console.print(table)

    @staticmethod
    def _force_consistent_df_column_names(df: pd.DataFrame) -> None:
        """Make dataframe columns consistent

        Parameters
        ----------
        df : pd.DataFrame
            Dataframe to parse
        """
        # In the df, all the values of the dict should be replaced by the
        # respective key.
        _column_name_mappings = {
            "latitude": ["lat", "lat_deg"],
            "longitude": ["lon", "lon_deg"],
            "seconds": ["sec", "secs"],
            "altitude": ["alt_m"],
        }
        # Rename columns inplace for all key-value pairs in the dict.
        for new_name, old_names in _column_name_mappings.items():
            for old_name in old_names:
                df.rename(
                    columns={old_name: new_name}, inplace=True, errors="ignore"
                )  # Ignore if old_name not in df.

    def latitude(self, *args, **kwargs) -> np.ndarray:
        """Return latitude data.

        Returns
        -------
        np.ndarray
            Numpy array that holds the latitude data.
        """
        return self.get("latitude", *args, **kwargs)

    def longitude(self, *args, **kwargs) -> np.ndarray:
        """Return longitude data.

        Returns
        -------
        np.ndarray
            Numpy array that holds the longitude data.
        """
        return self.get("longitude", *args, **kwargs)

    def idx(self, *args, **kwargs) -> np.ndarray:
        """Return index data.

        Returns
        -------
        np.ndarray
            Numpy array that holds the index data.
        """

        tmp = self.latitude(*args, **kwargs)
        return np.arange(len(tmp), dtype=float)

    def hovertext(self, *args, **kwargs) -> list[str]:
        """Get a hover text for the plotly charts.

        Returns
        -------
        list[str]
            Text to be displayed at every datapoint when hovering over it.
        """
        n = self.basename
        return [
            f"<b>{n}</b><br>idx: {int(i)}<br>lon: {lo:+.4f}<br>lat: {la:+.4f}"
            for i, lo, la in zip(self.idx(), self.longitude(), self.latitude())
        ]

    def get(self, column: str, *args, **kwargs) -> np.ndarray:
        """Getter method to retrieve data from dataframe.

        Parameters
        ----------
        column : str
            Column name to get data from

        Returns
        -------
        np.ndarray
            Either the respective data when available or an empty array.
        """
        df = self.dataframe(*args, **kwargs)
        if df is not None:
            if column in list(df):
                return df[column].values
        return np.empty(0)

    def printdf(
        self,
        name: str,
        to_pager: bool = False,
        *args,
        **kwargs,
    ) -> None:
        """Exposed wrapper for `_printdf`

        Parameters
        ----------
        name : str
            Title for plotted dataframe
        to_pager : bool, optional
            Whether to write to pager, by default False. Experimental
        """
        df = self.dataframe(*args, **kwargs)
        if df is not None:
            self._printdf(df, name, to_pager)

    
