"""Battery lifetime estimation helpers."""

from __future__ import annotations

from typing import Optional, Union


def estimate_battery_lifetime_days( #FIXME : the formula and constant should be edited
    charge_percent: Union[str, int, float, None],
    capacity_mah: Union[str, int, float, None],
    uplink_period_s: Union[str, int, float, None],
    gps_decimation_factor: Union[str, int, float, None],
) -> Optional[float]:
    return (_as_float(capacity_mah)/7000.0)*_as_float(charge_percent)*4 #FIXME : this is an approximation 




# def WIP_estimate_battery_lifetime_days( #FIXME : the formula and constant should be edited
#     charge_percent: Union[str, int, float, None],
#     capacity_mah: Union[str, int, float, None],
#     uplink_period_s: Union[str, int, float, None],
#     gps_decimation_factor: Union[str, int, float, None],
# ) -> Optional[float]:
#     """Estimate the remaining battery lifetime in days.

#     The device draws current in a handful of operating phases:

#       * Uplink routine — every ``uplink_period_s`` seconds the device wakes,
#         samples the sensors, and transmits an uplink. The dominant energy
#         draw is the LoRa radio transmit (roughly 130 mA for ~0.18 s on a
#         typical SF12 + confirmed uplink).
#       * GPS acquisition — every ``gps_decimation_factor``-th uplink routine
#         the GPS module is powered up for a fix (~35 mA for ~45 s).
#       * Sleep / deep sleep — the dominant idle state between wake-ups.

#     Using these phase currents, capacities, and durations, the average
#     current draw (mA) is:

#         avg_current = (130mA * 0.18s +
#                        35mA * 45s / gps_decimation_factor) / uplink_period_s

#     For a usable battery we assume only the rated capacity minus the self
#     discharge / unusable margin is actually available — we use 90% of the
#     declared capacity in the estimate.

#     Given the total capacity (mAh) and the remaining charge (percent), the
#     remaining usable capacity is ``capacity * 0.9 * (percent / 100)``.

#     Lifetime (hours) = usable_capacity / avg_current, converted to days.

#     This is a conservative planning estimate, not a measurement.

#     Args:
#         charge_percent: Remaining battery charge as a percentage (0-100).
#         capacity_mah: Total battery capacity in milliamp-hours.
#         uplink_period_s: Uplink period in seconds.
#         gps_decimation_factor: GPS decimation factor (1 = GPS every uplink,
#             0 disables GPS).
#     """
#     percent = _as_float(charge_percent)
#     capacity = _as_float(capacity_mah)
#     period = _as_float(uplink_period_s)

#     if percent is None or capacity is None or period is None or period <= 0:
#         return None

#     # GPS decimation: 0 disables GPS → no GPS current draw.
#     if gps_decimation_factor is None:
#         gps_factor = 1.0
#     else:
#         gps_factor = _as_float(gps_decimation_factor)
#         if gps_factor is None:
#             return None

#     transmit_charge_mah = 130.0 * (0.18 / 3600.0)          # mA * h per uplink
#     gps_charge_mah = 35.0 * (45.0 / 3600.0) / gps_factor if gps_factor > 0 else 0.0

#     charge_per_uplink_mah = transmit_charge_mah + gps_charge_mah
#     avg_current_ma = charge_per_uplink_mah * 3600.0 / period

#     if avg_current_ma <= 0:
#         return None

#     usable_capacity_mah = capacity * 0.9 * (percent / 100.0)
#     lifetime_hours = usable_capacity_mah / avg_current_ma
#     return lifetime_hours / 24.0


def _as_float(value: Union[str, int, float, None]) -> Optional[float]:
    """Parse a string/number to float, returning None when unparsable."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None