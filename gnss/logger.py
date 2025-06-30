"""
Handles GNSS data logging to hourly CSV files, and loading logs for analysis.
"""

# stdlib
import csv
from datetime import (
  datetime,
  timezone,
)
from pathlib import Path

# pypi
import pandas as pd

# local
from .utils import GNSSID_NAMES


class HourlyLogWriter:
  """
  Handles writing GNSS satellite observations into hourly rotated CSV logs.
  """

  def __init__(self, logdir: Path) -> None:
    """ Initialize the HourlyLogWriter.

    Args:
      logdir (Path): Root directory for log storage.
    """
    self.logdir = logdir
    self.current_hour = None
    self.file = None
    self.writer = None

  def _open_new_file(self, dt: datetime) -> None:
    """ Close any existing file and open a new one for the new hour.

    Args:
      dt (datetime): The UTC datetime to determine the log file name.
    """
    if self.file:
      self.file.close()

    path = self.get_hour_path(dt)
    is_new = not path.exists()

    self.file = open(path, 'a')
    self.writer = csv.writer(self.file, lineterminator="\n")

    if is_new:
      self.writer.writerow(['time', 'GNSS', 'SVID', 'PRN', 'el', 'az', 'ss'])

  def close(self) -> None:
    """ Close the current log file if open. """
    if self.file:
      self.file.close()
      self.file = None

  def get_hour_path(self, dt: datetime) -> Path:
    """ Return the hourly CSV path for UTC datetime dt.

    Args:
      dt (datetime): UTC datetime.

    Returns:
      Path: Path to the CSV file for the given hour.
    """
    folder = self.logdir / dt.strftime("%Y-%m/%Y-%m-%d")
    folder.mkdir(parents=True, exist_ok=True)
    filename = dt.strftime("%Y-%m-%dT%H.csv")
    return folder / filename

  def write_satellites(self, ts_iso: str, sats: list[dict]) -> None:
    """ Write a batch of satellite observations in one go.

    Args:
      ts_iso (str): ISO timestamp string for determining file rotation.
      sats (list of dict): Satellite observation dictionaries.
    """
    self.rotate_if_needed(ts_iso)

    rows = []
    for sat in sats:
      # print(f"DEBUG: {sat}")
      gnssid = sat.get('gnssid')
      gnss_name = GNSSID_NAMES.get(gnssid, gnssid)
      row = [ts_iso,
             gnss_name, sat.get('svid'), sat.get('PRN'),
             sat.get('el'), sat.get('az'), sat.get('ss')]
      # print(row)
      rows.append(row)
    self.writer.writerows(rows)
    self.file.flush()

  def rotate_if_needed(self, ts_iso: str) -> None:
    """
    Check timestamp and rotate file if new hour has started.

    Args:
      ts_iso (str): ISO timestamp string.
    """
    # parse e.g. "2025-06-28T17:52:03.000Z"
    dt = datetime.strptime(ts_iso[:19], "%Y-%m-%dT%H:%M:%S")
    dt = dt.replace(tzinfo=timezone.utc)

    hour_str = dt.strftime("%Y-%m-%dT%H")
    if hour_str != self.current_hour:
      self._open_new_file(dt)
      self.current_hour = hour_str

# ----------------------------------------------------------------------

def load_logs(logdir: Path) -> pd.DataFrame:
  """ Load all CSV logs into a single DataFrame.

  Args:
    logdir (Path): Directory containing CSV logs.

  Returns:
    pd.DataFrame: Combined DataFrame from all logs.
  """
  files = list(logdir.rglob("*.csv"))
  if not files:
    raise FileNotFoundError("No CSV files found!")
  # print(files)

  dfs = []
  for f in files:
    df = pd.read_csv(f)
    dfs.append(df)

  return pd.concat(dfs, ignore_index=True)
