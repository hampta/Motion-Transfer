bl_info = {
	"name": "Motion Transfer",
	"author": "Grey Ruessler",
	"version": (1, 0, 0),
	"blender": (2, 79, 0),
	"location": "Search > Motion Transfer",
	"description": "Transfer all animations from the selected armature to the active armature",
	"warning": "",
	"wiki_url": "",
	"category": "Object",
}

import bpy

def exec(skeleton_source,skeleton_target):
	import bpy

	boneparents_original = {}

	#Setup source and target

	source = skeleton_source
	target = skeleton_target

	bpy.context.scene.objects.active = source
	bpy.context.object.data.pose_position = 'REST'
	bpy.context.scene.objects.active = target
	bpy.context.object.data.pose_position = 'POSE'

	bpy.context.scene.objects.active = target
	bpy.ops.object.mode_set(mode='POSE')

	#Save parents

	for bone in target.data.bones:
		if not bone.parent is None:
			boneparents_original[bone.name] = bone.parent.name	   
		else:
			boneparents_original[bone.name] = "None"

	#Prevent duplicates

	for bone in source.data.bones:
		if bone.name in target.data.bones:
			bone.name = bone.name + "_src"

	#Apply target armature modifier, make them target source
			
	for ob in bpy.context.scene.objects:
		ob.select = False

	for ob in bpy.context.scene.objects:
		ob.select = True
		bpy.context.scene.objects.active = ob
		for mod in ob.modifiers:
			if mod.type == "ARMATURE":
				if mod.object == target:
					bpy.ops.object.modifier_apply(apply_as='DATA', modifier = mod.name )
					ob.modifiers.new(name = 'Skeleton', type = 'ARMATURE')
					ob.modifiers['Skeleton'].object = source
		ob.select = False

	#Merge skeletons

	target.select = True
	bpy.context.scene.objects.active = target
	bpy.ops.pose.armature_apply()

	source.select = True
	target.select = True
	bpy.context.scene.objects.active = source
	bpy.ops.object.join()

	#Reparent

	bpy.ops.object.mode_set(mode='EDIT')

	for bone in source.data.edit_bones:
		appendedname = bone.name + "_src" 
		if appendedname in source.data.edit_bones:
			bone.parent = source.data.edit_bones[ appendedname ]

	bpy.ops.object.mode_set(mode='POSE')
	bpy.context.object.data.pose_position = 'POSE'

	for a in bpy.data.actions:
		for fcu in a.fcurves:
			bone = fcu.data_path.split('"')[1]
			appendedname = bone + "_src"
			if appendedname in source.data.bones:		
				fcu.data_path = fcu.data_path.replace( bone, bone+"_src" )

	#Duplicate skeleton into final

	bpy.ops.object.mode_set(mode='OBJECT')

	source.select = True
	bpy.context.scene.objects.active = source
	source.animation_data.action = None

	bpy.ops.object.duplicate()

	bpy.context.scene.objects.active.name = "final_skeleton"

	final = bpy.data.objects["final_skeleton"]
	source.select = False
	final.select = True
	bpy.context.scene.objects.active = final

	#Reparent final skeleton to the original target specs

	bpy.ops.object.mode_set(mode='EDIT')

	for bone in final.data.edit_bones:
		par = bone.parent
		if not par is None:
			parname = par.name
			if parname.find("_src")!=-1:
				parname = parname.replace("_src","")
				if parname in final.data.edit_bones:
					bone.parent = final.data.edit_bones[parname]


	for bone in final.data.edit_bones:
		if bone.name.find("_src") != -1:
			final.data.edit_bones.remove( bone )
			
	bpy.ops.object.mode_set(mode='POSE')

	#Remove obsolete constraints

	for bone in final.pose.bones:
		for c in bone.constraints:
			bone.constraints.remove( c )

	#Copy positions/rotations from source, for baking

	for bone in final.pose.bones:	
		if bone.name in source.pose.bones:
			nc = bone.constraints.new(type='COPY_ROTATION')
			nc.target = source
			nc.subtarget = bone.name
			nc.influence = 1
			nc_pos = bone.constraints.new(type='COPY_LOCATION')
			nc_pos.target = source
			nc_pos.subtarget = bone.name
			nc_pos.influence = 1

	#Bake animation data

	actioncache = {}

	for a in bpy.data.actions:
		if not a.name in actioncache:
			actioncache[a.name] = True

	print(actioncache)

	for namev in actioncache:
		a = bpy.data.actions.get( namev )
		lenv = 1
		for fcu in a.fcurves:
			rng = fcu.range()
			lenv = max(rng[1],lenv)
		newName = a.name
		a.name = "old_" + a.name
		source.animation_data.action = a
		bakeaction = bpy.data.actions.new( name = newName )
		bakeaction.use_fake_user = True
		final.animation_data.action = bakeaction
		bpy.ops.nla.bake(frame_start=0, frame_end=lenv, only_selected=False, visual_keying=True, clear_constraints=False, use_current_action=True, bake_types={'POSE'})
		a.use_fake_user = False
		source.animation_data.action = None
		a.user_clear()
		bpy.data.actions.remove( a )

	#Cleanup Source

	for bone in final.pose.bones:
		for c in bone.constraints:
			bone.constraints.remove( c )

	for ob in bpy.context.scene.objects:
		if ob.type == "MESH":
			for mod in ob.modifiers:
				if mod.type == "ARMATURE":
					ob.modifiers.remove(mod)
			mod = ob.modifiers.new(name = 'Skelemod', type = 'ARMATURE')
			mod.object = final
			ob.parent = final
				
	final.select = False
	source.select = True
	bpy.context.scene.objects.active = source
	bpy.ops.object.delete() 



class MotionTransfer(bpy.types.Operator):
	bl_idname = "armature.motion_transfer"
	bl_label = "Motion Transfer"
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	
	def poll(cls, context):
		numSelected = 0
		for ob in context.scene.objects:
			if ob.select and ob.type=='ARMATURE':
				numSelected = numSelected + 1
		return numSelected>=2
	def execute(self, context):
		src = None
		trg = context.scene.objects.active
		for ob in context.scene.objects:
			if ob != trg and ob.select and ob.type=='ARMATURE':
				src = ob
		exec(src,trg)
		return {'FINISHED'}

def menu_func(self, context):  
	self.layout.operator(MotionTransfer.bl_idname)

def register():
	bpy.utils.register_module(__name__)
	bpy.types.VIEW3D_MT_pose.append(menu_func)
	bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.VIEW3D_MT_pose.remove(menu_func)
	bpy.types.VIEW3D_MT_object.remove(menu_func)

if __name__ == "__main__":
	register()
