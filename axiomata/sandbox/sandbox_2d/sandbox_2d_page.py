"""2D Scientific Sandbox.

A real-time interactive 2D physics editor. Users add circles/boxes, drag them,
adjust properties in an inspector, control gravity, and play/pause/step the
simulation. The simulation runs on the tested Engine2D; rendering is done on a
custom QPainter widget. Recorded time-series data can be charted.
"""
from __future__ import annotations

import math
import uuid
from typing import Optional

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QTabWidget, QVBoxLayout, QWidget,
)

from ...core.application import AppContext
from ...ui.panels.base_page import BasePage
from ...ui.widgets.chart_widget import ChartWidget
from ...ui.themes.theme import ACCENT, ACCENT_BLUE, BG_INPUT, BORDER, TEXT
from ..simulation_engine import Body2D, Engine2D, World2D


# --------------------------------------------------------------------------
# Canvas widget
# --------------------------------------------------------------------------
class SandboxCanvas(QWidget):
    """QPainter-based view of the 2D world with grid, axes, and bodies.

    Click to add a body of the selected type; drag existing bodies.
    """

    body_selected = Signal(str)
    add_requested = Signal(float, float)  # world coords

    def __init__(self, world: World2D, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.world = world
        self.setMinimumSize(500, 400)
        self.setMouseTracking(True)
        self.scale = 80.0        # pixels per metre
        self.origin = QPointF(0, 0)  # world (0,0) in pixels (set in resize/paint)
        self.selected_id: Optional[str] = None
        self.add_mode = "circle"  # 'circle' | 'box' | 'select'
        self._drag_id: Optional[str] = None
        self._drag_offset = QPointF(0, 0)
        self.grid_spacing_m = 1.0

    # -- coordinate conversion -------------------------------------------
    def world_to_screen(self, wx: float, wy: float) -> QPointF:
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        return QPointF(cx + wx * self.scale, cy - wy * self.scale)

    def screen_to_world(self, sx: float, sy: float) -> tuple[float, float]:
        cx = self.width() / 2.0
        cy = self.height() / 2.0
        return ((sx - cx) / self.scale, -(sy - cy) / self.scale)

    # -- painting ---------------------------------------------------------
    def paintEvent(self, event):  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        # Background
        p.fillRect(self.rect(), QColor(BG_INPUT))
        self._draw_grid(p)
        self._draw_axes(p)
        self._draw_bodies(p)
        # Selection highlight
        if self.selected_id and self.selected_id in self.world.bodies:
            body = self.world.bodies[self.selected_id]
            self._draw_selection(p, body)
        p.end()

    def _draw_grid(self, p: QPainter) -> None:
        pen = QPen(QColor(BORDER))
        pen.setCosmetic(True)
        p.setPen(pen)
        spacing = self.grid_spacing_m * self.scale
        if spacing < 8:
            return
        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0
        x = cx % spacing
        while x < w:
            p.drawLine(int(x), 0, int(x), h)
            x += spacing
        y = cy % spacing
        while y < h:
            p.drawLine(0, int(y), w, int(y))
            y += spacing

    def _draw_axes(self, p: QPainter) -> None:
        pen = QPen(QColor(ACCENT))
        pen.setCosmetic(True)
        pen.setStyle(Qt.DashLine)
        p.setPen(pen)
        cx, cy = self.width() / 2.0, self.height() / 2.0
        p.drawLine(0, int(cy), self.width(), int(cy))
        p.drawLine(int(cx), 0, int(cx), self.height())

    def _draw_bodies(self, p: QPainter) -> None:
        for body in self.world.bodies.values():
            sp = self.world_to_screen(body.position[0], body.position[1])
            color = QColor(body.color)
            if body.is_static:
                color = QColor("#8aa0bd")
            brush = QBrush(QColor(color.red(), color.green(), color.blue(), 180))
            p.setBrush(brush)
            p.setPen(QPen(color.darker(120), 1.5))
            if body.shape == "circle":
                r = body.radius * self.scale
                p.drawEllipse(sp, r, r)
                # velocity vector
                if body.velocity[0] or body.velocity[1]:
                    vp = self.world_to_screen(
                        body.position[0] + body.velocity[0] * 0.2,
                        body.position[1] + body.velocity[1] * 0.2)
                    vp_pen = QPen(QColor(ACCENT_BLUE))
                    p.setPen(vp_pen)
                    p.setBrush(Qt.NoBrush)
                    p.drawLine(sp, vp)
                    p.setBrush(brush)
                    p.setPen(QPen(color.darker(120), 1.5))
            else:
                hw = body.half_width * self.scale
                hh = body.half_height * self.scale
                rect = QRectF(sp.x() - hw, sp.y() - hh, 2 * hw, 2 * hh)
                p.save()
                p.translate(sp)
                p.rotate(-math.degrees(body.angle))
                p.translate(-sp)
                p.drawRect(rect)
                p.restore()

    def _draw_selection(self, p: QPainter, body: Body2D) -> None:
        sp = self.world_to_screen(body.position[0], body.position[1])
        pen = QPen(QColor(ACCENT))
        pen.setCosmetic(True)
        pen.setStyle(Qt.DashLine)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        if body.shape == "circle":
            r = body.radius * self.scale + 4
            p.drawEllipse(sp, r, r)
        else:
            hw = body.half_width * self.scale + 4
            hh = body.half_height * self.scale + 4
            p.drawRect(QRectF(sp.x() - hw, sp.y() - hh, 2 * hw, 2 * hh))

    # -- mouse interaction ------------------------------------------------
    def _hit_test(self, sx: float, sy: float) -> Optional[str]:
        # Test from last to first (top-most).
        for body in reversed(list(self.world.bodies.values())):
            wx, wy = self.screen_to_world(sx, sy)
            dx = wx - body.position[0]
            dy = wy - body.position[1]
            if body.shape == "circle":
                if dx * dx + dy * dy <= body.radius**2:
                    return body.id
            else:
                if abs(dx) <= body.half_width and abs(dy) <= body.half_height:
                    return body.id
        return None

    def mousePressEvent(self, event):  # noqa: N802
        sx, sy = event.position().x(), event.position().y()
        if event.button() == Qt.LeftButton:
            if self.add_mode in ("circle", "box"):
                wx, wy = self.screen_to_world(sx, sy)
                self.add_requested.emit(wx, wy)
            else:
                hit = self._hit_test(sx, sy)
                if hit:
                    self.selected_id = hit
                    self.body_selected.emit(hit)
                    body = self.world.bodies[hit]
                    wpos = self.world_to_screen(body.position[0], body.position[1])
                    self._drag_id = hit
                    self._drag_offset = QPointF(sx - wpos.x(), sy - wpos.y())
                else:
                    self.selected_id = None
                    self.body_selected.emit("")
        self.update()

    def mouseMoveEvent(self, event):  # noqa: N802
        if self._drag_id and self._drag_id in self.world.bodies:
            sx = event.position().x() - self._drag_offset.x()
            sy = event.position().y() - self._drag_offset.y()
            wx, wy = self.screen_to_world(sx, sy)
            self.world.bodies[self._drag_id].position = (wx, wy)
            self.update()

    def mouseReleaseEvent(self, event):  # noqa: N802
        self._drag_id = None

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self.update()


# --------------------------------------------------------------------------
# Sandbox page
# --------------------------------------------------------------------------
class Sandbox2DPage(BasePage):
    def __init__(self, ctx: AppContext, parent: Optional[QWidget] = None):
        super().__init__("2D Sandbox",
                         "Interactive physics sandbox — add bodies, apply gravity, and simulate.",
                         parent)
        self.ctx = ctx
        self.world = World2D(gravity=(0.0, -9.80665))
        self.world.bounds = (-20, -12, 20, 12)
        self.engine = Engine2D(self.world)
        self.engine.collision_enabled = True

        self.canvas = SandboxCanvas(self.world)

        # Playback timer (~60 Hz)
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._tick)
        self.time_scale = 1.0

        self._build_controls()
        self._build_layout()
        self._seed_demo_scene()

    def _build_controls(self) -> None:
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setObjectName("Primary")
        self.play_btn.clicked.connect(self._toggle_play)
        self.step_btn = QPushButton("Step")
        self.step_btn.clicked.connect(self._single_step)
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self._reset)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear)

        self.add_combo = QComboBox()
        self.add_combo.addItem("Add Circle", "circle")
        self.add_combo.addItem("Add Box", "box")
        self.add_combo.addItem("Select / Drag", "select")
        self.add_combo.currentIndexChanged.connect(self._on_add_mode)

        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.1, 4.0)
        self.speed_spin.setDecimals(1)
        self.speed_spin.setValue(1.0)
        self.speed_spin.setSuffix("×")

        self.gravity_spin = QDoubleSpinBox()
        self.gravity_spin.setRange(-30, 30)
        self.gravity_spin.setDecimals(2)
        self.gravity_spin.setValue(-9.80665)
        self.gravity_spin.setSuffix(" m/s²")
        self.gravity_spin.valueChanged.connect(
            lambda v: setattr(self.world, "gravity", (0.0, v)))

    def _build_layout(self) -> None:
        # Toolbar row
        toolbar = QHBoxLayout()
        for w in (self.play_btn, self.step_btn, self.reset_btn, self.clear_btn):
            toolbar.addWidget(w)
        toolbar.addSpacing(12)
        toolbar.addWidget(QLabel("Tool:"))
        toolbar.addWidget(self.add_combo)
        toolbar.addSpacing(12)
        toolbar.addWidget(QLabel("Speed:"))
        toolbar.addWidget(self.speed_spin)
        toolbar.addSpacing(12)
        toolbar.addWidget(QLabel("Gravity:"))
        toolbar.addWidget(self.gravity_spin)
        toolbar.addStretch(1)
        self.add_toolbar_widget(self._hwrap(toolbar))

        # Main: canvas (left) + inspector/chart (right)
        body = QHBoxLayout()
        body.setSpacing(12)
        body.addWidget(self.canvas, 3)

        right = QVBoxLayout()
        right.setSpacing(8)
        # Inspector
        self.inspector_box = QGroupBox("Selected body")
        il = QFormLayout(self.inspector_box)
        self.insp_id = QLabel("—")
        self.insp_shape = QLabel("—")
        self.insp_pos = QLabel("—")
        self.insp_vel = QLabel("—")
        self.insp_mass = QDoubleSpinBox(); self.insp_mass.setRange(0.1, 1000); self.insp_mass.setValue(1.0)
        self.insp_mass.valueChanged.connect(self._update_selected_mass)
        self.insp_radius = QDoubleSpinBox(); self.insp_radius.setRange(0.1, 10); self.insp_radius.setValue(0.5)
        self.insp_radius.valueChanged.connect(self._update_selected_radius)
        self.insp_restitution = QDoubleSpinBox(); self.insp_restitution.setRange(0, 1); self.insp_restitution.setDecimals(2); self.insp_restitution.setValue(0.5)
        self.insp_restitution.valueChanged.connect(self._update_selected_restitution)
        il.addRow("ID", self.insp_id)
        il.addRow("Shape", self.insp_shape)
        il.addRow("Position", self.insp_pos)
        il.addRow("Velocity", self.insp_vel)
        il.addRow("Mass (kg)", self.insp_mass)
        il.addRow("Radius (m)", self.insp_radius)
        il.addRow("Restitution", self.insp_restitution)
        right.addWidget(self.inspector_box)

        # Chart of recorded speeds
        right.addWidget(QLabel("Recorded speeds (m/s)"))
        self.chart = ChartWidget(height=180)
        right.addWidget(self.chart, 1)
        body.addLayout(right, 1)
        self.add_body_widget(self._lwrap(body), 1)

        self.canvas.add_requested.connect(self._add_body)
        self.canvas.body_selected.connect(self._select_body)
        self._enable_recording()

    @staticmethod
    def _hwrap(layout: QHBoxLayout) -> QWidget:
        w = QWidget()
        w.setLayout(layout)
        return w

    @staticmethod
    def _lwrap(layout: QHBoxLayout) -> QWidget:
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addLayout(layout)
        return w

    # -- scene ------------------------------------------------------------
    def _seed_demo_scene(self) -> None:
        # A ground, a couple of circles, and a box.
        ground = Body2D(id="ground", shape="box", position=(0.0, -5.5),
                        half_width=15.0, half_height=0.5, is_static=True, color="#8aa0bd")
        self.world.add_body(ground)
        self._add_body(-4.0, 3.0, shape="circle", radius=0.6, color=ACCENT)
        self._add_body(-1.0, 5.0, shape="circle", radius=0.4, color=ACCENT_BLUE)
        self._add_body(2.0, 4.0, shape="box", color="#f59e0b")

    def _add_body(self, x: float, y: float, shape: Optional[str] = None,
                  radius: float = 0.5, color: Optional[str] = None) -> None:
        shape = shape or self.canvas.add_mode
        if shape == "select":
            return
        bid = f"b{len(self.world.bodies)}"
        if shape == "circle":
            body = Body2D(id=bid, shape="circle", position=(x, y), radius=radius,
                          color=color or ACCENT)
        else:
            body = Body2D(id=bid, shape="box", position=(x, y),
                          half_width=radius, half_height=radius, color=color or ACCENT_BLUE)
        self.world.add_body(body)
        self.canvas.update()

    # -- playback ---------------------------------------------------------
    def _tick(self) -> None:
        dt = (1.0 / 60.0) * self.time_scale
        # sub-step for stability at high time scales
        steps = max(1, int(self.time_scale))
        for _ in range(steps):
            self.engine.step(dt / steps)
        self.canvas.update()
        self._update_inspector()
        self._update_chart()

    def _toggle_play(self) -> None:
        if self.timer.isActive():
            self.timer.stop()
            self.play_btn.setText("▶ Play")
        else:
            self.timer.start()
            self.play_btn.setText("❚❚ Pause")

    def _single_step(self) -> None:
        self.engine.step(1.0 / 60.0)
        self.canvas.update()
        self._update_inspector()

    def _reset(self) -> None:
        self.timer.stop()
        self.play_btn.setText("▶ Play")
        # Store initial positions would require snapshot; here we just zero velocities.
        for body in self.world.bodies.values():
            body.velocity = (0.0, 0.0)
            body.angular_velocity = 0.0
            body.force = (0.0, 0.0)
        self.engine.reset()
        self.canvas.update()

    def _clear(self) -> None:
        self.timer.stop()
        self.play_btn.setText("▶ Play")
        self.world.clear()
        self.canvas.update()

    # -- inspector sync ---------------------------------------------------
    def _on_add_mode(self) -> None:
        self.canvas.add_mode = self.add_combo.currentData()

    def _select_body(self, body_id: str) -> None:
        if body_id and body_id in self.world.bodies:
            b = self.world.bodies[body_id]
            self.insp_id.setText(b.id)
            self.insp_shape.setText(b.shape)
            self.insp_mass.blockSignals(True); self.insp_mass.setValue(b.mass); self.insp_mass.blockSignals(False)
            self.insp_radius.blockSignals(True); self.insp_radius.setValue(b.radius); self.insp_radius.blockSignals(False)
            self.insp_restitution.blockSignals(True); self.insp_restitution.setValue(b.restitution); self.insp_restitution.blockSignals(False)
        self._update_inspector()

    def _update_inspector(self) -> None:
        sid = self.canvas.selected_id
        if sid and sid in self.world.bodies:
            b = self.world.bodies[sid]
            self.insp_pos.setText(f"({b.position[0]:.2f}, {b.position[1]:.2f})")
            self.insp_vel.setText(f"({b.velocity[0]:.2f}, {b.velocity[1]:.2f})")

    def _update_selected_mass(self, v: float) -> None:
        sid = self.canvas.selected_id
        if sid and sid in self.world.bodies:
            self.world.bodies[sid].mass = v

    def _update_selected_radius(self, v: float) -> None:
        sid = self.canvas.selected_id
        if sid and sid in self.world.bodies:
            b = self.world.bodies[sid]
            if b.shape == "circle":
                b.radius = v
            else:
                b.half_width = v; b.half_height = v
            self.canvas.update()

    def _update_selected_restitution(self, v: float) -> None:
        sid = self.canvas.selected_id
        if sid and sid in self.world.bodies:
            self.world.bodies[sid].restitution = v

    def _update_chart(self) -> None:
        if len(self.world.recordings) < 2:
            return
        # Plot speed of each circle body over time.
        series = []
        times = [s["time"] for s in self.world.recordings]
        for bid, body in self.world.bodies.items():
            if body.is_static or body.shape != "circle":
                continue
            ys = [s.get(f"{bid}.speed", 0.0) for s in self.world.recordings]
            series.append((times, ys, bid, ACCENT if len(series) == 0 else ACCENT_BLUE))
        if series:
            self.chart.plot_series(series, "time (s)", "speed (m/s)", "Body speeds")

    # Enable recording.
    def _enable_recording(self) -> None:
        self.world.record_interval = 0.05