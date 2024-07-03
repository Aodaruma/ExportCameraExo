# -*- coding: utf-8 -*-
import bpy
import math
from mathutils import Vector
from bpy_extras.io_utils import ExportHelper
import configparser
from copy import deepcopy

# import numpy as np

bl_info = {
    "name": "AviUtl Camera Exporting",
    "author": "Aodaruma",
    "version": (1, 1, 0),
    "blender": (4, 10, 0),
    "location": "File > Export > Camera Export (.exo)",
    "description": "Exporting Camera data to exo file",
    "warning": "",
    "support": "COMMUNITY",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export",
}
####################################

# class UIpanel(bpy.types.Panel):
#     bl_label = "BPM marker"
#     bl_space_type = "VIEW_3D"
#     bl_region_type = "TOOLS"
#     bl_category = "Tools"
#     def draw(self, context):x
#         self.layout.operator("my.mark", text="Mark")

# ------------------------------------------------ #


class ExportAviutlCamera(bpy.types.Operator, ExportHelper):
    bl_idname = "export_scene.export_aul_camera"
    bl_label = "Export Camera"
    bl_description = "Export Camera file (.exo)"
    bl_options = {"REGISTER", "UNDO", "PRESET"}
    filename_ext = ".exo"

    scale: bpy.props.FloatProperty(
        name="scale for AviUtl camera",
        description="Camera unit scale for AviUtl camera",
        default=100.0,
    )  # type: ignore

    # obj_name = ""

    def __init__(self):
        pass

    def execute(self, context):
        print("Execute was called.")

        # self.parse_command_line_options()

        # if (self.obj_name == ""):
        #     print("No suitable object name was provided")
        #     return {'FINISHED'}

        print("Executing......")

        self.export()

        print("Finished")
        return {"FINISHED"}

    def export(self):
        scene = bpy.context.scene
        obj = scene.objects

        config = configparser.ConfigParser()
        config.optionxform = str  # for case-sensitive
        config["exedit"] = {
            "width": scene.render.resolution_x,
            "height": scene.render.resolution_y,
            "rate": scene.render.fps,
            "scale": 1,
            # "length" : scene.frame_end - scene.frame_start
            # "audio_rate" : 44100
            # "audio_ch" : 2
        }

        def convTarget(m, fd):
            # ref: https://blender.stackexchange.com/questions/13738/how-to-calculate-the-direction-and-up-vector-of-a-camera
            q = m.to_quaternion()

            nz = Vector((0, 0, 1))
            vd = q @ Vector((0.0, 0.0, -1.0))
            vu = q @ Vector((0.0, 1.0, 0.0))

            target = (vd * fd + m.to_translation()) * self.scale

            s_phi = math.sqrt(1 - vd.dot(nz) ** 2)
            # print(s_phi)
            if s_phi > 0:
                t = vu.dot(nz) / s_phi
                if -1 <= t <= 1:
                    rz = math.acos(t)
                else:
                    rz = 0
            elif s_phi == 0:
                e = m.to_euler("ZYX")
                rz = e[2]
            rz *= 180 / math.pi

            tx, ty, tz = target
            # print(target)

            return tx, ty, tz, rz

        def convFOV(x):
            # ゴリ押し申し訳ねえ...
            return 1.155e-5 * x**3 - 5.1839e-5 * x**2 + 0.561 * x + 0.0477

        i = -1
        pre = []
        frame = scene.frame_start
        while frame <= scene.frame_end:
            # print("exporting '{} / {}'".format(i+2,scene.frame_end-scene.frame_start))
            print("----------")
            scene.frame_set(frame)
            # print(pre)
            # print("----")
            # loc, rot, fov, fd = [], [], 0, 0

            o = scene.camera
            if o is None:
                print("No camera found.")
                return {"CANCELLED"}
            cam: bpy.types.Camera = o.data  # type: ignore
            mtx = o.matrix_world
            loc = mtx.to_translation() * self.scale
            fov = cam.angle / math.pi * 180
            fd = cam.dof.focus_distance

            if i >= 0:
                tx, ty, tz, rz = convTarget(mtx, fd)
                ptx, pty, ptz, prz = convTarget(pre["mtx"], pre["fd"])

                config[str(i)] = {"start": i + 1, "end": i + 2, "layer": 1}
                if i > 0:
                    config[str(i)]["chain"] = "1"

                config[str(i) + ".0"] = {
                    "_name": "カメラ制御",
                    "X": "{:.1f},{:.1f},1".format(pre["loc"][0], loc[0]),
                    "Y": "{:.1f},{:.1f},1".format(-pre["loc"][2], -loc[2]),
                    "Z": "{:.1f},{:.1f},1".format(pre["loc"][1], loc[1]),
                    "目標X": "{:.1f},{:.1f},1".format(ptx, tx),
                    "目標Y": "{:.1f},{:.1f},1".format(-ptz, -tz),
                    "目標Z": "{:.1f},{:.1f},1".format(pty, ty),
                    "目標ﾚｲﾔ": "0",
                    "傾き": "{:.2f},{:.2f},1".format(prz, rz),
                    "深度ぼけ": "0",
                    "視野角": "{:.2f},{:.2f},1".format(
                        convFOV(pre["fov"]), convFOV(fov)
                    ),
                    "Zバッファ/シャドウマップを有効にする": "1",
                }
                # print()

            now = {"loc": loc, "fov": fov, "fd": fd, "mtx": mtx}
            pre = deepcopy(now)
            i += 1
            frame += 1

        with open(self.filepath, "w", encoding="shift_jis", newline="\r\n") as f:
            config.write(f, space_around_delimiters=False)

        return {"FINISHED"}


# Define a function to create the menu option for exporting.
def create_menu(self, context):
    self.layout.operator(ExportAviutlCamera.bl_idname, text="Export camera (.exo)")


####################################
classes = ExportAviutlCamera


def register():
    # for c in classes:
    # bpy.utils.register_class(c)
    bpy.utils.register_class(ExportAviutlCamera)
    bpy.types.TOPBAR_MT_file_export.append(create_menu)
    print(bl_info["name"] + " -> ON")


def unregister():
    # for c in reversed(classes):
    bpy.utils.unregister_class(ExportAviutlCamera)
    bpy.types.TOPBAR_MT_file_export.remove(create_menu)
    print(bl_info["name"] + " -> OFF")


if __name__ == "__main__":

    print("Registering...")
    register(classes)

    print("Executing...")
    bpy.ops.export_scene.export_aul_camera()

####################################

# print("done!")
