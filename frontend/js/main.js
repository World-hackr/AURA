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

        renderCategorizedPalette(data);
        backendOnline = true;
        draw();
    } catch (e) {
        backendOnline = false;
        draw();
    }
}

const CATEGORY_ICONS = {
    'Recent': '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z"/></svg>',
    'MCU': '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M6,4H18V5H21V7H18V9H21V11H18V13H21V15H18V17H21V19H18V20H6V19H3V17H6V15H3V13H6V11H3V9H6V7H3V5H6V4M11,15H13V17H11V15M11,11H13V13H11V11M11,7H13V9H11V7Z"/></svg>',
    'Passives': '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M2,11H7L10.07,15.35L13.11,4L18,11H22V13H16L13.15,19.32L9.9,7L7,13H2V11Z"/></svg>',
    'Optoelectronics': '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M12,2A7,7 0 0,0 5,9C5,11.38 6.19,13.47 8,14.74V17A1,1 0 0,0 9,18H15A1,1 0 0,0 16,17V14.74C17.81,13.47 19,11.38 19,9A7,7 0 0,0 12,2M9,21V20H15V21A1,1 0 0,1 14,22H10A1,1 0 0,1 9,21Z"/></svg>',
    'Switches': '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M17,7H7V17H17V7M17,5A2,2 0 0,1 19,7V17A2,2 0 0,1 17,19H7A2,2 0 0,1 5,17V7A2,2 0 0,1 7,5H17M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9Z"/></svg>',
    'Uncategorized': '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M12,2L3,7L12,12L21,7L12,2M12,14.67L3,9.67V16.5L12,21.5L21,16.5V9.67L12,14.67Z"/></svg>'
};

function getCategoryIcon(name) {
    return CATEGORY_ICONS[name] || CATEGORY_ICONS['Uncategorized'];
}

let recentComponents = [];
let activeCategory = 'Recent';

function renderCategorizedPalette(data) {
    const container = document.getElementById("component-palette");
    if (!container) return;
    container.innerHTML = "";

    // Add search bar
    const searchWrapper = document.createElement("div");
    searchWrapper.style.marginBottom = "10px";
    
    const searchInput = document.createElement("input");
    searchInput.type = "text";
    searchInput.placeholder = "Search components...";
    searchInput.className = "component-search";
    
    searchWrapper.appendChild(searchInput);
    container.appendChild(searchWrapper);

    const categories = {};
    
    // Auto-inject Recents if they exist
    if (recentComponents.length > 0) {
        categories['Recent'] = recentComponents.map(id => data.find(p => p.type === id)).filter(Boolean);
    }

    data.forEach(part => {
        const cat = part.category || 'Uncategorized';
        if (!categories[cat]) categories[cat] = [];
        categories[cat].push(part);
    });

    // If 'Recent' is empty and active, fallback to first available
    if (!categories[activeCategory] && Object.keys(categories).length > 0) {
        activeCategory = Object.keys(categories).sort()[0];
    }

    // Force rendering order: Recent first, then others alphabetically
    const sortedCats = Object.keys(categories).sort((a, b) => {
        if (a === 'Recent') return -1;
        if (b === 'Recent') return 1;
        return a.localeCompare(b);
    });

    // Create Icon Row
    const iconRow = document.createElement("div");
    iconRow.className = "category-row";
    
    // Create List Container
    const listContainer = document.createElement("div");
    listContainer.className = "category-content-container";

    let currentListDiv = null;

    // Build the UI
    for (const catName of sortedCats) {
        const parts = categories[catName];
        if (parts.length === 0) continue;

        // Icon Header
        const header = document.createElement("div");
        header.className = "category-header" + (activeCategory === catName ? " expanded" : "");
        header.setAttribute("data-tooltip", catName);
        header.innerHTML = getCategoryIcon(catName);
        
        // Parts List (Hidden unless active)
        const list = document.createElement("div");
        list.className = "category-list";
        list.style.display = (activeCategory === catName) ? "flex" : "none";
        list.style.flexDirection = "column";
        list.style.gap = "4px";

        if (activeCategory === catName) {
            currentListDiv = list;
        }

        header.onclick = () => {
            activeCategory = catName;
            searchInput.value = ''; // clear search on category switch
            renderCategorizedPalette(data); // re-render to update classes
        };

        const buttons = [];
        parts.forEach(part => {
            const btn = document.createElement("button");
            btn.className = "tool-btn mini";
            btn.innerText = part.label;
            btn.dataset.label = part.label.toLowerCase();
            btn.onclick = () => {
                document.querySelectorAll('.tool-btn.mini').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Track recent
                if (!recentComponents.includes(part.type)) {
                    recentComponents.unshift(part.type);
                    if (recentComponents.length > 8) recentComponents.pop();
                    renderCategorizedPalette(data);
                }
                
                addComponent(part.type);
            };
            list.appendChild(btn);
            buttons.push(btn);
        });

        iconRow.appendChild(header);
        listContainer.appendChild(list);

        // Map them for search logic
        categories[catName].listEl = list;
        categories[catName].buttons = buttons;
        categories[catName].headerEl = header;
    }

    container.appendChild(iconRow);
    container.appendChild(listContainer);

    // Search logic
    searchInput.oninput = (e) => {
        const query = e.target.value.toLowerCase();
        
        // If searching, hide the icon row to show all matching across all categories
        if (query.trim() !== "") {
            iconRow.style.display = "none";
            
            for (const catName of sortedCats) {
                const catData = categories[catName];
                if(!catData.listEl) continue;
                
                let hasMatch = false;
                catData.buttons.forEach(btn => {
                    if (btn.dataset.label.includes(query)) {
                        btn.style.display = "flex";
                        hasMatch = true;
                    } else {
                        btn.style.display = "none";
                    }
                });

                if (hasMatch) {
                    catData.listEl.style.display = "flex";
                } else {
                    catData.listEl.style.display = "none";
                }
            }
        } else {
            // Restore normal view
            iconRow.style.display = "flex";
            for (const catName of sortedCats) {
                const catData = categories[catName];
                if(!catData.listEl) continue;
                catData.buttons.forEach(btn => btn.style.display = "flex");
                catData.listEl.style.display = (activeCategory === catName) ? "flex" : "none";
            }
        }
    };
}

// Resizer logic
let isResizingPanel = false;
document.addEventListener('DOMContentLoaded', () => {
    const resizer = document.getElementById('panel-resizer');
    const leftPanel = document.getElementById('left-panel');
    
    if (resizer && leftPanel) {
        resizer.addEventListener('mousedown', (e) => {
            isResizingPanel = true;
            resizer.classList.add('resizing');
            document.body.style.cursor = 'ew-resize';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizingPanel) return;
            // Get offset left of the ui-root to calculate true width
            const offset = leftPanel.getBoundingClientRect().left;
            let newWidth = e.clientX - offset;
            
            // Constrain width
            if (newWidth < 250) newWidth = 250;
            if (newWidth > 800) newWidth = 800;
            
            leftPanel.style.width = newWidth + 'px';
            leftPanel.style.minWidth = newWidth + 'px';
            
            // Re-calc canvas resize
            resizeWorkspace();
        });

        document.addEventListener('mouseup', () => {
            if (isResizingPanel) {
                isResizingPanel = false;
                resizer.classList.remove('resizing');
                document.body.style.cursor = 'default';
                resizeWorkspace();
            }
        });
    }
});

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
    drawRulers();
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

function drawRulers() {
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
        scaleCtx.roundRect(contRect.width/2 - 90, 60, 180, 30, 15);
        scaleCtx.fill();
        scaleCtx.fillStyle = "white";
        scaleCtx.textAlign = "center";
        scaleCtx.font = "bold 13px 'JetBrains Mono', Monospace";
        scaleCtx.fillText("PRESS 'R' TO ROTATE", contRect.width/2, 80);
    }
    const isLight = frame.style.background === "rgb(255, 255, 255)";
    scaleCtx.textAlign = "left";
    scaleCtx.fillStyle = backendOnline ? "#4caf50" : "#f44336";
    scaleCtx.font = "bold 12px 'JetBrains Mono', Monospace";
    scaleCtx.fillText(backendOnline ? "● BACKEND: ONLINE" : "● BACKEND: OFFLINE", startX + 16, startY - 35);
    scaleCtx.fillStyle = isLight ? "#111" : (accentColor || "#4a90e2");
    scaleCtx.font = "bold 14px 'JetBrains Mono', Monospace";
    scaleCtx.fillText("AURA | VIRTUAL GRID SYSTEM", startX + 16, startY - 18);
    scaleCtx.fillStyle = isLight ? "rgba(0,0,0,0.6)" : "rgba(255,255,255,0.6)";
    scaleCtx.font = "12px 'JetBrains Mono', Monospace";
    scaleCtx.fillText(`UNIT: ${BASE_UNIT_MM}mm | CAL: ${pixelsPerUnit}px/u | ZOOM: ${zoom.toFixed(2)}x`, startX + 16, startY - 4);
    
    const pxPerU = pixelsPerUnit * zoom;
    const potentialSteps = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000];
    let unitStep = potentialSteps.find(s => s * pxPerU >= 55) || 1000;
    const spacing = unitStep * pxPerU;
    
    scaleCtx.fillStyle = isLight ? "rgba(0,0,0,0.6)" : "rgba(255,255,255,0.6)";
    scaleCtx.font = "11px 'JetBrains Mono', Monospace";
    scaleCtx.textAlign = "center";
    for(let x = Math.ceil(-offsetX / spacing) * spacing + offsetX; x < rect.width; x += spacing) {
        if (x < -1) continue;
        scaleCtx.fillText(Math.round((x - offsetX) / pxPerU) + "u", startX + x, startY + rect.height + 16);
    }
    scaleCtx.textAlign = "right";
    for(let y = Math.ceil(-offsetY / spacing) * spacing + offsetY; y < rect.height; y += spacing) {
        if (y < -1) continue;
        scaleCtx.fillText(Math.round((offsetY - y) / pxPerU) + "u", startX - 8, startY + y + 4);
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
                        const orad = (otherComp.rotation || 0) * Math.PI / 180;
                        const orx = otherPin.uX * Math.cos(orad) - (-otherPin.uY) * Math.sin(orad);
                        const ory = otherPin.uX * Math.sin(orad) + (-otherPin.uY) * Math.cos(orad);
                        const targetX = otherComp.uX + orx;
                        const targetY = otherComp.uY + (-ory);
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