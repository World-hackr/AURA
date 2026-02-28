const CanvasEngine = {

svg:null,
workspaceGroup:null,

cameraX:0,
cameraY:0,
zoom:1,

minZoom:1,
maxZoom:20,

viewportW:0,
viewportH:0,

init(){

const app=document.getElementById("app")

// tools panel
const tools=document.createElement("div")
tools.className="tools-panel"
tools.innerHTML=`
<div style="color:white">TOOLS</div>
<hr style="border-color:white22">
<div>Move</div>
<div>Wire</div>
<div>Component</div>
`
app.appendChild(tools)

// workspace panel
const workspacePanel=document.createElement("div")
workspacePanel.className="workspace-panel"
app.appendChild(workspacePanel)

const frame=document.createElement("div")
frame.className="workspace-frame"
workspacePanel.appendChild(frame)

// svg
this.svg=document.createElementNS(
"http://www.w3.org/2000/svg","svg")

this.svg.classList.add("workspace-svg")

frame.appendChild(this.svg)

// get correct size AFTER layout
requestAnimationFrame(()=>{

this.viewportW=this.svg.clientWidth
this.viewportH=this.svg.clientHeight

this.workspaceGroup=this.createGroup()

this.loadTexture()

this.enablePan()
this.enableZoom()

})

},

createGroup(){

const g=document.createElementNS(
"http://www.w3.org/2000/svg","g")

this.svg.appendChild(g)
return g

},

loadTexture(){

const img=new Image()

img.onload=()=>{

this.workspacePixelW=
img.width/AURA.TEXTURE_PIXELS_PER_GRID_UNIT*
AURA.GRID_PIXEL_SIZE

this.workspacePixelH=
img.height/AURA.TEXTURE_PIXELS_PER_GRID_UNIT*
AURA.GRID_PIXEL_SIZE

// correct minimum zoom
this.minZoom=Math.max(
this.viewportW/this.workspacePixelW,
this.viewportH/this.workspacePixelH
)

this.zoom=this.minZoom

// texture
const texture=document.createElementNS(
"http://www.w3.org/2000/svg","image")

texture.setAttribute("href",AURA.CURRENT_TEXTURE)
texture.setAttribute("width",this.workspacePixelW)
texture.setAttribute("height",this.workspacePixelH)

this.workspaceGroup.appendChild(texture)

// grid
this.drawGrid()

this.centerCamera()
this.updateCamera()

}

img.src=AURA.CURRENT_TEXTURE

},

drawGrid(){

const spacing=AURA.GRID_PIXEL_SIZE

for(let x=0;x<this.workspacePixelW;x+=spacing){

const line=document.createElementNS(
"http://www.w3.org/2000/svg","line")

line.setAttribute("x1",x)
line.setAttribute("y1",0)
line.setAttribute("x2",x)
line.setAttribute("y2",this.workspacePixelH)

line.setAttribute("stroke","white")
line.setAttribute("stroke-opacity","0.08")

this.workspaceGroup.appendChild(line)

}

for(let y=0;y<this.workspacePixelH;y+=spacing){

const line=document.createElementNS(
"http://www.w3.org/2000/svg","line")

line.setAttribute("x1",0)
line.setAttribute("y1",y)
line.setAttribute("x2",this.workspacePixelW)
line.setAttribute("y2",y)

line.setAttribute("stroke","white")
line.setAttribute("stroke-opacity","0.08")

this.workspaceGroup.appendChild(line)

}

},

centerCamera(){

this.cameraX=
(this.viewportW-this.workspacePixelW*this.zoom)/2

this.cameraY=
(this.viewportH-this.workspacePixelH*this.zoom)/2

},

updateCamera(){

const minX=this.viewportW-this.workspacePixelW*this.zoom
const minY=this.viewportH-this.workspacePixelH*this.zoom

this.cameraX=Math.min(0,Math.max(minX,this.cameraX))
this.cameraY=Math.min(0,Math.max(minY,this.cameraY))

this.workspaceGroup.setAttribute(
"transform",
`translate(${this.cameraX},${this.cameraY}) scale(${this.zoom})`
)

},

enablePan(){

let dragging=false,lastX,lastY

this.svg.onmousedown=e=>{
dragging=true
lastX=e.clientX
lastY=e.clientY
}

window.onmouseup=()=>dragging=false

window.onmousemove=e=>{

if(!dragging)return

this.cameraX+=e.clientX-lastX
this.cameraY+=e.clientY-lastY

lastX=e.clientX
lastY=e.clientY

this.updateCamera()

}

},

enableZoom(){

this.svg.onwheel=e=>{

e.preventDefault()

const rect=this.svg.getBoundingClientRect()

const mouseX=e.clientX-rect.left
const mouseY=e.clientY-rect.top

const oldZoom=this.zoom

if(e.deltaY<0)
this.zoom*=1.1
else
this.zoom/=1.1

this.zoom=Math.max(this.minZoom,
Math.min(this.maxZoom,this.zoom))

this.cameraX=
mouseX-(mouseX-this.cameraX)*(this.zoom/oldZoom)

this.cameraY=
mouseY-(mouseY-this.cameraY)*(this.zoom/oldZoom)

this.updateCamera()

}

}

}