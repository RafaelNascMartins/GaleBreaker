// Shared body of the stage cel materials.
// Derived from eldskald/godot4-cel-shader (MIT, (c) 2023 Rafael de Lima Bordoni), see LICENSE.md.
// Changes: fixed alpha cutoff threshold, repeatable texture, scrolling UV offset,
// and LIGHT_COLOR divided by PI (Godot 4 pre-multiplies it by PI for custom light()).

#include "includes/base-cel-shader.gdshaderinc"

uniform vec4 color: source_color = vec4(1.0);
uniform sampler2D base_texture: source_color, filter_linear_mipmap, repeat_enable, hint_default_white;
uniform vec4 specular: source_color = vec4(0.3, 0.3, 0.3, 0.0);
uniform vec4 fresnel: source_color = vec4(0.25, 0.25, 0.25, 0.22);
uniform vec2 uv_offset = vec2(0.0);
#ifdef CEL_CUTOUT
uniform float alpha_cutoff: hint_range(0.0, 1.0) = 0.5;
#endif

varying vec3 SPECULAR_COLOR;
varying float SPECULAR_STRENGTH;
varying vec3 FRESNEL_COLOR;
varying float FRESNEL_STRENGTH;

void vertex() {
	UV = UV + uv_offset;
}

void fragment() {
	vec4 tex = texture(base_texture, UV);
	ALBEDO = color.rgb * tex.rgb;
#ifdef CEL_CUTOUT
	ALPHA = color.a * tex.a;
	ALPHA_SCISSOR_THRESHOLD = alpha_cutoff;
#endif
	SPECULAR_COLOR = specular.rgb;
	SPECULAR_STRENGTH = specular.a;
	FRESNEL_COLOR = fresnel.rgb;
	FRESNEL_STRENGTH = fresnel.a;
}

void light() {
	vec3 light_color = LIGHT_COLOR / PI;
	DIFFUSE_LIGHT += diffuse_light(ALBEDO, light_color, LIGHT, NORMAL, ATTENUATION);
	SPECULAR_LIGHT += specular_light(light_color, SPECULAR_COLOR, SPECULAR_STRENGTH, NORMAL, VIEW, LIGHT, ATTENUATION);
	SPECULAR_LIGHT += fresnel_light(light_color, FRESNEL_COLOR, FRESNEL_STRENGTH, NORMAL, VIEW, LIGHT, ATTENUATION);
}
