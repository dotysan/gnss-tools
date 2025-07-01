""" Application entry point for GNSS tools.

Contains GNSSApp, which orchestrates GNSS log collection
and plotting from command-line usage.
"""

# stdlib
from pathlib import Path

# pypi
import gps
from gps.client import dictwrapper

# local
from .logger import (
  HourlyLogWriter,
  load_logs,
)
from .plotting import (
  plot_heatmap,
)


class GNSSApp:
  """
  Main application object for GNSS skylog collection and plotting.
  """

  def __init__(self, logdir: str = 'skylogs', plotdir: str = 'heatmaps') -> None:
    """
    Initialize the GNSSApp.

    Args:
      logdir (Path): Root directory for hourly CSV logs.
      plotdir (Path): Directory to store heatmap PNGs.
    """
    self.logdir = Path(logdir)
    self.plotdir = Path(plotdir)
    self.logger = HourlyLogWriter(self.logdir)

  def collect(self) -> None:
    """
    Continuously read gpspipe JSON output, process SKY messages,
    and writes valid GNSS observations into hourly CSV logs.
    """
    session = gps.gps(
      mode=gps.WATCH_ENABLE | gps.WATCH_JSON,
      reconnect=True,
      verbose=1,  # change to 2 to see raw data
    )

    try:
      for msg in session:

        if isinstance(msg, dictwrapper):
          msg_class = msg.get('class')
          print(f"{msg_class}: {len(msg)} fields")
          if msg_class == 'SKY':
            self.process_sky(msg)
          elif msg_class == 'VERSION':
            print(f"GPSD version: {msg.get('release')}")
          elif msg_class == 'DEVICES':
            for device in msg.get('devices', []):  # type: ignore
              print(f"Device: {device.get('path')}, driver: {device.get('driver')}")
          elif msg_class == 'WATCH':
            print(f"Watch: {msg}")

        else:
          print(f"Received non-dict message: {msg}")
          print(session)
          continue

    except KeyboardInterrupt:
      print("Interrupted by user. Exiting.")

    finally:
      self.logger.close()

  def process_sky(self, msg: dictwrapper) -> None:
    """
    Processes a single SKY JSON message and logs healthy, used satellites.

    Args:
      msg (dict): Parsed SKY JSON message.
    """
    ts = msg.get('time')
    if not ts:
      print(f"ERROR missing timestamp in: {msg}")
      return

    valid_sats = []
    for sat in msg.get('satellites', []):  # type: ignore
      if sat.get('gnssid') == 1:  # skip SBAS
        continue
      if not sat.get('used'):
        continue
      if sat.get('health') != 1:
        continue
      valid_sats.append(sat)
    if valid_sats:
      self.logger.write_satellites(ts, valid_sats)

  def plot(self) -> None:
    """
    Loads all skylog CSV files and generates a polar heatmap
    showing GNSS signal-to-noise ratios.

    This method reads all logs from self.logdir and saves plots
    into self.plotdir.
    """
    df = load_logs(self.logdir)
    print(df.head())
    print(f"Loaded {len(df):,} rows.")

    plot_heatmap(df, self.plotdir)
