class_name GaleHeadTurn
extends SkeletonModifier3D
## Turns the head (and a little of the neck) about the skeleton's up axis after the animation is
## applied, so the face reads toward the camera. Modifier results are recomputed every frame, so
## the turn never accumulates over held (stepped) poses.

@export var degrees := 0.0
var bones: Array[Vector2] = []  # (bone index, share of the turn)

func setup(skeleton: Skeleton3D) -> void:
	bones.clear()
	for entry: Array in [["neck", 0.35], ["head", 0.65]]:
		var index := skeleton.find_bone(entry[0])
		if index >= 0:
			bones.append(Vector2(index, entry[1]))

func _process_modification() -> void:
	var skeleton := get_skeleton()
	if skeleton == null or is_zero_approx(degrees):
		return
	for entry: Vector2 in bones:
		var index := int(entry.x)
		var pose := skeleton.get_bone_global_pose(index)
		var turn := Basis(Vector3.UP, deg_to_rad(degrees * entry.y))
		pose.basis = turn * pose.basis
		skeleton.set_bone_global_pose(index, pose)
