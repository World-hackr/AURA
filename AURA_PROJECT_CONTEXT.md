# AURA PROJECT — COMPLETE CONTEXT AND ARCHITECTURE SPECIFICATION

## PURPOSE OF THIS FILE

This file exists to instantly transfer full project context to any AI assistant without re-explaining the project.

This file defines:

* Project motive
* Architecture
* UI vision
* Simulation model
* Grid and coordinate system
* AI integration plan
* Current implementation status
* Next steps
* Interaction rules for AI assistants

Any AI reading this must treat this file as the authoritative source.

---

# PROJECT NAME

AURA — AI-Assisted Unified Circuit Realization and Analysis

---

# CORE PROJECT GOAL

AURA is a circuit learning, generation, simulation, and physical-mapping platform designed primarily for students and learning environments.

It must be able to:

1. Generate circuits using AI
2. Validate circuits using logical simulation
3. Map circuit nodes to real physical hardware nodes
4. Visually display circuits in true physical scale
5. Allow hardware node identification via LED indication
6. Work as both learning tool and physical realization assistant

This is NOT intended to replace professional tools like LTSpice or KiCad.

This is a learning-focused system prioritizing clarity and physical realism.

---

# CORE DIFFERENTIATOR

Unlike existing tools, AURA connects:

AI circuit generation

* logical simulation
* real-world hardware node mapping
* true physical coordinate grid

into one unified system.

---

# SYSTEM ARCHITECTURE OVERVIEW

The system consists of 4 major layers:

1. Frontend UI (visual editor)
2. Backend engine (logic, validation, routing)
3. Database (component definitions)
4. AI integration layer

---

# FRONTEND ARCHITECTURE

Technology:

HTML
CSS
JavaScript
Canvas rendering

Future possible migration:

WebGL or SVG hybrid

---

# CORE FRONTEND CONCEPT

The workspace is a fixed rectangular viewing frame containing:

Texture background
Grid overlay
Scale overlay
Circuit elements
Wire routing

The workspace represents real physical space.

---

# WORKSPACE REQUIREMENTS

Workspace must:

* Have fixed 4:3 aspect ratio
* Be positioned on right side of screen
* Have rounded white border
* Be visually separate from UI background
* Contain grid aligned to physical units
* Support smooth zoom and pan
* Prevent viewing outside valid bounds
* Maintain consistent coordinate system

---

# GRID SYSTEM DESIGN

This is critical.

Grid represents real physical spacing.

Base grid unit:

0.635 mm

This was chosen because it is half of 1.27 mm which is the most common electronics spacing.

Examples:

Breadboards use 2.54 mm
Headers use 2.54 mm
IC pins use 2.54 mm

0.635 mm provides enough resolution to represent all packages.

---

# GRID SCALE CONVERSION MODEL

We define:

grid_unit = 0.635 mm

pixel_per_grid_unit = variable (adjustable slider)

Example:

25 pixels per grid unit

means

25 pixels = 0.635 mm

---

# TEXTURE SYSTEM

Textures are visual only.

They simulate real surface:

fabric
leather
desk material

Texture does NOT define coordinate system.

Grid defines coordinate system.

Texture must scale with zoom.

---

# CAMERA MODEL

Camera properties:

zoom
offsetX
offsetY

Zoom must:

Zoom toward cursor position
Have minimum zoom limit
Have maximum zoom limit

Camera must NEVER allow showing outside valid workspace area.

---

# SCALE DISPLAY REQUIREMENTS

Scale must:

Show real coordinate values
Adjust dynamically with zoom
Avoid clutter
Increase spacing when zoomed out
Decrease spacing when zoomed in

Units supported:

mm
cm
inch (future)

---

# COMPONENT MODEL

Each component will be defined using JSON:

Example:

{
"type": "resistor",
"pins":
[
{ "x":0, "y":0 },
{ "x":10, "y":0 }
]
}

Pins MUST align to grid units.

Component position is defined by grid coordinates, not pixels.

---

# SIMULATION MODEL

Simulation is logical, not SPICE.

Each component has behavior rules.

Example LED:

If current > threshold → brightness proportional to current

Example transistor:

Base current controls collector current

Simulation propagates signals across graph network.

---

# DATABASE DESIGN

Database stores:

components
pin definitions
physical dimensions
simulation properties

Database format:

JSON initially
SQL later

---

# AI INTEGRATION MODEL

AI must output STRICT JSON.

AI is NOT trusted to generate executable logic.

AI only generates:

component list
connections
values

Backend validates everything.

AI providers interchangeable:

Gemini
OpenAI
local models future

AI interface must be modular.

---

# HARDWARE INTEGRATION GOAL

Physical nodes exist in real hardware.

Each node has address.

Software sends address → hardware → LED lights up.

User can locate real component.

---

# UI DESIGN PHILOSOPHY

UI must:

Be calm
Not overwhelming
Have textured background
Have hand-drawn aesthetic inspiration
Focus attention on circuit

Inspired by:

Moritz Klein circuit visuals

NOT professional CAD look.

Learning-focused.

---

# CURRENT IMPLEMENTATION STATUS

Completed:

Basic frontend structure
Canvas rendering
Zoom system
Pan system
Grid rendering
Texture rendering
Scale rendering
Texture switching
Grid size control

Not yet complete:

Correct workspace frame positioning
Component rendering
Wire rendering
Database integration
Simulation engine
AI integration

---

# CURRENT PROBLEM STATE

Workspace frame positioning unstable.

Root cause:

CSS layout conflict.

Not a logic problem.

Pure layout problem.

Must be solved cleanly in future step.

---

# NEXT DEVELOPMENT PRIORITY ORDER

Priority 1:

Fix workspace frame positioning permanently

Priority 2:

Implement component rendering

Priority 3:

Implement wire rendering

Priority 4:

Implement component database

Priority 5:

Implement logical simulation engine

Priority 6:

Implement AI interface

Priority 7:

Implement hardware node mapping

---

# AI ASSISTANT INTERACTION RULES

AI assistants must:

Never hallucinate features
Ask when unsure
Make minimal changes
Avoid breaking architecture
Prioritize correctness over speed
Prefer complete file replacements over partial edits

AI must assume:

User understands electronics well
User prefers precise control
User wants efficient implementation

AI must avoid:

unnecessary explanations
UI redesign without permission
changing core coordinate system

---

# USER WORK STYLE RULES

User prefers:

Terminal based workflow
Python backend
Precise control
No unnecessary abstraction
No token waste

AI responses should be:

Precise
Direct
Structured

---

# FINAL ARCHITECTURE PRINCIPLE

Grid is source of truth.

Everything derives from grid:

components
wires
scale
simulation
hardware mapping

NOT pixels.

Pixels are only visualization.

---

END OF FILE

