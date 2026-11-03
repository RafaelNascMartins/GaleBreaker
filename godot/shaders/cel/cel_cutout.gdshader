// Alpha-cut cel foliage (leaves, flowers, corals), lit from both sides (see cel_body.gdshaderinc).
shader_type spatial;
render_mode cull_disabled;

#define CEL_CUTOUT
#include "cel_body.gdshaderinc"
