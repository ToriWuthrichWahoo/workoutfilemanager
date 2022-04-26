import os


class Paths:
    """
    A class that provides path(s) for necessary binaries.
    """

    def __init__(self):
        self._set_crFitToolPath()

    def _set_crFitToolPath(self) -> None:
        """Sets the path to the `crFitTool` binary.
        New user of this tool can just add a new entry to the `locations` list.
        """
        locations = [
            """/Users/thomascamminady/Projects/crux_common/tools/crFitTool/bin/crFitTool""",  # noqa: E501
            """/Users/toriwuthrich/dev/RNNR/crux_common/tools/crFitTool/bin/crFitTool""",  # noqa: E501
        ]
        for location in locations:
            if os.path.isfile(location):
                self.crFitToolPath = location
                return
