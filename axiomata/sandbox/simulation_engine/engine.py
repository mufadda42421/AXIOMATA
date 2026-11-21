"""A 2D rigid-body physics simulation engine.

This is a real, deterministic physics integrator (semi-implicit Euler) with:
  * circles and axis-aligned boxes (treated as boxes for collision),
  * forces (gravity, drag, springs, user forces),
  * collision detection and response (impulse-based with restitution + friction),
  * measurement probes and recorded time-series data.

The engine is UI-agnostic: it operates on plain data structures so it can be
driven by the 2D sandbox, tests, or a headless batch run. SI units are used
throughout (metres, kilograms, seconds); the renderer scales to pixels.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Optional

Vec2 = tuple[float, float]


def _add(a: Vec2, b: Vec2) -> Vec2:
    return (a[0] + b[0], a[1] + b[1])


def _sub(a: Vec2, b: Vec2) -> Vec2:
    return (a[0] - b[0], a[1] - b[1])


def _mul(a: Vec2, s: float) -> Vec2:
    return (a[0] * s, a[1] * s)


def _dot(a: Vec2, b: Vec2) -> float:
    return a[0] * b[0] + a[1] * b[1]


def _length(a: Vec2) -> float:
    return math.hypot(a[0], a[1])


def _normalize(a: Vec2) -> Vec2:
    l = _length(a)
    if l == 0:
        return (0.0, 0.0)
    return (a[0] / l, a[1] / l)


# --------------------------------------------------------------------------
# World / body definitions
# --------------------------------------------------------------------------
@dataclass
class Body2D:
    """A rigid body in the 2D world.

    Shape is one of: 'circle' (radius) or 'box' (half_width, half_height).
    Dynamic bodies respond to forces; static bodies (inv_mass == 0) do not move.
    """
    id: str
    shape: str = "circle"
    position: Vec2 = (0.0, 0.0)
    velocity: Vec2 = (0.0, 0.0)
    angle: float = 0.0          # radians (rotation about z)
    angular_velocity: float = 0.0
    radius: float = 0.5
    half_width: float = 0.5
    half_height: float = 0.5
    mass: float = 1.0
    color: str = "#22d3ee"
    restitution: float = 0.5
    friction: float = 0.3
    is_static: bool = False
    # accumulated force for the current step
    force: Vec2 = (0.0, 0.0)
    torque: float = 0.0
    # bookkeeping
    contacts: int = 0

    @property
    def inv_mass(self) -> float:
        return 0.0 if self.is_static else (1.0 / self.mass if self.mass > 0 else 0.0)

    @property
    def inertia(self) -> float:
        if self.is_static or self.mass <= 0:
            return 0.0
        if self.shape == "circle":
            return 0.5 * self.mass * self.radius**2
        # solid box about z axis
        w = 2 * self.half_width
        h = 2 * self.half_height
        return self.mass * (w**2 + h**2) / 12.0

    @property
    def inv_inertia(self) -> float:
        i = self.inertia
        return 0.0 if i <= 0 else 1.0 / i

    def apply_force(self, fx: float, fy: float) -> None:
        self.force = (self.force[0] + fx, self.force[1] + fy)

    def apply_torque(self, t: float) -> None:
        self.torque += t


@dataclass
class Measurement:
    name: str
    body_id: str
    value: float
    time: float


@dataclass
class World2D:
    """A collection of bodies plus environment parameters.

    The coordinate system is right-handed with +y up (the renderer flips y for
    screen coordinates). Gravity is a vector so it can be reoriented.
    """
    bodies: dict[str, Body2D] = field(default_factory=dict)
    gravity: Vec2 = (0.0, -9.80665)
    linear_damping: float = 0.0     # fraction of velocity lost per second
    angular_damping: float = 0.0
    time: float = 0.0
    bounds: Optional[tuple[float, float, float, float]] = None  # xmin,ymin,xmax,ymax
    # recorded time-series data: list of dicts
    recordings: list[dict] = field(default_factory=list)
    record_interval: float = 0.0     # if > 0, sample at this interval
    _last_record: float = 0.0

    def add_body(self, body: Body2D) -> Body2D:
        self.bodies[body.id] = body
        return body

    def remove_body(self, body_id: str) -> None:
        self.bodies.pop(body_id, None)

    def get_body(self, body_id: str) -> Optional[Body2D]:
        return self.bodies.get(body_id)

    def clear(self) -> None:
        self.bodies.clear()
        self.recordings.clear()
        self.time = 0.0


# --------------------------------------------------------------------------
# Collision detection (circle-circle, circle-box approx, box-box via AABB)
# --------------------------------------------------------------------------
def _circle_circle(a: Body2D, b: Body2D) -> Optional[tuple[Vec2, float]]:
    d = _sub(b.position, a.position)
    dist = _length(d)
    rsum = a.radius + b.radius
    if dist < rsum and dist > 0:
        return _mul(d, 1.0 / dist), rsum - dist  # normal, penetration
    if dist == 0:
        return (1.0, 0.0), rsum
    return None


def _circle_box(circle: Body2D, box: Body2D) -> Optional[tuple[Vec2, float]]:
    # Closest point on the (axis-aligned, un-rotated for simplicity) box to circle.
    cx = max(box.position[0] - box.half_width,
             min(circle.position[0], box.position[0] + box.half_width))
    cy = max(box.position[1] - box.half_height,
             min(circle.position[1], box.position[1] + box.half_height))
    closest = (cx, cy)
    d = _sub(circle.position, closest)
    dist = _length(d)
    if dist < circle.radius:
        if dist == 0:
            n = (0.0, 1.0)
        else:
            n = _mul(d, 1.0 / dist)
        return n, circle.radius - dist  # normal points from box to circle
    return None


def _box_box_aabb(a: Body2D, b: Body2D) -> Optional[tuple[Vec2, float]]:
    dx = b.position[0] - a.position[0]
    px = (a.half_width + b.half_width) - abs(dx)
    if px <= 0:
        return None
    dy = b.position[1] - a.position[1]
    py = (a.half_height + b.half_height) - abs(dy)
    if py <= 0:
        return None
    if px < py:
        n = (1.0 if dx > 0 else -1.0, 0.0)
        return n, px
    n = (0.0, 1.0 if dy > 0 else -1.0)
    return n, py


def detect_collision(a: Body2D, b: Body2D) -> Optional[tuple[Vec2, float]]:
    """Return (normal from a to b, penetration depth) or None."""
    if a.shape == "circle" and b.shape == "circle":
        res = _circle_circle(a, b)
        return res
    if a.shape == "circle" and b.shape == "box":
        res = _circle_box(a, b)
        return res
    if a.shape == "box" and b.shape == "circle":
        # normal from box to circle; flip to a->b
        res = _circle_box(b, a)
        if res is None:
            return None
        n, pen = res
        return (_mul(n, -1.0), pen)
    return _box_box_aabb(a, b)


# --------------------------------------------------------------------------
# The engine
# --------------------------------------------------------------------------
class Engine2D:
    """Advances a :class:`World2D` forward in time.

    Integration is semi-implicit (symplectic) Euler for stability. Collision
    response uses sequential impulses with restitution and Coulomb friction.
    """

    def __init__(self, world: World2D):
        self.world = world
        self.collision_enabled = True

    def step(self, dt: float) -> None:
        if dt <= 0:
            return
        world = self.world

        # 1. Integrate forces -> velocity.
        for body in world.bodies.values():
            if body.is_static:
                continue
            ax = world.gravity[0] + body.force[0] / body.mass if body.mass > 0 else 0.0
            ay = world.gravity[1] + body.force[1] / body.mass if body.mass > 0 else 0.0
            # linear damping
            damp = max(0.0, 1.0 - world.linear_damping * dt)
            body.velocity = (body.velocity[0] * damp + ax * dt,
                             body.velocity[1] * damp + ay * dt)
            # angular
            if body.inv_inertia > 0:
                body.angular_velocity += body.torque * body.inv_inertia * dt
            adamp = max(0.0, 1.0 - world.angular_damping * dt)
            body.angular_velocity *= adamp
            # reset accumulators
            body.force = (0.0, 0.0)
            body.torque = 0.0
            body.contacts = 0

        # 2. Integrate velocity -> position.
        for body in world.bodies.values():
            if body.is_static:
                continue
            body.position = (body.position[0] + body.velocity[0] * dt,
                             body.position[1] + body.velocity[1] * dt)
            body.angle += body.angular_velocity * dt

        # 3. Collision detection + response (a few iterations for stability).
        if self.collision_enabled:
            bodies = list(world.bodies.values())
            for _iter in range(4):
                resolved_any = False
                for i in range(len(bodies)):
                    for j in range(i + 1, len(bodies)):
                        if self._resolve(bodies[i], bodies[j]):
                            resolved_any = True
                if not resolved_any:
                    break

        # 4. Bounds constraint (keep bodies inside world bounds if set).
        self._enforce_bounds()

        # 5. Advance time and record.
        world.time += dt
        if world.record_interval > 0 and world.time - world._last_record >= world.record_interval:
            self._record(world.time)

    def _resolve(self, a: Body2D, b: Body2D) -> bool:
        col = detect_collision(a, b)
        if col is None:
            return False
        n, penetration = col
        # Positional correction (split by inverse mass).
        total_inv = a.inv_mass + b.inv_mass
        if total_inv > 0:
            correction = _mul(n, penetration / total_inv * 0.8)
            a.position = _sub(a.position, _mul(correction, a.inv_mass))
            b.position = _add(b.position, _mul(correction, b.inv_mass))
        # Relative velocity along normal.
        rv = _sub(b.velocity, a.velocity)
        vel_along_normal = _dot(rv, n)
        if vel_along_normal > 0:
            return True  # separating; skip impulse
        e = min(a.restitution, b.restitution)
        j_impulse = -(1 + e) * vel_along_normal / total_inv if total_inv > 0 else 0.0
        impulse = _mul(n, j_impulse)
        a.velocity = _sub(a.velocity, _mul(impulse, a.inv_mass))
        b.velocity = _add(b.velocity, _mul(impulse, b.inv_mass))

        # Friction (tangent impulse).
        tangent = _sub(rv, _mul(n, _dot(rv, n)))
        if _length(tangent) > 1e-9:
            t = _normalize(tangent)
            jt = -_dot(rv, t) / total_inv if total_inv > 0 else 0.0
            mu = math.sqrt(a.friction * b.friction)
            # Coulomb clamp
            max_friction = abs(j_impulse) * mu
            jt = max(-max_friction, min(max_friction, jt))
            friction_impulse = _mul(t, jt)
            a.velocity = _sub(a.velocity, _mul(friction_impulse, a.inv_mass))
            b.velocity = _add(b.velocity, _mul(friction_impulse, b.inv_mass))

        a.contacts += 1
        b.contacts += 1
        return True

    def _enforce_bounds(self) -> None:
        b = self.world.bounds
        if b is None:
            return
        xmin, ymin, xmax, ymax = b
        for body in self.world.bodies.values():
            if body.is_static:
                continue
            if body.shape == "circle":
                r = body.radius
                p = list(body.position)
                v = list(body.velocity)
                if p[0] - r < xmin:
                    p[0] = xmin + r; v[0] = -v[0] * body.restitution
                elif p[0] + r > xmax:
                    p[0] = xmax - r; v[0] = -v[0] * body.restitution
                if p[1] - r < ymin:
                    p[1] = ymin + r; v[1] = -v[1] * body.restitution
                elif p[1] + r > ymax:
                    p[1] = ymax - r; v[1] = -v[1] * body.restitution
                body.position = (p[0], p[1])
                body.velocity = (v[0], v[1])
            else:
                p = list(body.position)
                v = list(body.velocity)
                hw, hh = body.half_width, body.half_height
                if p[0] - hw < xmin:
                    p[0] = xmin + hw; v[0] = -v[0] * body.restitution
                elif p[0] + hw > xmax:
                    p[0] = xmax - hw; v[0] = -v[0] * body.restitution
                if p[1] - hh < ymin:
                    p[1] = ymin + hh; v[1] = -v[1] * body.restitution
                elif p[1] + hh > ymax:
                    p[1] = ymax - hh; v[1] = -v[1] * body.restitution
                body.position = (p[0], p[1])
                body.velocity = (v[0], v[1])

    def _record(self, t: float) -> None:
        snapshot: dict = {"time": t}
        for bid, body in self.world.bodies.items():
            snapshot[f"{bid}.x"] = body.position[0]
            snapshot[f"{bid}.y"] = body.position[1]
            snapshot[f"{bid}.vx"] = body.velocity[0]
            snapshot[f"{bid}.vy"] = body.velocity[1]
            snapshot[f"{bid}.speed"] = _length(body.velocity)
        self.world.recordings.append(snapshot)

    # -- helpers for the sandbox -----------------------------------------
    def reset(self) -> None:
        self.world.time = 0.0
        self.world.recordings.clear()
        self.world._last_record = 0.0