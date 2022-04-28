from typing import Union

import numpy as np
import pandas as pd
from pynmeagps import NMEAReader
import re
import os
from datetime import datetime
import pdb

from .WorkoutFile import WorkoutFile

ISOFORMAT = "ISO-8859-1"


class WorkoutLogFile(WorkoutFile):
    """Derived class to hold nmea data."""

    def __init__(self, path: str):
        super().__init__(path)

    def dataframe(self, *args, **kwargs) -> Union[None, pd.DataFrame]:
        return self.dfdict.get("nmea")

    def time(self, *args, **kwargs) -> np.ndarray:
        return self.idx(*args, **kwargs)

    def get_log_file_year(self) -> str:
        if "BoltApp.WO" in os.path.basename(self.path):
            year_str = os.path.basename(self.path).split("-", 1)[1][:4]
        else:
            year_str = str(datetime.now().year)
            print("Warning: could not auto-detect year")
        return year_str

    def parse(self, rename_df_cols: bool = True, *args, **kwargs) -> None:
        
        file = open(self.path, encoding=ISOFORMAT)
        
        # Parse logs, including: NMEA messages, barometer data, autopauses, workout start & end, temperature, and location messages
        df_nmea = self.parse_nmea()
        df_barometer = self.parse_barometer()
        df_autopause = self.parse_autopause()
        df_workout = self.parse_workout()
        df_temp = self.parse_temperature()
        df_location = self.parse_location_change()
        df_psvlf = self.parse_psvlf()

        df = pd.concat(
            [
                df_nmea,
                df_barometer,
                df_autopause,
                df_workout,
                df_temp,
                df_location,
                df_psvlf,
            ]
        )
        df.lat = pd.to_numeric(df.lat_summary)
        df.lon = pd.to_numeric(df.lon_summary)
        self.dfdict["nmea"] = df

        # df["lat"] = np.where(df["lat_dir"] == "S", -df["lat"], df["lat"])
        # df["lon"] = np.where(df["lon_dir"] == "E", -df["lon"], df["lon"])

        if rename_df_cols:
            for key, df in self.dfdict.items():
                self._force_consistent_df_column_names(df)
                self.dfdict.update({key: df})

    def parse_nmea(self) -> pd.DataFrame:
        """Parse NMEA messages. Add a "from_nmea" field, and set to 'false' to indicate that these messages do NOT come from NMEA logs."""
        file = open(self.path, encoding=ISOFORMAT)
        parsed_lines = []
        data = {}
        for _, line in enumerate(file.readlines()):
            if "$" in line:
                content = "$" + line.split("$")[-1]
                try:
                    # msg = pynmea2.parse(content)
                    # data = dict(zip(msg.name_to_idx.keys(), msg.data))
                    reTime = "(\d\d)-(\d\d)\s+(\d\d):(\d\d):(\d\d).(\d\d\d)"
                    timeMatch = re.findall(reTime, line)[0]
                    year_str = self.get_log_file_year()
                    timestamp = self._match_to_timestamp(year_str, timeMatch)

                    msg = NMEAReader.parse(content)

                    if msg.identity == "GPGGA":
                        data = {
                            "timestamp": timestamp,
                            "EW_GGA": msg.EW,
                            "NS_GGA": msg.NS,
                            "HDOP_GGA": msg.HDOP,
                            "lat": msg.lat,
                            "lon": msg.lon,
                            "numSV_GGA": msg.numSV,
                            "identity_GGA": msg.identity,
                            "alt_GGA": msg.alt,
                            "msgID_GGA": msg.msgID,
                            "payload_GGA": msg.payload,
                            "quality_GGA": msg.quality,
                        }
                    elif msg.identity == "GNGSA":
                        data = {"timestamp": timestamp, "navMode_GSA": msg.navMode}
                    elif msg.identity == "GNRMC":
                        data = {
                            "timestamp": timestamp,
                            "speed_RMC": msg.spd
                            * 0.51444,  # Message speed is in knots. 1 kt = 0.5144 m/s
                            "status_RMC": msg.status,
                            "navStatus_RMC": msg.navStatus,
                        }
                    elif msg.identity == "GNGLL":
                        status = 1
                        if msg.status == "A":
                            status = 1
                        elif msg.status == "V":
                            status = 0
                        else:
                            print("PROBLEM WITH GNGLL STATUS")

                        data = {"timestamp": timestamp, "status_GLL": status}
                    else:
                        continue

                    try:
                        # data["sentence_type"] = msg.sentence_type
                        data["sentence_type"] = msg.identity
                    except Exception:
                        data["sentence_type"] = "NA"
                    parsed_lines.append(data)
                except Exception:
                    continue
        return pd.DataFrame(parsed_lines)

    def parse_barometer(self) -> pd.DataFrame:
        """Parse the barometer data - includes pressure, standard elevation, and calibrated elevation."""
        # Example barometer data string:
        # 02-21 12:49:33.986  1421  1421 V BaromHelper: [2] notifyPressureData PressureCapabilityData [pressureNpM2=102745 stdElevM=-119 calibElevM=32.96028405738108]

        fId = open(self.path)
        lines = fId.read()
        reBarometer = "(\d\d)-(\d\d)\s+(\d\d):(\d\d):(\d\d).(\d\d\d)\s+\d+\s+\d+.*?BaromHelper:\s+\[([0-9]+)\]\s+.*?pressureNpM2=([0-9]+)\s+stdElevM=(-?[0-9]+)\s+calibElevM=(.*?)]"

        matches = re.findall(reBarometer, lines)
        year_str = self.get_log_file_year()
        timestamps = [self._match_to_timestamp(year_str, m) for m in matches]
        pressure = [m[7] for m in matches]
        std_elevation = [m[8] for m in matches]
        calib_elevation = [m[9] for m in matches]

        data = {
            "timestamp": timestamps,
            "pressure": pressure,
            "std_elevation": std_elevation,
            "calib_elevation": calib_elevation,
        }

        return pd.DataFrame(data)

    def parse_autopause(self) -> pd.DataFrame:
        # Example autopause data string:
        # 02-21 12:55:15.273  1421  1421 D StdAutoPauseManagerV1: [2] [2] setMoving changed from true to false
        """Parse the autopause data. Outputs a struct of "moving" states
        indicated by booleans, for each time the moving state changes"""

        fId = open(self.path)
        lines = fId.read()
        reAutoPause = "(\d\d)-(\d\d)\s+(\d\d):(\d\d):(\d\d).(\d\d\d)\s+\d+\s+\d+.*?StdAutoPauseManager.*?setMoving changed from (\S+) to (\S+)"

        matches = re.findall(reAutoPause, lines)
        year_str = self.get_log_file_year()

        prev_valid_state = -1
        moving = []
        timestamps = []

        # Loop through matches. State could be 'null', and we want to ignore lines where
        # that is the case. We only care about transitions from True -> False and vice versa.
        for match in matches:
            temp_state = match[7]
            if temp_state != "null" and temp_state != prev_valid_state:
                timestamp = self._match_to_timestamp(year_str, match)

                moving.append(temp_state.lower() == "true")
                timestamps.append(timestamp)
                prev_valid_state = temp_state

        data = {"timestamp": timestamps, "moving": moving}
        return pd.DataFrame(data)

    def parse_workout(self) -> pd.DataFrame:
        """Parse workout start and end time information"""
        # Example workout start string:
        # 02-04 09:39:31.899  1375  1375 I StdSessionManager: [2] [2] startWorkout
        # Example workout end string:
        # 02-21 13:05:29.829  1421  1421 I StdSessionWorkout-ELEMNT BOLT 981E:115: [2] liveEndWorkout 1645466729830 full=true
        fId = open(self.path)
        lines = fId.read()
        reStartWorkout = "(\d\d)-(\d\d)\s+(\d\d):(\d\d):(\d\d).(\d\d\d)\s+\d+\s+\d+.*?\s\S\sStdSessionManager:\s\[\d\]\s\[\d\] startWorkout"
        reEndWorkout = "(\d\d)-(\d\d)\s+(\d\d):(\d\d):(\d\d).(\d\d\d)\s+\d+\s+\d+\s+\S\sStdSessionWorkout.*?\[\d\]\s+liveEndWorkout\s+\d+\s+.*"

        startMatches = re.findall(reStartWorkout, lines)
        endMatches = re.findall(reEndWorkout, lines)
        year_str = self.get_log_file_year()

        startTime = []
        endTime = []

        if startMatches:
            startTime = [self._match_to_timestamp(year_str, startMatches[0])]
        if endMatches:
            endTime = [self._match_to_timestamp(year_str, endMatches[0])]

        data = {"start": startTime, "end": endTime}
        return pd.DataFrame(data)

    def parse_temperature(self) -> pd.DataFrame:
        """Parse temperature data in degrees Celcius"""
        # Example temperature string:
        # 2-21 12:49:33.823  1421  1421 V TempHelper: [2] notifyTemperatureData TemperatureCapabilityData [Temperature [degC=11.630000114440918]]

        fId = open(self.path)
        lines = fId.read()
        reTemp = "(\d\d)-(\d\d)\s+(\d\d):(\d\d):(\d\d).(\d\d\d)\s+\d+\s+\d+\s+\S\sTempHelper:\s+\[\d\]\s+notifyTemperatureData\s+TemperatureCapabilityData\s+\[Temperature\s+\[degC=(.*?)]]"

        matches = re.findall(reTemp, lines)
        year_str = self.get_log_file_year()

        timestamps = [self._match_to_timestamp(year_str, m) for m in matches]
        temps = [m[6] for m in matches]

        data = {"timestamp": timestamps, "temperature": temps}
        return pd.DataFrame(data)

    def parse_location_change(self) -> pd.DataFrame:
        """Parse log onLocationChanged messages. Includes lat/lon, altitude, horizontal GPS accuracy, bearing, gps speed, and number of satellites.
        Add a "from_nmea" field, and set to 'false' to indicate that these messages do NOT come from NMEA logs."""
        # Example location change string:
        # 02-21 12:49:36.389  1421  1421 V GPSDevice: [2] onLocationChanged 493306632 loc=41.547325,-70.988937 alt=11.10 horAcc=6.60 bearing=210.90 gpsSpeed=2.83 sats=12
        fId = open(self.path)
        lines = fId.read()
        reLocationChange = "(\d\d)-(\d\d)\s+(\d\d):(\d\d):(\d\d).(\d\d\d)\s+\d+\s+\d+\s+\S\s+GPSDevice:\s+\[\d\]\s+onLocationChanged\s+(\S+)\s+loc=(-?[0-9]\d*\.\d+),(-?[0-9]\d*\.\d+)\s+alt=(-?[0-9]\d*\.\d+)\s+horAcc=(-?[0-9]\d*\.\d+)\s+bearing=(-?[0-9]\d*\.\d+)\s+gpsSpeed=(-?[0-9]\d*\.\d+)\ssats=(\d+)"

        matches = re.findall(reLocationChange, lines)
        year_str = self.get_log_file_year()

        timestamps = [self._match_to_timestamp(year_str, m) for m in matches]
        lat = [m[7] for m in matches]
        lon = [m[8] for m in matches]
        alt = [m[9] for m in matches]
        horzAcc = [m[10] for m in matches]
        heading = [m[11] for m in matches]
        speed = [m[12] for m in matches]
        sats = [m[13] for m in matches]

        data = {
            "timestamp": timestamps,
            "lat_summary": lat,
            "lon_summary": lon,
            "alt_summary": alt,
            "HDOP_summary": horzAcc,
            "heading_summary": heading,
            "speed_summary": speed,
            "numSV_summary": sats,
        }

        return pd.DataFrame(data)

    def parse_psvlf(self) -> pd.DataFrame:
        # Example location change string:
        # 02-04 09:39:22.949  1386  1386 V GPSDevice: [2] onNmeaMessage 1643963962 $PSVLF,1.16,0.65,242.1,-0.57,-0.30,0.96*61
        fId = open(self.path)
        lines = fId.read()
        rePSVLF = "(\d\d)-(\d\d)\s+(\d\d):(\d\d):(\d\d).(\d\d\d)\s+\d+\s+\d+\s+\S+\s+GPSDevice:\s+\[\d\]\s+onNmeaMessage\s+\d+\s+\$PSVLF,([-+]?\d+\.\d+),([-+]?\d+\.\d+),([-+]?\d+\.\d+),([-+]?\d+\.\d+),([-+]?\d+\.\d+),([-+]?\d+\.\d+)\S+"

        matches = re.findall(rePSVLF, lines)
        year_str = self.get_log_file_year()
        timestamps = [self._match_to_timestamp(year_str, m) for m in matches]

        parse_matches = lambda idx: [float(match[idx]) / 3.6 for match in matches]

        velocity_3d = parse_matches(6)
        velocity_2d = parse_matches(7)
        velocity_heading = parse_matches(8)
        velocity_east = parse_matches(9)
        velocity_north = parse_matches(10)
        velocity_up = parse_matches(11)

        data = {
            "timestamp": timestamps,
            "velocity_VLF_3d": velocity_3d,
            "speed_VLF": velocity_2d,
            "heading": velocity_heading,
            "velocity_east": velocity_east,
            "velocity_north": velocity_north,
            "velocity_up": velocity_up,
        }

        return pd.DataFrame(data)

    def _match_to_timestamp(self, year: str, timeMatch: str) -> str:
        """Convert a regular expression match from the log file into a timestamp in format YYYY-mm-ddTHH:MM:ss.SSSZ

        Parameters
        ----------
        year : str
            String representing the year
        timeMatch : str
            Regular expression timestamp match

        Returns
        -------
        str
            Timestamp string
        """
        return (
            year
            + "-"
            + timeMatch[0]
            + "-"
            + timeMatch[1]
            + "T"
            + timeMatch[2]
            + ":"
            + timeMatch[3]
            + ":"
            + timeMatch[4]
            + "."
            + timeMatch[5]
            + "Z"
        )
