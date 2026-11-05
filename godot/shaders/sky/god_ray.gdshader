// Soft additive light beam (garage god rays): a smooth bell across the beam with no hard
// edge, bright near the window and fading toward the floor, and fading out when seen
// edge-on; a slow drift of dust keeps it alive.
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;

uniform vec3 tint : source_color = vec3(1.0, 0.86, 0.6);
uniform float strength = 0.4;

void fragment() {
	float x = UV.x * 2.0 - 1.0;
	float across = exp(-x * x * 5.0) * (1.0 - abs(x));
	float along = smoothstep(0.0, 0.18, UV.y) * pow(1.0 - UV.y, 1.6);
	float facing = smoothstep(0.05, 0.5, abs(dot(NORMAL, VIEW)));
	float dust = 0.88 + 0.12 * sin(UV.y * 16.0 - TIME * 0.5 + UV.x * 5.0);
	ALBEDO = tint * across * along * facing * dust * strength;
}
