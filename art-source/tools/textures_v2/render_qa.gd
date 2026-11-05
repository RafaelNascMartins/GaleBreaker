extends SceneTree

var output:String
var package:String
var layer:Control
var texture_cache:Dictionary={}
var shader:Shader

func _initialize()->void:call_deferred("capture")

func texture(file:String)->Texture2D:
	if not texture_cache.has(file):
		var image:=Image.load_from_file(package+"/"+file)
		image.generate_mipmaps()
		texture_cache[file]=ImageTexture.create_from_image(image)
	return texture_cache[file]

func panel(index:int,columns:int,rows:int,file:String,band:float,repeats:float=2.0,mask:String="",alpha:bool=false)->void:
	var cell:=Vector2i(1440/columns,960/rows)
	var holder:=SubViewportContainer.new()
	holder.position=Vector2(index%columns*cell.x,index/columns*cell.y)
	holder.size=cell
	root.add_child(holder)
	var viewport:=SubViewport.new()
	viewport.size=cell;viewport.own_world_3d=true
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	holder.add_child(viewport)
	var world:=Node3D.new();viewport.add_child(world)
	var environment:=WorldEnvironment.new();environment.environment=Environment.new()
	environment.environment.background_mode=Environment.BG_COLOR
	environment.environment.background_color=Color("26303e") if index%2==0 else Color("d9e2d7")
	environment.environment.tonemap_mode=Environment.TONE_MAPPER_LINEAR
	world.add_child(environment)
	var camera:=Camera3D.new();world.add_child(camera)
	camera.position=Vector3(0,0,4);camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.size=2.18
	var mesh:=MeshInstance3D.new();mesh.mesh=QuadMesh.new();mesh.mesh.size=Vector2(2,2);world.add_child(mesh)
	var material:=ShaderMaterial.new();material.shader=shader
	material.set_shader_parameter("surface_tex",texture(file));material.set_shader_parameter("band",band)
	material.set_shader_parameter("uv_repeat",repeats);material.set_shader_parameter("cutout",alpha)
	if not mask.is_empty():
		material.set_shader_parameter("hot_mask",texture(mask));material.set_shader_parameter("emits",true)
	mesh.material_override=material
	var caption:=Label.new();caption.position=Vector2(8,7);caption.text=file.get_file().trim_suffix(".png")+" / "+str(band)
	caption.add_theme_font_size_override("font_size",12);holder.add_child(caption)

func settle()->void:
	for frame in 6:await process_frame
	await RenderingServer.frame_post_draw

func reset()->void:
	for child in root.get_children():child.queue_free()
	await process_frame

func capture()->void:
	root.size=Vector2i(1440,960)
	output=ProjectSettings.globalize_path("res://../qa/renderer")
	package=ProjectSettings.globalize_path("res://../package")
	DirAccess.make_dir_recursive_absolute(output)
	shader=Shader.new()
	shader.code="""shader_type spatial;
render_mode unshaded,cull_disabled;
uniform sampler2D surface_tex: source_color,filter_linear_mipmap,repeat_enable;
uniform sampler2D hot_mask: filter_linear_mipmap,repeat_enable;
uniform float band=1.0;
uniform float uv_repeat=2.0;
uniform bool cutout=false;
uniform bool emits=false;
void fragment(){
 vec4 color=texture(surface_tex,UV*uv_repeat);
 ALBEDO=color.rgb*band;
 if(cutout){ALPHA=color.a;ALPHA_SCISSOR_THRESHOLD=0.05;}
 if(emits){ALBEDO+=color.rgb*texture(hot_mask,UV*uv_repeat).r*0.85;}
}
"""
	var cases=["textures-v2/santuario/santuario_piso-calcario_albedo.png","textures-v2/bazaar/bazaar_azulejo-cobalto-marfim_albedo.png","textures-v2/forja/forja_piso-basalto_albedo.png","textures-v2/praia/praia_telhas-azul-marinho_albedo.png"]
	for row in 3:
		for column in 4:panel(row*4+column,4,3,cases[column],[0.55,0.78,1.0][row])
	await settle()
	root.get_texture().get_image().save_png(output+"/toon-three-bands.png")
	await reset()
	var manifest:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(package+"/manifest-v2.json"))
	var recortes:Array=manifest.textures.filter(func(entry:Dictionary)->bool:return entry.alpha=="straight")
	for i in recortes.size():panel(i,5,3,recortes[i].file,1.0,1.0,"",true)
	await settle()
	root.get_texture().get_image().save_png(output+"/cutouts-linear-mip.png")
	await reset()
	var emissive:Array=manifest.textures.filter(func(entry:Dictionary)->bool:return entry.type=="emission")
	for i in emissive.size():
		panel(i*2,4,2,emissive[i].pair,0.55,1.0,"",emissive[i].pair.contains("abertura"))
		panel(i*2+1,4,2,emissive[i].pair,0.55,1.0,emissive[i].file,emissive[i].pair.contains("abertura"))
	await settle()
	root.get_texture().get_image().save_png(output+"/emission-pairs.png")
	print("TEXTURES V2 GPU QA COMPLETE: three bands, RGBA/mipmaps and 4 emission pairs")
	quit()
