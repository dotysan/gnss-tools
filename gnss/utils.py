"""
GNSS constants and shared utility definitions.
"""

from typing import TypedDict

GNSSID_NAMES = {
  0: 'GPS',
  1: 'SBAS',
  2: 'Galileo',
  3: 'BeiDou',
  4: 'IMES',
  5: 'QZSS',
  6: 'GLONASS',
}


class Satellite(TypedDict):
  gnssid: int
  svid: int
  PRN: int
  el: float
  az: float
  ss: float
  used: bool
  health: int
