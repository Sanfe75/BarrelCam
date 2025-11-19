# Copyright 2022 Simone <sanfe75@gmail.com>
#
# Licensed under the Apache License, Version 2.0(the "License"); you may not use this file except
# in compliance with the License.You may obtain a copy of the License at:
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
# on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License
# for the specific language governing permissions and limitations under the License.
#

import copy

from PySide6.QtGui import QUndoCommand


class CamAddCommand(QUndoCommand):
    """
    Undo command for Cam Add
    """

    def __init__(self, main_window, cam_profile, text, parent=None):
        """
        Undo Command Constructor
        """

        super(CamAddCommand, self).__init__(text, parent)

        self.main_window = main_window
        self.cam_profile = cam_profile
        self.text = text

    def redo(self):
        """
        Redo: Readds the removed profile
        """

        self.main_window.cam.add_cam(self.cam_profile)
        self.main_window.scene.update_scene()
        self.main_window.cam.set_dirty(True)
        self.main_window.update_widgets()
        self.main_window.update_status(self.text)

    def undo(self):
        """
        Undo: Removes the added profile
        """

        self.main_window.cam.del_cam(self.cam_profile)
        self.main_window.scene.update_scene()
        self.main_window.cam.set_dirty(True)
        self.main_window.update_widgets()


class CamCommand(QUndoCommand):
    """
    Undo command for Cam settings Edit
    """

    def __init__(self, main_window, cam, edited_cam, text, parent=None):
        """
        Undo Command Constructor
        """

        super(CamCommand, self).__init__(text, parent)

        self.main_window = main_window
        self.cam = cam
        self.original_cam = copy.deepcopy(cam)
        self.edited_cam = edited_cam
        self.text = text

    def undo(self):
        """
        Undo the profile editing
        """

        self.cam.set_speed(self.original_cam.speed())
        self.cam.set_radius(self.original_cam.radius())
        for i, cam_profile in enumerate(self.cam):
            cam_profile.set_color(self.original_cam[i].color())
            cam_profile.set_depth(self.original_cam[i].depth())
            cam_profile.set_height(self.original_cam[i].height())
            cam_profile.check_cam()
        self.main_window.scene.update_scene()
        self.main_window.cam.set_dirty(True)
        self.main_window.update_widgets()

    def redo(self):
        """
        Redo the profile editing
        """

        self.cam.set_speed(self.edited_cam.speed())
        self.cam.set_radius(self.edited_cam.radius())
        for i, cam_profile in enumerate(self.cam):
            cam_profile.set_color(self.edited_cam[i].color())
            cam_profile.set_depth(self.edited_cam[i].depth())
            cam_profile.set_height(self.edited_cam[i].height())
            cam_profile.check_cam()
        self.main_window.scene.update_scene()
        self.main_window.cam.set_dirty(True)
        self.main_window.update_widgets()
        self.main_window.update_status(self.text)


class CamEditCommand(QUndoCommand):
    """
    Undo command for Cam Edit
    """

    def __init__(self, main_window, cam_profile, edited_cam_profile, text, parent=None):
        """
        Undo Command Constructor
        """

        super(CamEditCommand, self).__init__(text, parent)

        self.main_window = main_window
        self.cam_profile = cam_profile
        self.original_cam_profile = copy.deepcopy(cam_profile)
        self.edited_cam_profile = edited_cam_profile
        self.text = text

    def undo(self):
        """
        Undo the profile editing
        """

        self.update_cam_profile(self.original_cam_profile)
        self.main_window.scene.update_scene()
        self.main_window.cam.set_dirty(True)
        self.main_window.update_widgets()

    def redo(self):
        """
        Redo the profile editing
        """

        self.update_cam_profile(self.edited_cam_profile)
        self.main_window.scene.update_scene()
        self.main_window.cam.set_dirty(True)
        self.main_window.update_widgets()
        self.main_window.update_status(self.text)

    def update_cam_profile(self, cam_profile):
        """
        Update the cam Profile
        """

        self.cam_profile.set_label(cam_profile.label())
        self.cam_profile.set_color(cam_profile.color())


class CamMirrorCommand(QUndoCommand):
    """
    Undo command for Cam Mirror
    """

    def __init__(self, main_window, text, parent=None):
        """
        Undo Command Constructor
        """

        super(CamMirrorCommand, self).__init__(text, parent)

        self.main_window = main_window
        self.text = text

    def redo(self):
        """
        Redo the cam mirroring
        """

        self.main_window.scene.clearSelection()
        self.main_window.cam.mirror()
        self.main_window.scene.update_scene()
        self.main_window.cam.set_dirty(True)
        self.main_window.update_widgets()
        self.main_window.update_status(self.text)

    def undo(self):
        """
        Undo the cam mirroring
        """

        self.main_window.scene.clearSelection()
        self.main_window.cam.mirror()
        self.main_window.scene.update_scene()
        self.main_window.cam.set_dirty(True)
        self.main_window.update_widgets()


class CamMoveCommand(QUndoCommand):
    """
    Undo command for Cam Move
    """

    def __init__(self, main_window, cam_profiles, translation, text, parent=None):
        """
        Undo Command Constructor
        """

        super(CamMoveCommand, self).__init__(text, parent)

        self.main_window = main_window
        self.cam_profiles = cam_profiles
        self.translation = translation
        self.text = text

    def redo(self):
        """
        Redo the profile editing
        """

        for cam_profile in self.cam_profiles:
            cam_profile.move(self.translation)
        self.main_window.scene.update_scene()
        self.main_window.cam.set_dirty(True)
        self.main_window.update_widgets()
        self.main_window.update_status(self.text)

    def undo(self):
        """
        Undo the profile editing
        """

        for cam_profile in self.cam_profiles:
            cam_profile.move(-self.translation)
        self.main_window.scene.update_scene()
        self.main_window.cam.set_dirty(True)
        self.main_window.update_widgets()


class EditDeleteCommand(QUndoCommand):
    """
    Undo command for Edit Delete
    """

    def __init__(self, main_window, cam_profile_list, cam_point_list, text, parent=None):
        """
        Undo Command Constructor
        """

        super(EditDeleteCommand, self).__init__(text, parent)

        self.main_window = main_window
        self.cam_profile_list = cam_profile_list
        self.cam_point_list = cam_point_list
        self.text = text

    def redo(self):
        """
        Redo the items delete
        """

        for point, cam_profile in self.cam_point_list:
            cam_profile.del_point(point)
        for cam_profile in self.cam_profile_list:
            self.main_window.cam.del_cam(cam_profile)
        self.main_window.scene.update_scene()
        self.main_window.cam.set_dirty(True)
        self.main_window.update_widgets()
        self.main_window.update_status(self.text)

    def undo(self):
        """
        Undo the items delete
        """

        for cam_profile in self.cam_profile_list:
            self.main_window.cam.add_cam(cam_profile)
        for point, cam_profile in self.cam_point_list:
            cam_profile.add_point(point)
        self.main_window.scene.update_scene()
        self.main_window.cam.set_dirty(True)
        self.main_window.update_widgets()


class PointAddCommand(QUndoCommand):
    """
    Undo command for Point Add
    """

    def __init__(self, main_window, cam_profile, point, text, parent=None):
        """
        Undo Command Constructor
        """

        super(PointAddCommand, self).__init__(text, parent)

        self.main_window = main_window
        self.cam_profile = cam_profile
        self.point = point
        self.text = text

    def redo(self):
        """
        Redo: Adds the removed point
        """

        self.cam_profile.add_point(self.point)
        self.cam_profile.check_cam()
        self.main_window.scene.update_scene()
        self.main_window.cam.set_dirty(True)
        self.main_window.update_widgets()
        self.main_window.update_status(self.text)

    def undo(self):
        """
        Undo: Removes the added point
        """

        self.cam_profile.del_point(self.point)
        self.cam_profile.check_cam()
        self.main_window.scene.updateScene()
        self.main_window.cam.set_dirty(True)
        self.main_window.update_widgets()


class PointEditCommand(QUndoCommand):
    """
    Undo command for Point Edit
    """

    def __init__(self, main_window, cam_profile, cam_point, edited_cam_point, text, parent=None):
        """
        Undo Command Constructor
        """

        super(PointEditCommand, self).__init__(text, parent)

        self.main_window = main_window
        self.cam_profile = cam_profile
        self.cam_point = cam_point
        self.original_cam_point = copy.deepcopy(cam_point)
        self.edited_cam_point = edited_cam_point
        self.text = text

    def redo(self):
        """
        Redo the point editing
        """

        self.cam_profile.edit_point(self.edited_cam_point, self.cam_point)
        self.cam_profile.check_cam()
        self.main_window.scene.update_scene()
        self.main_window.cam.set_dirty(True)
        self.main_window.update_widgets()
        self.main_window.update_status(self.text)

    def undo(self):
        """
        Undo the point editing
        """

        self.cam_profile.edit_point(self.original_cam_point, self.cam_point)
        self.cam_profile.check_cam()
        self.main_window.scene.update_scene()
        self.main_window.cam.set_dirty(True)
        self.main_window.update_widgets()


class PointMoveCommand(QUndoCommand):
    """
    Undo command for Point Move
    """

    def __init__(self, scene, cam_point_item, value, done, text, parent=None):
        """
        Undo Command Constructor
        """

        super(PointMoveCommand, self).__init__(text, parent)

        self.scene = scene
        self.cam_point_item = cam_point_item
        self.cam_point = cam_point_item.cam_point
        self.start_angle = self.cam_point.angle()
        self.start_displacement = self.cam_point.displacement()
        self.stop_angle = value.x() / self.scene.angle_steps
        self.stop_displacement = value.y() / self.scene.displacement_steps
        self.done = done

    def id(self):
        """
        Command id from cam_point
        """

        unsigned_mask = 0xFFFFFFF
        return id(self.cam_point) & unsigned_mask

    def mergeWith(self, command):
        """
        Merges 2 movements
        """

        self.stop_angle = command.stop_angle
        self.stop_displacement = command.stop_displacement

        return True

    def redo(self):
        """
        Redo the point editing
        """

        self.cam_point.set_angle(self.stop_angle)
        self.cam_point.set_displacement(self.stop_displacement)
        self.scene.modified()

        if self.done:
            self.scene.update_scene()

    def undo(self):
        """
        Undo the point editing
        """

        self.cam_point.set_angle(self.start_angle)
        self.cam_point.set_displacement(self.start_displacement)
        self.scene.modified()
        self.scene.update_scene()
        self.done = True


class PointsMoveCommand(QUndoCommand):
    """
    Undo command for Points Move
    self.undoStack.push(PointsMoveCommand(self, point_list, delta_angle, delta_displacement, "Cam Points Moved"))
    """

    def __init__(self, main_window, point_list, delta_angle, delta_displacement, text, parent=None):
        """
        Undo Command Constructor
        """

        super(PointsMoveCommand, self).__init__(text, parent)

        self.mainWindow = main_window
        self.pointList = point_list
        self.delta_angle = delta_angle
        self.delta_displacement = delta_displacement
        self.text = text

    def redo(self):
        """
        Redo the points editing
        """

        for camPoint in self.pointList:
            camPoint[0].move(self.delta_angle, self.delta_displacement)
        self.mainWindow.scene.update_scene()
        self.mainWindow.cam.set_dirty(True)
        self.mainWindow.update_widgets()
        self.mainWindow.update_status(self.text)

    def undo(self):
        """
        Undo the points editing
        """

        for camPoint in self.pointList:
            camPoint[0].move(-self.delta_angle, -self.delta_displacement)
        self.mainWindow.scene.update_scene()
        self.mainWindow.cam.set_dirty(True)
        self.mainWindow.update_widgets()