# stdlib
from pathlib import Path
import sys

# pypi
import pandas as pd
import pytest

# local
import skylog


def test_skylog_no_args(monkeypatch: pytest.MonkeyPatch, patch_gnssapp: Path, capsys: pytest.CaptureFixture) -> None:
  """ Runs skylog.py with no arguments.

  Should default to plotting, load dummy logs,
  and print confirmation output.
  """
  monkeypatch.setattr(sys, 'argv', ['skylog.py'])
  skylog.main()

  out, _ = capsys.readouterr()
  assert 'No command provided. Defaulting to plot.' in out
  assert 'Loaded' in out


def test_skylog_plot(monkeypatch, patch_gnssapp, capsys):
  """ Runs skylog.py plot explicitly.
  Should attempt plotting and create PNG files.
  """
  monkeypatch.setattr(sys, 'argv', ['skylog.py', 'plot'])
  skylog.main()

  out, _ = capsys.readouterr()
  assert 'Loaded' in out

  plot_files = list((patch_gnssapp / 'plots').glob('*.png'))
  assert len(plot_files) > 0


def test_skylog_unknown(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
  """ Runs skylog.py with an unknown command and verifies SystemExit. """

  monkeypatch.setattr(sys, 'argv', ['skylog.py', 'bozo'])
  with pytest.raises(SystemExit) as excinfo:
    skylog.main()
  out, _ = capsys.readouterr()

  assert excinfo.value.code == 1
  assert 'Unknown command: bozo' in out


def test_skylog_collect_interrupt(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture):
  """
  Simulates running skylog.py collect and interrupts immediately.
  Verifies graceful KeyboardInterrupt handling.
  """

  class DummySession:
    def __iter__(self):
      raise KeyboardInterrupt()
  monkeypatch.setattr('gnss.app.gps.gps', lambda *_a, **_kw: DummySession())
  monkeypatch.setattr(sys, 'argv', ['skylog.py', 'collect'])

  skylog.main()
  out, _ = capsys.readouterr()
  assert 'Interrupted by user' in out


@pytest.fixture
def patch_gnssapp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
  """
  Fixture that:
    - monkeypatches GNSSApp.__init__ to use tmp_path
    - creates dummy CSV log data
  """

  def fake_init(self, logdir='dummy', plotdir='dummy'):
    self.logdir = tmp_path
    self.plotdir = tmp_path / 'plots'
    self.logger = None
  monkeypatch.setattr('gnss.app.GNSSApp.__init__', fake_init)

  path = tmp_path / '2025-06' / '2025-06-30' / '2025-06-30T12.csv'
  path.parent.mkdir(parents=True, exist_ok=True)

  df = pd.DataFrame([{
    'time': '2025-06-30T12:00:00Z',
    'GNSS': 'GPS',
    'SVID': 5,
    'PRN': 5,
    'el': 45.0,
    'az': 100.0,
    'ss': 38.0,
  }])
  df.to_csv(path, index=False)

  return tmp_path
