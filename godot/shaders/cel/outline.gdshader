// Outline pass from eldskald/godot4-cel-shader (MIT, (c) 2023 Rafael de Lima Bordoni), see LICENSE.md.
// Used as next_pass: back faces pushed out in screen space draw a constant-width ink line.
shader_type spatial;

render_mode cull_front, unshaded, depth_draw_never;

global uniform vec4 outline_color;
global uniform float outline_width;

void vertex() {
	vec4 clip_position = 
			PROJECTION_MATRIX *
			(MODELVIEW_MATRIX * vec4(VERTEX, 1.0));
	vec3 clip_normal =
			mat3(PROJECTION_MATRIX) *
			(mat3(MODELVIEW_MATRIX) * NORMAL);
	clip_position.xy +=
			normalize(clip_normal.xy) /
			VIEWPORT_SIZE *
			clip_position.w *
			outline_width;
	POSITION = clip_position;
}

void fragment() {
	ALBEDO = outline_color.rgb;
}
