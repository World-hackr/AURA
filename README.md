# AURA | Virtual Circuit Designer

A professional-grade, web-based circuit visualization and design environment built for sub-pixel precision and realistic "Digital Twin" component interaction.

## 🚀 Key Features
- **Golden Unit System:** Built on a physical constant where `1u = 0.3175mm`, ensuring perfect alignment with standard electronic pitches (8u = 2.54mm).
- **Modular Library Architecture:** A "One-Folder-per-Part" system allowing for easy sharing and discovery of components via `manifest.json`.
- **High-Fidelity Rendering:** High-DPI HTML5 Canvas rendering with realistic SVG assets derived from the Fritzing ecosystem.
- **Precision Interaction:** 90-degree rotation engine and rotation-aware Pin Magnet snapping for perfectly aligned layouts.
- **Interactive HUD:** Live coordinate tracking, pin labels, and context-aware design instructions.

## 🛠 Tech Stack
- **Backend:** FastAPI (Python) - Modular component scanner and electronic logic engine.
- **Frontend:** Vanilla JavaScript (ESM) & HTML5 Canvas.
- **Styling:** Custom CSS with theme support (Dark, Blueprint, Light).

## 📥 Setup & Installation

### 1. Backend
```bash
cd backend
python -m venv venv
source venv/Scripts/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 2. Frontend
Simply open `frontend/index.html` in any modern web browser or serve via Live Server.

---
*Created by Santo - Documentation Updated: Feb 28, 2026*
