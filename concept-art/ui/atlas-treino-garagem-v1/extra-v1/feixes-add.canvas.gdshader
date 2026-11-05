shader_type canvas_item;
render_mode blend_add, unshaded;
uniform float gain : hint_range(0.0, 4.0) = 1.0;
uniform vec4 light_tint : source_color = vec4(1.0);
void fragment() {
    vec4 beam = texture(TEXTURE, UV);
    COLOR = vec4(beam.rgb * light_tint.rgb * gain, beam.a * light_tint.a);
}
