extends Node3D

const GROUND_Y := 6.5
const IDLER_X := 48.0
const HYDR_MOUNT_X := 28.0
const HYDR_EXTEND := 42.0
const PIVOT_X := IDLER_X
const TRACK_LENGTH := 96.0
const TRACK_WIDTH := 16.0
const STAIR_RISE := 18.0
const STAIR_RUN := 24.0
const NUM_STEPS := 5

var chair: RigidBody3D
var hydr_ext := 0.0
var hydr_extending := false
var hydr_retracting := false
var cam: Camera3D
var cam_target := Vector3.ZERO
var hydr_mesh: MeshInstance3D

func _ready() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.82, 0.82, 0.85)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.7, 0.7, 0.7)
	env.ambient_light_energy = 0.6
	env.tonemap_mode = Environment.TONE_MAP_ACES
	var sky := WorldEnvironment.new()
	sky.environment = env
	add_child(sky)

	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50, 30, 0)
	sun.light_energy = 1.4
	sun.shadow_enabled = true
	add_child(sun)

	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(20, -120, 0)
	fill.light_energy = 0.4
	add_child(fill)

	cam = Camera3D.new()
	cam.fov = 40
	cam.near = 0.1
	cam.far = 1000
	add_child(cam)

	_create_ground()
	_create_stairs()
	_create_chair()

func _load_obj(path: String) -> ArrayMesh:
	var verts := []
	var norms := []
	var vert_data := []  # [[pos_x,y,z, nx,ny,nz], ...]
	var face_indices := []

	var file := FileAccess.open(path, FileAccess.READ)
	if not file:
		push_error("Cannot open: " + path)
		return null

	while not file.eof_reached():
		var line = file.get_line().strip_edges()
		if line.begins_with("v "):
			var p = line.split(" ")
			verts.append(Vector3(p[1].to_float(), p[2].to_float(), p[3].to_float()))
		elif line.begins_with("vn "):
			var p = line.split(" ")
			norms.append(Vector3(p[1].to_float(), p[2].to_float(), p[3].to_float()))
		elif line.begins_with("f "):
			var parts = line.split(" ")
			var face := []
			for i in range(1, parts.size()):
				if parts[i] == "":
					continue
				var indices = parts[i].split("/")
				var vi = indices[0].to_int() - 1
				var ni = -1
				if indices.size() >= 3 and indices[2] != "":
					ni = indices[2].to_int() - 1
				face.append([vi, ni])
			if face.size() >= 3:
				face_indices.append(face)

	# Build per-vertex arrays (triangulate faces)
	var positions := PackedVector3Array()
	var normals_arr := PackedVector3Array()
	var indices_arr := PackedInt32Array()

	for face in face_indices:
		for i in range(1, face.size() - 1):
			var tri := [face[0], face[i], face[i + 1]]
			for corner in tri:
				var vi = corner[0]
				var ni = corner[1]
				positions.append(verts[vi])
				if ni >= 0 and ni < norms.size():
					normals_arr.append(norms[ni])
				else:
					normals_arr.append(Vector3.ZERO)
				indices_arr.append(indices_arr.size())

	# Compute smooth normals for vertices that got ZERO
	for i in range(positions.size()):
		if normals_arr[i].length() < 0.01:
			var sum := Vector3.ZERO
			for j in range(positions.size()):
				if j != i and positions[j].distance_to(positions[i]) < 0.01:
					sum += normals_arr[j]
			if sum.length() > 0:
				normals_arr[i] = sum.normalized()

	# If still zero, compute from adjacent triangles
	for i in range(positions.size()):
		if normals_arr[i].length() < 0.01:
			normals_arr[i] = Vector3(0, 1, 0)

	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = positions
	arrays[Mesh.ARRAY_NORMAL] = normals_arr
	arrays[Mesh.ARRAY_INDEX] = indices_arr

	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh

func _create_ground() -> void:
	var body := StaticBody3D.new()
	body.position = Vector3(0, -5, 0)
	var col := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(600, 10, 200)
	col.shape = box
	body.add_child(col)

	var m := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(600, 1, 200)
	m.mesh = bm
	m.position.y = 5
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.35, 0.33, 0.30)
	mat.roughness = 0.9
	m.material_override = mat
	body.add_child(m)
	add_child(body)

func _create_stairs() -> void:
	for i in NUM_STEPS:
		var body := StaticBody3D.new()
		var sx = IDLER_X + 30.0 + i * STAIR_RUN
		var sy = GROUND_Y - STAIR_RISE * (i + 1)
		body.position = Vector3(sx, sy, 0)
		var col := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = Vector3(STAIR_RUN, STAIR_RISE * 2, 100)
		col.shape = box
		body.add_child(col)
		var m := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(STAIR_RUN, STAIR_RISE, 100)
		m.mesh = bm
		m.position.y = -STAIR_RISE / 2
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.50, 0.47, 0.43)
		mat.roughness = 0.85
		m.material_override = mat
		body.add_child(m)
		add_child(body)

func _create_chair() -> void:
	chair = RigidBody3D.new()
	chair.position = Vector3(0, 50, 0)
	chair.mass = 50.0
	chair.gravity_scale = 1.0
	chair.linear_damp = 2.0
	chair.angular_damp = 5.0
	chair.can_sleep = false

	# Physics collision (simplified box)
	var col := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(TRACK_LENGTH, 40, TRACK_WIDTH * 2 + 10)
	col.shape = box
	col.position = Vector3(0, GROUND_Y + 20, 0)
	chair.add_child(col)

	# --- Visual: load full assembly OBJ ---
	var assembly_mesh = _load_obj("res://parts/chair_assembly.obj")
	if assembly_mesh:
		var visual := MeshInstance3D.new()
		visual.mesh = assembly_mesh
		visual.rotation.x = -PI / 2
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.55, 0.57, 0.60)
		mat.metallic = 0.3
		mat.roughness = 0.5
		visual.material_override = mat
		visual.cast_shadow = GeometryInstance3D.SHADOW_CAST_SETTING_ON
		chair.add_child(visual)

	# --- Hydraulic (separate for animation) ---
	var hydr_mesh_data = _load_obj("res://parts/hydraulic.obj")
	if hydr_mesh_data:
		hydr_mesh = MeshInstance3D.new()
		hydr_mesh.mesh = hydr_mesh_data
		hydr_mesh.rotation.x = -PI / 2
		hydr_mesh.position = Vector3(-HYDR_MOUNT_X, GROUND_Y, 0)
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(0.35, 0.37, 0.40)
		mat.metallic = 0.4
		mat.roughness = 0.4
		hydr_mesh.material_override = mat
		chair.add_child(hydr_mesh)

	add_child(chair)

func _process(_delta: float) -> void:
	if chair and cam:
		cam_target = cam_target.lerp(chair.position, 0.05)
		var cam_pos = cam_target + Vector3(-80, 60, 100)
		cam.look_at_from_position(cam_pos, cam_target, Vector3.UP)

func _physics_process(delta: float) -> void:
	if not chair:
		return

	if hydr_extending:
		hydr_ext = min(hydr_ext + 100.0 * delta, HYDR_EXTEND)
	elif hydr_retracting:
		hydr_ext = max(hydr_ext - 100.0 * delta, 0.0)

	if hydr_mesh:
		hydr_mesh.position.y = GROUND_Y - hydr_ext

	# Hydraulic force
	if hydr_ext > 0:
		var local_bottom = Vector3(-HYDR_MOUNT_X, GROUND_Y - hydr_ext, 0)
		var world_bottom = chair.to_global(local_bottom)
		if world_bottom.y <= GROUND_Y + 2:
			var pen = (GROUND_Y + 2) - world_bottom.y
			var push = pen * 8000.0
			chair.apply_central_force(Vector3(0, push, 0))
			var arm = local_bottom.x - PIVOT_X
			chair.apply_torque(Vector3(0, 0, -push * arm * 0.4))

	# Ground contact
	if chair.global_position.y < GROUND_Y:
		var pen = GROUND_Y - chair.global_position.y
		chair.apply_central_force(Vector3(0, pen * 10000.0, 0))

	# Stair contact
	var chair_x = chair.global_position.x
	for i in NUM_STEPS:
		var step_left = IDLER_X + 30.0 + i * STAIR_RUN
		var step_right = step_left + STAIR_RUN
		if step_left - 10 < chair_x and chair_x < step_right + 10:
			var step_top = GROUND_Y - STAIR_RISE * (i + 1)
			if chair.global_position.y < step_top + 5:
				var lift = (step_top + 5 - chair.global_position.y) * 6000.0
				chair.apply_central_force(Vector3(0, lift, 0))

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey:
		if event.pressed:
			match event.keycode:
				KEY_1:
					hydr_extending = true
					hydr_retracting = false
				KEY_2:
					hydr_retracting = true
					hydr_extending = false
				KEY_W, KEY_UP:
					chair.apply_central_force(Vector3(3000, 0, 0))
				KEY_S, KEY_DOWN:
					chair.apply_central_force(Vector3(-3000, 0, 0))
				KEY_R:
					chair.position = Vector3(0, 50, 0)
					chair.rotation = Vector3.ZERO
					chair.linear_velocity = Vector3.ZERO
					chair.angular_velocity = Vector3.ZERO
					hydr_ext = 0
					cam_target = Vector3.ZERO
		else:
			if event.keycode == KEY_1:
				hydr_extending = false
			elif event.keycode == KEY_2:
				hydr_retracting = false
