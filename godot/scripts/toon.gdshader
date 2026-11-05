shader_type spatial;
render_mode unshaded, cull_back;

uniform vec4 base_color : source_color = vec4(1.0);
uniform bool glow = false;
uniform bool use_textures = false;
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D mask_tex : hint_default_black, filter_linear_mipmap;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap;
uniform vec4 palette_primary : source_color = vec4(0.16, 0.40, 0.31, 1.0);
uniform vec4 palette_secondary : source_color = vec4(0.52, 0.66, 0.55, 1.0);
uniform vec4 palette_accent : source_color = vec4(0.29, 0.84, 0.62, 1.0);
uniform float flash_amount : hint_range(0.0, 1.0) = 0.0;
// Expression atlas over the flat face (UV2 from model_rig.flat_face; UV2 < 0 elsewhere).
uniform bool use_face = false;
uniform sampler2D face_tex : source_color, filter_linear_mipmap, repeat_disable;
uniform vec2 face_grid = vec2(4.0, 2.0);
uniform float face_cell = 0.0;
// PS1 Legends pages (256 px, 15 colours): sampled texel by texel, no mipmaps.
uniform bool pixelated = false;
uniform sampler2D albedo_px : source_color, filter_nearest, repeat_disable;
uniform sampler2D face_px : source_color, filter_nearest, repeat_disable;

void fragment() {
	vec3 n = NORMAL;
	if (use_textures && !pixelated) {
		vec3 nmap = texture(normal_tex, UV).rgb * 2.0 - 1.0;
		vec3 mapped = normalize(TANGENT * nmap.x + BINORMAL * nmap.y + NORMAL * nmap.z);
		n = normalize(mix(NORMAL, mapped, 0.24));
	}
	vec3 world_normal = normalize((INV_VIEW_MATRIX * vec4(n, 0.0)).xyz);
	float light = max(dot(world_normal, normalize(vec3(-0.42, 0.82, 0.58))), 0.0);
	float band = floor(light * 3.0) / 3.0;
	float rim = pow(1.0 - max(dot(NORMAL, VIEW), 0.0), 3.0);

	vec3 surface = base_color.rgb;
	float accent_mask = 0.0;
	if (use_textures) {
		vec3 tex = pixelated ? texture(albedo_px, UV).rgb : texture(albedo_tex, UV).rgb;
		vec3 m = texture(mask_tex, UV).rgb;
		float lum = dot(tex, vec3(0.299, 0.587, 0.114));
		vec3 detail_factor = clamp(tex / max(lum, 0.08), 0.55, 1.45);
		// Apply palette only to masked clothing/equipment regions; skin & Ignis sunburn (m == 0) stay intact!
		surface = tex;
		surface = mix(surface, palette_primary.rgb * detail_factor * (0.45 + lum * 0.75), clamp(m.r, 0.0, 1.0));
		surface = mix(surface, palette_secondary.rgb * detail_factor * (0.45 + lum * 0.75), clamp(m.g, 0.0, 1.0));
		surface = mix(surface, palette_accent.rgb * detail_factor * (0.55 + lum * 0.65), clamp(m.b, 0.0, 1.0));
		accent_mask = clamp(m.b, 0.0, 1.0);
	}
	if (use_face && UV2.x >= 0.0) {
		vec2 cell = vec2(mod(face_cell, face_grid.x), floor(face_cell / face_grid.x));
		vec2 fuv = (cell + clamp(UV2, 0.002, 0.998)) / face_grid;
		vec4 face = pixelated ? texture(face_px, fuv) : texture(face_tex, fuv);
		surface = mix(surface, face.rgb, face.a);
	}

	vec3 shaded = surface * (0.52 + band * 0.48) + surface * rim * 0.14;
	shaded = mix(shaded, vec3(1.0), flash_amount);
	ALBEDO = shaded;
	EMISSION = glow ? surface * 0.16 : (palette_accent.rgb * accent_mask * 0.22);
}
