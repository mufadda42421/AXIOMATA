"""3D Scientific Sandbox.

A PyVista-powered 3D viewport driven by the built-in Engine3D. Users add spheres
and boxes, control gravity, and play/pause/reset the simulation. The renderer
reads body transforms each frame; physics runs on Engine3D with a clean
separation between the two. If a 3D OpenGL context cannot be created (e.g. a
headless/offscreen environment), the page degrades gracefully to a message
while keeping the simulation engine fully usable.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from ...core.application import AppContext
from ...ui.panels.base_page import BasePage
from ...ui.themes.theme import ACCENT, ACCENT_BLUE, WARNING
from ..simulation_engine.engine3d import Body3D, Engine3D, World3D

PYVISTA_OK = True
PYVISTA_ERROR = ""
try:
    import pyvista as pv
    from pyvistaqt import QtInteractor
except Exception as exc:  # noqa: BLE001
    PYVISTA_OK = False
    PYVISTA_ERROR = str(exc)


class Sandbox3DPage(BasePage):
    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None):
        super().__init__("3D Sandbox",
                         "Interactive 3D physics — spheres & boxes, gravity, real-time simulation.",
                         parent)
        self.ctx = ctx
        self.world = World3D(gravity=(0.0, -9.80665, 0.0), ground_y=0.0, has_ground=True)
        self.engine = Engine3D(self.world)
        self._playing = False

        self._build_controls()
        self._build_viewport()
        self._build_layout()
        self._seed_scene()

        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._tick)

    def _build_controls(self) -> None:
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setObjectName("Primary")
        self.play_btn.clicked.connect(self._toggle_play)
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self._reset)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear)

        self.add_combo = QComboBox()
        self.add_combo.addItem("Add Sphere", "sphere")
        self.add_combo.addItem("Add Box", "box")
        self.add_btn = QPushButton("+ Add Object")
        self.add_btn.setObjectName("Primary")
        self.add_btn.clicked.connect(self._add_object)

        self.gravity_spin = QDoubleSpinBox()
        self.gravity_spin.setRange(-30, 30)
        self.gravity_spin.setDecimals(2)
        self.gravity_spin.setValue(-9.80665)
        self.gravity_spin.setSuffix(" m/s²")
        self.gravity_spin.valueChanged.connect(
            lambda v: setattr(self.world, "gravity", (0.0, v, 0.0)))

    def _build_viewport(self) -> None:
        global PYVISTA_OK
        self.plotter = None
        self.canvas_widget = None
        if not PYVISTA_OK:
            warn = QLabel(
                f"3D viewport unavailable: {PYVISTA_ERROR}\n"
                "The simulation engine still works; rendering requires an OpenGL context."
            )
            warn.setObjectName("MutedLabel")
            warn.setWordWrap(True)
            self.canvas_widget = warn
            return
        try:
            self.plotter = QtInteractor(self)
            self.plotter.set_background("#0e1728")
            # Ground plane
            self.plotter.add_mesh(
                pv.Plane(center=(0, -0.01, 0), direction=(0, 1, 0),
                         i_size=20, j_size=20),
                color="#172238", opacity=0.6, show_edges=False,
            )
            self.plotter.add_axes()
            self.plotter.show_grid(color="#223047")
            self.plotter.camera_position = "iso"
            self.canvas_widget = self.plotter
        except Exception as exc:  # noqa: BLE001
            PYVISTA_OK = False
            self.plotter = None
            warn = QLabel(f"3D viewport could not start: {exc}")
            warn.setObjectName("MutedLabel")
            self.canvas_widget = warn

    def _build_layout(self) -> None:
        toolbar = QHBoxLayout()
        for w in (self.play_btn, self.reset_btn, self.clear_btn):
            toolbar.addWidget(w)
        toolbar.addSpacing(12)
        toolbar.addWidget(QLabel("Object:"))
        toolbar.addWidget(self.add_combo)
        toolbar.addWidget(self.add_btn)
        toolbar.addSpacing(12)
        toolbar.addWidget(QLabel("Gravity:"))
        toolbar.addWidget(self.gravity_spin)
        toolbar.addStretch(1)
        t = QWidget(); t.setLayout(toolbar)
        self.add_toolbar_widget(t)

        body = QHBoxLayout()
        body.setSpacing(12)
        body.addWidget(self.canvas_widget, 3)

        right = QVBoxLayout()
        info = QGroupBox("Scene info")
        fl = QFormLayout(info)
        self.lbl_bodies = QLabel("0")
        self.lbl_time = QLabel("0.00 s")
        self.lbl_backend = QLabel("built-in Engine3D")
        fl.addRow("Bodies", self.lbl_bodies)
        fl.addRow("Time", self.lbl_time)
        fl.addRow("Physics", self.lbl_backend)
        right.addWidget(info)

        help_lbl = QLabel(
            "Drag to orbit · Scroll to zoom · Right-drag to pan.\n"
            "Add objects, set gravity, and press Play."
        )
        help_lbl.setObjectName("MutedLabel")
        help_lbl.setWordWrap(True)
        right.addWidget(help_lbl)
        right.addStretch(1)
        body.addLayout(right, 0)

        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addLayout(body)
        self.add_body_widget(w, 1)

    # -- scene ------------------------------------------------------------
    def _seed_scene(self) -> None:
        ground = Body3D(id="ground", shape="box", position=(0.0, -0.5, 0.0),
                        half_extents=(10.0, 0.5, 10.0), is_static=True, color="#8aa0bd")
        self.world.add_body(ground)
        self._spawn(("sphere", (0.0, 4.0, 0.0), 0.6, ACCENT))
        self._spawn(("sphere", (-2.0, 6.0, 1.0), 0.5, ACCENT_BLUE))
        self._spawn(("box", (2.0, 5.0, -1.0), 0.7, "#f59e0b"))
        self._refresh_labels()

    def _spawn(self, spec, ) -> None:
        shape, pos, size, color = spec
        bid = f"b{len(self.world.bodies)}"
        if shape == "sphere":
            body = Body3D(id=bid, shape="sphere", position=pos, radius=size, color=color)
        else:
            body = Body3D(id=bid, shape="box", position=pos,
                          half_extents=(size, size, size), color=color)
        self.world.add_body(body)
        self._sync_mesh(body)

    def _add_object(self) -> None:
        shape = self.add_combo.currentData()
        x = (len(self.world.bodies) % 5 - 2) * 1.5
        self._spawn((shape, (x, 6.0, 0.0), 0.5, ACCENT if shape == "sphere" else ACCENT_BLUE))
        self._refresh_labels()

    # -- rendering sync ---------------------------------------------------
    def _sync_mesh(self, body: Body3D) -> None:
        if self.plotter is None:
            return
        if body.is_static:
            return
        existing = getattr(body, "_actor", None)
        if existing is None:
            if body.shape == "sphere":
                mesh = pv.Sphere(radius=body.radius)
            else:
                mesh = pv.Box(bounds=(-body.half_extents[0], body.half_extents[0],
                                      -body.half_extents[1], body.half_extents[1],
                                      -body.half_extents[2], body.half_extents[2]))
            actor = self.plotter.add_mesh(mesh, color=body.color, smooth_shading=True)
            body._actor = actor  # type: ignore[attr-defined]

    def _update_actors(self) -> None:
        if self.plotter is None:
            return
        for body in self.world.bodies.values():
            if body.is_static:
                continue
            self._sync_mesh(body)
            actor = getattr(body, "_actor", None)
            if actor is not None:
                actor.SetPosition(*body.position)

    # -- playback ---------------------------------------------------------
    def _tick(self) -> None:
        self.engine.step(1.0 / 60.0)
        self._update_actors()
        self._refresh_labels()

    def _toggle_play(self) -> None:
        if self._playing:
            self.timer.stop()
            self._playing = False
            self.play_btn.setText("▶ Play")
        else:
            self.timer.start()
            self._playing = True
            self.play_btn.setText("❚❚ Pause")

    def _reset(self) -> None:
        self.timer.stop()
        self._playing = False
        self.play_btn.setText("▶ Play")
        # Return bodies to initial positions by clearing and reseeding.
        actors = [getattr(b, "_actor", None) for b in self.world.bodies.values()]
        if self.plotter is not None:
            for a in actors:
                if a is not None:
                    try:
                        self.plotter.remove_actor(a)
                    except Exception:  # noqa: BLE001
                        pass
        self.world.clear()
        self._seed_scene()
        self._refresh_labels()

    def _clear(self) -> None:
        self.timer.stop()
        self._playing = False
        self.play_btn.setText("▶ Play")
        if self.plotter is not None:
            # Remove dynamic actors.
            for body in self.world.bodies.values():
                actor = getattr(body, "_actor", None)
                if actor is not None:
                    try:
                        self.plotter.remove_actor(actor)
                    except Exception:  # noqa: BLE001
                        pass
        # Keep ground; remove others.
        ground = self.world.bodies.get("ground")
        self.world.clear()
        if ground:
            self.world.add_body(ground)
        self._refresh_labels()

    def _refresh_labels(self) -> None:
        dynamic = [b for b in self.world.bodies.values() if not b.is_static]
        self.lbl_bodies.setText(str(len(dynamic)))
        self.lbl_time.setText(f"{self.world.time:.2f} s")