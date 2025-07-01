# GNSS Skylog

Collect GNSS satellite data & plot heatmap.

This really only makes sens with a stationary receiver.

## Usage

  `skylog.py collect`
    Collect SKY observations from gpspipe into hourly CSV logs.

  `skylog.py plot`
    Load logs and plot 95th percentile SNR heatmap.

If no command is given, plotting is the default.

## Development

`code .`

### Testing

 - `uv pip install pytest-cov`
 - `uv run pytest`
