const canvas = document.getElementById("workspace");
const ctx = canvas.getContext("2d");
const scaleCanvas = document.getElementById("scale-overlay");
const scaleCtx = scaleCanvas.getContext("2d");

let texture = new Image();
texture.src = "assets/textures/texture1.jpg";

let zoom = 1.0;
let offsetX = 0;
let offsetY = 0;
let texZoom = 1.0;
let texOffsetX = 0;
let texOffsetY = 0;

let isEditingTexture = false;
let isFirstLoad = true;
let dpr = window.devicePixelRatio || 1;

const BASE_UNIT_MM = 0.3175; 
let pixelsPerUnit = 10;
let accentColor = "#4a90e2";

let dragging = false;
let draggedComponent = null;
let selectedComponent = null;
let placingComponent = null;
let hoveredPin = null;

let showGrid = true;
let gridOpacity = 0.4;
let textureIsDark = true;
let useSketchyStyle = true;

const SymbolManager = {
    cache: {},
    async load(type, viewPath) {
        if (this.cache[type]) return this.cache[type];
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = "anonymous";
            img.onload = () => {
                this.cache[type] = img;
                resolve(img);
            };
            img.onerror = (e) => {
                console.error(`Failed to fetch ${type}`);
                reject(e);
            };
            img.src = `http://127.0.0.1:8000/symbols/${viewPath}?t=${Date.now()}`;
        });
    }
};

let COMPONENT_DEFS = {};
let backendOnline = false;

async function initLibrary() {
    try {
        const response = await fetch("http://127.0.0.1:8000/api/components");
        if (!response.ok) throw new Error();
        const data = await response.json();
        
        COMPONENT_DEFS = {}; 
        data.forEach(comp => {
            COMPONENT_DEFS[comp.type] = comp;
        });

        renderFlatPalette(data);
        backendOnline = true;
        draw();
    } catch (e) {
        backendOnline = false;
        draw();
    }
}

function renderFlatPalette(data) {
    const container = document.getElementById("component-palette");
    if (!container) return;
    container.innerHTML = "";

    data.forEach(part => {
        const btn = document.createElement("button");
        btn.className = "tool-btn";
        btn.innerText = part.label.split(' ')[0]; // Simple short name
        btn.onclick = () => {
            document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            addComponent(part.type);
        };
        container.appendChild(btn);
    });
}

let components = [];

async function addComponent(type) {
    if (!backendOnline) {
        alert("Backend is offline.");
        await initLibrary();
        return;
    }
    const def = COMPONENT_DEFS[type];
    if (!def) return;

    placingComponent = { 
        type: type, 
        uX: 0, uY: 0,
        rotation: 0,
        state: { pwr_on: true, d13_on: true, tx_on: true, rx_on: true } 
    };
    SymbolManager.load(type, def.views.breadboard).then(() => draw());
}

window.onkeydown = (e) => {
    const key = e.key.toLowerCase();
    if (key === 'r') {
        if (selectedComponent) {
            selectedComponent.rotation = (selectedComponent.rotation + 90) % 360;
            draw();
        } else if (placingComponent) {
            placingComponent.rotation = (placingComponent.rotation + 90) % 360;
            draw();
        }
    }
    if (e.key === 'Delete' || e.key === 'Backspace') {
        if (selectedComponent) {
            components = components.filter(c => c !== selectedComponent);
            selectedComponent = null;
            draw();
        }
    }
};

function toggleStyle() {
    useSketchyStyle = !useSketchyStyle;
    const btn = document.getElementById("style-toggle-btn");
    if (btn) btn.innerText = useSketchyStyle ? "STYLE: SKETCHY" : "STYLE: CLEAN";
    draw();
}

function getMouseInUnits(e) {
    const rect = canvas.getBoundingClientRect();
    const uX = Math.round((e.clientX - rect.left - offsetX) / (zoom * pixelsPerUnit));
    const uY = Math.round((offsetY - (e.clientY - rect.top)) / (zoom * pixelsPerUnit));
    return { uX, uY };
}

function isMouseOverComponent(uX, uY, comp) {
    const def = COMPONENT_DEFS[comp.type];
    if (!def) return false;
    const rad = -(comp.rotation || 0) * Math.PI / 180;
    const dx = uX - comp.uX;
    const dy = uY - comp.uY;
    const rx = dx * Math.cos(rad) - dy * Math.sin(rad);
    const ry = dx * Math.sin(rad) + dy * Math.cos(rad);
    return Math.abs(rx) <= def.uW / 2 && Math.abs(ry) <= def.uH / 2;
}

function draw() {
    ctx.clearRect(0, 0, canvas.width / dpr, canvas.height / dpr);
    if (texture.complete) {
        ctx.save();
        ctx.translate(texOffsetX, texOffsetY);
        ctx.scale(texZoom, texZoom);
        ctx.drawImage(texture, 0, 0);
        ctx.restore();
    }
    if (showGrid) drawGrid();
    drawAllComponents();
    if (placingComponent) drawGhost();
    if (hoveredPin) drawPinLabel(hoveredPin);
    drawScale();
}

function drawGrid() {
    const step = pixelsPerUnit * zoom;
    const width = canvas.width / dpr;
    const height = canvas.height / dpr;
    const colorBase = textureIsDark ? 255 : 0;
    ctx.lineWidth = 1 / dpr;
    if (step > 5) {
        ctx.strokeStyle = `rgba(${colorBase}, ${colorBase}, ${colorBase}, ${gridOpacity * 0.15})`;
        ctx.beginPath();
        for(let x = offsetX % step; x < width; x += step) { ctx.moveTo(x, 0); ctx.lineTo(x, height); }
        for(let y = offsetY % step; y < height; y += step) { ctx.moveTo(0, y); ctx.lineTo(width, y); }
        ctx.stroke();
    }
    const majorStep = step * 8;
    if (majorStep > 5) {
        ctx.strokeStyle = `rgba(${colorBase}, ${colorBase}, ${colorBase}, ${gridOpacity * 0.4})`;
        ctx.beginPath();
        for(let x = offsetX % majorStep; x < width; x += majorStep) { ctx.moveTo(x, 0); ctx.lineTo(x, height); }
        for(let y = offsetY % majorStep; y < height; y += majorStep) { ctx.moveTo(0, y); ctx.lineTo(width, y); }
        ctx.stroke();
    }
    ctx.strokeStyle = `rgba(${colorBase}, ${colorBase}, ${colorBase}, ${gridOpacity})`;
    ctx.beginPath();
    if (offsetX >= 0 && offsetX <= width) { ctx.moveTo(offsetX, 0); ctx.lineTo(offsetX, height); }
    if (offsetY >= 0 && offsetY <= height) { ctx.moveTo(0, offsetY); ctx.lineTo(width, offsetY); }
    ctx.stroke();
}

function drawAllComponents() { components.forEach(comp => drawComponent(comp, comp === selectedComponent ? 1.0 : 0.9)); }
function drawGhost() { if (placingComponent) drawComponent(placingComponent, 0.5); }

function drawComponent(comp, opacity) {
    const def = COMPONENT_DEFS[comp.type];
    const img = SymbolManager.cache[comp.type];
    if (!def || !img) return;
    const u = pixelsPerUnit * zoom;
    const screenX = offsetX + comp.uX * u;
    const screenY = offsetY - comp.uY * u;
    
    ctx.save();
    ctx.translate(screenX, screenY);
    ctx.rotate((comp.rotation || 0) * Math.PI / 180);
    ctx.imageSmoothingEnabled = false;
    const drawX = Math.round(-def.originX * u);
    const drawY = Math.round(-def.originY * u);
    const drawW = Math.round(def.uW * u);
    const drawH = Math.round(def.uH * u);
    ctx.globalAlpha = opacity;
    ctx.drawImage(img, drawX, drawY, drawW, drawH);
    
    if (def.indicators && comp.state) {
        def.indicators.forEach(ind => {
            let isOn = false;
            if (ind.id === 'PWR') isOn = comp.state.pwr_on;
            else if (ind.id === 'L') isOn = comp.state.d13_on;
            else if (ind.id === 'TX') isOn = comp.state.tx_on;
            else if (ind.id === 'RX') isOn = comp.state.rx_on;
            if (isOn) {
                ctx.fillStyle = ind.color;
                ctx.beginPath();
                ctx.arc(ind.uX * u, -ind.uY * u, 1.5 * zoom, 0, Math.PI * 2);
                ctx.fill();
            }
        });
    }
    ctx.globalAlpha = opacity * 0.7;
    ctx.fillStyle = accentColor || "#4a90e2";
    if (def.pins) {
        def.pins.forEach(pin => {
            ctx.beginPath();
            ctx.arc(pin.uX * u, -pin.uY * u, 2 * zoom, 0, Math.PI * 2);
            ctx.fill();
        });
    }
    if (comp === selectedComponent) {
        ctx.strokeStyle = accentColor || "#4a90e2";
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.strokeRect(drawX - 2, drawY - 2, drawW + 4, drawH + 4);
    }
    ctx.restore();
}

function drawPinLabel(pin) {
    const u = pixelsPerUnit * zoom;
    const screenX = offsetX + pin.uX * u;
    const screenY = offsetY - pin.uY * u;
    ctx.save();
    ctx.font = `bold ${Math.max(10, 12 * zoom)}px Monospace`;
    const txt = pin.label;
    const tw = ctx.measureText(txt).width;
    ctx.fillStyle = "rgba(0,0,0,0.8)";
    ctx.fillRect(screenX + 10, screenY - 25, tw + 10, 20);
    ctx.fillStyle = accentColor || "#4a90e2";
    ctx.fillText(txt, screenX + 15, screenY - 10);
    ctx.strokeStyle = "white";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(screenX, screenY, 4 * zoom, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
}

function drawScale() {
    const frame = document.getElementById("workspace-frame");
    const container = document.getElementById("workspace-container");
    if (!frame || !container) return;
    const rect = frame.getBoundingClientRect();
    const contRect = container.getBoundingClientRect();
    const startX = rect.left - contRect.left;
    const startY = rect.top - contRect.top;
    scaleCtx.clearRect(0, 0, scaleCanvas.width / dpr, scaleCanvas.height / dpr);
    if (selectedComponent) {
        scaleCtx.fillStyle = "rgba(0,0,0,0.7)";
        scaleCtx.beginPath();
        scaleCtx.roundRect(contRect.width/2 - 80, 60, 160, 24, 12);
        scaleCtx.fill();
        scaleCtx.fillStyle = "white";
        scaleCtx.textAlign = "center";
        scaleCtx.font = "bold 10px Monospace";
        scaleCtx.fillText("PRESS 'R' TO ROTATE", contRect.width/2, 75);
    }
    const isLight = frame.style.background === "rgb(255, 255, 255)";
    scaleCtx.textAlign = "left";
    scaleCtx.fillStyle = backendOnline ? "#4caf50" : "#f44336";
    scaleCtx.font = "bold 9px Monospace";
    scaleCtx.fillText(backendOnline ? "● BACKEND: ONLINE" : "● BACKEND: OFFLINE", startX, startY - 30);
    scaleCtx.fillStyle = isLight ? "#111" : (accentColor || "#4a90e2");
    scaleCtx.font = "bold 11px Monospace";
    scaleCtx.fillText("AURA | VIRTUAL GRID SYSTEM", startX, startY - 18);
    scaleCtx.fillStyle = isLight ? "rgba(0,0,0,0.6)" : "rgba(255,255,255,0.5)";
    scaleCtx.font = "9px Monospace";
    scaleCtx.fillText(`UNIT: ${BASE_UNIT_MM}mm | CAL: ${pixelsPerUnit}px/u | ZOOM: ${zoom.toFixed(2)}x`, startX, startY - 6);
    const pxPerU = pixelsPerUnit * zoom;
    const potentialSteps = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000];
    let unitStep = potentialSteps.find(s => s * pxPerU >= 45) || 1000;
    const spacing = unitStep * pxPerU;
    scaleCtx.fillStyle = isLight ? "rgba(0,0,0,0.4)" : "rgba(255,255,255,0.4)";
    scaleCtx.textAlign = "center";
    for(let x = Math.ceil(-offsetX / spacing) * spacing + offsetX; x < rect.width; x += spacing) {
        if (x < -1) continue;
        scaleCtx.fillText(Math.round((x - offsetX) / pxPerU) + "u", startX + x, startY + rect.height + 16);
    }
    scaleCtx.textAlign = "right";
    for(let y = Math.ceil(-offsetY / spacing) * spacing + offsetY; y < rect.height; y += spacing) {
        if (y < -1) continue;
        scaleCtx.fillText(Math.round((offsetY - y) / pxPerU) + "u", startX - 10, startY + y + 3);
    }
}

canvas.onmousedown = (e) => {
    const { uX, uY } = getMouseInUnits(e);
    draggedComponent = components.find(c => isMouseOverComponent(uX, uY, c));
    selectedComponent = draggedComponent; 
    isPanning = !draggedComponent;
    dragging = true;
    lastX = e.clientX;
    lastY = e.clientY;
    draw();
};
window.onmouseup = () => { dragging = false; draggedComponent = null; };
window.onmousemove = (e) => {
    const { uX, uY } = getMouseInUnits(e);
    const coordEl = document.getElementById("coord-display");
    if (coordEl) coordEl.innerText = `${uX}u, ${uY}u`;
    hoveredPin = null;
    for (const comp of components) {
        const def = COMPONENT_DEFS[comp.type];
        if (def && def.pins) {
            for (const pin of def.pins) {
                const rad = (comp.rotation || 0) * Math.PI / 180;
                const rx = pin.uX * Math.cos(rad) - (-pin.uY) * Math.sin(rad);
                const ry = pin.uX * Math.sin(rad) + (-pin.uY) * Math.cos(rad);
                const pinWorldX = comp.uX + rx;
                const pinWorldY = comp.uY + (-ry);
                const dist = Math.sqrt((uX - pinWorldX)**2 + (uY - pinWorldY)**2);
                if (dist < 3) { hoveredPin = { label: pin.label, uX: pinWorldX, uY: pinWorldY }; break; }
            }
        }
        if (hoveredPin) break;
    }
    if (placingComponent) { placingComponent.uX = uX; placingComponent.uY = uY; draw(); return; }
    if (!dragging) { draw(); return; }
    if (draggedComponent) {
        const dragDef = COMPONENT_DEFS[draggedComponent.type];
        let snapOffset = { x: 0, y: 0 };
        let activeSnap = false;
        if (dragDef && dragDef.pins) {
            for (const dragPin of dragDef.pins) {
                const rad = (draggedComponent.rotation || 0) * Math.PI / 180;
                const rx = dragPin.uX * Math.cos(rad) - (-dragPin.uY) * Math.sin(rad);
                const ry = dragPin.uX * Math.sin(rad) + (-dragPin.uY) * Math.cos(rad);
                const myPinX = uX + rx;
                const myPinY = uY + (-ry);
                for (const otherComp of components) {
                    if (otherComp === draggedComponent) continue;
                    const otherDef = COMPONENT_DEFS[otherComp.type];
                    if (!otherDef || !otherDef.pins) continue;
                    for (const otherPin of otherDef.pins) {
                        const orad = (other.rotation || 0) * Math.PI / 180;
                        const orx = otherPin.uX * Math.cos(orad) - (-otherPin.uY) * Math.sin(orad);
                        const ory = otherPin.uX * Math.sin(orad) + (-otherPin.uY) * Math.cos(orad);
                        const targetX = other.uX + orx;
                        const targetY = other.uY + (-ory);
                        const dist = Math.sqrt((myPinX - targetX)**2 + (myPinY - targetY)**2);
                        if (dist < 4) {
                            activeSnap = true; 
                            snapOffset.x = targetX - rx;
                            snapOffset.y = targetY - (-ry);
                            break;
                        }
                    }
                    if (activeSnap) break;
                }
                if (activeSnap) break;
            }
        }
        if (activeSnap) { draggedComponent.uX = snapOffset.x; draggedComponent.uY = snapOffset.y; }
        else { draggedComponent.uX = uX; draggedComponent.uY = uY; }
    } else if (isPanning) {
        const dx = e.clientX - lastX; const dy = e.clientY - lastY;
        if (isEditingTexture) { texOffsetX += dx; texOffsetY += dy; }
        else { offsetX += dx; offsetY += dy; }
    }
    lastX = e.clientX; lastY = e.clientY; draw();
};
canvas.onclick = (e) => {
    if (placingComponent) {
        const { uX, uY } = getMouseInUnits(e);
        const newComp = { ...placingComponent, uX, uY, id: Date.now() };
        components.push(newComp);
        selectedComponent = newComp; 
        placingComponent = null; draw();
    }
};
canvas.onwheel = (e) => {
    e.preventDefault();
    const isTex = isEditingTexture;
    let currentZoom = isTex ? texZoom : zoom;
    let newZoom = currentZoom * (e.deltaY < 0 ? 1.1 : 0.9);
    newZoom = Math.max(0.1, Math.min(50, newZoom));
    const mouseX = e.offsetX; const mouseY = e.offsetY;
    if (isTex) {
        const wx = (mouseX - texOffsetX) / texZoom; const wy = (mouseY - texOffsetY) / texZoom;
        texZoom = newZoom; texOffsetX = mouseX - wx * texZoom; texOffsetY = mouseY - wy * texZoom;
    } else {
        const wx = (mouseX - offsetX) / zoom; const wy = (mouseY - offsetY) / zoom;
        zoom = newZoom; offsetX = mouseX - wx * zoom; offsetY = mouseY - wy * zoom;
    }
    draw();
};

function setGridOpacity(v) { gridOpacity = v/100; draw(); }
function toggleGrid() { showGrid = !showGrid; const btn = document.getElementById("grid-toggle-btn"); if (btn) btn.classList.toggle("active", showGrid); draw(); }
function toggleTextureLock() { isEditingTexture = !isEditingTexture; const btn = document.getElementById("bg-lock-btn"); const sg = document.getElementById("status-group"); const st = document.getElementById("status-text"); if (btn) btn.classList.toggle("active", isEditingTexture); if (sg) sg.classList.toggle("editing", isEditingTexture); if (st) st.innerText = isEditingTexture ? "ALIGN" : "GRID"; }
function resetOrigin() { const rect = canvas.getBoundingClientRect(); zoom = 1.0; offsetX = 0; offsetY = rect.height; draw(); }
function setGridResolution(v) { pixelsPerUnit = parseFloat(v); draw(); }
function setAccentColor(c) { accentColor = c; document.documentElement.style.setProperty('--accent-color', c); const light = document.getElementById("status-light"); const text = document.getElementById("status-text"); if (light) { light.style.background = c; light.style.boxShadow = `0 0 8px ${c}`; } if (text) text.style.color = c; draw(); }
function setTheme(theme) { const frame = document.getElementById("workspace-frame"); const container = document.getElementById("workspace-container"); if (!frame || !container) return; if(theme === 'blueprint') { frame.style.background = "#003366"; container.style.background = "radial-gradient(circle at center, #002244 0%, #001122 100%)"; } else if(theme === 'light') { frame.style.background = "#ffffff"; container.style.background = "#dcdcdc"; } else { frame.style.background = "#000"; container.style.background = "radial-gradient(circle at center, #1a1a1a 0%, #0a0a0a 100%)"; } draw(); }
function setTexture(n) { texture.src = "assets/textures/" + n; texture.onload = () => { analyzeTextureBrightness(); draw(); }; }
function analyzeTextureBrightness() { if (!texture.complete || texture.width === 0) return; const tc = document.createElement('canvas'); tc.width = tc.height = 1; const tctx = tc.getContext('2d'); tctx.drawImage(texture, 0, 0, 1, 1); const d = tctx.getImageData(0, 0, 1, 1).data; textureIsDark = ((d[0] * 299 + d[1] * 587 + d[2] * 114) / 1000) < 128; draw(); }
function resizeWorkspace() {
    const frame = document.getElementById("workspace-frame");
    const container = document.getElementById("workspace-container");
    dpr = window.devicePixelRatio || 1;
    const rect = frame.getBoundingClientRect();
    const contRect = container.getBoundingClientRect();
    canvas.width = rect.width * dpr; canvas.height = rect.height * dpr;
    canvas.style.width = rect.width + "px"; canvas.style.height = rect.height + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    scaleCanvas.width = contRect.width * dpr; scaleCanvas.height = contRect.height * dpr;
    scaleCanvas.style.width = contRect.width + "px"; scaleCanvas.style.height = contRect.height + "px";
    scaleCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (isFirstLoad) { offsetX = 0; offsetY = rect.height; isFirstLoad = false; initLibrary(); }
    draw();
}
window.onresize = resizeWorkspace;
window.onload = resizeWorkspace;