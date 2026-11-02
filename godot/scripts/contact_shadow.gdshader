shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never;
uniform float strength = 0.22;
void fragment() {
	float radius = length((UV - vec2(0.5)) * 2.0);
	ALBEDO = vec3(0.025, 0.035, 0.035);
	ALPHA = (1.0 - smoothstep(0.25, 1.0, radius)) * strength;
}
