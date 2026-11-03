// Toon water: colour by depth below the surface, foam where it meets anything,
// scrolling surface lines and the painted water texture as detail.
// Based on Erik Roystan Ross's toon water (roystan.net/articles/toon-water.html,
// github.com/IronWarrior/ToonWaterShader, MIT), rewritten for Godot 4 / Compatibility:
// depth is linearised with INV_PROJECTION_MATRIX and foam width is constant.
shader_type spatial;
render_mode unshaded, depth_draw_never, cull_disabled, shadows_disabled;

uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform sampler2D surface_noise : repeat_enable, filter_linear;
uniform sampler2D distort_noise : repeat_enable, filter_linear;
uniform sampler2D detail_tex : source_color, repeat_enable, filter_linear_mipmap;

uniform vec4 shallow_color : source_color = vec4(0.42, 0.92, 0.84, 0.30);
uniform vec4 deep_color : source_color = vec4(0.10, 0.52, 0.86, 0.94);
uniform float depth_max = 9.0;
uniform float foam_distance = 1.3;
uniform vec4 foam_color : source_color = vec4(1.0, 1.0, 1.0, 0.95);
uniform float noise_cutoff : hint_range(0.0, 1.0) = 0.9;
uniform float distortion : hint_range(0.0, 1.0) = 0.27;
uniform vec2 noise_scroll = vec2(0.02, 0.03);
uniform float noise_scale = 0.12;
uniform float detail_scale = 0.09;
uniform float detail_strength : hint_range(0.0, 1.0) = 0.45;

varying vec3 world_pos;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	// View-space distance from the water surface to whatever is behind it.
	float d = texture(depth_tex, SCREEN_UV).r;
	vec4 behind = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d * 2.0 - 1.0, 1.0);
	behind.xyz /= behind.w;
	float gap = max(0.0, VERTEX.z - behind.z);

	vec4 water = mix(shallow_color, deep_color, clamp(gap / depth_max, 0.0, 1.0));
	vec2 plane_uv = world_pos.xz;
	vec2 wobble = (texture(distort_noise, plane_uv * noise_scale * 0.5).xy * 2.0 - 1.0) * distortion;
	float lines = texture(surface_noise, plane_uv * noise_scale + TIME * noise_scroll + wobble).r;
	// Near contact the cutoff drops, so the noise turns into a solid foam rim.
	float cutoff = clamp(gap / foam_distance, 0.0, 1.0) * noise_cutoff;
	float foam = smoothstep(cutoff - 0.01, cutoff + 0.01, lines);

	vec3 detail = texture(detail_tex, plane_uv * detail_scale + TIME * vec2(0.004, 0.006)).rgb;
	vec3 colour = mix(water.rgb, water.rgb * (0.6 + detail * 0.8), detail_strength);
	ALBEDO = mix(colour, foam_color.rgb, foam * foam_color.a);
	ALPHA = mix(water.a, 1.0, foam * foam_color.a);
}
