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
from mathutils import Matrix

def GetWorldSpaceBonePosition(ob,bone):
	mat = ob.matrix_world * bone.matrix_local
	loc, rot, scale = mat.decompose()
	return loc

def GetClosestBone(armature,pos,*args):
	biggestLength = 999999999
	if len(args)>=1:
		biggestLength = args[0]
	retVal = None
	for bone in armature.data.bones:
		wsPos = GetWorldSpaceBonePosition(armature,bone)
		localVec = (wsPos-pos)
		if localVec.length < biggestLength:
			retVal = bone
			biggestLength = localVec.length
	return retVal

class MotionTransfer(bpy.types.Operator):
	bl_idname = "armature.motion_transfer"
	bl_label = "Motion Transfer"
	bl_options = {'REGISTER', 'UNDO'}

	searchRadius = bpy.props.FloatProperty(name="Bone Search Radius", description = "If there isn't a matching bone name on the source, we search this far from the head", default = 1 )
	searchBlacklist = bpy.props.StringProperty(name="Bone Search Blacklist", description = "Ignore bones containing these parameters, separated by commas", default = "dummy" )
	cleanTransfer = bpy.props.BoolProperty(name="Clean Transfer", description = "Remove all bones which aren't in the target skeleton?", default = False )

	def exec(self,context,skeleton_source,skeleton_target):
		boneParentsOG = {}
		boneLinks = {}
		bonesToClean = {}
		targetBones = {}

		#Setup source and target

		source = skeleton_source
		target = skeleton_target

		context.scene.objects.active = source
		context.object.data.pose_position = 'REST'
		context.scene.objects.active = target
		context.object.data.pose_position = 'POSE'

		context.scene.objects.active = target
		bpy.ops.object.mode_set(mode='POSE')

		#Save parents

		for bone in target.data.bones:
			if not bone.parent is None:
				boneParentsOG[bone.name] = bone.parent.name
			else:
				boneParentsOG[bone.name] = "None"

		#Prevent duplicates and link same-named bones

		for bone in source.data.bones:
			if bone.name in target.data.bones:
				boneLinks[bone.name] = bone.name + "_src"
				bonesToClean[bone.name+"_src"] = True
				bone.name = bone.name + "_src"

		#Build link cache

		blacklistTable = self.searchBlacklist.split(",")
		if blacklistTable is None:
			if len(self.searchBlacklist)>0:
				blacklistTable = [self.searchBlacklist]
			else:
				blacklistTable = []

		for bone in target.data.bones:
			targetBones[bone.name] = True
			if not bone in boneLinks:
				doLink = True
				for blacklistString in blacklistTable:
					if bone.name.find(blacklistString)!=-1:
						print("discovered: " + blacklistString)
						doLink = False
				if doLink:
					closestBone = GetClosestBone(source,GetWorldSpaceBonePosition(target,bone),self.searchRadius)
					if closestBone is not None:
						boneLinks[bone.name] = closestBone.name
						bonesToClean[closestBone.name] = True

		#Apply target armature modifier, make them target source

		for ob in context.scene.objects:
			ob.select = False

		for ob in context.scene.objects:
			ob.select = True
			#context.scene.objects.active = ob
			for mod in ob.modifiers:
				if mod.type == "ARMATURE":
					if mod.object == target:
						bpy.ops.object.modifier_apply(apply_as='DATA', modifier = mod.name )
						ob.modifiers.new(name = 'Skeleton', type = 'ARMATURE')
						ob.modifiers['Skeleton'].object = source
			ob.select = False

		#Merge a duplicate of the target into source

		target.select = True
		context.scene.objects.active = target
		bpy.ops.pose.armature_apply()

		bpy.ops.object.mode_set(mode='OBJECT')
		target_dupe = target.copy()
		target_dupe.data = target.data.copy()
		target_dupe.animation_data_clear()
		context.scene.objects.link(target_dupe)
		target.select = False
		source.select = True
		target_dupe.select = True
		context.scene.objects.active = source
		bpy.ops.object.join()
		source.select = False
		target.select = True
		context.scene.objects.active = target
		#now clean and prepare targe to become our final skeleton
		bpy.ops.object.mode_set(mode='EDIT')
		for bone in target.data.edit_bones:
			target.data.edit_bones.remove(bone)
		bpy.ops.object.mode_set(mode='OBJECT')
		context.scene.objects.active = source
		source.select = True
		target.select = False
		#Reparent

		bpy.ops.object.mode_set(mode='EDIT')

		for bone in source.data.edit_bones:
			if bone.name in boneLinks:
				linkedBone = boneLinks[bone.name]
				if linkedBone in source.data.edit_bones:
					bone.parent = source.data.edit_bones[ linkedBone ]

		bpy.ops.object.mode_set(mode='POSE')
		context.object.data.pose_position = 'POSE'

		for a in bpy.data.actions:
			for fcu in a.fcurves:
				bone = fcu.data_path.split('"')[1]
				appendedname = bone + "_src"
				if appendedname in source.data.bones:
					fcu.data_path = fcu.data_path.replace( bone, bone+"_src" )

		#Duplicate source into target as final

		bpy.ops.object.mode_set(mode='OBJECT')

		source.animation_data.action = None

		src_dupe = source.copy()
		src_dupe.data = source.data.copy()
		context.scene.objects.link(src_dupe)


		final = target
		source.select = False
		src_dupe.select = True
		final.select = True
		context.scene.objects.active = final
		bpy.ops.object.join()

		#Reparent final skeleton to the original target specs

		bpy.ops.object.mode_set(mode='EDIT')

		for bone in final.data.edit_bones:
			par = bone.parent
			if par is not None:
				if bone.name in boneParentsOG:
					parBoneName = boneParentsOG[bone.name]
					if parBoneName in final.data.edit_bones:
						bone.parent = final.data.edit_bones[parBoneName]

		if self.cleanTransfer:
			for bone in final.data.edit_bones:
				if not bone.name in targetBones:
					final.data.edit_bones.remove( bone )
		else:
			for bone in final.data.edit_bones:
				if bone.name in bonesToClean:
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

		for namev in actioncache:
			a = bpy.data.actions.get( namev )
			lenv = 1
			for fcu in a.fcurves:
				rng = fcu.range()
				lenv = max(rng[1],lenv)
			newName = a.name
			a.name = "old_" + a.name
			source.animation_data.action = a
			#make the new one
			bakeaction = bpy.data.actions.new( name = newName )
			bakeaction.use_fake_user = True
			final.animation_data.action = bakeaction
			bpy.ops.nla.bake(frame_start=0, frame_end=lenv, only_selected=False, visual_keying=True, clear_constraints=False, use_current_action=True, bake_types={'POSE'})
			#remove the old one
			a.use_fake_user = False
			source.animation_data.action = None
			a.user_clear()
			bpy.data.actions.remove( a )

		#Cleanup Source

		for bone in final.pose.bones:
			for c in bone.constraints:
				bone.constraints.remove( c )

		for ob in context.scene.objects:
			if ob.type == "MESH":
				for mod in ob.modifiers:
					if mod.type == "ARMATURE":
						ob.modifiers.remove(mod)
				mod = ob.modifiers.new(name = 'Skelemod', type = 'ARMATURE')
				mod.object = final
				ob.parent = final

		final.select = False
		source.select = True
		context.scene.objects.active = source
		bpy.ops.object.delete()
		context.scene.objects.active = target
		target.select = True
		bpy.ops.object.mode_set(mode='POSE')

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
		self.exec(context,src,trg)
		return {'FINISHED'}

	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_props_dialog(self,640)

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
