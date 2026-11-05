shader_type spatial;
render_mode blend_add, depth_draw_never, cull_disabled, unshaded, shadows_disabled;

uniform sampler2D beam_texture : source_color;
uniform vec4 light_tint : source_color = vec4(1.0);
uniform float gain : hint_range(0.0, 4.0) = 1.0;

void fragment() {
    vec4 beam = texture(beam_texture, UV);
    ALBEDO = beam.rgb * light_tint.rgb * gain;
    ALPHA = beam.a * light_tint.a;
}
