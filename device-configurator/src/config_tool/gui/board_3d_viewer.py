"""3D board orientation viewer using VPython.

Displays a cuboid representing the embedded board, rotated according
to tilt_x (roll) and tilt_y (pitch) angles from an inclinometer sensor.

This module is **fully isolated** from the rest of the application.
It exposes a single function :func:`launch` which spawns a VPython
window in a background daemon thread.

Notes
-----
VPython normally calls ``signal.signal(SIGINT, ...)`` at import time,
which crashes if called from a non-main thread. To avoid this we
monkey-patch ``signal.signal`` into a no-op *immediately before* the
first VPython import inside the thread, then restore it.  This is
safe for PyInstaller packaging since everything runs in the same
process.

The viewer reads orientation angles from a shared thread-safe
:class:`AngleSource` object.  While the viewer is running the
application should periodically call
:meth:`AngleSource.push(tilt_x_deg, tilt_y_deg)` with the latest
sensor readings.

Usage::

    from config_tool.gui.board_3d_viewer import AngleSource, launch

    source = AngleSource()
    source.push(12.5, -8.3)   # push real sensor data
    launch(angle_source=source)
"""

from __future__ import annotations

import math
import threading
import time

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CUBOID_DIMS = (1.0, 0.2, 0.6)   # length (X), height (Y), width (Z)
CUBOID_COLOR = (0.15, 0.55, 0.8)  # blue-grey
AXIS_LENGTH = 1.2
AXIS_RADIUS = 0.02
GROUND_R = 0.9           # ground-ring radius
SWEEP_PERIOD = 6.0       # seconds for a full fake sweep cycle (fallback)
MAX_ANGLE = 45.0         # degrees — peak tilt during sweep (fallback)
STALE_THRESHOLD = 2.0    # seconds — fall back to fake data if no push

# ---------------------------------------------------------------------------
# Thread-safe angle source
# ---------------------------------------------------------------------------


class AngleSource:
    """Thread-safe container that holds the latest tilt angles.

    One thread calls :meth:`push` with real sensor data, while the
    VPython thread calls :meth:`pull` each frame to get the most recent
    values.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tilt_x: float = 0.0
        self._tilt_y: float = 0.0
        self._timestamp: float = time.monotonic()

    def push(self, tilt_x_deg: float, tilt_y_deg: float) -> None:
        """Update the stored angles (called from the polling thread)."""
        with self._lock:
            self._tilt_x = tilt_x_deg
            self._tilt_y = tilt_y_deg
            self._timestamp = time.monotonic()

    def pull(self) -> tuple[float, float]:
        """Return *(tilt_x_deg, tilt_y_deg, age_seconds)*.

        If no data has been pushed for more than *STALE_THRESHOLD*
        seconds the caller may decide to fall back to fake data.
        """
        with self._lock:
            age = time.monotonic() - self._timestamp
            return self._tilt_x, self._tilt_y, age


# ---------------------------------------------------------------------------
# Internal implementation
# ---------------------------------------------------------------------------

class _BoardViewer:
    """Owns the VPython canvas, cuboid, and animation loop.

    Runs in a daemon thread.  The thread terminates automatically when
    the user closes the VPython browser window (the ``while`` loop
    exits because VPython's ``rate()`` raises when the canvas is gone).

    When real sensor data is unavailable (stale) the viewer falls back
    to a gentle sweep to keep the visual interesting.
    """

    def __init__(self, angle_source: AngleSource | None = None) -> None:
        self._angle_source = angle_source or AngleSource()

    # ----------------------------------------------------------------
    # Fake data generator — sweep between -MAX_ANGLE .. +MAX_ANGLE
    # ----------------------------------------------------------------

    @staticmethod
    def _fake_angles(t: float) -> tuple[float, float]:
        """Return (tilt_x, tilt_y) in degrees for time *t* (seconds)."""
        phase = (t % SWEEP_PERIOD) / SWEEP_PERIOD  # 0..1
        raw = math.sin(phase * 2.0 * math.pi) * MAX_ANGLE
        # Tilt X and Y follow sine waves offset by 90° so they sweep
        # through different combinations.
        tilt_x = raw
        tilt_y = math.sin((phase + 0.25) * 2.0 * math.pi) * MAX_ANGLE
        return tilt_x, tilt_y

    # ----------------------------------------------------------------
    # Scene builder
    # ----------------------------------------------------------------

    def _build_scene(self):
        """Import VPython lazily and set up the 3D scene."""
        from vpython import (
            canvas,
            box,
            cylinder,
            cone,
            sphere,
            ring,
            vector,
        )

        scene = canvas(
            title="Board Orientation",
            width=700,
            height=520,
            center=vector(0, 0, 0),
            background=vector(0.18, 0.18, 0.18),
            ambient=vector(0.25, 0.25, 0.25),
        )

        # --- world-frame axes (static) ---
        _axis_arrow(vector(0, 0, 0), vector(AXIS_LENGTH, 0, 0), vector(1, 0, 0))
        _axis_arrow(vector(0, 0, 0), vector(0, AXIS_LENGTH, 0), vector(0, 1, 0))
        _axis_arrow(vector(0, 0, 0), vector(0, 0, AXIS_LENGTH), vector(0, 0, 1))

        # --- ground reference ring ---
        ring(
            pos=vector(0, -0.55, 0),
            axis=vector(0, 1, 0),
            radius=GROUND_R,
            thickness=0.01,
            color=vector(0.35, 0.35, 0.35),
            opacity=0.4,
        )

        # --- board cuboid ---
        board = box(
            pos=vector(0, 0, 0),
            size=vector(*CUBOID_DIMS),
            color=vector(*CUBOID_COLOR),
            opacity=0.88,
        )

        # --- small coloured dots on cuboid faces to disambiguate orientation ---
        face_indicators: list = []
        face_indicators.append(
            _face_dot(vector(CUBOID_DIMS[0] / 2 + 0.02, 0, 0), vector(1, 0, 0))
        )
        face_indicators.append(
            _face_dot(vector(-CUBOID_DIMS[0] / 2 - 0.02, 0, 0), vector(0.6, 0, 0))
        )
        face_indicators.append(
            _face_dot(vector(0, CUBOID_DIMS[1] / 2 + 0.02, 0), vector(0, 1, 0))
        )
        face_indicators.append(
            _face_dot(vector(0, -CUBOID_DIMS[1] / 2 - 0.02, 0), vector(0, 0.5, 0))
        )
        face_indicators.append(
            _face_dot(vector(0, 0, CUBOID_DIMS[2] / 2 + 0.02), vector(0, 0, 1))
        )
        face_indicators.append(
            _face_dot(vector(0, 0, -CUBOID_DIMS[2] / 2 - 0.02), vector(0, 0, 0.5))
        )

        return scene, board, face_indicators

    # ----------------------------------------------------------------
    # Main loop (blocking — runs in daemon thread)
    # ----------------------------------------------------------------

    def run(self) -> None:
        # Monkey-patch signal.signal to a no-op for the entire lifetime of
        # this thread. VPython's no_notebook.py calls signal.signal() both at
        # import time and inside object constructors (cylinder, etc.), which
        # crashes with ValueError in a non-main thread.
        # We never restore it because this is a daemon thread — safe for
        # PyInstaller packaging since everything runs in the same process.
        import signal as _signal_mod

        _signal_mod.signal = lambda _signum, _handler: None

        from vpython import rate, vector, radians

        scene, board, face_dots = self._build_scene()
        t0 = time.monotonic()

        while True:
            try:
                rate(30)
            except Exception:
                # Rate raises when the canvas is gone — exit silently.
                break

            # ---- Read the latest real or fake angles ----
            real_tilt_x, real_tilt_y, age = self._angle_source.pull()

            if age < STALE_THRESHOLD:
                # Use real sensor data
                tilt_x_deg = real_tilt_x
                tilt_y_deg = real_tilt_y
                mode = "REAL"
            else:
                # Fall back to fake sweep
                elapsed = time.monotonic() - t0
                tilt_x_deg, tilt_y_deg = self._fake_angles(elapsed)
                mode = "FAKE"

            pitch = radians(tilt_y_deg)
            roll = radians(tilt_x_deg)

            # Step 1 – pitch around Z
            ax_x = math.cos(pitch)
            ax_y = math.sin(pitch)
            ax_z = 0.0

            up_x = -math.sin(pitch)
            up_y = math.cos(pitch)
            up_z = 0.0

            # Step 2 – roll around the pitched X-axis
            up_final = _rotate_around(up_x, up_y, up_z, ax_x, ax_y, ax_z, roll)

            board.axis = vector(ax_x, ax_y, ax_z)
            board.up = vector(*up_final)

            for dot in face_dots:
                dot.axis = board.axis
                dot.up = board.up

            scene.title = (
                f"Board Orientation  [{mode}]  |  "
                f"tilt_x = {tilt_x_deg:+.1f}\u00b0  "
                f"tilt_y = {tilt_y_deg:+.1f}\u00b0"
            )


# ---------------------------------------------------------------------------
# Vector helpers (pure maths — no VPython dependency)
# ---------------------------------------------------------------------------


def _axis_arrow(origin_v, direction_v, color_v):
    from vpython import cylinder, cone

    cylinder(pos=origin_v, axis=direction_v, radius=AXIS_RADIUS, color=color_v)
    cone(
        pos=origin_v + direction_v,
        axis=direction_v.norm() * 0.15,
        radius=AXIS_RADIUS * 3,
        color=color_v,
    )


def _face_dot(position_v, color_v):
    from vpython import sphere

    return sphere(pos=position_v, radius=0.04, color=color_v, emissive=True)


def _rotate_around(
    px: float, py: float, pz: float,
    ax: float, ay: float, az: float,
    angle: float,
) -> tuple[float, float, float]:
    """Rotate point *p* around axis *a* by *angle* (radians) using Rodrigues' formula."""
    c = math.cos(angle)
    s = math.sin(angle)
    oc = 1.0 - c

    cx = ay * pz - az * py
    cy = az * px - ax * pz
    cz = ax * py - ay * px
    dot = ax * px + ay * py + az * pz

    return (
        px * c + cx * s + ax * dot * oc,
        py * c + cy * s + ay * dot * oc,
        pz * c + cz * s + az * dot * oc,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def launch(
    angle_source: AngleSource | None = None,
) -> threading.Thread:
    """Launch the 3D board viewer in a background daemon thread.

    Parameters
    ----------
    angle_source:
        Optional :class:`AngleSource` that provides real tilt readings.
        If ``None`` (default) the viewer creates its own source and
        falls back to a gentle automated sweep.

    Returns
    -------
    threading.Thread
        The daemon thread running the viewer. The thread terminates
        automatically when the user closes the VPython browser tab
        or when the main application exits.
    """
    viewer = _BoardViewer(angle_source=angle_source)
    thread = threading.Thread(target=viewer.run, daemon=True, name="vpython-3d")
    thread.start()
    return thread