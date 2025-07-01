"""
Functions for plotting GNSS data, including heatmaps and satellite overlays.
"""

# stdlib
from datetime import (
  datetime,
  timezone,
)
from pathlib import Path
from typing import cast

# pypi
from matplotlib.axes import Axes
from matplotlib.projections.polar import PolarAxes
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_heatmap(df: pd.DataFrame, plot_dir: Path) -> None:
  """
  Plot a high-resolution polar heatmap of observed SNR
  at each (az, el) grid coordinate.

  Args:
    df (pd.DataFrame): DataFrame of observations.
    plot_dir (Path): Directory to save PNG plots
  """

  az_edges, el_edges, df_binned = bin_data(df)
  grid = aggregate_max_snr(df_binned, az_edges, el_edges)
  theta_grid, r_grid = create_mesh(az_edges, el_edges)

  fig, ax = plot_heatmap_grid(grid, theta_grid, r_grid)
  # overlay_latest_satellites(df, ax)
  save_figure(fig, plot_dir)


# ----------------------------------------------------------------------

def bin_data(
  df: pd.DataFrame,
  az_bin_size: float = 1,  # in degrees
  el_bin_size: float = 1,  # in degrees
) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
  """ Bin azimuth and elevation into discrete bins.

  Args:
    df (pd.DataFrame): DataFrame of observations.
    az_bin_size (float): Bin width for azimuth, degrees.
    el_bin_size (float): Bin width for elevation, degrees.

  Returns:
    (az_edges, el_edges, binned DataFrame)
  """

  # Create bin edges
  az_edges = np.arange(0, 360 + az_bin_size, az_bin_size)
  el_edges = np.arange(0, 90 + el_bin_size, el_bin_size)

  # Bin azimuth and elevation
  az_bins = np.digitize(df["az"], az_edges) - 1
  el_bins = np.digitize(df["el"], el_edges) - 1

  # Remove out-of-range values
  mask = (
      (az_bins >= 0) & (az_bins < len(az_edges) - 1) &
      (el_bins >= 0) & (el_bins < len(el_edges) - 1)
  )
  df = df.loc[mask].copy()

  df["az_bin"] = az_bins[mask]
  df["el_bin"] = el_bins[mask]

  return az_edges, el_edges, df


def aggregate_max_snr(df: pd.DataFrame, az_edges: np.ndarray, el_edges: np.ndarray) -> np.ndarray:
  """ Aggregate 90th percentile SNR into grid matrix.

  Args:
    df (pd.DataFrame): Binned DataFrame.
    az_edges (np.ndarray): Azimuth bin edges.
    el_edges (np.ndarray): Elevation bin edges.

  Returns:
    np.ndarray: 2D grid of SNR values.
  """

  # Aggregate max SNR per cell
  # df_agg = df.groupby(['el_bin', 'az_bin'])['ss'].max().reset_index()
  # Aggregate 90th percentile SNR per cell
  df_agg = df.groupby(['el_bin', 'az_bin'])['ss'].quantile(0.9).reset_index()

  # Create empty grid
  grid = np.zeros((len(el_edges) - 1, len(az_edges) - 1))

  # Fill grid with 90th percentile SNR values
  for _, row in df_agg.iterrows():
    grid[int(row['el_bin']), int(row['az_bin'])] = row['ss']

  return grid


def create_mesh(az_edges: np.ndarray, el_edges: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
  """
  Create theta/radius mesh for polar pcolormesh.

  Args:
    az_edges (np.ndarray): Azimuth edges in degrees.
    el_edges (np.ndarray): Elevation edges in degrees.

  Returns:
    (theta_grid, r_grid)
  """

  # Compute mesh grid for pcolormesh
  theta_edges = np.deg2rad(az_edges)

  r_edges = 90 - el_edges  # polar radius = 90 - elevation

  return np.meshgrid(theta_edges, r_edges)


def plot_heatmap_grid(grid: np.ndarray, theta_grid: np.ndarray, r_grid: np.ndarray) -> tuple[Figure, Axes]:
  """ Plot the heatmap grid on polar coordinates.

  Args:
    grid (np.ndarray): SNR grid.
    theta_grid (np.ndarray): Azimuth mesh grid.
    r_grid (np.ndarray): Radius mesh grid.

  Returns:
    (fig, ax)
  """
  fig, ax = plt.subplots(subplot_kw=dict(projection='polar'), figsize=(8, 8))
  pax = cast(PolarAxes, ax)
  pcm = pax.pcolormesh(theta_grid, r_grid, grid, cmap='viridis', shading='auto')

  pax.set_theta_zero_location('N')
  pax.set_theta_direction(-1)
  pax.set_ylim(0, 90)
  pax.set_yticks([0, 30, 60, 90])
  pax.set_yticklabels(['90°', '60°', '30°', '0°'])

  plt.colorbar(pcm, ax=pax, label='90th%ile SNR (dB-Hz)')
  plt.title('Courtney GNSS Receiver Coverage (90th%ile SNR)')

  return fig, pax


def save_figure(fig: Figure, plot_dir: Path) -> None:
  """
  Save the heatmap figure to a timestamped PNG.

  Args:
    fig (plt.Figure): The matplotlib figure.
    plot_dir (Path): Directory to save the PNG.
  """
  plot_dir.mkdir(parents=True, exist_ok=True)

  ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
  filename = plot_dir / f"gnss_sky_heatmap.{ts}.png"
  fig.savefig(filename, dpi=300, bbox_inches='tight')
  print(f"Saved high-res heatmap to {filename}")


def TODO_overlay_latest_satellites(df: pd.DataFrame, ax: Axes) -> None:
  """
  Overlay last known positions of each satellite.
  """
  df_latest = (df.sort_values('time')
                 .drop_duplicates(subset=['GNSS', 'SVID'], keep='last')
                 .copy())

  # convert timestamps to datetime
  df_latest['time_dt'] = pd.to_datetime(df_latest['time'])
  # compute age
  now_utc = pd.Timestamp.now(tz='UTC')
  # df_latest['age_sec'] = (now_utc - df_latest['time_dt']).dt.total_seconds()
  # above fails Pylance, why? below seems to make it happy
  df_latest['age_sec'] = df_latest['time_dt'].apply(
    lambda t: (now_utc - t).total_seconds()
  )

  # mute below 5deg and over an hour old
  df_latest['muted'] = (
    (df_latest['age_sec'] > 3600) &
    (df_latest['el'] < 5)
  )

  # split into muted and normal
  df_visible = df_latest[~df_latest['muted']]
  df_muted = df_latest[df_latest['muted']]

  # theta = np.deg2rad(df_latest['az'])
  # radius = 90 - df_latest['el']

  # normal satellite dots
  ax.scatter(
    np.deg2rad(df_visible['az']),
    90 - df_visible['el'] - 3,
    color='white',
    edgecolor='black',
    s=50,
    zorder=10,
    label='Latest Satellite'
  )

  # muted satellite dots
  ax.scatter(
    np.deg2rad(df_muted['az']),
    90 - df_muted['el'] - 3,
    color='gray',
    edgecolor='black',
    s=50,
    alpha=0.3,
    zorder=9,
    label='Muted Satellite'
  )

  # labels
  for _, row in df_latest.iterrows():
    label = f"{row['GNSS']}-{int(row['SVID'])}"
    ax.text(
      np.deg2rad(row['az']),
      90 - row['el'],
      label,
      fontsize=8,
      ha='center',
      va='center',
      color='gray' if row['muted'] else 'black',
      bbox=dict(
        boxstyle='round,pad=0.3',
        facecolor='white',
        edgecolor='gray' if row['muted'] else 'black',
        linewidth=0.5,
        alpha=0.5 if row['muted'] else 0.8,
      ),
      zorder=11
    )
