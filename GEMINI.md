# AURA | Circuit Designer - Project Documentation

## 1. Project Vision
AURA is a professional-grade, web-based circuit visualization and design environment. Its core motive is to provide a "Digital Twin" system where components follow real-world physical dimensions, enabling AI-driven automated circuit generation and layout.

---

## 2. Technical Standards

### 2.1 The "Golden Unit" ($u$)
The entire coordinate system is built on a fixed physical constant:
- **1 Unit ($u$) = 0.3175mm (12.5 mils)**
- This unit was chosen because its multiples perfectly define standard electronic pitch:
    - **8u = 2.54mm (0.1")**: Standard DIP/Header pitch.
    - **4u = 1.27mm**: Standard SOIC pitch.
- **AI-Driven Design:** By using integers ($u$) instead of decimals ($mm$), LLMs can treat circuit design as a discrete grid-based layout task, eliminating rounding errors and improving precision.

---

## 3. Key Achievements

### 3.1 Advanced Workspace UI (Feb 27, 2026)
- **Centered Design Frame:** A rounded-corner workspace frame centered with a professional 3D shadow effect.
- **High-DPI Support:** Canvas backing-store scaling for perfectly sharp text and grid lines.
- **Intelligent Grid:** Level-of-Detail (LOD) system with Major (8u), Minor (1u), and Super (64u) grids.

### 3.2 Modular Architecture & Precision (Feb 28, 2026)
- **Modular Library System:** Migrated from a flat file structure to a professional **"One-Folder-per-Part"** system. Each component is now self-contained with its own `manifest.json` and assets.
- **Auto-Scanning Backend:** FastAPI now automatically discovers and registers components by scanning the `parts_library/` directory.
- **Rotation System:** Implemented a robust **90-degree rotation** engine (R key). All logical pins and hitboxes are rotation-aware, ensuring perfect grid alignment at any angle.
- **Pin Magnet Snap:** Implemented a sophisticated magnet system that allows pins to "jump" and lock onto each other with sub-unit precision ($4u$ range).
- **Geometric Calibration:** Performed mathematical sub-pixel alignment for resistors based on SVG `<rect>` snap anchors, ensuring a perfectly straight "axis" line when connecting parts tip-to-tip.
- **Interactive Pin HUD:** 
    - **Hover Labels:** Real-time tooltip labels derived from Fritzing metadata (e.g., "D13", "GND").
    - **Coordinate Stability:** Fixed coordinate display jitter using monospaced layout and minimum-width containers.
    - **Dynamic HUD:** Sleek top-center instruction pill for context-aware guidance (e.g., "PRESS R TO ROTATE").

### 3.3 AI-Augmented Library & Digital Twin (March 2, 2026)
- **AI-Powered Importer:** Integrated Google Gemini 2.0 Flash into `fritzing_importer.py`. The script now uses AI to cross-reference Fritzing metadata with official datasheets to fix pin labels and categories.
- **Mass Library Aurification:** Successfully processed 25+ components, normalizing categories (Passive, Microcontroller, etc.) and pin names (e.g., `VSS` -> `GND`, `Terminal 1`).
- **Interactive Component Mapping:** Introduced the "Digital Twin" metadata standard. Added `interactive` blocks to JSON manifests and injected specific IDs into SVGs (e.g., `led_glow`, `path_segA`) to allow real-time frontend animation.
- **Coordinate Sanity Engine:** Implemented coordinate validation logic to detect and fix "floating pins" caused by complex Fritzing SVG transforms, ensuring all components snap perfectly to the $1u$ grid.

---

## 4. Environment Structure
- **Backend:** FastAPI (Python) with Modular Component Scanner.
- **Frontend:** Vanilla JavaScript + HTML5 Canvas.
- **Library:** JSON-manifest driven folders (`backend/parts_library/`).

---

*Documentation updated: Feb 28, 2026*
