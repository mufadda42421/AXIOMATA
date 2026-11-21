"""Simulation engine (2D physics) tests."""
import math

import pytest

from axiomata.sandbox.simulation_engine import Body2D, Engine2D, World2D


def test_free_fall_matches_gravity():
    world = World2D(gravity=(0.0, -9.80665))
    body = Body2D(id="a", position=(0.0, 100.0))
    world.add_body(body)
    engine = Engine2D(world)
    dt = 0.001
    for _ in range(1000):  # 1 second
        engine.step(dt)
    # y should drop by ~ 0.5 g t^2 = 4.903
    assert body.position[1] == pytest.approx(100.0 - 0.5 * 9.80665 * 1.0, abs=0.01)
    # velocity ~ -g t
    assert body.velocity[1] == pytest.approx(-9.80665, abs=0.05)


def test_static_body_does_not_move():
    world = World2D()
    body = Body2D(id="wall", position=(0.0, 0.0), is_static=True)
    world.add_body(body)
    engine = Engine2D(world)
    for _ in range(100):
        engine.step(0.01)
    assert body.position == (0.0, 0.0)


def test_force_acceleration():
    world = World2D(gravity=(0.0, 0.0))
    body = Body2D(id="a", mass=2.0)
    world.add_body(body)
    engine = Engine2D(world)
    # apply 10 N for 1 second -> a = 5 m/s^2, v = 5 m/s
    for _ in range(100):
        body.apply_force(10.0, 0.0)
        engine.step(0.01)
    assert body.velocity[0] == pytest.approx(5.0, abs=0.05)


def test_circle_collision_conserves_momentum():
    world = World2D(gravity=(0.0, 0.0))
    a = Body2D(id="a", position=(-0.6, 0.0), velocity=(2.0, 0.0), mass=1.0, radius=0.5)
    b = Body2D(id="b", position=(0.6, 0.0), velocity=(-2.0, 0.0), mass=1.0, radius=0.5)
    world.add_body(a); world.add_body(b)
    engine = Engine2D(world)
    p_before = a.mass * a.velocity[0] + b.mass * b.velocity[0]
    for _ in range(200):
        engine.step(0.001)
    p_after = a.mass * a.velocity[0] + b.mass * b.velocity[0]
    # Momentum should be conserved (equal masses, head-on).
    assert p_after == pytest.approx(p_before, abs=1e-3)
    # With restitution 0.5 they should bounce apart somewhat.
    assert a.velocity[0] < 0 and b.velocity[0] > 0


def test_inelastic_collision_merges_velocity():
    world = World2D(gravity=(0.0, 0.0))
    a = Body2D(id="a", position=(-0.6, 0.0), velocity=(1.0, 0.0), mass=1.0, radius=0.5, restitution=0.0)
    b = Body2D(id="b", position=(0.6, 0.0), velocity=(0.0, 0.0), mass=1.0, radius=0.5, restitution=0.0)
    world.add_body(a); world.add_body(b)
    engine = Engine2D(world)
    for _ in range(300):
        engine.step(0.001)
    # They should end up moving together at roughly the same velocity.
    assert abs(a.velocity[0] - b.velocity[0]) < 0.1
    assert a.velocity[0] == pytest.approx(0.5, abs=0.05)


def test_bounds_keep_body_inside():
    world = World2D(gravity=(0.0, -9.8), bounds=(0.0, 0.0, 10.0, 10.0))
    body = Body2D(id="a", position=(5.0, 1.0), radius=0.5)
    world.add_body(body)
    engine = Engine2D(world)
    for _ in range(500):
        engine.step(0.001)
    # body rests on the floor (y ~= radius)
    assert body.position[1] >= 0.4
    assert body.position[1] <= 1.0


def test_recording_produces_timeseries():
    world = World2D(gravity=(0.0, -9.8), record_interval=0.1)
    body = Body2D(id="a", position=(0.0, 10.0))
    world.add_body(body)
    engine = Engine2D(world)
    for _ in range(200):
        engine.step(0.01)
    assert len(world.recordings) > 0
    snap = world.recordings[0]
    assert "time" in snap
    assert "a.y" in snap and "a.speed" in snap


def test_box_box_collision():
    from axiomata.sandbox.simulation_engine.engine import detect_collision
    a = Body2D(id="a", shape="box", position=(0.0, 0.0), half_width=1.0, half_height=1.0)
    b = Body2D(id="b", shape="box", position=(1.5, 0.0), half_width=1.0, half_height=1.0)
    col = detect_collision(a, b)
    assert col is not None  # overlapping by 0.5
    n, pen = col
    assert pen == pytest.approx(0.5, abs=0.01)


def test_circle_box_collision():
    from axiomata.sandbox.simulation_engine.engine import detect_collision
    box = Body2D(id="box", shape="box", position=(0.0, 0.0), half_width=1.0, half_height=1.0)
    circle = Body2D(id="c", shape="circle", position=(1.4, 0.0), radius=0.5)
    col = detect_collision(box, circle)
    assert col is not None


def test_no_collision_when_separated():
    from axiomata.sandbox.simulation_engine.engine import detect_collision
    a = Body2D(id="a", position=(0.0, 0.0), radius=0.5)
    b = Body2D(id="b", position=(5.0, 5.0), radius=0.5)
    assert detect_collision(a, b) is None


def test_energy_roughly_conserved_elastic():
    world = World2D(gravity=(0.0, 0.0))
    a = Body2D(id="a", position=(-1.0, 0.0), velocity=(1.0, 0.0), mass=1.0, radius=0.5, restitution=1.0)
    b = Body2D(id="b", position=(1.0, 0.0), velocity=(-1.0, 0.0), mass=1.0, radius=0.5, restitution=1.0)
    world.add_body(a); world.add_body(b)
    engine = Engine2D(world)
    ke_before = 0.5 * a.mass * 1.0**2 + 0.5 * b.mass * 1.0**2
    for _ in range(200):
        engine.step(0.001)
    ke_after = 0.5 * a.mass * a.velocity[0]**2 + 0.5 * b.mass * b.velocity[0]**2
    assert ke_after == pytest.approx(ke_before, rel=0.02)