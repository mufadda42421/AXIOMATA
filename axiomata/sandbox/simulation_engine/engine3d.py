"""A lightweight 3D rigid-body physics engine (renderer-agnostic).

This provides real 3D rigid-body dynamics for spheres and boxes under gravity
with ground-plane contact and sphere-sphere / sphere-box collisions. It is a
cleanly separated simulation core: the PyVista viewport in ``sandbox_3d_page``
only reads body transforms from this engine.

When PyBullet is available it can be used as a higher-fidelity backend, but the
built-in engine keeps the 3D sandbox fully functional offline with no extra
dependencies. Both share the same ``Body3D`` / ``World3D`` data model.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

Vec3 = tuple[float, float, float]


def _add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _mul(a: Vec3, s: float) -> Vec3:
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _length(a: Vec3) -> float:
    return math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2)


@dataclass
class Body3D:
    id: str
    shape: str = "sphere"          # 'sphere' | 'box'
    position: Vec3 = (0.0, 0.0, 0.0)
    velocity: Vec3 = (0.0, 0.0, 0.0)
    radius: float = 0.5
    half_extents: Vec3 = (0.5, 0.5, 0.5)
    mass: float = 1.0
    color: str = "#22d3ee"
    restitution: float = 0.4
    is_static: bool = False
    force: Vec3 = (0.0, 0.0, 0.0)

    @property
    def inv_mass(self) -> float:
        if self.is_static:
            return 0.0
        return 1.0 / self.mass if self.mass > 0 else 0.0

    def apply_force(self, fx: float, fy: float, fz: float) -> None:
        self.force = (self.force[0] + fx, self.force[1] + fy, self.force[2] + fz)


@dataclass
class World3D:
    bodies: dict[str, Body3D] = field(default_factory=dict)
    gravity: Vec3 = (0.0, -9.80665, 0.0)
    ground_y: float = 0.0
    has_ground: bool = True
    time: float = 0.0

    def add_body(self, body: Body3D) -> Body3D:
        self.bodies[body.id] = body
        return body

    def remove_body(self, body_id: str) -> None:
        self.bodies.pop(body_id, None)

    def clear(self) -> None:
        self.bodies.clear()
        self.time = 0.0


class Engine3D:
    """Advances a :class:`World3D` using semi-implicit Euler integration."""

    def __init__(self, world: World3D):
        self.world = world

    def step(self, dt: float) -> None:
        if dt <= 0:
            return
        for body in self.world.bodies.values():
            if body.is_static:
                continue
            ax = self.world.gravity[0] + body.force[0] * body.inv_mass
            ay = self.world.gravity[1] + body.force[1] * body.inv_mass
            az = self.world.gravity[2] + body.force[2] * body.inv_mass
            body.velocity = (body.velocity[0] + ax * dt,
                             body.velocity[1] + ay * dt,
                             body.velocity[2] + az * dt)
            body.force = (0.0, 0.0, 0.0)
            body.position = (body.position[0] + body.velocity[0] * dt,
                             body.position[1] + body.velocity[1] * dt,
                             body.position[2] + body.velocity[2] * dt)
        self._resolve_collisions()
        self._ground_constraint()
        self.world.time += dt

    def _ground_constraint(self) -> None:
        if not self.world.has_ground:
            return
        gy = self.world.ground_y
        for body in self.world.bodies.values():
            if body.is_static:
                continue
            if body.shape == "sphere":
                floor = gy + body.radius
                if body.position[1] < floor:
                    body.position = (body.position[0], floor, body.position[2])
                    if body.velocity[1] < 0:
                        body.velocity = (body.velocity[0],
                                         -body.velocity[1] * body.restitution,
                                         body.velocity[2])
            else:
                floor = gy + body.half_extents[1]
                if body.position[1] < floor:
                    body.position = (body.position[0], floor, body.position[2])
                    if body.velocity[1] < 0:
                        body.velocity = (body.velocity[0],
                                         -body.velocity[1] * body.restitution,
                                         body.velocity[2])

    def _resolve_collisions(self) -> None:
        # Include static bodies as collision partners, but only iterate dynamic
        # bodies as the "a" side to avoid double-handling.
        all_bodies = list(self.world.bodies.values())
        dynamic = [b for b in all_bodies if not b.is_static]
        for a in dynamic:
            for b in all_bodies:
                if b.id == a.id:
                    continue
                self._collide_pair(a, b)

    def _collide_pair(self, a: Body3D, b: Body3D) -> None:
        if a.shape == "sphere" and b.shape == "sphere":
            d = _sub(b.position, a.position)
            dist = _length(d)
            rsum = a.radius + b.radius
            if 0 < dist < rsum:
                n = _mul(d, 1.0 / dist)
                self._impulse(a, b, n, rsum - dist)
        elif a.shape == "sphere" and b.shape == "box":
            # approximate box as sphere of radius = min half extent
            self._sphere_box(a, b)
        elif a.shape == "box" and b.shape == "sphere":
            self._sphere_box(b, a)

    def _sphere_box(self, sphere: Body3D, box: Body3D) -> None:
        # Closest point on AABB to sphere centre.
        cx = max(box.position[0] - box.half_extents[0],
                 min(sphere.position[0], box.position[0] + box.half_extents[0]))
        cy = max(box.position[1] - box.half_extents[1],
                 min(sphere.position[1], box.position[1] + box.half_extents[1]))
        cz = max(box.position[2] - box.half_extents[2],
                 min(sphere.position[2], box.position[2] + box.half_extents[2]))
        closest = (cx, cy, cz)
        d = _sub(sphere.position, closest)
        dist = _length(d)
        if 0 < dist < sphere.radius:
            # Normal from box to sphere; impulse() expects normal a->b,
            # so pass (box, sphere) with normal pointing box->sphere.
            n = _mul(d, 1.0 / dist)
            self._impulse(box, sphere, n, sphere.radius - dist)

    def _impulse(self, a: Body3D, b: Body3D, n: Vec3, penetration: float) -> None:
        total_inv = a.inv_mass + b.inv_mass
        if total_inv <= 0:
            return
        correction = _mul(n, penetration / total_inv * 0.8)
        a.position = _sub(a.position, _mul(correction, a.inv_mass))
        b.position = _add(b.position, _mul(correction, b.inv_mass))
        rv = _sub(b.velocity, a.velocity)
        vn = _dot(rv, n)
        if vn > 0:
            return
        e = min(a.restitution, b.restitution)
        j = -(1 + e) * vn / total_inv
        impulse = _mul(n, j)
        a.velocity = _sub(a.velocity, _mul(impulse, a.inv_mass))
        b.velocity = _add(b.velocity, _mul(impulse, b.inv_mass))

    def reset(self) -> None:
        for body in self.world.bodies.values():
            body.velocity = (0.0, 0.0, 0.0)
            body.force = (0.0, 0.0, 0.0)
        self.world.time = 0.0