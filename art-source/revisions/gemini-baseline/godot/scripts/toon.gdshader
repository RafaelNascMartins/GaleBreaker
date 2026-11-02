shader_type spatial;
render_mode unshaded, cull_back;

uniform vec4 base_color : source_color = vec4(1.0);
uniform bool glow = false;
uniform bool use_textures = false;
uniform sampler2D albedo_tex : source_color, filter_linear_mipmap;
uniform sampler2D mask_tex : hint_default_black, filter_linear_mipmap;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap;
uniform vec4 palette_primary : source_color = vec4(0.16, 0.40, 0.31, 1.0);
uniform vec4 palette_secondary : source_color = vec4(0.52, 0.66, 0.55, 1.0);
uniform vec4 palette_accent : source_color = vec4(0.29, 0.84, 0.62, 1.0);
uniform float flash_amount : hint_range(0.0, 1.0) = 0.0;

void fragment() {
	vec3 n = NORMAL;
	if (use_textures) {
		vec3 nmap = texture(normal_tex, UV).rgb * 2.0 - 1.0;
		n = normalize(NORMAL + nmap * 0.35);
	}
	vec3 world_normal = normalize((INV_VIEW_MATRIX * vec4(n, 0.0)).xyz);
	float light = max(dot(world_normal, normalize(vec3(-0.42, 0.82, 0.58))), 0.0);
	float band = floor(light * 3.0) / 3.0;
	float rim = pow(1.0 - max(dot(NORMAL, VIEW), 0.0), 3.0);

	vec3 surface = base_color.rgb;
	float accent_mask = 0.0;
	if (use_textures) {
		vec3 tex = texture(albedo_tex, UV).rgb;
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

	vec3 shaded = surface * (0.52 + band * 0.48) + surface * rim * 0.14;
	shaded = mix(shaded, vec3(1.0), flash_amount);
	ALBEDO = shaded;
	EMISSION = glow ? surface * 0.16 : (palette_accent.rgb * accent_mask * 0.22);
}
