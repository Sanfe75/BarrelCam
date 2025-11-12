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

import ezdxf
import os
import pickle
import sys

from bisect import insort_left
#from cadquery.vis import show
from cadquery import exporters, Workplane
from numpy import array, cos, linalg, pi, sin
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

MAGIC_NUMBER = 20140112
FILE_VERSION = 1

# defaults:
RADIUS = 149.0
SPEED = 20.0  # round per minute
angle_steps = 10  # steps per degree
displacement_steps = 10  # steps per millimeter
_ACI_ = ((0, 0, 0),
         (255, 0, 0),
         (255, 255, 0),
         (0, 255, 0),
         (0, 255, 255),
         (0, 0, 255),
         (255, 0, 255),
         (255, 255, 255),
         (128, 128, 128),
         (192, 192, 192),
         (255, 0, 0),
         (255, 127, 127),
         (204, 0, 0),
         (204, 102, 102),
         (153, 0, 0),
         (153, 76, 76),
         (127, 0, 0),
         (127, 63, 63),
         (76, 0, 0),
         (76, 38, 38),
         (255, 63, 0),
         (255, 159, 127),
         (204, 51, 0),
         (204, 127, 102),
         (153, 38, 0),
         (153, 95, 76),
         (127, 31, 0),
         (127, 79, 63),
         (76, 19, 0),
         (76, 47, 38),
         (255, 127, 0),
         (255, 191, 127),
         (204, 102, 0),
         (204, 153, 102),
         (153, 76, 0),
         (153, 114, 76),
         (127, 63, 0),
         (127, 95, 63),
         (76, 38, 0),
         (76, 57, 38),
         (255, 191, 0),
         (255, 223, 127),
         (204, 153, 0),
         (204, 178, 102),
         (153, 114, 0),
         (153, 133, 76),
         (127, 95, 0),
         (127, 111, 63),
         (76, 57, 0),
         (76, 66, 38),
         (255, 255, 0),
         (255, 255, 127),
         (204, 204, 0),
         (204, 204, 102),
         (152, 152, 0),
         (152, 152, 76),
         (127, 127, 0),
         (127, 127, 63),
         (76, 76, 0),
         (76, 76, 38),
         (191, 255, 0),
         (223, 255, 127),
         (153, 204, 0),
         (178, 204, 102),
         (114, 152, 0),
         (133, 152, 76),
         (95, 127, 0),
         (111, 127, 63),
         (57, 76, 0),
         (66, 76, 38),
         (127, 255, 0),
         (191, 255, 127),
         (102, 204, 0),
         (153, 204, 102),
         (76, 152, 0),
         (114, 152, 76),
         (63, 127, 0),
         (95, 127, 63),
         (38, 76, 0),
         (57, 76, 38),
         (63, 255, 0),
         (159, 255, 127),
         (51, 204, 0),
         (127, 204, 102),
         (38, 152, 0),
         (95, 152, 76),
         (31, 127, 0),
         (79, 127, 63),
         (19, 76, 0),
         (47, 76, 38),
         (0, 255, 0),
         (127, 255, 127),
         (0, 204, 0),
         (102, 204, 102),
         (0, 152, 0),
         (76, 152, 76),
         (0, 127, 0),
         (63, 127, 63),
         (0, 76, 0),
         (38, 76, 38),
         (0, 255, 63),
         (127, 255, 159),
         (0, 204, 51),
         (102, 204, 127),
         (0, 152, 38),
         (76, 152, 95),
         (0, 127, 31),
         (63, 127, 79),
         (0, 76, 19),
         (38, 76, 47),
         (0, 255, 127),
         (127, 255, 191),
         (0, 204, 102),
         (102, 204, 153),
         (0, 152, 76),
         (76, 152, 114),
         (0, 127, 63),
         (63, 127, 95),
         (0, 76, 38),
         (38, 76, 57),
         (0, 255, 191),
         (127, 255, 223),
         (0, 204, 153),
         (102, 204, 178),
         (0, 152, 114),
         (76, 152, 133),
         (0, 127, 95),
         (63, 127, 111),
         (0, 76, 57),
         (38, 76, 66),
         (0, 255, 255),
         (127, 255, 255),
         (0, 204, 204),
         (102, 204, 204),
         (0, 152, 152),
         (76, 152, 152),
         (0, 127, 127),
         (63, 127, 127),
         (0, 76, 76),
         (38, 76, 76),
         (0, 191, 255),
         (127, 223, 255),
         (0, 153, 204),
         (102, 178, 204),
         (0, 114, 152),
         (76, 133, 152),
         (0, 95, 127),
         (63, 111, 127),
         (0, 57, 76),
         (38, 66, 76),
         (0, 127, 255),
         (127, 191, 255),
         (0, 102, 204),
         (102, 153, 204),
         (0, 76, 152),
         (76, 114, 152),
         (0, 63, 127),
         (63, 95, 127),
         (0, 38, 76),
         (38, 57, 76),
         (0, 63, 255),
         (127, 159, 255),
         (0, 51, 204),
         (102, 127, 204),
         (0, 38, 152),
         (76, 95, 152),
         (0, 31, 127),
         (63, 79, 127),
         (0, 19, 76),
         (38, 47, 76),
         (0, 0, 255),
         (127, 127, 255),
         (0, 0, 204),
         (102, 102, 204),
         (0, 0, 152),
         (76, 76, 152),
         (0, 0, 127),
         (63, 63, 127),
         (0, 0, 76),
         (38, 38, 76),
         (63, 0, 255),
         (159, 127, 255),
         (51, 0, 204),
         (127, 102, 204),
         (38, 0, 152),
         (95, 76, 152),
         (31, 0, 127),
         (79, 63, 127),
         (19, 0, 76),
         (47, 38, 76),
         (127, 0, 255),
         (191, 127, 255),
         (102, 0, 204),
         (153, 102, 204),
         (76, 0, 152),
         (114, 76, 152),
         (63, 0, 127),
         (95, 63, 127),
         (38, 0, 76),
         (57, 38, 76),
         (191, 0, 255),
         (223, 127, 255),
         (153, 0, 204),
         (178, 102, 204),
         (114, 0, 152),
         (133, 76, 152),
         (95, 0, 127),
         (111, 63, 127),
         (57, 0, 76),
         (66, 38, 76),
         (255, 0, 255),
         (255, 127, 255),
         (204, 0, 204),
         (204, 102, 204),
         (152, 0, 152),
         (152, 76, 152),
         (127, 0, 127),
         (127, 63, 127),
         (76, 0, 76),
         (76, 38, 76),
         (255, 0, 191),
         (255, 127, 223),
         (204, 0, 153),
         (204, 102, 178),
         (152, 0, 114),
         (152, 76, 133),
         (127, 0, 95),
         (127, 63, 111),
         (76, 0, 57),
         (76, 38, 66),
         (255, 0, 127),
         (255, 127, 191),
         (204, 0, 102),
         (204, 102, 153),
         (152, 0, 76),
         (152, 76, 114),
         (127, 0, 63),
         (127, 63, 95),
         (76, 0, 38),
         (76, 38, 57),
         (255, 0, 63),
         (255, 127, 159),
         (204, 0, 51),
         (204, 102, 127),
         (152, 0, 38),
         (152, 76, 95),
         (127, 0, 31),
         (127, 63, 79),
         (76, 0, 19),
         (76, 38, 47),
         (51, 51, 51),
         (91, 91, 91),
         (132, 132, 132),
         (173, 173, 173),
         (214, 214, 214),
         (255, 255, 255))


class CamPoint(object):
    """
    Define a point in the cam where the law of motion changes
    angle           ->    point's angle
    displacement    ->    point height
    law             ->    law of motion
    """

    _LAW_LINEAR = 0
    _LAW_SINUSOIDAL = 1
    _LAW_PARABOLIC = 2
    _LAW_CUBIC = 3  # Not yet implemented
    _LAWS = (_LAW_LINEAR, _LAW_SINUSOIDAL, _LAW_PARABOLIC)

    def __init__(self, angle, displacement=0.0, law=_LAW_LINEAR):
        """
        Constructor
        """

        self.__angle = angle
        self.__displacement = displacement
        self.__law = law

    def __iadd__(self, other):
        """
        Implements addition with assignment
        """

        self.set_displacement(self.displacement() + other)

    def __lt__(self, other):
        """
        Returns True if self.__angle is less than other.__angle
        """

        return self.__angle < other.__angle

    def move(self, delta_angle, delta_displacement):
        """
        Moves the point of the given deltas
        """

        self.set_angle(self.angle() + delta_angle)
        self.set_displacement(self.displacement() + delta_displacement)
        return self

    def angle(self):
        """
        Returns the point angle
        """

        return self.__angle

    def displacement(self):
        """
        Returns the point displacement
        """

        return self.__displacement

    def law(self):
        """
        Returns the point law
        """

        return self.__law

    def law_description(self):
        """
        Returns the point law description as text
        """

        return ["Linear", "Sinusoidal", "Parabolic"][self.__law]

    def set_angle(self, angle):
        """
        Sets the point angle to the nearest angle
        """

        if 0 < angle <= 360:
            self.__angle = int(angle * angle_steps) / angle_steps
        else:
            raise ValueError("The angle must be greater than 0 and equal or less than 360")

    def set_displacement(self, displacement):
        """
        Sets the point displacement
        """

        if displacement >= 0:
            self.__displacement = displacement
        else:
            raise ValueError("The displacement must be equal or greater than 0")

    def set_law(self, law):
        """
        Sets the point law
        """
        if law in CamPoint._LAWS:
            self.__law = law
        else:
            raise ValueError("Law {0} not implemented".format(law))


class CamProfile(object):
    """
    Defines the scheme of a cam displacement diagram
    Keeps a list of cam points
    """

    def __init__(self, points=None, label=None, color=Qt.black):
        """
        Creates the points list
        """

        if points is not None:
            self.__points = points
        else:
            self.__points = []
            self.__points.append(CamPoint(360))
        if label is not None:
            self.__label = label
        self.__color = color
        self.__height = 35.5
        self.__depth = 16.5

    def __iter__(self):
        """
        Returns an iterator of cam points
        """

        return iter(self.__points)

    def __getitem__(self, key):
        """
        Returns the point in key position if it exists
        """

        return self.__points[key]

    def __len__(self):
        """
        Returns the number of points in the profile
        """

        return len(self.__points)

    def add_point(self, point):
        """
        Adds the point in angle order, if the angle already exists
        the new point replaces the existing point.
        Returns True if the angle already exists False otherwise
        """

        for i, p in enumerate(self.__points):
            if p.angle() == point.angle():
                self.__points[i] = point
                return True
        else:
            insort_left(self.__points, point)
            return False

    def check_cam(self):
        """
        Checks the cam for errors and corrects them
        """

        for point in self.__points:
            prev_point = self.get_prev_point(point)
            if prev_point is not None:
                if point.displacement() == prev_point.displacement():
                    point.set_law(CamPoint._LAW_LINEAR)
                if point.displacement() != prev_point.displacement() and point.law() == CamPoint._LAW_LINEAR:
                    point.set_law(CamPoint._LAW_SINUSOIDAL)
            else:
                if point.displacement() == self.__points[-1].displacement():
                    point.set_law(CamPoint._LAW_LINEAR)
                if point.displacement() != self.__points[-1].displacement() and point.law() == CamPoint._LAW_LINEAR:
                    point.set_law(CamPoint._LAW_SINUSOIDAL)

    def color(self):
        """
        Returns the cam color
        """

        return self.__color

    def del_point(self, point):
        """
        Removes the point from the cam
        """

        self.__points.remove(point)

    def depth(self):
        """
        Returns the cam profile depth
        """

        return self.__depth

    def displacements(self):
        """
        Returns a list of displacements
        """

        displacements = []

        for point in self.__points:
            displacements.append(point.displacement())
        return displacements

    def edit_point(self, new_point, old_point):
        """
        Replace the old point with the new one
        """

        old_point.set_angle(new_point.angle())
        old_point.set_displacement(new_point.displacement())
        old_point.set_law(new_point.law())

    def first_derivative(self, angle_steps=angle_steps):
        """
        Returns the first derivative of the list using the function
        """

        self.check_cam()
        first_derivative = []
        prev_point = CamPoint(0, self.__points[-1].displacement())
        for point in self.__points:
            if point.law() == CamPoint._LAW_LINEAR:
                for x in range(int(prev_point.angle() * angle_steps), int(point.angle() * angle_steps)):
                    first_derivative.append((x, 0))
                    if point.angle() == 360:
                        first_derivative.append((360, 0))
            elif point.law() == CamPoint._LAW_SINUSOIDAL:
                a, b, c, d = self.sine_params(point, prev_point)
                for x in range(int(prev_point.angle() * angle_steps), int(point.angle() * angle_steps)):
                    first_derivative.append(((x / angle_steps), c * cos((a * (x / angle_steps) + b) * (pi / 180)) * a))
                if point.angle() == 360:
                    first_derivative.append((360, c * cos((a * 360 + b) * (pi / 180)) * a))
            elif point.law() == CamPoint._LAW_PARABOLIC:
                a1, b1, c1, a2, b2, c2 = self.quadratic_params(point, prev_point)
                for x in range(int(prev_point.angle() * angle_steps),
                               int(angle_steps * (prev_point.angle() + point.angle()) / 2)):
                    first_derivative.append(((x / angle_steps), (2 * a1 * (x / angle_steps) + b1) / (pi / 180)))
                for x in range(int(angle_steps * (prev_point.angle() + point.angle()) / 2),
                               int(point.angle() * angle_steps)):
                    first_derivative.append(((x / angle_steps), (2 * a2 * (x / angle_steps) + b2) / (pi / 180)))
                if point.angle() == 360:
                    first_derivative.append((360, (2 * a2 * 360 + b2) / (pi / 180)))
            prev_point = point
        return first_derivative

    def get_next_point(self, point):
        """
        Returns the point following point, None if point is the last
        Raises keyError if the point is not in the profile
        """

        if point not in self:
            raise KeyError("This point is not in the profile")
        else:
            if point == self.__points[-1]:
                return None
            else:
                for i, p in enumerate(self):
                    if p == point:
                        break
                return self[i + 1]

    def get_prev_point(self, point):
        """
        Returns the point preceding point, None if point is the first
        Raises keyError if the point is not in the profile
        """

        if point not in self:
            raise KeyError("This point is not in the profile")
        else:
            for i, p in enumerate(self):
                if p == point:
                    break
            if i == 0:
                return None
            else:
                return self[i - 1]

    def height(self):
        """
        Returns the cam profile height
        """

        return self.__height

    def label(self):
        """
        Returns the cam label
        """

        return self.__label

    def max_displacement(self):
        """
        Returns the max displacement
        """

        return max(self.displacements())

    def min_displacement(self):
        """
        Returns the max displacement
        """

        return min(self.displacements())

    def mirror(self):
        """
        Mirrors the profile
        """

        if len(self.__points) > 1:
            old_points = self.__points[:]
            self.__points = []
            for i in range(len(old_points) - 2, -1, -1):
                self.__points.append(CamPoint(360 - old_points[i].angle(),
                                              old_points[i].displacement(),
                                              old_points[i + 1].law()))
            self.__points.append(CamPoint(360, old_points[-1].displacement(), old_points[0].law()))

    def move(self, translation):
        """
        Moves the profile
        """

        for point in self:
            point += translation

    def polyline(self, complete, angle_steps=angle_steps):
        """
        Returns the polyline points

        complete is a boolean parameter, if false the polyline includes only first and last of aligned points
        """

        self.check_cam()
        polyline = []
        prev_point = CamPoint(0, self.__points[-1].displacement())
        for point in self.__points:
            if point.law() == CamPoint._LAW_LINEAR:
                if not complete:
                    polyline.append((prev_point.angle() , prev_point.displacement()))
                else:
                    for x in range(int(prev_point.angle() * angle_steps), int(point.angle() * angle_steps)):
                        polyline.append((x / angle_steps, point.displacement()))
            elif point.law() == CamPoint._LAW_SINUSOIDAL:
                a, b, c, d = self.sine_params(point, prev_point)
                for x in range(int(prev_point.angle() * angle_steps), int(point.angle() * angle_steps)):
                    polyline.append((x / angle_steps, c * sin((a * (x / angle_steps) + b) * (pi / 180)) + d))
            elif point.law() == CamPoint._LAW_PARABOLIC:
                a1, b1, c1, a2, b2, c2 = self.quadratic_params(point, prev_point)
                for x in range(int(prev_point.angle() * angle_steps),
                               int(((prev_point.angle() + point.angle()) / 2) * angle_steps)):
                    polyline.append((x / angle_steps, a1 * pow(x / angle_steps, 2) + b1 * (x / angle_steps) + c1))
                for x in range(int(((prev_point.angle() + point.angle()) / 2) * angle_steps),
                               int(point.angle() * angle_steps)):
                    polyline.append((x / angle_steps, a2 * pow(x / angle_steps, 2) + b2 * (x / angle_steps) + c2))
            prev_point = point
        polyline.append((360.0, self.__points[-1].displacement()))
        return polyline

    def quadratic_params(self, point, prev_point):
        """
        Finds the parameters of the quadratic functions that have the
        max and min in point and prevPoint
        """

        mid_angle = (prev_point.angle() + point.angle()) / 2
        mid_displacement = (prev_point.displacement() + point.displacement()) / 2
        a = array([[prev_point.angle() ** 2, prev_point.angle(), 1, 0, 0, 0],
                   [2 * prev_point.angle(), 1, 0, 0, 0, 0],
                   [mid_angle ** 2, mid_angle, 1, 0, 0, 0],
                   [0, 0, 0, mid_angle ** 2, mid_angle, 1],
                   [0, 0, 0, point.angle() ** 2, point.angle(), 1],
                   [0, 0, 0, 2 * point.angle(), 1, 0]])
        b = array([[prev_point.displacement()], [0], [mid_displacement], [mid_displacement],
                   [point.displacement()], [0]])
        x = linalg.solve(a, b)
        return x[:, 0]

    def second_derivative(self, angle_steps=angle_steps):
        """
        Returns the second derivative of the list using the function
        """

        self.check_cam()
        second_derivative = []
        prev_point = CamPoint(0, self.__points[-1].displacement())
        for point in self.__points:
            if point.law() == CamPoint._LAW_LINEAR:
                for x in range(int(prev_point.angle() * angle_steps), int(point.angle() * angle_steps)):
                    second_derivative.append(((x / angle_steps), 0))
                    if point.angle() == 360:
                        second_derivative.append((360, 0))
            elif point.law() == CamPoint._LAW_SINUSOIDAL:
                a, b, c, d = self.sine_params(point, prev_point)
                for x in range(int(prev_point.angle() * angle_steps), int(point.angle() * angle_steps)):
                    second_derivative.append(((x / angle_steps),
                                              c * sin((a * (x / angle_steps) + b) * (pi / 180)) * (a ** 2)))
                if point.angle() == 360:
                    second_derivative.append((360, c * sin((a * 360 + b) * (pi / 180)) * (a ** 2)))
            elif point.law() == CamPoint._LAW_PARABOLIC:
                a1, b1, c1, a2, b2, c2 = self.quadratic_params(point, prev_point)
                for x in range(int(prev_point.angle() * angle_steps),
                               int(angle_steps * (prev_point.angle() + point.angle()) / 2)):
                    second_derivative.append(((x / angle_steps), (2 * a1) / (pi / 180) ** 2))
                for x in range(int(angle_steps * (prev_point.angle() + point.angle()) / 2),
                               int(point.angle() * angle_steps)):
                    second_derivative.append(((x / angle_steps), (2 * a2) / (pi / 180) ** 2))
                if point.angle() == 360:
                    second_derivative.append((360, (2 * a2) / (pi / 180) ** 2))
            prev_point = point
        return second_derivative

    def set_color(self, color):
        """
        Sets the cam color
        """

        self.__color = color

    def set_depth(self, depth):
        """Setter for self.__depth.
        """

        self.__depth = depth

    def set_height(self, height):
        """Setter for self.__depth.
        """

        self.__height = height

    def set_label(self, label):
        """
        Sets the cam label
        """

        self.__label = str(label)

    def sine_params(self, point, prev_point):
        """
        Finds the parameters of the sine function that has the
        max and min in point and prevPoint
        """

        a = array([[prev_point.angle(), 1, 0, 0],
                   [point.angle(), 1, 0, 0],
                   [0, 0, -1, 1],
                   [0, 0, 1, 1]])
        b = array([[-90], [90], [prev_point.displacement()], [point.displacement()]])
        x = linalg.solve(a, b)
        return x[:, 0]


class Cam(object):
    """
    Holds the cam list and the cam physical details
    """

    def __init__(self, speed=SPEED, radius=RADIUS, cams=None, displacement_steps=displacement_steps,
                 angle_steps=angle_steps):
        """
        Creates the cam
        """

        self.__file_name = None
        self.__speed = speed
        self.__radius = radius
        self.__angle_steps = angle_steps
        self.__displacement_steps = displacement_steps
        if cams is not None:
            self.__cams = cams
            self.__dirty = True
        else:
            self.__cams = []
            self.__dirty = False

    def __iter__(self):
        """
        Returns an iterator of cams
        """

        return iter(self.__cams)

    def __len__(self):
        """
        Returns the number of cams
        """

        return len(self.__cams)

    def __getitem__(self, key):
        """
        Returns the cam in key position if it exists
        """

        return self.__cams[key]

    def __setitem__(self, key, cam):
        """
        Sets the cam in key position if it exists
        """

        self.__cams[key] = cam
        self.__dirty = True

    def __delitem__(self, key):
        """
        Deletes the cam in key position if it exists
        """

        del self.__cams[key]
        self.__dirty = True

    def add_cam(self, cam=None):
        """
        Adds a new cam
        """

        if cam is None:
            cam = CamProfile()
        if cam.label() == "":
            cam.set_label("Cam {0}".format(len(self.__cams) + 1))
        self.__cams.append(cam)
        self.__dirty = True

    def angle_steps(self):
        """ Return the angle steps

        Return:
        int: steps in 1 degree
        """

        return self.__angle_steps

    def del_cam(self, cam):
        """
        Removes the specified cam
        """

        self.__cams.remove(cam)
        self.__dirty = True

    def displacement_steps(self):
        """ Return the displacement steps

        Return:
        int: steps in 1 mm
        """

        return self.__displacement_steps

    def dirty(self):
        """Return the dirty status.

        Return:
        bool: the dirty flag
        """

        return self.__dirty

    def file_name(self):
        """Return the file name.

        Return:
        str: the file name
        """

        return self.__file_name

    def load(self, file_name=""):
        """Load a file.

        Parameters:
        file_name (str): the full name of the file

        Return:
        bool: a boolean to represent if the load was successful
        str: a message
        """

        if file_name:
            self.__file_name = file_name

        with open(self.__file_name, 'rb') as fh:
            magic = pickle.load(fh)
            if magic != MAGIC_NUMBER:
                raise IOError("unrecognized file type")
            version = pickle.load(fh)
            if version != FILE_VERSION:
                raise IOError("unrecognized file version")

            self.__angle_steps = int(1 / pickle.load(fh))
            self.__displacement_steps = int(1 / pickle.load(fh))
            self.__speed = pickle.load(fh)
            self.__radius = pickle.load(fh)
            self.__cams = pickle.load(fh)

        self.__dirty = False
        return True, "Loaded {0} cam from {1}".format(len(self.__cams), os.path.basename(self.__file_name))

    def max_displacement(self):
        """
        returns the max displacement for all the cams
        """

        displacements = []

        for cam in self.__cams:
            displacements.append(cam.max_displacement())
        return max(displacements)

    def mirror(self):
        """
        Mirrors all the profiles
        """

        for cam_profile in self.__cams:
            cam_profile.mirror()

    def radius(self):
        """
        Returns the cam radius
        """

        return self.__radius

    def save(self):
        """
        Saves the Cam Data to file_name
        """

        with open(self.file_name(), 'wb') as fh:
            pickle.dump(MAGIC_NUMBER, fh)
            pickle.dump(FILE_VERSION, fh)
            pickle.dump(1 / self.angle_steps(), fh)
            pickle.dump(1 / self.displacement_steps(), fh)
            pickle.dump(self.__speed, fh)
            pickle.dump(self.__radius, fh)
            pickle.dump(self.__cams, fh)

        self.__dirty = False

    def save_2D_DXF(self, file_name):
        """
        Exports the Cam Data to file_name
        """

        polylines = []
        ezdxf.options.template_dir = 'templates'
        drawing = ezdxf.new('AC1015')
        model_space = drawing.modelspace()
        for i, cam_profile in enumerate(self.__cams):
            drawing.layers.add(name=cam_profile.label())
            layer = drawing.layers.get(cam_profile.label())
            layer.set_color(qColor_to_ACI(cam_profile.color()))
            polylines.append([])
            points = cam_profile.polyline(True)
            for point in points:
                polylines[i].append((-2 * pi * self.__radius * point[0] / 360, point[1]))
            model_space.add_lwpolyline(polylines[i])
            polyline = model_space.query('LWPOLYLINE')[i]
            polyline.dxf.layer = cam_profile.label()
        drawing.saveas(file_name)

    def save_3D_STP(self, file_name):
        """
        Exports the Cam Data to file_name
        """

        results = []
        for i, cam_profile in enumerate(self.__cams):
            polyline = []
            aux = []
            points = cam_profile.polyline(True)

            height = cam_profile.height()
            depth = cam_profile.depth()

            for j in range(0, len(points), 10):
                polyline.append((self.__radius * cos(points[j][0] * (pi / 180)),
                                self.__radius * sin(points[j][0] * (pi / 180)), -points[j][1]))
                aux.append((self.__radius * cos(points[j][0] * (pi / 180)),
                            self.__radius * sin(points[j][0] * (pi / 180)), -points[j][1] + height/2))

            section = Workplane("XZ").move(self.radius() - depth/2, -points[0][1]).rect(depth, height)
            path = Workplane("XY").spline(polyline)
            aux_spine = Workplane("XY").spline(aux)

            results.append(section.sweep(path, auxSpine=aux_spine))

        result = results[0]
        for i in range(1, len(results)):
            result = result.union(results[i])
        #exporters.export(result, file_name, exporters.ExportTypes.STEP)
        result.val().exportStep(file_name)

    def set_dirty(self, dirty):
        """Setter for self.__dirty.
        """

        self.__dirty = dirty

    def set_file_name(self, file_name):
        """Setter for self.__file_name.
        """

        self.__file_name = file_name
        self.__dirty = True

    def set_radius(self, radius):
        """
        Sets the cam radius
        """

        if radius > 0:
            self.__radius = radius
            self.__dirty = True
        else:
            raise ValueError("The radius must be greater than 0")

    def set_speed(self, speed):
        """
        Sets the cam rotation speed
        """

        if speed > 0:
            self.__speed = speed
            self.__dirty = True
        else:
            raise ValueError("The speed must be greater than 0")

    def speed(self):
        """
        Returns the cam rotation speed
        """

        return self.__speed


def qColor_to_ACI(color):
    """
    Returns the ACI index closest to the given color
    """

    min_distance = sys.maxsize
    chosen = 0
    qcolor = QColor(color)
    r, g, b, alpha = qcolor.getRgb()
    i = 0

    for red, green, blue in _ACI_:
        distance = ((red - r) ** 2 +
                    (green - g) ** 2 +
                    (blue - b) ** 2)
        if distance < min_distance:
            min_distance = distance
            chosen = i
        i += 1

        return chosen
