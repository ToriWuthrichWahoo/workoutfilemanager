import os
from typing import Union

from rich.console import Console

from workoutfilemanager.WorkoutFile import WorkoutFile
from .WorkoutFitFile import WorkoutFitFile
from .WorkoutGpxFile import WorkoutGpxFile
from .WorkoutLogFile import WorkoutLogFile


class WorkoutFileManager:
    """A convenience class that manages the workouts that are being added."""

    def __init__(self):
        self.collection: list[WorkoutFile] = []
        self.console = Console()
        # self.visualizer = Visualizer()

    def add(self, file: str) -> None:
        """Add workout to collection.

        Parameters
        ----------
        file : str
            Workout file name.
        """
        try:
            if (workout := self._get_workoutfile(file)) is not None:
                workout.parse()
                self.collection.append(workout)
            else:
                msg = "Skipping file with unknown ending: {file}."
                msg += "\nEnding must be .fit, .gpx, or .txt."
                self.console.print(msg, style="orange")
        except Exception as e:
            pass
            print(e)

    def sort(self) -> None:
        """Sort workouts by first letter in filename."""

        def key(w):
            return w.basename.lower()

        self.collection = sorted(self.collection, key=key)

    def remove(self, file: str) -> None:
        """Remove workout from collection.

        Parameters
        ----------
        file : str
            Workout name to delete
        """
        self.collection = [w for w in self.collection if w.path != file]

    def getfilesrec(self, folder: str, ending: str = "") -> list[str]:
        """Get all files in a folder and all its subfolders, i.e. recursively.

        Parameters
        ----------
        folder : str
            Folder name to look for files in.
        ending : str, optional
            Select only files that end with this ending, by default ""

        Returns
        -------
        list[str]
            List of full paths to the matched files
        """
        matches: list[str] = []
        for path, subdirs, files in os.walk(folder):
            for f in files:
                if f.endswith(ending) or ending == "":
                    matches.append(os.path.join(path, f))
        return matches

    def _get_workoutfile(self, file: str) -> Union[None, WorkoutFile]:
        """Get the right workout class for a given file.

        Parameters
        ----------
        file : str
            File to get workout type for.

        Returns
        -------
        Union[None, WorkoutFile]
            Returns WorkoutFitFile if workout ends with .fit, WorkoutGpxFile
            if workout ends with ".gpx" and WorkoutNmeaFile if ends with
            ".txt". Otherwise returns None.
        """
        if file.lower().endswith(".fit"):
            return WorkoutFitFile(file)
        elif file.lower().endswith(".gpx"):
            return WorkoutGpxFile(file)
        elif file.lower().endswith(".txt"):
            return WorkoutLogFile(file)
        # elif file.lower().endswith(".txt.gz"):
        #  command = f"""unzip  -o -f {file} -d {file.strip(".gz")}"""
        #  print(command)
        #   try:
        #       subprocess.call(command)
        #   except Exception as e:
        #       print(e)
        #    try:
        #        return WorkoutNmeaFile(file.strip(".gz"))
        #    except Exception as e:
        #        print(e)
        #        return None
        return None
