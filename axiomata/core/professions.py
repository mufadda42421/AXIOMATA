"""Profession definitions and per-profession workspace configuration.

Profession selection is a *personalisation* layer, NOT an access-control
system. Every profession has access to every department; the selection only
influences the default dashboard, sidebar ordering, and quick-start suggestions.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Profession:
    key: str
    name: str
    description: str
    icon: str
    # Navigation destinations the profession cares most about (ordered).
    shortcuts: list[str] = field(default_factory=list)
    # Quick-start actions emphasised on the dashboard.
    quick_start: list[str] = field(default_factory=list)
    welcome: str = ""


PROFESSIONS: list[Profession] = [
    Profession(
        key="physicist",
        name="Physicist",
        description="Mechanics, thermodynamics, fields, and optics.",
        icon="⚛",
        shortcuts=["physics", "mathematics", "sandbox_3d", "data_analysis"],
        quick_start=["physics", "sandbox_3d", "data_analysis"],
        welcome="Welcome, Physicist. Your virtual laboratory is ready.",
    ),
    Profession(
        key="chemist",
        name="Chemist",
        description="Periodic table, molecules, reactions, stoichiometry.",
        icon="⚗",
        shortcuts=["chemistry", "mathematics", "data_analysis"],
        quick_start=["chemistry", "data_analysis"],
        welcome="Welcome, Chemist. Explore molecular structures and reactions.",
    ),
    Profession(
        key="biologist",
        name="Biologist",
        description="Cells, genetics, populations, and ecosystems.",
        icon="🧬",
        shortcuts=["biology", "sandbox_2d", "data_analysis"],
        quick_start=["biology", "sandbox_2d"],
        welcome="Welcome, Biologist. Investigate life from cells to ecosystems.",
    ),
    Profession(
        key="astronomer",
        name="Astronomer",
        description="Orbital mechanics, planets, stars, and eclipses.",
        icon="🔭",
        shortcuts=["astronomy", "mathematics", "sandbox_3d"],
        quick_start=["astronomy", "sandbox_3d"],
        welcome="Welcome, Astronomer. Model the mechanics of the cosmos.",
    ),
    Profession(
        key="mechanical_engineer",
        name="Mechanical Engineer",
        description="Forces, motion, rotational dynamics, mechanisms.",
        icon="⚙",
        shortcuts=["engineering", "physics", "sandbox_2d", "sandbox_3d"],
        quick_start=["engineering", "sandbox_2d"],
        welcome="Welcome, Engineer. Build and analyse mechanical systems.",
    ),
    Profession(
        key="electrical_engineer",
        name="Electrical Engineer",
        description="Circuits, voltage, current, resistance, fields.",
        icon="🔌",
        shortcuts=["engineering", "physics", "mathematics"],
        quick_start=["engineering", "physics"],
        welcome="Welcome, Engineer. Simulate and analyse electrical circuits.",
    ),
    Profession(
        key="civil_engineer",
        name="Civil Engineer",
        description="Structural loads, beams, stress, and strain.",
        icon="🏗",
        shortcuts=["engineering", "sandbox_2d", "mathematics"],
        quick_start=["engineering", "sandbox_2d"],
        welcome="Welcome, Engineer. Explore structural mechanics and loads.",
    ),
    Profession(
        key="mathematician",
        name="Mathematician",
        description="Algebra, calculus, matrices, symbolic solving.",
        icon="∑",
        shortcuts=["mathematics", "data_analysis", "sandbox_2d"],
        quick_start=["mathematics", "data_analysis"],
        welcome="Welcome, Mathematician. Compute, solve, and visualise.",
    ),
    Profession(
        key="researcher",
        name="Scientific Researcher",
        description="Projects, experiments, notebooks, and analysis.",
        icon="🔬",
        shortcuts=["projects", "notebook", "data_analysis", "library"],
        quick_start=["project", "notebook", "data_analysis"],
        welcome="Welcome, Researcher. Organise projects and analyse data.",
    ),
    Profession(
        key="student",
        name="Student",
        description="Guided labs across every scientific discipline.",
        icon="🎓",
        shortcuts=["physics", "chemistry", "biology", "mathematics", "sandbox_2d"],
        quick_start=["physics", "chemistry", "mathematics"],
        welcome="Welcome, Student. Explore interactive science across disciplines.",
    ),
    Profession(
        key="interdisciplinary",
        name="Interdisciplinary Scientist",
        description="Combine departments, simulations, and data freely.",
        icon="🧭",
        shortcuts=[
            "physics",
            "chemistry",
            "biology",
            "astronomy",
            "engineering",
            "mathematics",
            "sandbox_3d",
            "data_analysis",
        ],
        quick_start=["sandbox_3d", "data_analysis", "notebook"],
        welcome="Welcome. Bridge disciplines in one scientific workspace.",
    ),
    Profession(
        key="custom",
        name="Custom Workspace",
        description="A blank slate with every tool available.",
        icon="🛠",
        shortcuts=["projects", "sandbox_2d", "data_analysis", "notebook"],
        quick_start=["project", "sandbox_2d", "data_analysis"],
        welcome="Welcome. Your custom scientific workspace is ready.",
    ),
]

PROFESSION_BY_KEY: dict[str, Profession] = {p.key: p for p in PROFESSIONS}


def get_profession(key: str | None) -> Profession | None:
    if not key:
        return None
    return PROFESSION_BY_KEY.get(key)