const Workspace={

svg:null,
frame:null,
group:null,
texture:null,
gridGroup:null,

workspaceWidth:0,
workspaceHeight:0,

init(container){

this.frame=document.createElement("div")
this.frame.className="workspace-frame"
container.appendChild(this.frame)

this.svg=document.createElementNS(
"http://www.w3.org/2000/svg","svg")

this.svg.classList.add("workspace-svg")
this.frame.appendChild(this.svg)

// main group
this.group=document.createElementNS(
"http://www.w3.org/2000/svg","g")

this.svg.appendChild(this.group)

// grid group
this.gridGroup=document.createElementNS(
"http://www.w3.org/2000/svg","g")

this.group.appendChild(this.gridGroup)

// attach camera
Camera.attach(this.svg)

},

setTexture(src){

if(this.texture) this.texture.remove()

const img=new Image()

img.onload=()=>{

// derive workspace size from texture resolution
this.workspaceWidth=
img.width / AURA.TEXTURE_PIXELS_PER_GRID_UNIT *
AURA.GRID_PIXEL_SIZE

this.workspaceHeight=
img.height / AURA.TEXTURE_PIXELS_PER_GRID_UNIT *
AURA.GRID_PIXEL_SIZE

// create texture
this.texture=document.createElementNS(
"http://www.w3.org/2000/svg","image")

this.texture.setAttribute("href",src)
this.texture.setAttribute("width",this.workspaceWidth)
this.texture.setAttribute("height",this.workspaceHeight)

this.group.insertBefore(this.texture,this.gridGroup)

// draw grid
this.drawGrid()

// fit camera properly
Camera.fit()

}

img.src=src

},

drawGrid(){

// clear old grid
this.gridGroup.innerHTML=""

const spacing=AURA.GRID_PIXEL_SIZE

// vertical lines
for(let x=0;x<=this.workspaceWidth;x+=spacing){

const line=document.createElementNS(
"http://www.w3.org/2000/svg","line")

line.setAttribute("x1",x)
line.setAttribute("y1",0)
line.setAttribute("x2",x)
line.setAttribute("y2",this.workspaceHeight)

line.setAttribute("stroke","#ffffff")
line.setAttribute("stroke-opacity","0.08")

this.gridGroup.appendChild(line)

}

// horizontal lines
for(let y=0;y<=this.workspaceHeight;y+=spacing){

const line=document.createElementNS(
"http://www.w3.org/2000/svg","line")

line.setAttribute("x1",0)
line.setAttribute("y1",y)
line.setAttribute("x2",this.workspaceWidth)
line.setAttribute("y2",y)

line.setAttribute("stroke","#ffffff")
line.setAttribute("stroke-opacity","0.08")

this.gridGroup.appendChild(line)

}

},

setBorder(width){

this.frame.style.borderWidth=width+"px"

}

}