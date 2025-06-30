#! /usr/bin/env -S uv run
"""
GNSS Skylog

Usage:
  skylog.py collect
    Collect SKY observations from gpspipe into hourly CSV logs.

  skylog.py plot
    Load logs and plot 95th percentile SNR heatmap.

If no command is given, plotting is the default.
"""

# stdlib
import sys

# local
from gnss import GNSSApp


def main() -> None:
  """
  Entry point for the CLI tool.
  Dispatches to collect() or plot() based on CLI arguments.
  Defaults to plot if no arguments are provided.
  """
  app = GNSSApp()

  if len(sys.argv) < 2:
    print('No command provided. Defaulting to plot.')
    app.plot()
    return

  cmd = sys.argv[1].lower()
  if cmd == 'collect':
    app.collect()
  elif cmd == 'plot':
    app.plot()

  else:
    print(f"Unknown command: {cmd}")
    print(__doc__)
    raise SystemExit(1)


if __name__ == '__main__':
  main()
