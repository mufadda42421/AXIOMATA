"""Central navigation model: the single source of truth for destinations.

Each destination has a stable key, a label, a Lucide icon name, and a group.
The sidebar, project switcher, command search, and dashboard quick-start all read
from here so adding a department is a one-line change.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NavItem:
    key: str
    label: str
    icon: str
    group: str  # workspace | laboratories | simulation | research | tools


NAV_ITEMS: list[NavItem] = [
    NavItem("home", "Overview", "home", "workspace"),
    NavItem("projects", "Research Projects", "folder", "workspace"),
    NavItem("experiments", "Recent Experiments", "activity", "workspace"),
    NavItem("physics", "Physics", "atom", "laboratories"),
    NavItem("chemistry", "Chemistry", "flask", "laboratories"),
    NavItem("biology", "Biology", "dna", "laboratories"),
    NavItem("astronomy", "Astronomy", "orbit", "laboratories"),
    NavItem("engineering", "Engineering", "settings", "laboratories"),
    NavItem("mathematics", "Mathematics", "calculator", "laboratories"),
    NavItem("sandbox_2d", "2D Sandbox", "grid", "simulation"),
    NavItem("sandbox_3d", "3D Sandbox", "cube", "simulation"),
    NavItem("data_analysis", "Data Analysis", "chart", "research"),
    NavItem("notebook", "Research Notebook", "note", "research"),
    NavItem("library", "Scientific Library", "book", "research"),
    NavItem("settings", "Settings", "settings", "tools"),
]

NAV_BY_KEY: dict[str, NavItem] = {item.key: item for item in NAV_ITEMS}

# Ordered section definitions for the sidebar.
GROUP_TITLES = {
    "workspace": "Workspace",
    "laboratories": "Laboratories",
    "simulation": "Simulation",
    "research": "Research Tools",
    "tools": "",
}

GROUP_ORDER = ["workspace", "laboratories", "simulation", "research", "tools"]