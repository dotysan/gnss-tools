# stdlib
from datetime import (
  datetime,
  timedelta,
)
from pathlib import Path

# pypi
from gps.client import dictwrapper
import pytest

# local
from gnss.app import GNSSApp
from gnss.logger import (
  HourlyLogWriter,
  load_logs,
)


def test_load_logs_no_files(tmp_path: Path):
  """
  load_logs() should raise FileNotFoundError
  if no CSV files exist in the log directory.
  """
  with pytest.raises(FileNotFoundError):
    load_logs(tmp_path)


def test_process_sky_missing_timestamp(capsys: pytest.CaptureFixture, tmp_path: Path) -> None:
  """
  GNSSApp.process_sky should print an error if the SKY message
  has no timestamp field.
  """
  app = GNSSApp(logdir=str(tmp_path))
  msg = dictwrapper({'class': 'SKY'})  # no 'time'

  app.process_sky(msg)
  out, _ = capsys.readouterr()

  assert 'ERROR missing timestamp' in out


def test_process_sky_no_valid_satellites(capsys: pytest.CaptureFixture, tmp_path: Path) -> None:
  """
  GNSSApp.process_sky should do nothing if no satellites
  are valid (all unhealthy, unused, or SBAS).
  """
  app = GNSSApp(logdir=str(tmp_path))
  msg = dictwrapper({
    'class': 'SKY',
    'time': '2025-06-29T12:34:56.000Z',
    'satellites': [
      {'gnssid': 1, 'used': False, 'health': 0},  # SBAS, unused, unhealthy
      {'gnssid': 0, 'used': False, 'health': 0},  # GPS, unused, unhealthy
      {'gnssid': 0, 'used': True, 'health': 0},  # GPS, used, unhealthy ??
    ],
  })

  app.process_sky(msg)
  out, _ = capsys.readouterr()

  # Should not print error nor call write_satellites
  assert 'ERROR' not in out


def test_open_new_file_closes_previous(tmp_path: Path) -> None:
  """
  HourlyLogWriter should close the previous file
  when opening a new log file for a different hour.
  """
  logger = HourlyLogWriter(tmp_path)

  # open first file
  dt1 = datetime(2025, 6, 28, 12, 0, 0)
  logger._open_new_file(dt1)
  first_file = logger.file

  assert first_file is not None
  assert not first_file.closed

  # open second file one hour later
  dt2 = dt1 + timedelta(hours=1)
  logger._open_new_file(dt2)

  # old file should be closed
  assert first_file.closed
  assert logger.file is not None
  assert not logger.file.closed
  assert logger.file != first_file

  logger.close()


def test_collect_with_fake_messages(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
  """
  Test GNSSApp.collect() with a dummy gps session,
  verifying all message types are handled and logs are written.
  """

  class DummySession:
    def __iter__(self):
      yield dictwrapper(DUMMY_VERSION_MSG)
      yield dictwrapper(DUMMY_DEVICES_MSG)
      yield dictwrapper(DUMMY_WATCH_MSG)
      yield dictwrapper(DUMMY_TPV_MSG)
      yield dictwrapper(DUMMY_SKY_MSG)
      yield 'non-dict message'
      raise KeyboardInterrupt()
  monkeypatch.setattr('gnss.app.gps.gps', lambda *a, **kw: DummySession())

  app = GNSSApp(logdir=str(tmp_path))
  app.collect()
  out, _ = capsys.readouterr()

  assert 'VERSION:' in out
  assert 'GPSD version:' in out
  assert 'DEVICES:' in out
  assert 'Device: /dev/ttyACM0, driver: u-blox' in out
  assert 'Device: /dev/ttyACM0' in out
  assert 'WATCH:' in out
  assert 'TPV:' in out
  assert 'SKY:' in out
  assert 'Interrupted by user' in out

  files = list(tmp_path.rglob('*.csv'))
  assert len(files) > 0

  contents = files[0].read_text()
  assert 'GPS' in contents
  assert 'SBAS' not in contents


DUMMY_VERSION_MSG = {
  'class': 'VERSION',
  'release': '3.22',
  'rev': 'dummy',
  'proto_major': 3,
  'proto_minor': 14
}

DUMMY_DEVICES_MSG = {
  'class': 'DEVICES',
  'devices': [
    {'path': '/dev/ttyACM0', 'driver': 'u-blox'},
  ]
}

DUMMY_WATCH_MSG = {
  'class': 'WATCH',
  'enable': True,
  'json': True,
  'nmea': False,
  'raw': 0,
  'scaled': False,
  'timing': False,
  'split24': False,
  'pps': False
}

DUMMY_TPV_MSG = {
  'class': 'TPV',
  'device': '/dev/ttyACM0',
  'mode': 3,
  'lat': 37.7749,
  'lon': -122.4194,
  'alt': 10.0,
  'speed': 0.1,
  'track': 150.0
}

DUMMY_SKY_MSG = {
  'class': 'SKY',
  'time': '2025-06-30T12:00:00.000Z',
  'satellites': [
    {
      'gnssid': 0,
      'svid': 5,
      'PRN': 5,
      'el': 45.0,
      'az': 100.0,
      'ss': 38.0,
      'used': True,
      'health': 1
    },
    {
      'gnssid': 1,  # SBAS, should be skipped
      'svid': 50,
      'PRN': 50,
      'el': 30.0,
      'az': 150.0,
      'ss': 22.0,
      'used': True,
      'health': 1
    }
  ]
}
