bl_info = {
    "name": "Image Denoise Operator",
    "author": "Martin Lorentzon",
    "version": (1, 0),
    "blender": (4, 1, 0),
    "location": "Image Editor > Image > Filters",
    "description": "Denoise image with Open Image Denoise",
    "warning": "",
    "doc_url": "",
    "support": "COMMUNITY",
    "category": "Image",
}

# ==================== NOTICE ====================
# Feel free to derive from this code when writing
# your own image processing operators.
# Important bits of this script file are marked
# with an asterisk (*) and need to be updated.
# Do not get rid of this notice.
# ================================================

import bpy
from bpy.props import BoolProperty, EnumProperty, StringProperty

SCENE_NAME = "Image Denoise Scene"  # <-- Temporary compositing scene*
BL_IDNAME  = 'image.denoise'  # <-- Operator bl_idname*



# == Menu ==
# (Modifications are disadvised)
class IMAGE_MT_filters(bpy.types.Menu):
    bl_label = "Filters"
    
    def draw(self, _context):
        layout = self.layout
        
        layout.operator(BL_IDNAME)


def menu_func(self, context):
    layout = self.layout
    
    if context.edit_image:
        layout.separator()
        
        layout.menu("IMAGE_MT_filters")



# == Operator ==
class IMAGE_OT_denoise(bpy.types.Operator):
    bl_idname = 'image.denoise'
    bl_label = "Denoise"
    bl_description = "Denoise image with Open Image Denoise"
    
    image: StringProperty(options={'HIDDEN'})
    
    prefilter: EnumProperty(
        name="Prefilter",
        description="Denoising prefilter",
        items=[('NONE', "None", "No prefiltering"),
               ('FAST', "Fast", "Denoise image and guiding passes together"),
               ('ACCURATE', "Accurate", "Prefilter noisy guiding passes before denoising image")],
        default='ACCURATE')
    
    use_hdr: BoolProperty(
        name="HDR", 
        description="Preserve colors outside the 0 to 1 range", 
        default=True)
    
    @classmethod
    def poll(cls, context):
        return getattr(context, 'edit_image', None)
    
    
    def execute(self, context):
        # -- Get source image --
        if self.image != "":
            source_image = self.image
        else:
            source_image = context.edit_image
        
        # -- Create scene --
        if SCENE_NAME in bpy.data.scenes:
            scene = bpy.data.scenes[SCENE_NAME]
        else:
            scene = bpy.data.scenes.new(SCENE_NAME)
        
        # -- Set up compositor --
        scene.use_nodes = True
        node_tree = scene.node_tree
        nodes = node_tree.nodes
        links = node_tree.links
        
        nodes.clear()
        
        image_node   = nodes.new('CompositorNodeImage')
        denoise_node = nodes.new('CompositorNodeDenoise')
        viewer_node  = nodes.new('CompositorNodeViewer')
        
        image_node.location   = (-200,0)
        denoise_node.location = (0,0)
        viewer_node.location  = (200,0)
        
        links.new(denoise_node.inputs[0], image_node.outputs[0])
        links.new(viewer_node.inputs[0], denoise_node.outputs[0])
        
        # -- Change node parameters --
        image_node.image = source_image
        denoise_node.prefilter = self.prefilter
        denoise_node.use_hdr = self.use_hdr
        
        # -- Render --
        bpy.ops.render.render(animation=False, 
                              write_still=False, 
                              use_viewport=False, 
                              layer="", 
                              scene=SCENE_NAME)
        
        viewer_image = next((img for img in bpy.data.images if img.type == 'COMPOSITING'), None)
        
        source_image.pixels = viewer_image.pixels[:]
        
        # -- Remove scene --
        bpy.data.scenes.remove(scene)
        return {'FINISHED'}
    
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)



# == Register ==
def register():
    bpy.utils.register_class(IMAGE_OT_denoise)  # <-- Register operator*
    
    # -- Append/update filters menu --
    # (Modifications are disadvised)
    img_filters_menu = getattr(bpy.types, 'IMAGE_MT_filters', None)
    
    if not img_filters_menu:
        bpy.utils.register_class(IMAGE_MT_filters)
        bpy.types.IMAGE_MT_image.append(menu_func)
    else:
        original_draw_method = img_filters_menu.draw
        
        
        def new_draw_method(self, context):
            layout = self.layout
            
            original_draw_method(self, context)
            
            layout.operator(BL_IDNAME)
        
        
        img_filters_menu.draw = new_draw_method


def unregister():
    bpy.utils.unregister_class(IMAGE_OT_denoise)  # <-- Unregister operator*


if __name__ == "__main__":
    register()
    #bpy.ops.image.denoise(image='noise.png')