"""3D engine tests."""
import pytest

from axiomata.sandbox.simulation_engine.engine3d import (
    Body3D, Engine3D, World3D,
)


def test_free_fall_3d():
    world = World3D(gravity=(0.0, -9.80665, 0.0), has_ground=False)
    body = Body3D(id="a", position=(0.0, 100.0, 0.0))
    world.add_body(body)
    engine = Engine3D(world)
    for _ in range(1000):
        engine.step(0.001)
    assert body.position[1] == pytest.approx(100.0 - 0.5 * 9.80665, abs=0.01)
    assert body.velocity[1] == pytest.approx(-9.80665, abs=0.05)


def test_ground_bounce():
    world = World3D(gravity=(0.0, -9.80665, 0.0), has_ground=True, ground_y=0.0)
    body = Body3D(id="a", position=(0.0, 1.0, 0.0), radius=0.5, restitution=0.5)
    world.add_body(body)
    engine = Engine3D(world)
    for _ in range(500):
        engine.step(0.001)
    # Body should be resting on/above the floor.
    assert body.position[1] >= 0.49
    assert body.position[1] <= 1.0


def test_sphere_collision_conserves_momentum():
    world = World3D(gravity=(0.0, 0.0, 0.0), has_ground=False)
    a = Body3D(id="a", position=(-0.6, 0.0, 0.0), velocity=(2.0, 0.0, 0.0), mass=1.0, radius=0.5)
    b = Body3D(id="b", position=(0.6, 0.0, 0.0), velocity=(-2.0, 0.0, 0.0), mass=1.0, radius=0.5)
    world.add_body(a); world.add_body(b)
    engine = Engine3D(world)
    p_before = a.mass * a.velocity[0] + b.mass * b.velocity[0]
    for _ in range(200):
        engine.step(0.001)
    p_after = a.mass * a.velocity[0] + b.mass * b.velocity[0]
    assert p_after == pytest.approx(p_before, abs=1e-3)
    assert a.velocity[0] < 0 and b.velocity[0] > 0


def test_force_in_3d():
    world = World3D(gravity=(0.0, 0.0, 0.0), has_ground=False)
    body = Body3D(id="a", mass=2.0)
    world.add_body(body)
    engine = Engine3D(world)
    for _ in range(100):
        body.apply_force(0.0, 0.0, 10.0)
        engine.step(0.01)
    # a = 5 m/s^2 for 1s -> vz = 5
    assert body.velocity[2] == pytest.approx(5.0, abs=0.05)


def test_static_body_static():
    world = World3D(gravity=(0.0, -9.8, 0.0))
    body = Body3D(id="g", position=(0.0, -0.5, 0.0), is_static=True, shape="box",
                  half_extents=(10, 0.5, 10))
    world.add_body(body)
    engine = Engine3D(world)
    for _ in range(100):
        engine.step(0.01)
    assert body.position == (0.0, -0.5, 0.0)


def test_sphere_box_collision():
    world = World3D(gravity=(0.0, -9.80665, 0.0), has_ground=False)
    sphere = Body3D(id="s", shape="sphere", position=(0.0, 1.5, 0.0), radius=0.5, velocity=(0, -1, 0))
    box = Body3D(id="box", shape="box", position=(0.0, 0.0, 0.0), half_extents=(1, 0.5, 1), is_static=True)
    world.add_body(sphere); world.add_body(box)
    engine = Engine3D(world)
    hit = False
    for _ in range(300):
        engine.step(0.001)
        if sphere.velocity[1] > 0:
            hit = True
            break
    assert hit  # sphere bounced off the box