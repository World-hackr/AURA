const Controls={

init(container){

const tools=document.createElement("div")
tools.className="tools-panel"

container.appendChild(tools)

tools.innerHTML=`

<div>Textures</div>

<button onclick="Workspace.setTexture('assets/textures/texture1.jpg')">Texture 1</button>
<button onclick="Workspace.setTexture('assets/textures/texture2.jpg')">Texture 2</button>
<button onclick="Workspace.setTexture('assets/textures/texture3.jpg')">Texture 3</button>
<button onclick="Workspace.setTexture('assets/textures/texture4.jpg')">Texture 4</button>

<div class="tool-section">

Border Width

<input type="range" min="0" max="6" value="2"
oninput="Workspace.setBorder(this.value)">

</div>

`

}

}