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

// INTERACTION MODES
let currentTool = 'select'; // 'select' or 'wire'

// WIRING STATE
let wires = [];
let activeWire = null;
let currentWireColor = "#f44336"; // Default red wire
let wireWidth = 4; // Default wire width
let mouseUx = 0;
let mouseUy = 0;

let dragging = false;
let draggedComponent = null;
let selectedComponent = null;
let placingComponent = null;
let hoveredPin = null;

let showGrid = true;
let gridOpacity = 0.4;
let textureIsDark = true;
let useSketchyStyle = true;

// HISTORY SYSTEM
let history = [];
let historyIndex = -1;

function saveHistory() {
    if (historyIndex < history.length - 1) {
        history = history.slice(0, historyIndex + 1);
    }
    const snapshot = JSON.stringify({
        components: components.map(c => ({...c, _lastValidImg: undefined, _reloadTimer: undefined})),
        wires: wires
    });
    if (history.length > 0 && history[history.length - 1] === snapshot) return;
    history.push(snapshot);
    if (history.length > 50) history.shift();
    historyIndex = history.length - 1;
}

function undo() {
    if (historyIndex > 0) {
        historyIndex--;
        const state = JSON.parse(history[historyIndex]);
        components = state.components;
        wires = state.wires;
        selectedComponent = null;
        closeInspector();
        draw();
    }
}

function redo() {
    if (historyIndex < history.length - 1) {
        historyIndex++;
        const state = JSON.parse(history[historyIndex]);
        components = state.components;
        wires = state.wires;
        draw();
    }
}

const SymbolManager = {
    cache: {},
    pending: {}, 
    getCacheKey(type, properties) {
        if (!properties || Object.keys(properties).length === 0) return type;
        try {
            const propStr = Object.entries(properties)
                .sort((a, b) => a[0].localeCompare(b[0]))
                .map(entry => `${entry[0]}=${encodeURIComponent(entry[1])}`)
                .join('&');
            return `${type}?${propStr}`;
        } catch(e) {
            return type;
        }
    },
    async load(type, viewPath, properties = null) {
        const cacheKey = this.getCacheKey(type, properties);
        if (this.cache[cacheKey] && this.cache[cacheKey].complete) return this.cache[cacheKey];
        if (this.pending[cacheKey]) return this.pending[cacheKey];

        this.pending[cacheKey] = new Promise(async (resolve) => {
            // Ensure base image exists
            if (!this.cache[type]) {
                await new Promise((resBase) => {
                    const baseImg = new Image();
                    baseImg.crossOrigin = "anonymous";
                    baseImg.onload = () => { this.cache[type] = baseImg; resBase(); };
                    baseImg.onerror = () => { resBase(); }; 
                    baseImg.src = `http://127.0.0.1:8000/symbols/${viewPath}?t=base`;
                });
            }

            const img = new Image();
            img.crossOrigin = "anonymous";
            img.onload = () => {
                this.cache[cacheKey] = img;
                delete this.pending[cacheKey];
                resolve(img);
            };
            img.onerror = () => {
                delete this.pending[cacheKey];
                resolve(this.cache[type]); 
            };

            const def = COMPONENT_DEFS[type];
            const isDynamic = def && def.interactive;
            const hasIndicators = def && def.indicators;
            
            if ((isDynamic || hasIndicators) && properties && Object.keys(properties).length > 0) {
                const params = new URLSearchParams();
                for (const [k, v] of Object.entries(properties)) params.append(k, v);
                
                if (hasIndicators) {
                    // If a general 'brightness' property exists, use it for all indicators
                    const b = properties.brightness !== undefined ? properties.brightness : "100";
                    def.indicators.forEach(ind => {
                        if (!params.has(`${ind.id}_brightness`)) {
                            params.append(`${ind.id}_brightness`, b);
                        }
                    });
                }
                
                img.src = `http://127.0.0.1:8000/api/dynamic_svg/${type}?${params.toString()}&t=${Date.now()}`;
            } else {
                img.src = `http://127.0.0.1:8000/symbols/${viewPath}?t=${Date.now()}`;
            }
        });
        return this.pending[cacheKey];
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
        data.forEach(comp => { COMPONENT_DEFS[comp.type] = comp; });
        renderCategorizedPalette(data);
        backendOnline = true;
        saveHistory(); // Save initial state
        draw();
    } catch (e) {
        backendOnline = false;
        draw();
    }
}

const CATEGORY_ICONS = {
    'Recent': '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4A8,8 0 0,0 12,20M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22C6.47,22 2,17.5 2,12A10,10 0 0,1 12,2M12.5,7V12.25L17,14.92L16.25,16.15L11,13V7H12.5Z"/></svg>',
    'MCU': '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M6,4H18V5H21V7H18V9H21V11H18V13H21V15H18V17H21V19H18V20H6V19H3V17H6V15H3V13H6V11H3V9H6V7H3V5H6V4M11,15H13V17H11V15M11,11H13V13H11V11M11,7H13V9H11V7Z"/></svg>',
    'Passives': '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M2,11H7L10.07,15.35L13.11,4L18,11H22V13H16L13.15,19.32L9.9,7L7,13H2V11Z"/></svg>',
    'Optoelectronics': '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M12,2A7,7 0 0,0 5,9C5,11.38 6.19,13.47 8,14.74V17A1,1 0 0,0 9,18H15A1,1 0 0,0 16,17V14.74C17.81,13.47 19,11.38 19,9A7,7 0 0,0 12,2M9,21V20H15V21A1,1 0 0,1 14,22H10A1,1 0 0,1 9,21Z"/></svg>',
    'Switches': '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M17,7H7V17H17V7M17,5A2,2 0 0,1 19,7V17A2,2 0 0,1 17,19H7A2,2 0 0,1 5,17V7A2,2 0 0,1 7,5H17M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9Z"/></svg>',
    'Power': '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M16.56,5.44L15.11,6.89C16.84,7.94 18,9.83 18,12A6,6 0 0,1 12,18A6,6 0 0,1 6,12C6,9.83 7.16,7.94 8.88,6.88L7.44,5.44C5.36,6.88 4,9.28 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12C20,9.28 18.64,6.88 16.56,5.44M11,3V13H13V3H11Z"/></svg>',
    'Uncategorized': '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M12,2L3,7L12,12L21,7L12,2M12,14.67L3,9.67V16.5L12,21.5L21,16.5V9.67L12,14.67Z"/></svg>'
};

function getCategoryIcon(name) { return CATEGORY_ICONS[name] || CATEGORY_ICONS['Uncategorized']; }

let recentComponents = [];
let activeCategory = 'Recent';

function renderCategorizedPalette(data) {
    const container = document.getElementById("component-palette");
    if (!container) return;
    container.innerHTML = "";
    const searchWrapper = document.createElement("div");
    searchWrapper.style.marginBottom = "10px";
    const searchInput = document.createElement("input");
    searchInput.type = "text"; searchInput.placeholder = "Search components..."; searchInput.className = "component-search";
    searchWrapper.appendChild(searchInput);
    container.appendChild(searchWrapper);
    const categories = {};
    if (recentComponents.length > 0) { categories['Recent'] = recentComponents.map(id => data.find(p => p.type === id)).filter(Boolean); }
    data.forEach(part => {
        const cat = part.category || 'Uncategorized';
        if (!categories[cat]) categories[cat] = [];
        categories[cat].push(part);
    });
    if (!categories[activeCategory] && Object.keys(categories).length > 0) { activeCategory = Object.keys(categories).sort()[0]; }
    const sortedCats = Object.keys(categories).sort((a, b) => {
        if (a === 'Recent') return -1; if (b === 'Recent') return 1; return a.localeCompare(b);
    });
    const iconRow = document.createElement("div"); iconRow.className = "category-row";
    const listContainer = document.createElement("div"); listContainer.className = "category-content-container";
    for (const catName of sortedCats) {
        const parts = categories[catName]; if (parts.length === 0) continue;
        const header = document.createElement("div");
        header.className = "category-header" + (activeCategory === catName ? " expanded" : "");
        header.setAttribute("data-tooltip", catName);
        header.innerHTML = getCategoryIcon(catName);
        const list = document.createElement("div");
        list.className = "category-list"; list.style.display = (activeCategory === catName) ? "flex" : "none";
        list.style.flexDirection = "column"; list.style.gap = "4px";
        header.onclick = () => { activeCategory = catName; searchInput.value = ''; renderCategorizedPalette(data); };
        const buttons = [];
        parts.forEach(part => {
            const btn = document.createElement("button"); btn.className = "tool-btn mini"; btn.innerText = part.label; btn.dataset.label = part.label.toLowerCase();
            btn.onclick = () => {
                document.querySelectorAll('.tool-btn.mini').forEach(b => b.classList.remove('active')); btn.classList.add('active');
                if (!recentComponents.includes(part.type)) { recentComponents.unshift(part.type); if (recentComponents.length > 8) recentComponents.pop(); renderCategorizedPalette(data); }
                addComponent(part.type);
            };
            list.appendChild(btn); buttons.push(btn);
        });
        iconRow.appendChild(header); listContainer.appendChild(list);
        categories[catName].listEl = list; categories[catName].buttons = buttons;
    }
    container.appendChild(iconRow); container.appendChild(listContainer);
    searchInput.oninput = (e) => {
        const query = e.target.value.toLowerCase();
        if (query.trim() !== "") {
            iconRow.style.display = "none";
            for (const catName of sortedCats) {
                const catData = categories[catName]; if(!catData.listEl) continue;
                let hasMatch = false;
                catData.buttons.forEach(btn => {
                    if (btn.dataset.label.includes(query)) { btn.style.display = "flex"; hasMatch = true; } else { btn.style.display = "none"; }
                });
                catData.listEl.style.display = hasMatch ? "flex" : "none";
            }
        } else {
            iconRow.style.display = "flex";
            for (const catName of sortedCats) {
                const catData = categories[catName]; if(!catData.listEl) continue;
                catData.buttons.forEach(btn => btn.style.display = "flex");
                catData.listEl.style.display = (activeCategory === catName) ? "flex" : "none";
            }
        }
    };
}

let isResizingPanel = false;
document.addEventListener('DOMContentLoaded', () => {
    const resizer = document.getElementById('panel-resizer');
    const leftPanel = document.getElementById('left-panel');
    if (resizer && leftPanel) {
        resizer.addEventListener('mousedown', (e) => { isResizingPanel = true; resizer.classList.add('resizing'); document.body.style.cursor = 'ew-resize'; });
        document.addEventListener('mousemove', (e) => {
            if (!isResizingPanel) return;
            const offset = leftPanel.getBoundingClientRect().left;
            let newWidth = e.clientX - offset;
            if (newWidth < 250) newWidth = 250; if (newWidth > 800) newWidth = 800;
            leftPanel.style.width = newWidth + 'px'; leftPanel.style.minWidth = newWidth + 'px';
            resizeWorkspace();
        });
        document.addEventListener('mouseup', () => { if (isResizingPanel) { isResizingPanel = false; resizer.classList.remove('resizing'); document.body.style.cursor = 'default'; resizeWorkspace(); } });
    }
});

let components = [];

async function addComponent(type) {
    if (!backendOnline) { alert("Backend is offline."); await initLibrary(); return; }
    const def = COMPONENT_DEFS[type]; if (!def) return;
    let defaultProps = {};
    if ((def.category === "Passives" || def.category === "Passive") && type.includes("resistor")) {
        const is5Band = type.includes("5band");
        defaultProps = { 
            resistance: "1000", 
            unit: "Ω",
            tolerance: is5Band ? "Brown" : "Gold" 
        };
    }
    if (def.category === "Optoelectronics" && type.includes("led")) defaultProps = { color: "Red", brightness: "0" };
    if (type.includes("arduino_nano")) defaultProps = { brightness: "100" };
    if (type.includes("arduino_pro_mini")) defaultProps = { brightness: "100" };
    
    placingComponent = { type: type, uX: 0, uY: 0, rotation: 0, properties: defaultProps };
    SymbolManager.load(type, def.views.breadboard, defaultProps).then(() => draw());
}

function closeInspector() { const inspector = document.getElementById("property-inspector"); if (inspector) inspector.style.display = "none"; }

function openInspector(comp) {
    const inspector = document.getElementById("property-inspector");
    const title = document.getElementById("inspector-title");
    const content = document.getElementById("inspector-content");
    if (!inspector || !title || !content) return;
    if (!comp) { closeInspector(); return; }
    const def = COMPONENT_DEFS[comp.type];
    title.innerText = def ? def.label : "Component";
    content.innerHTML = ""; 
    if (!comp.properties || Object.keys(comp.properties).length === 0) {
        content.innerHTML = `<div class="empty-state">No editable properties for this part.</div>`;
    } else {
        for (const [key, value] of Object.entries(comp.properties)) {
            const group = document.createElement("div"); group.className = "prop-group";
            const label = document.createElement("label"); label.innerText = key.toUpperCase();
            let input;
            
            // SPECIALIZED INPUTS
            if (key === 'tolerance' && comp.type.includes('resistor')) {
                input = document.createElement("select"); input.className = "prop-input";
                // Adding percentages as requested, keeping the value pure for backend
                const tolerances = [
                    {val: "Gold", text: "Gold (5%)"},
                    {val: "Silver", text: "Silver (10%)"},
                    {val: "Brown", text: "Brown (1%)"},
                    {val: "Red", text: "Red (2%)"},
                    {val: "Green", text: "Green (0.5%)"},
                    {val: "Blue", text: "Blue (0.25%)"},
                    {val: "Violet", text: "Violet (0.1%)"}
                ];
                tolerances.forEach(t => {
                    const opt = document.createElement("option"); 
                    opt.value = t.val; 
                    opt.innerText = t.text; 
                    if (t.val === value) opt.selected = true; 
                    input.appendChild(opt);
                });
                
                // Real-time update while scrolling/navigating the dropdown
                input.oninput = (e) => {
                    comp.properties[key] = e.target.value;
                    SymbolManager.load(comp.type, def.views.breadboard, comp.properties).then(() => draw());
                };
                input.onchange = (e) => { 
                    saveHistory(); 
                    comp.properties[key] = e.target.value; 
                    SymbolManager.load(comp.type, def.views.breadboard, comp.properties).then(() => draw()); 
                };
                
            } else if (key === 'unit' && (comp.type.includes('resistor') || comp.type.includes('potentiometer'))) {
                input = document.createElement("select"); input.className = "prop-input";
                ["Ω", "kΩ", "MΩ", "GΩ"].forEach(u => {
                    const opt = document.createElement("option"); opt.value = opt.innerText = u; if (u === value) opt.selected = true; input.appendChild(opt);
                });
                input.oninput = (e) => {
                    comp.properties[key] = e.target.value;
                    SymbolManager.load(comp.type, def.views.breadboard, comp.properties).then(() => draw());
                };
                input.onchange = (e) => {
                    saveHistory();
                    comp.properties[key] = e.target.value;
                    SymbolManager.load(comp.type, def.views.breadboard, comp.properties).then(() => draw());
                };
                
            } else if (key === 'color' && comp.type.includes('led')) {
                // Group color and brightness together for LEDs
                const colorRow = document.createElement("div"); colorRow.style.display = "flex"; colorRow.style.flexDirection = "column"; colorRow.style.gap = "8px";
                
                // Color Select
                input = document.createElement("select"); input.className = "prop-input";
                ["Red", "Green", "Blue", "Yellow", "White"].forEach(c => {
                    const opt = document.createElement("option"); opt.value = opt.innerText = c; if (c === value) opt.selected = true; input.appendChild(opt);
                });
                input.oninput = (e) => {
                    comp.properties[key] = e.target.value;
                    SymbolManager.load(comp.type, def.views.breadboard, comp.properties).then(() => draw());
                };
                input.onchange = (e) => { saveHistory(); comp.properties[key] = e.target.value; SymbolManager.load(comp.type, def.views.breadboard, comp.properties).then(() => draw()); };
                
                colorRow.appendChild(input);
                group.appendChild(label); group.appendChild(colorRow); content.appendChild(group); continue;
                
            } else if (key === 'brightness' && (comp.type.includes('led') || comp.type.includes('arduino'))) {
                const valRow = document.createElement("div"); valRow.style.display = "flex"; valRow.style.gap = "8px"; valRow.style.alignItems = "center";
                input = document.createElement("input"); input.type = "range"; input.min = "0"; input.max = "100"; input.value = value; input.style.flex = "1";
                const valDisp = document.createElement("span"); valDisp.innerText = value + "%"; valDisp.style.minWidth = "40px";
                input.onmousedown = () => saveHistory();
                input.oninput = (e) => { 
                    valDisp.innerText = e.target.value + "%"; 
                    comp.properties[key] = e.target.value; 
                    SymbolManager.load(comp.type, def.views.breadboard, comp.properties).then(() => draw()); 
                };
                valRow.appendChild(input); valRow.appendChild(valDisp); group.appendChild(label); group.appendChild(valRow); content.appendChild(group); continue;
                
            } else if (key === 'value' && comp.type.includes('potentiometer')) {
                const valRow = document.createElement("div"); valRow.style.display = "flex"; valRow.style.gap = "8px"; valRow.style.alignItems = "center";
                input = document.createElement("input"); input.type = "range"; input.min = "0"; input.max = "100"; input.value = value; input.style.flex = "1";
                const valDisp = document.createElement("span"); valDisp.innerText = value + "%"; valDisp.style.minWidth = "40px";
                input.onmousedown = () => saveHistory();
                input.oninput = (e) => { valDisp.innerText = e.target.value + "%"; comp.properties[key] = e.target.value; draw(); };
                valRow.appendChild(input); valRow.appendChild(valDisp); group.appendChild(label); group.appendChild(valRow); content.appendChild(group); continue; 
                
            } else if (key === 'voltage' && comp.type.includes('battery')) {
                const valRow = document.createElement("div"); valRow.style.display = "flex"; valRow.style.gap = "8px"; valRow.style.alignItems = "center";
                input = document.createElement("input"); input.type = "range"; input.min = "0"; input.max = "24"; input.step = "0.1"; input.value = value; input.style.flex = "1";
                const valDisp = document.createElement("span"); valDisp.innerText = value + "V"; valDisp.style.minWidth = "40px";
                input.onmousedown = () => saveHistory();
                input.oninput = (e) => { valDisp.innerText = e.target.value + "V"; comp.properties[key] = e.target.value; draw(); };
                valRow.appendChild(input); valRow.appendChild(valDisp); group.appendChild(label); group.appendChild(valRow); content.appendChild(group); continue; 
                
            } else if (key === 'resistance' && comp.type.includes('resistor')) {
                input = document.createElement("input"); input.type = "number"; input.min = "0"; input.className = "prop-input"; input.value = value;
                input.onfocus = () => { input._originalValue = input.value; };
                input.oninput = (e) => {
                    comp.properties[key] = e.target.value;
                    clearTimeout(comp._reloadTimer);
                    comp._reloadTimer = setTimeout(() => { SymbolManager.load(comp.type, def.views.breadboard, comp.properties).then(() => draw()); }, 300);
                };
                input.onchange = () => { if (input.value !== input._originalValue) saveHistory(); };
                
            } else {
                input = document.createElement("input"); input.type = "text"; input.className = "prop-input"; input.value = value;
                input.onfocus = () => { input._originalValue = input.value; };
                input.oninput = (e) => {
                    comp.properties[key] = e.target.value;
                    clearTimeout(comp._reloadTimer);
                    comp._reloadTimer = setTimeout(() => { SymbolManager.load(comp.type, def.views.breadboard, comp.properties).then(() => draw()); }, 300);
                };
                input.onchange = () => { if (input.value !== input._originalValue) saveHistory(); };
            }
            group.appendChild(label); group.appendChild(input); content.appendChild(group);
        }
    }
    inspector.style.display = "flex";
}

function setTool(tool) { currentTool = tool; if (tool !== 'wire') { activeWire = null; } const st = document.getElementById("status-text"); if (st) st.innerText = (tool === 'wire') ? "WIRE" : (isEditingTexture ? "ALIGN" : "GRID"); draw(); }

function getMouseInUnits(e) {
    const rect = canvas.getBoundingClientRect();
    const uX = Math.round((e.clientX - rect.left - offsetX) / (zoom * pixelsPerUnit));
    const uY = Math.round((offsetY - (e.clientY - rect.top)) / (zoom * pixelsPerUnit));
    return { uX, uY };
}

function isMouseOverComponent(uX, uY, comp) {
    const def = COMPONENT_DEFS[comp.type]; if (!def) return false;
    const rad = -(comp.rotation || 0) * Math.PI / 180;
    const dx = uX - comp.uX; const dy = uY - comp.uY;
    const rx = dx * Math.cos(rad) - dy * Math.sin(rad); const ry = dx * Math.sin(rad) + dy * Math.cos(rad);
    return Math.abs(rx) <= def.uW / 2 && Math.abs(ry) <= def.uH / 2;
}

function draw() {
    ctx.clearRect(0, 0, canvas.width / dpr, canvas.height / dpr);
    if (texture.complete) { ctx.save(); ctx.translate(texOffsetX, texOffsetY); ctx.scale(texZoom, texZoom); ctx.drawImage(texture, 0, 0); ctx.restore(); }
    if (showGrid) drawGrid(); drawWires(); drawAllComponents(); if (placingComponent) drawGhost(); if (hoveredPin) drawPinLabel(hoveredPin); drawRulers();
}

function drawGrid() {
    const step = pixelsPerUnit * zoom; const width = canvas.width / dpr; const height = canvas.height / dpr;
    const colorBase = textureIsDark ? 255 : 0; ctx.lineWidth = 1 / dpr;
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

function drawWires() {
    const u = pixelsPerUnit * zoom;
    const drawPath = (points, width) => {
        if (points.length < 2) return;
        const screenPts = points.map(p => ({ x: offsetX + p.uX * u, y: offsetY - p.uY * u }));
        ctx.beginPath(); ctx.moveTo(screenPts[0].x, screenPts[0].y);
        if (screenPts.length === 2) { ctx.lineTo(screenPts[1].x, screenPts[1].y); } else {
            const maxRadius = 12 * zoom; 
            for (let i = 1; i < screenPts.length - 1; i++) {
                const p0 = screenPts[i - 1]; const p1 = screenPts[i]; const p2 = screenPts[i + 1];
                const d1 = Math.hypot(p1.x - p0.x, p1.y - p0.y); const d2 = Math.hypot(p2.x - p1.x, p2.y - p1.y);
                const r = Math.min(maxRadius, d1 / 2, d2 / 2); ctx.arcTo(p1.x, p1.y, p2.x, p2.y, r);
            }
            ctx.lineTo(screenPts[screenPts.length - 1].x, screenPts[screenPts.length - 1].y);
        }
        ctx.stroke();
    };
    wires.forEach(wire => {
        if (wire.points.length < 2) return;
        ctx.strokeStyle = wire.color; ctx.lineWidth = (wire.width || 4) * zoom; ctx.lineCap = "round"; ctx.lineJoin = "round";
        drawPath(wire.points, wire.width || 4);
        ctx.fillStyle = wire.color; const start = wire.points[0]; const end = wire.points[wire.points.length - 1];
        const nodeRadius = ((wire.width || 4) / 2 + 1) * zoom;
        ctx.beginPath(); ctx.arc(offsetX + start.uX * u, offsetY - start.uY * u, nodeRadius, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(offsetX + end.uX * u, offsetY - end.uY * u, nodeRadius, 0, Math.PI * 2); ctx.fill();
    });
    if (activeWire && activeWire.points.length > 0) {
        ctx.strokeStyle = activeWire.color; ctx.lineWidth = (activeWire.width || 4) * zoom; ctx.lineCap = "round"; ctx.lineJoin = "round";
        let targetX = mouseUx; let targetY = mouseUy; if (hoveredPin) { targetX = hoveredPin.uX; targetY = hoveredPin.uY; }
        const previewPts = [...activeWire.points, { uX: targetX, uY: targetY }];
        ctx.globalAlpha = 0.7; drawPath(previewPts, activeWire.width || 4); ctx.globalAlpha = 1.0;
        ctx.fillStyle = activeWire.color; const nodeRadius = ((activeWire.width || 4) / 2 + 1) * zoom;
        ctx.beginPath(); ctx.arc(offsetX + targetX * u, offsetY - targetY * u, nodeRadius, 0, Math.PI * 2); ctx.fill();
    }
}

function drawAllComponents() { 
    components.forEach(comp => {
        try {
            drawComponent(comp, comp === selectedComponent ? 1.0 : 0.9);
        } catch (err) {
            console.error(`Error drawing component ${comp.type}:`, err);
        }
    }); 
}
function drawGhost() { 
    if (placingComponent) {
        try {
            drawComponent(placingComponent, 0.5);
        } catch (err) {
            console.error("Error drawing ghost component:", err);
        }
    }
}

function drawComponent(comp, opacity) {
    const def = COMPONENT_DEFS[comp.type]; if (!def) return;
    const cacheKey = SymbolManager.getCacheKey(comp.type, comp.properties);
    const img = SymbolManager.cache[cacheKey];
    let displayImg = (img && img.complete && img.naturalWidth > 0) ? img : comp._lastValidImg;
    if (!displayImg || !displayImg.complete) { displayImg = SymbolManager.cache[comp.type]; }
    if (!displayImg || !displayImg.complete || displayImg.naturalWidth === 0) return;
    if (img && img.complete && img.naturalWidth > 0) { comp._lastValidImg = img; }
    
    const u = pixelsPerUnit * zoom; const screenX = offsetX + comp.uX * u; const screenY = offsetY - comp.uY * u;
    ctx.save(); 
    
    try {
        ctx.translate(screenX, screenY); ctx.rotate((comp.rotation || 0) * Math.PI / 180); ctx.imageSmoothingEnabled = false;
        const drawX = Math.round(-(def.originX || 0) * u); const drawY = Math.round(-(def.originY || 0) * u); 
        const drawW = Math.round((def.uW || 0) * u); const drawH = Math.round((def.uH || 0) * u);
        
        ctx.globalAlpha = opacity; ctx.drawImage(displayImg, drawX, drawY, drawW, drawH);
        
        ctx.globalAlpha = opacity * 0.7; ctx.fillStyle = accentColor || "#4a90e2";
        if (def.pins) { 
            def.pins.forEach(pin => { 
                ctx.beginPath(); ctx.arc((pin.uX||0) * u, -(pin.uY||0) * u, 2 * zoom, 0, Math.PI * 2); ctx.fill(); 
            }); 
        }
        
        if (comp === selectedComponent) { 
            ctx.strokeStyle = accentColor || "#4a90e2"; ctx.lineWidth = 2; ctx.setLineDash([5, 5]); 
            ctx.strokeRect(drawX - 2, drawY - 2, drawW + 4, drawH + 4); 
        }
    } finally {
        ctx.restore();
    }
}

function drawPinLabel(pin) {
    const u = pixelsPerUnit * zoom; const screenX = offsetX + pin.uX * u; const screenY = offsetY - pin.uY * u;
    ctx.save(); ctx.font = `bold ${Math.max(10, 12 * zoom)}px Monospace`;
    const txt = pin.label; const tw = ctx.measureText(txt).width;
    ctx.fillStyle = "rgba(0,0,0,0.8)"; ctx.fillRect(screenX + 10, screenY - 25, tw + 10, 20);
    ctx.fillStyle = accentColor || "#4a90e2"; ctx.fillText(txt, screenX + 15, screenY - 10);
    ctx.strokeStyle = "white"; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(screenX, screenY, 4 * zoom, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
}

function drawRulers() {
    const frame = document.getElementById("workspace-frame"); const container = document.getElementById("workspace-container"); if (!frame || !container) return;
    const rect = frame.getBoundingClientRect(); const contRect = container.getBoundingClientRect();
    const startX = rect.left - contRect.left; const startY = rect.top - contRect.top;
    scaleCtx.clearRect(0, 0, scaleCanvas.width / dpr, scaleCanvas.height / dpr);
    if (selectedComponent) {
        scaleCtx.fillStyle = "rgba(0,0,0,0.7)"; scaleCtx.beginPath(); if (typeof scaleCtx.roundRect === 'function') { scaleCtx.roundRect(contRect.width/2 - 90, 60, 180, 30, 15); } else { scaleCtx.rect(contRect.width/2 - 90, 60, 180, 30); }
        scaleCtx.fill(); scaleCtx.fillStyle = "white"; scaleCtx.textAlign = "center"; scaleCtx.font = "bold 13px 'JetBrains Mono', Monospace"; scaleCtx.fillText("PRESS 'R' TO ROTATE", contRect.width/2, 80);
    } else if (currentTool === 'wire') {
        scaleCtx.fillStyle = "rgba(0,0,0,0.7)"; scaleCtx.beginPath(); if (typeof scaleCtx.roundRect === 'function') { scaleCtx.roundRect(contRect.width/2 - 120, 60, 240, 30, 15); } else { scaleCtx.rect(contRect.width/2 - 120, 60, 240, 30); }
        scaleCtx.fill(); scaleCtx.fillStyle = currentWireColor || "#f44336"; scaleCtx.textAlign = "center"; scaleCtx.font = "bold 13px 'JetBrains Mono', Monospace"; scaleCtx.fillText(activeWire ? "CLICK TO ROUTE, ESC TO CANCEL" : "CLICK PIN TO START WIRING", contRect.width/2, 80);
    }
    const isLight = frame.style.background === "rgb(255, 255, 255)";
    scaleCtx.textAlign = "left"; scaleCtx.fillStyle = backendOnline ? "#4caf50" : "#f44336"; scaleCtx.font = "bold 12px 'JetBrains Mono', Monospace";
    scaleCtx.fillText(backendOnline ? "● BACKEND: ONLINE" : "● BACKEND: OFFLINE", startX + 16, startY - 35);
    scaleCtx.fillStyle = isLight ? "#111" : (accentColor || "#4a90e2"); scaleCtx.font = "bold 14px 'JetBrains Mono', Monospace";
    scaleCtx.fillText("AURA | VIRTUAL GRID SYSTEM", startX + 16, startY - 18);
    scaleCtx.fillStyle = isLight ? "rgba(0,0,0,0.6)" : "rgba(255,255,255,0.6)"; scaleCtx.font = "12px 'JetBrains Mono', Monospace";
    scaleCtx.fillText(`UNIT: ${BASE_UNIT_MM}mm | CAL: ${pixelsPerUnit}px/u | ZOOM: ${zoom.toFixed(2)}x`, startX + 16, startY - 4);
    const pxPerU = pixelsPerUnit * zoom; const potentialSteps = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000];
    let unitStep = potentialSteps.find(s => s * pxPerU >= 55) || 1000; const spacing = unitStep * pxPerU;
    scaleCtx.fillStyle = isLight ? "rgba(0,0,0,0.6)" : "rgba(255,255,255,0.6)"; scaleCtx.font = "11px 'JetBrains Mono', Monospace"; scaleCtx.textAlign = "center";
    for(let x = Math.ceil(-offsetX / spacing) * spacing + offsetX; x < rect.width; x += spacing) { if (x < -1) continue; scaleCtx.fillText(Math.round((x - offsetX) / pxPerU) + "u", startX + x, startY + rect.height + 16); }
    scaleCtx.textAlign = "right";
    for(let y = Math.ceil(-offsetY / spacing) * spacing + offsetY; y < rect.height; y += spacing) { if (y < -1) continue; scaleCtx.fillText(Math.round((offsetY - y) / pxPerU) + "u", startX - 8, startY + y + 4); }
}

let dragStarted = false;
let isTurningKnob = false;

canvas.onmousedown = (e) => {
    if (e.button === 2) { if (activeWire) { activeWire = null; draw(); } return; }
    const { uX, uY } = getMouseInUnits(e);
    if (currentTool === 'wire') {
        let targetX = uX; let targetY = uY; if (hoveredPin) { targetX = hoveredPin.uX; targetY = hoveredPin.uY; }
        if (!activeWire) { activeWire = { id: "wire_" + Date.now(), color: currentWireColor, width: wireWidth, points: [{ uX: targetX, uY: targetY }] }; }
        else { activeWire.points.push({ uX: targetX, uY: targetY }); if (hoveredPin) { saveHistory(); wires.push(activeWire); activeWire = null; } }
        draw(); return;
    }
    draggedComponent = components.find(c => isMouseOverComponent(uX, uY, c));
    
    if (draggedComponent && draggedComponent.type.includes('potentiometer')) {
        const rad = -(draggedComponent.rotation || 0) * Math.PI / 180;
        const dx = uX - draggedComponent.uX; const dy = uY - draggedComponent.uY;
        const rx = dx * Math.cos(rad) - dy * Math.sin(rad); const ry = dx * Math.sin(rad) + dy * Math.cos(rad);
        if (Math.hypot(rx, ry) < 6) {
            isTurningKnob = true;
            dragStarted = true;
            selectedComponent = draggedComponent;
            lastY = e.clientY;
            openInspector(selectedComponent);
            return;
        }
    }

    selectedComponent = draggedComponent; if (selectedComponent) { openInspector(selectedComponent); dragStarted = true; } else { closeInspector(); }
    isPanning = !draggedComponent; dragging = true; lastX = e.clientX; lastY = e.clientY; draw();
};

window.onmouseup = () => { if (dragging && dragStarted && draggedComponent) { saveHistory(); } if (isTurningKnob) { saveHistory(); } dragging = false; draggedComponent = null; dragStarted = false; isTurningKnob = false; };

window.onmousemove = (e) => {
    const { uX, uY } = getMouseInUnits(e); mouseUx = uX; mouseUy = uY;
    const coordEl = document.getElementById("coord-display"); if (coordEl) coordEl.innerText = `${uX}u, ${uY}u`;
    hoveredPin = null;
    for (const comp of components) {
        const def = COMPONENT_DEFS[comp.type];
        if (def && def.pins) {
            for (const pin of def.pins) {
                const rad = (comp.rotation || 0) * Math.PI / 180;
                const rx = pin.uX * Math.cos(rad) - (-pin.uY) * Math.sin(rad); const ry = pin.uX * Math.sin(rad) + (-pin.uY) * Math.cos(rad);
                const pinWorldX = comp.uX + rx; const pinWorldY = comp.uY + (-ry);
                if (Math.sqrt((uX - pinWorldX)**2 + (uY - pinWorldY)**2) < 3) { hoveredPin = { label: pin.label, uX: pinWorldX, uY: pinWorldY }; break; }
            }
        }
        if (hoveredPin) break;
    }
    if (currentTool === 'wire' && activeWire) { draw(); return; }
    if (placingComponent) { placingComponent.uX = uX; placingComponent.uY = uY; draw(); return; }
    
    if (isTurningKnob && draggedComponent) {
        let deltaY = lastY - e.clientY;
        let val = parseFloat(draggedComponent.properties.value) || 0;
        val = Math.max(0, Math.min(100, val + deltaY * 0.5));
        draggedComponent.properties.value = Math.round(val);
        openInspector(draggedComponent);
        draw();
        lastY = e.clientY;
        return;
    }

    if (!dragging) { if (currentTool === 'wire' || hoveredPin) draw(); return; }
    if (draggedComponent && currentTool === 'select') {
        const dragDef = COMPONENT_DEFS[draggedComponent.type]; let snapOffset = { x: 0, y: 0 }; let activeSnap = false;
        if (dragDef && dragDef.pins) {
            for (const dragPin of dragDef.pins) {
                const rad = (draggedComponent.rotation || 0) * Math.PI / 180;
                const rx = dragPin.uX * Math.cos(rad) - (-dragPin.uY) * Math.sin(rad); const ry = dragPin.uX * Math.sin(rad) + (-dragPin.uY) * Math.cos(rad);
                const myPinX = uX + rx; const myPinY = uY + (-ry);
                for (const otherComp of components) {
                    if (otherComp === draggedComponent) continue;
                    const otherDef = COMPONENT_DEFS[otherComp.type]; if (!otherDef || !otherDef.pins) continue;
                    for (const otherPin of otherDef.pins) {
                        const orad = (otherComp.rotation || 0) * Math.PI / 180;
                        const orx = otherPin.uX * Math.cos(orad) - (-otherPin.uY) * Math.sin(orad); const ory = otherPin.uX * Math.sin(orad) + (-otherPin.uY) * Math.cos(orad);
                        const targetX = otherComp.uX + orx; const targetY = otherComp.uY + (-ory);
                        if (Math.sqrt((myPinX - targetX)**2 + (myPinY - targetY)**2) < 4) { activeSnap = true; snapOffset.x = targetX - rx; snapOffset.y = targetY - (-ry); break; }
                    }
                    if (activeSnap) break;
                }
                if (activeSnap) break;
            }
        }
        if (activeSnap) { draggedComponent.uX = snapOffset.x; draggedComponent.uY = snapOffset.y; } else { draggedComponent.uX = uX; draggedComponent.uY = uY; }
    } else if (isPanning) { const dx = e.clientX - lastX; const dy = e.clientY - lastY; if (isEditingTexture) { texOffsetX += dx; texOffsetY += dy; } else { offsetX += dx; offsetY += dy; } }
    lastX = e.clientX; lastY = e.clientY; draw();
};

window.addEventListener('keydown', (e) => {
    const key = e.key.toLowerCase();
    const isTyping = ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName) || document.activeElement.isContentEditable;
    if (e.ctrlKey && key === 'z') { e.preventDefault(); e.stopImmediatePropagation(); undo(); return; }
    if (e.ctrlKey && key === 'y') { e.preventDefault(); e.stopImmediatePropagation(); redo(); return; }
    if (isTyping) { if (key === 'backspace' || key === 'delete') { e.stopPropagation(); } return; }
    if (key === 'w') { setTool(currentTool === 'wire' ? 'select' : 'wire'); }
    if (key === 'escape') { if (activeWire) { activeWire = null; draw(); } else if (placingComponent) { placingComponent = null; draw(); } else { setTool('select'); } }
    if (key === 'r') { if (selectedComponent) { saveHistory(); selectedComponent.rotation = (selectedComponent.rotation + 90) % 360; draw(); } else if (placingComponent) { placingComponent.rotation = (placingComponent.rotation + 90) % 360; draw(); } }
    if (e.key === 'Delete' || e.key === 'Backspace') { if (selectedComponent) { saveHistory(); components = components.filter(c => c !== selectedComponent); selectedComponent = null; closeInspector(); draw(); } }
}, true);

canvas.onclick = (e) => {
    if (placingComponent) {
        const { uX, uY } = getMouseInUnits(e);
        const newComp = { ...placingComponent, uX, uY, id: Date.now() };
        components.push(newComp); saveHistory(); selectedComponent = newComp; placingComponent = null; openInspector(newComp); draw();
    }
};
canvas.oncontextmenu = (e) => { e.preventDefault(); };
canvas.onwheel = (e) => {
    e.preventDefault(); const isTex = isEditingTexture; let currentZoom = isTex ? texZoom : zoom; let newZoom = currentZoom * (e.deltaY < 0 ? 1.1 : 0.9); newZoom = Math.max(0.1, Math.min(50, newZoom));
    const mouseX = e.offsetX; const mouseY = e.offsetY;
    if (isTex) { const wx = (mouseX - texOffsetX) / texZoom; const wy = (mouseY - texOffsetY) / texZoom; texZoom = newZoom; texOffsetX = mouseX - wx * texZoom; texOffsetY = mouseY - wy * texZoom; }
    else { const wx = (mouseX - offsetX) / zoom; const wy = (mouseY - offsetY) / zoom; zoom = newZoom; offsetX = mouseX - wx * zoom; offsetY = mouseY - wy * zoom; }
    draw();
};

function setGridOpacity(v) { gridOpacity = v/100; draw(); }
function toggleGrid() { showGrid = !showGrid; const btn = document.getElementById("grid-toggle-btn"); if (btn) btn.classList.toggle("active", showGrid); draw(); }
function toggleTextureLock() { isEditingTexture = !isEditingTexture; const btn = document.getElementById("bg-lock-btn"); const sg = document.getElementById("status-group"); const st = document.getElementById("status-text"); if (btn) btn.classList.toggle("active", isEditingTexture); if (sg) sg.classList.toggle("editing", isEditingTexture); if (st) st.innerText = isEditingTexture ? "ALIGN" : "GRID"; }
function resetOrigin() { const rect = canvas.getBoundingClientRect(); zoom = 1.0; offsetX = 0; offsetY = rect.height; draw(); }
function setGridResolution(v) { pixelsPerUnit = parseFloat(v); const display = document.getElementById("grid-val-display"); if (display) display.innerText = v + "px/u"; draw(); }
function setAccentColor(c) { accentColor = c; document.documentElement.style.setProperty('--accent-color', c); const light = document.getElementById("status-light"); const text = document.getElementById("status-text"); if (light) { light.style.background = c; light.style.boxShadow = `0 0 8px ${c}`; } if (text) text.style.color = c; draw(); }
function setTheme(theme) { const frame = document.getElementById("workspace-frame"); const container = document.getElementById("workspace-container"); if (!frame || !container) return; if(theme === 'blueprint') { frame.style.background = "#003366"; container.style.background = "radial-gradient(circle at center, #002244 0%, #001122 100%)"; } else if(theme === 'light') { frame.style.background = "#ffffff"; container.style.background = "#dcdcdc"; } else { frame.style.background = "#000"; container.style.background = "radial-gradient(circle at center, #1a1a1a 0%, #0a0a0a 100%)"; } draw(); }
function setTexture(n) { texture.src = "assets/textures/" + n; texture.onload = () => { analyzeTextureBrightness(); draw(); }; }
function analyzeTextureBrightness() { if (!texture.complete || texture.width === 0) return; const tc = document.createElement('canvas'); tc.width = tc.height = 1; const tctx = tc.getContext('2d'); tctx.drawImage(texture, 0, 0, 1, 1); const d = tctx.getImageData(0, 0, 1, 1).data; textureIsDark = ((d[0] * 299 + d[1] * 587 + d[2] * 114) / 1000) < 128; draw(); }
function resizeWorkspace() {
    const frame = document.getElementById("workspace-frame"); const container = document.getElementById("workspace-container"); dpr = window.devicePixelRatio || 1; const rect = frame.getBoundingClientRect(); const contRect = container.getBoundingClientRect();
    canvas.width = rect.width * dpr; canvas.height = rect.height * dpr; canvas.style.width = rect.width + "px"; canvas.style.height = rect.height + "px"; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    scaleCanvas.width = contRect.width * dpr; scaleCanvas.height = contRect.height * dpr; scaleCanvas.style.width = contRect.width + "px"; scaleCanvas.style.height = contRect.height + "px"; scaleCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (isFirstLoad) { offsetX = 0; offsetY = rect.height; isFirstLoad = false; initLibrary(); }
    draw();
}
function setWireWidth(w) { wireWidth = parseFloat(w); const display = document.getElementById("wire-width-display"); if (display) display.innerText = w + "px"; if (activeWire) activeWire.width = wireWidth; draw(); }
function setWireColor(c) { currentWireColor = c; if (activeWire) activeWire.color = c; draw(); }
function generateNetlist() {
    let allPins = []; components.forEach(comp => {
        const def = COMPONENT_DEFS[comp.type]; if (!def || !def.pins) return;
        def.pins.forEach(pin => {
            const rad = (comp.rotation || 0) * Math.PI / 180; const rx = pin.uX * Math.cos(rad) - (-pin.uY) * Math.sin(rad); const ry = pin.uX * Math.sin(rad) + (-pin.uY) * Math.cos(rad);
            allPins.push({ comp: comp, pinDef: pin, worldX: Math.round(comp.uX + rx), worldY: Math.round(comp.uY + (-ry)), netId: null });
        });
    });
    const isPointOnSegment = (px, py, ax, ay, bx, by) => { const dAP = Math.hypot(px - ax, py - ay); const dPB = Math.hypot(bx - px, by - py); const dAB = Math.hypot(bx - ax, by - ay); return Math.abs((dAP + dPB) - dAB) < 0.1; };
    let adj = new Map(); for (let i = 0; i < allPins.length; i++) adj.set(i, []);
    for (let i = 0; i < allPins.length; i++) {
        for (let j = i + 1; j < allPins.length; j++) {
            let p1 = allPins[i]; let p2 = allPins[j];
            if (p1.worldX === p2.worldX && p1.worldY === p2.worldY) { adj.get(i).push(j); adj.get(j).push(i); continue; }
            for (const wire of wires) {
                if (wire.points.length < 2) continue;
                let p1Touches = false; let p2Touches = false;
                for (let w = 0; w < wire.points.length - 1; w++) {
                    const wa = wire.points[w]; const wb = wire.points[w+1];
                    if (!p1Touches && isPointOnSegment(p1.worldX, p1.worldY, wa.uX, wa.uY, wb.uX, wb.uY)) p1Touches = true;
                    if (!p2Touches && isPointOnSegment(p2.worldX, p2.worldY, wa.uX, wa.uY, wb.uX, wb.uY)) p2Touches = true;
                }
                if (p1Touches && p2Touches) { adj.get(i).push(j); adj.get(j).push(i); break; }
            }
        }
    }
    let nets = []; let visited = new Set(); let netCounter = 1;
    for (let i = 0; i < allPins.length; i++) {
        if (!visited.has(i)) {
            let currentNet = { id: `Net_${netCounter}`, nodes: [] }; let queue = [i]; visited.add(i);
            while (queue.length > 0) {
                let curr = queue.shift(); let pinData = allPins[curr]; pinData.netId = currentNet.id;
                currentNet.nodes.push({ componentId: pinData.comp.id, componentType: pinData.comp.type, pinName: pinData.pinDef.id, pinLabel: pinData.pinDef.label, worldCoords: `(${pinData.worldX}, ${pinData.worldY})` });
                for (let neighbor of adj.get(curr)) { if (!visited.has(neighbor)) { visited.add(neighbor); queue.push(neighbor); } }
            }
            if (currentNet.nodes.length > 1) { nets.push(currentNet); netCounter++; }
        }
    }
    const netlistPayload = { timestamp: Date.now(), totalNets: nets.length, nets: nets };
    console.log("=== AURA NETLIST GENERATED ==="); console.log(JSON.stringify(netlistPayload, null, 2));
    alert(`Netlist generated with ${nets.length} active nets! Check the browser console (F12) to view the JSON output.`);
    return netlistPayload;
}
window.onresize = resizeWorkspace;
window.onload = resizeWorkspace;