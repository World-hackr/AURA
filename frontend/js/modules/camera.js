const Camera={

svg:null,

zoom:1,
x:0,
y:0,

minZoom:0.01,
maxZoom:20,

attach(svg){

this.svg=svg

svg.addEventListener("wheel",(e)=>this.zoomEvent(e))
svg.addEventListener("mousedown",(e)=>this.panStart(e))

window.addEventListener("mousemove",(e)=>this.panMove(e))
window.addEventListener("mouseup",()=>this.panEnd())

},

fit(){

const rect=this.svg.getBoundingClientRect()

const zoomX=rect.width/Workspace.workspaceWidth
const zoomY=rect.height/Workspace.workspaceHeight

this.zoom=Math.max(zoomX,zoomY)

this.x=(rect.width-Workspace.workspaceWidth*this.zoom)/2
this.y=(rect.height-Workspace.workspaceHeight*this.zoom)/2

this.update()

},

update(){

// clamp camera
const rect=this.svg.getBoundingClientRect()

const minX=rect.width-Workspace.workspaceWidth*this.zoom
const minY=rect.height-Workspace.workspaceHeight*this.zoom

this.x=Math.min(0,Math.max(minX,this.x))
this.y=Math.min(0,Math.max(minY,this.y))

Workspace.group.setAttribute(
"transform",
`translate(${this.x},${this.y}) scale(${this.zoom})`
)

},

zoomEvent(e){

e.preventDefault()

const rect=this.svg.getBoundingClientRect()

const mx=e.clientX-rect.left
const my=e.clientY-rect.top

const oldZoom=this.zoom

if(e.deltaY<0)
this.zoom*=1.1
else
this.zoom/=1.1

this.zoom=Math.max(this.minZoom,
Math.min(this.maxZoom,this.zoom))

this.x=mx-(mx-this.x)*(this.zoom/oldZoom)
this.y=my-(my-this.y)*(this.zoom/oldZoom)

this.update()

},

dragging:false,

panStart(e){

this.dragging=true
this.lastX=e.clientX
this.lastY=e.clientY

},

panMove(e){

if(!this.dragging) return

this.x+=e.clientX-this.lastX
this.y+=e.clientY-this.lastY

this.lastX=e.clientX
this.lastY=e.clientY

this.update()

},

panEnd(){

this.dragging=false

}

}