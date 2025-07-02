# GNSS Skylog

Collect GNSS satellite data & plot heatmap.

This really only makes sense with a stationary receiver.

## Usage

  `skylog.py collect`
    Collect SKY observations from gpspipe into hourly CSV logs.

  `skylog.py plot`
    Load logs and plot 95th percentile SNR heatmap.

If no command is given, plotting is the default.

## Development

This project uses UV to manage the Python environment. If you don't have it installed yet, do this.

`curl --location https://gist.github.com/dotysan/fdbfc77b924a08ceab7197d010280dac/raw/uv-install.sh |bash`

To open project in VSCode.

`code .`

### Testing

 `uv run just tests`
