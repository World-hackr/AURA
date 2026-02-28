from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.engines.calculation_engine import calculate_led_resistor
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use ABSOLUTE paths for robust serving
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
parts_library_path = os.path.join(BASE_DIR, "parts_library")

class NoCacheStaticFiles(StaticFiles):
    def is_not_modified(self, response_headers, request_headers) -> bool:
        return False
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

# Mount the new modular library folder
app.mount("/symbols", NoCacheStaticFiles(directory=parts_library_path), name="symbols")

@app.get("/")
def root():
    return {"message": "AURA Backend running - Modular Mode"}

@app.get("/api/components")
def get_components():
    all_parts = []
    try:
        # Scan every folder in parts_library
        for part_dir in os.listdir(parts_library_path):
            manifest_path = os.path.join(parts_library_path, part_dir, "manifest.json")
            if os.path.exists(manifest_path):
                with open(manifest_path, "r") as f:
                    part_data = json.load(f)
                    
                    # Transform local paths to URL paths
                    # e.g. "assets/breadboard.svg" -> "arduino_nano/assets/breadboard.svg"
                    if "views" in part_data:
                        for view in part_data["views"]:
                            if part_data["views"][view]:
                                part_data["views"][view] = f"{part_dir}/{part_data['views'][view]}"
                    
                    all_parts.append(part_data)
        return all_parts
    except Exception as e:
        return {"error": f"Scanner failed: {str(e)}"}

@app.get("/calculate_led_resistor")
def led_resistor(vs: float, vf: float, current: float):
    resistance = calculate_led_resistor(vs, vf, current)
    return {"resistance": resistance, "unit": "ohms"}