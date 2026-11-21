# AXIOMATA — Scientific Research & Simulation Environment

**Explore. Experiment. Understand.**

AXIOMATA is a modular, offline scientific desktop workstation for Windows 10/11.
It combines research project management, virtual laboratories across six
scientific disciplines, interactive 2D and 3D physics sandboxes, a digital
research notebook, an offline scientific reference library, and a data-analysis
environment — all in one application.

There is **no login, account, or authentication**. On first launch you pick a
scientific profession purely to personalise your dashboard and shortcuts; every
discipline still has access to every department, and the profession can be
changed at any time in Settings without losing any data.

---

## Quick start

```powershell
# From the project root (D:\AXIOMATA)
python run.py
```

First launch shows the profession-selection screen. Pick a discipline, then
explore the sidebar.

### Where your data lives

All user data is stored **outside** the installation directory, in:

```
%APPDATA%\AXIOMATA\
    database\        axiomata.sqlite  scientific.duckdb  backups\
    projects\        <project_id>\ (project.json, experiments, datasets, …)
    library\         constants, periodic_table, astronomy, formulas
    cache\  logs\  settings\
```

The location can be overridden with the `AXIOMATA_DATA` environment variable.

---

## Features

### Workspaces (sidebar)
| Destination | What it does |
|---|---|
| **Home** | Welcome dashboard, quick-start, recent projects & activity |
| **Research Projects** | Create/edit/archive/duplicate projects; per-project folders |
| **Experiment Records** | Create experiments linked to a project; store results |
| **Research Notebook** | Markdown notes with live preview, autosave, `.md` export |
| **Scientific Library** | Offline constants, SI units, formulas, unit converter |
| **Physics Laboratory** | Projectile, pendulum, collisions, circuits, gas laws, optics |
| **Chemistry Laboratory** | Periodic table, molar mass, equation balancer, stoichiometry |
| **Biology Laboratory** | Mendelian genetics, population growth, predator–prey, selection |
| **Astronomy Laboratory** | Solar system data, orbits, Kepler, moon phases |
| **Engineering Laboratory** | Rotational dynamics, DC circuits, beam/structural analysis |
| **Mathematics Laboratory** | Symbolic calculus, matrices, vectors, plotting, numerical methods |
| **2D Sandbox** | Interactive physics editor with grid, objects, forces, charts |
| **3D Sandbox** | PyVista 3D viewport with spheres/boxes, gravity, simulation |
| **Data Analysis** | Import CSV/JSON/Excel/Parquet/HDF5; stats, regression, charts |
| **Settings** | Profession, theme, units, autosave, backup, data location |

### Scientific accuracy
- All calculations use SI units and are **unit-tested** (see `tests/`).
- Governing equations and model assumptions are shown in each lab.
- Results are labelled as *calculated*, *simulated*, or *reference* — never
  presented as laboratory measurements.
- Simplified engineering models carry explicit "not for safety-critical design"
  warnings.
- Imported datasets are never silently altered; transformations work on a copy.

---

## Architecture

```
axiomata/
    main.py                 entry point
    core/                   config, events, application context, professions
    database/               SQLite + DuckDB managers, repositories, migrations
    ui/                     main window, sidebar, dashboard, dialogs, themes, pages
    modules/                physics, chemistry, biology, astronomy, engineering, math
    sandbox/                simulation engine (2D + 3D), 2D & 3D sandbox pages
    analytics/              dataset import, statistics
    scientific_library/     constants, units, formulas, conversions
    services/               logging, (backup/import-export)
    tests/                  scientific-correctness tests
```

- **SQLite** stores metadata: projects, experiments, notes, datasets, activity,
  settings, with foreign keys, indexes, and migrations.
- **DuckDB** handles analytical queries on datasets (separate from metadata).
- The **simulation engine** is renderer-agnostic; the 2D and 3D sandboxes only
  read transforms from it, so physics can run headless or be driven by any view.
- UI panels receive a single `AppContext` (paths, settings, DB, event bus,
  repositories), avoiding scattered globals and keeping the app testable.

### Dependencies
Python 3.14 with: PySide6, NumPy, SciPy, SymPy, pandas, matplotlib, DuckDB,
Astropy, RDKit, PyVista, pyvistaqt. (PyBullet is optional; the 3D sandbox uses a
built-in physics engine so it works without it.) See `requirements.txt`.

---

## Tests

```powershell
python -m pytest tests/ -q
```

The suite verifies scientific correctness of every engine: projectile range,
Kepler's third law, Snell's law, Mendelian ratios, collision momentum/energy
conservation, regression slope, unit conversion, and more.

---

## Development status

Phases 1–5 are implemented and tested. Phase 6 (packaging) is in progress:
a PyInstaller spec and installer guidance will be added for Windows distribution.