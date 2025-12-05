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

from PySide6.QtCore import QMarginsF, Qt
from PySide6.QtGui import QBrush, QPageLayout, QPainter, QPixmap
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import QCheckBox, QColorDialog, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, \
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QTabWidget, QWidget

from BarrelCam import camdata


class CamPointDlg(QDialog):
    """
    Dialogs for adding and editing CamPoints
    """

    def __init__(self, cam, point=None, parent=None):
        """
        Constructor for the dialogs
        """

        super(CamPointDlg, self).__init__(parent)

        self.parent = parent
        angle_steps = self.parent.cam.angle_steps()
        displacement_steps = self.parent.cam.displacement_steps()

        angle_label = QLabel("&Angle:")
        self.angle_spinbox = QDoubleSpinBox()
        self.angle_spinbox.setAlignment(Qt.AlignRight)
        self.angle_spinbox.setSuffix("°")
        self.angle_spinbox.setSingleStep(1 / angle_steps)
        angle_label.setBuddy(self.angle_spinbox)
        displacement_label = QLabel("&Displacement:")
        self.displacement_spinbox = QDoubleSpinBox()
        self.displacement_spinbox.setAlignment(Qt.AlignRight)
        self.displacement_spinbox.setRange(0.0, 1000.0)
        self.displacement_spinbox.setSingleStep(1 / displacement_steps)
        displacement_label.setBuddy(self.displacement_spinbox)
        law_label = QLabel("&Law of motion:")
        self.law_combobox = QComboBox()
        self.law_combobox.addItems(["Linear", "Sinusoidal", "Parabolic"])
        self.law_combobox.setCurrentIndex(camdata.CamPoint._LAW_SINUSOIDAL)
        law_label.setBuddy(self.law_combobox)

        buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        if point is None:
            self.setWindowTitle("Barrel Cam Editor - Add Point")
            self.angle_spinbox.setRange(10 / angle_steps, 360 - 10 / displacement_steps)
            self.angle_spinbox.setValue(180.0)
        else:
            self.setWindowTitle("Barrel Cam Editor - Edit Point")
            try:
                prev_angle = cam.get_prev_point(point).angle()
            except AttributeError:
                prev_angle = 0
            try:
                next_angle = cam.get_next_point(point).angle()
            except AttributeError:
                self.angle_spinbox.setEnabled(False)
                next_angle = 360 + 10 / angle_steps
            self.angle_spinbox.setRange(prev_angle + 10 / angle_steps, next_angle - 10 / angle_steps)
            self.angle_spinbox.setValue(point.angle())
            self.displacement_spinbox.setValue(point.displacement())
            self.law_combobox.setCurrentIndex(point.law())

        cam_setting_grid = QGridLayout()
        cam_setting_grid.addWidget(angle_label, 0, 0)
        cam_setting_grid.addWidget(self.angle_spinbox, 0, 1)
        cam_setting_grid.addWidget(displacement_label, 1, 0)
        cam_setting_grid.addWidget(self.displacement_spinbox, 1, 1)
        cam_setting_grid.addWidget(law_label, 2, 0)
        cam_setting_grid.addWidget(self.law_combobox, 2, 1)

        layout = QVBoxLayout()
        layout.addLayout(cam_setting_grid)
        layout.addSpacing(30)
        layout.addWidget(buttonbox)

        self.setLayout(layout)

        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

    def point(self):
        """
        Returns the point created or edited
        """

        return camdata.CamPoint(self.angle_spinbox.value(), self.displacement_spinbox.value(),
                                self.law_combobox.currentIndex())


class CamPointMoveDlg(QDialog):
    """
    Dialogs for moving a CamPoints
    """

    def __init__(self, cam_points, parent=None):
        """
        Constructor for the dialogs
        """

        super(CamPointMoveDlg, self).__init__(parent)

        #self.anglePitch, self.displacementPitch = cam_points[0][0].getPitch()
        angle_steps = parent.cam.angle_steps()
        displacement_steps = parent.cam.displacement_steps()
        min_displacement = min([cam_point[0].displacement() for cam_point in cam_points])

        lower_range = 360
        upper_range = 360

        for cam_point in cam_points:
            try:
                prev_angle = cam_point[1].get_prev_point(cam_point[0]).angle()
            except AttributeError:
                prev_angle = 0
            try:
                next_angle = cam_point[1].get_next_point(cam_point[0]).angle()
            except AttributeError:
                prev_angle = cam_point[0].angle()
                next_angle = cam_point[0].angle()
            lower_temp = cam_point[0].angle() - prev_angle
            if lower_range > lower_temp:
                lower_range = lower_temp
            upper_temp = next_angle - cam_point[0].angle()
            if upper_range > upper_temp:
                upper_range = upper_temp

        lower_range -= 10 / angle_steps
        upper_range -= 10 / angle_steps

        angle_label = QLabel("&Angle:")
        self.angle_spinbox = QDoubleSpinBox()
        self.angle_spinbox.setAlignment(Qt.AlignRight)

        if lower_range <= 0 and upper_range <= 0:
            self.angle_spinbox.setEnabled(False)
        else:
            self.angle_spinbox.setRange(-lower_range, upper_range)
        self.angle_spinbox.setSuffix("°")
        self.angle_spinbox.setSingleStep(1 / angle_steps)
        angle_label.setBuddy(self.angle_spinbox)
        displacement_label = QLabel("&Displacement:")
        self.displacement_spinbox = QDoubleSpinBox()
        self.displacement_spinbox.setAlignment(Qt.AlignRight)
        self.displacement_spinbox.setRange(-min_displacement, 1000.0)
        self.displacement_spinbox.setSingleStep(1 / displacement_steps)
        displacement_label.setBuddy(self.displacement_spinbox)
        buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        self.setWindowTitle("Barrel Cam Editor - Move Points")

        cam_setting_grid = QGridLayout()
        cam_setting_grid.addWidget(angle_label, 0, 0, )
        cam_setting_grid.addWidget(self.angle_spinbox, 0, 1, 1, 2)
        cam_setting_grid.addWidget(displacement_label, 1, 0, )
        cam_setting_grid.addWidget(self.displacement_spinbox, 1, 1, 1, 2)

        layout = QVBoxLayout()
        layout.addLayout(cam_setting_grid)
        layout.addSpacing(30)
        layout.addWidget(buttonbox)

        self.setLayout(layout)

        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

    def move(self):
        """
        Returns the translation value
        """

        return self.angle_spinbox.value(), self.displacement_spinbox.value()


class CamProfileDlg(QDialog):
    """
    Dialogs for adding a CamProfile
    """

    def __init__(self, parent=None):
        """
        Constructor for the dialogs
        """

        super(CamProfileDlg, self).__init__(parent)

        self.color = Qt.black

        label_label = QLabel("&Label")
        self.labelLineEdit = QLineEdit()
        label_label.setBuddy(self.labelLineEdit)
        displacement_label = QLabel("&Displacement:")
        self.displacement_spinbox = QDoubleSpinBox()
        self.displacement_spinbox.setAlignment(Qt.AlignRight)
        self.displacement_spinbox.setRange(0.0, 1000.0)
        self.displacement_spinbox.setSingleStep(1.0 / parent.cam.displacement_steps())
        self.displacement_spinbox.setSuffix(" mm")
        displacement_label.setBuddy(self.displacement_spinbox)
        law_label = QLabel("&Law of motion:")
        self.law_combobox = QComboBox()
        self.law_combobox.addItems(["Linear", "Sinusoidal", "Parabolic"])
        self.law_combobox.setCurrentIndex(camdata.CamPoint._LAW_SINUSOIDAL)
        law_label.setBuddy(self.law_combobox)
        color_label = QLabel("Color:")
        self.color_label = QLabel()
        self.color_label.setPixmap(self.new_pixmap(100, 25))
        color_button = QPushButton("&Color...")

        buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        self.setWindowTitle("Barrel Cam Editor - Add Cam Profile")

        cam_setting_grid = QGridLayout()
        cam_setting_grid.addWidget(label_label, 0, 0)
        cam_setting_grid.addWidget(self.labelLineEdit, 0, 1, 1, 2)
        cam_setting_grid.addWidget(displacement_label, 1, 0)
        cam_setting_grid.addWidget(self.displacement_spinbox, 1, 1, 1, 2)
        cam_setting_grid.addWidget(law_label, 2, 0)
        cam_setting_grid.addWidget(self.law_combobox, 2, 1, 1, 2)
        cam_setting_grid.addWidget(color_label, 3, 0)
        cam_setting_grid.addWidget(self.color_label, 3, 1)
        cam_setting_grid.addWidget(color_button, 3, 2)

        layout = QVBoxLayout()
        layout.addLayout(cam_setting_grid)
        layout.addSpacing(30)
        layout.addWidget(buttonbox)

        self.setLayout(layout)

        color_button.clicked.connect(self.update_color)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

    def cam_profile(self):
        """
        Returns the cam profile created
        """

        return camdata.CamProfile([camdata.CamPoint(360, self.displacement_spinbox.value(),
                                  self.law_combobox.currentIndex())], self.labelLineEdit.text(), self.color)

    def new_pixmap(self, width, height):
        """
        Creates a new pixmap with the self.color
        """

        pixmap = QPixmap(width, height)
        painter = QPainter(pixmap)
        brush = QBrush(self.color, Qt.SolidPattern)
        painter.fillRect(pixmap.rect(), brush)
        return pixmap

    def update_color(self):
        """
        Updates the color of the pixmap
        """

        color = QColorDialog.getColor(self.color, self)
        if color.isValid():
            self.color = color
            self.color_label.setPixmap(self.new_pixmap(100, 25))


class CamProfileEditDlg(QDialog):
    """
    Dialogs for editing a CamProfile
    """

    def __init__(self, cam_profile, parent=None):
        """
        Constructor for the dialogs
        """

        super(CamProfileEditDlg, self).__init__(parent)

        self.cam_profile = copy.deepcopy(cam_profile)
        self.color = self.cam_profile.color()

        label_label = QLabel("&Label")
        self.label_lineedit = QLineEdit()
        self.label_lineedit.setText(self.cam_profile.label())
        label_label.setBuddy(self.label_lineedit)
        color_label = QLabel("Color:")
        self.color_label = QLabel()
        self.color_label.setPixmap(self.new_pixmap(100, 25))
        color_button = QPushButton("&Color...")

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        self.setWindowTitle("Barrel Cam Editor - Edit Cam Profile")

        cam_setting_grid = QGridLayout()
        cam_setting_grid.addWidget(label_label, 0, 0, )
        cam_setting_grid.addWidget(self.label_lineedit, 0, 1, 1, 2)
        cam_setting_grid.addWidget(color_label, 1, 0)
        cam_setting_grid.addWidget(self.color_label, 1, 1)
        cam_setting_grid.addWidget(color_button, 1, 2)

        layout = QVBoxLayout()
        layout.addLayout(cam_setting_grid)
        layout.addSpacing(30)
        layout.addWidget(button_box)

        self.setLayout(layout)

        color_button.clicked.connect(self.update_color)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def new_pixmap(self, width, height):
        """
        Creates a new pixmap with the self.color
        """

        pixmap = QPixmap(width, height)
        painter = QPainter(pixmap)
        brush = QBrush(self.color, Qt.SolidPattern)
        painter.fillRect(pixmap.rect(), brush)
        return pixmap

    def update_color(self):
        """
        Updates the color of the pixmap
        """

        color = QColorDialog.getColor(self.color, self)
        if color.isValid():
            self.color = color
            self.color_label.setPixmap(self.new_pixmap(100, 25))

    def update_cam_profile(self):
        """
        Updates the cam profile
        """

        changed = False
        label = self.label_lineedit.text()
        if label != self.cam_profile.label():
            self.cam_profile.set_label(label)
            changed = True
        if self.color != self.cam_profile.color():
            self.cam_profile.set_color(self.color)
            changed = True
        if not changed:
            return False
        return True

    def edited_cam_profile(self):
        """
        Returns the edited cam profile
        """

        return self.cam_profile


class CamProfileMoveDlg(QDialog):
    """
    Dialogs for moving a CamProfile
    """

    def __init__(self, cam_profiles, parent=None):
        """
        Constructor for the dialogs
        """

        super(CamProfileMoveDlg, self).__init__(parent)

        min_displacement = min([cam_profile.min_displacement() for cam_profile in cam_profiles])

        translation_label = QLabel("&Translation:")
        self.translation_spinbox = QDoubleSpinBox()
        self.translation_spinbox.setAlignment(Qt.AlignRight)
        self.translation_spinbox.setRange(-min_displacement, 1000.0)
        self.translation_spinbox.setSuffix(" mm")
        self.translation_spinbox.setSingleStep(1)
        translation_label.setBuddy(self.translation_spinbox)
        buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        self.setWindowTitle("Barrel Cam Editor - Move Cam Profile")

        cam_setting_grid = QGridLayout()
        cam_setting_grid.addWidget(translation_label, 0, 0, )
        cam_setting_grid.addWidget(self.translation_spinbox, 0, 1, 1, 2)

        layout = QVBoxLayout()
        layout.addLayout(cam_setting_grid)
        layout.addSpacing(30)
        layout.addWidget(buttonbox)

        self.setLayout(layout)

        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

    def move(self):
        """
        Returns the translation value
        """

        return self.translation_spinbox.value()


class CamSettings(QDialog):
    """
    Dialogs for editing settings
    """

    def __init__(self, cam, parent=None):
        """
        Constructor for the dialogs
        """

        super(CamSettings, self).__init__(parent)

        self.cam = cam
        if parent is not None:
            self.main_window = parent
        self.x_steps = self.main_window.scene.get_x_steps() - 1
        self.y_limit = self.main_window.scene.get_y_limit()
        self.y_steps = self.main_window.scene.get_y_steps() - 1
        self.colors = []
        self.heights = []
        self.depths = []
        tab_widget = QTabWidget()
        cam_setting_widget = QWidget()
        limits_setting_widget = QWidget()
        stp_setting_widget = QWidget()
        grid_setting_widget = QWidget()

        speed_label = QLabel("&Speed:")
        self.speed_spinbox = QDoubleSpinBox()
        self.speed_spinbox.setAlignment(Qt.AlignRight)
        self.speed_spinbox.setSuffix(" rpm")
        self.speed_spinbox.setRange(0.1, 50.0)
        self.speed_spinbox.setSingleStep(1)
        self.speed_spinbox.setValue(self.cam.speed())
        speed_label.setBuddy(self.speed_spinbox)
        radius_label = QLabel("&Radius:")
        self.radius_spinbox = QDoubleSpinBox()
        self.radius_spinbox.setAlignment(Qt.AlignRight)
        self.radius_spinbox.setSuffix(" mm")
        self.radius_spinbox.setRange(10, 1000.0)
        self.radius_spinbox.setSingleStep(1)
        self.radius_spinbox.setValue(self.cam.radius())
        radius_label.setBuddy(self.radius_spinbox)

        self.acc_checkbox = QCheckBox()
        self.acc_checkbox.setChecked(self.main_window.max_acceleration is not None)
        self.acc_limit_label = QLabel("&Acceleration limit:")
        self.acc_limit_spinbox = QDoubleSpinBox()
        self.acc_limit_spinbox.setAlignment(Qt.AlignRight)
        self.acc_limit_spinbox.setSuffix(" m/s\u00B2")
        self.acc_limit_spinbox.setRange(0, 50.0)
        self.acc_limit_spinbox.setSingleStep(0.1)
        self.acc_limit_label.setBuddy(self.acc_limit_spinbox)
        if self.main_window.max_acceleration is not None:
            self.acc_limit_spinbox.setValue(self.main_window.max_acceleration)
        self.min_distance_checkbox = QCheckBox()
        self.min_distance_checkbox.setChecked(self.main_window.min_distance is not None)
        self.min_distance_label = QLabel("&Minimum distance limit:")
        self.min_distance_spinbox = QDoubleSpinBox()
        self.min_distance_spinbox.setAlignment(Qt.AlignRight)
        self.min_distance_spinbox.setSuffix(" mm")
        self.min_distance_spinbox.setRange(0, 500.0)
        self.min_distance_spinbox.setSingleStep(0.5)
        self.min_distance_label.setBuddy(self.min_distance_spinbox)
        if self.main_window.min_distance is not None:
            self.min_distance_spinbox.setValue(self.main_window.min_distance)
        self.max_distance_checkbox = QCheckBox()
        self.max_distance_checkbox.setChecked(self.main_window.max_distance is not None)
        self.max_distance_label = QLabel("Ma&ximum distance limit:")
        self.max_distance_spinbox = QDoubleSpinBox()
        self.max_distance_spinbox.setAlignment(Qt.AlignRight)
        self.max_distance_spinbox.setSuffix(" mm")
        self.max_distance_spinbox.setRange(0, 500.0)
        self.max_distance_spinbox.setSingleStep(0.5)
        self.max_distance_label.setBuddy(self.max_distance_spinbox)
        if self.main_window.max_distance is not None:
            self.max_distance_spinbox.setValue(self.main_window.max_distance)

        pitch_label = QLabel("&Pitch:")
        self.pitch_spinbox = QSpinBox()
        self.pitch_spinbox.setAlignment(Qt.AlignRight)
        self.pitch_spinbox.setSuffix("°")
        self.pitch_spinbox.setRange(1, 6)
        self.pitch_spinbox.setSingleStep(1)
        self.pitch_spinbox.setValue(self.main_window.STP_angle_pitch)
        pitch_label.setBuddy(self.pitch_spinbox)

        x_steps_label = QLabel("&X Tick Steps:")
        self.x_steps_spinbox = QSpinBox()
        self.x_steps_spinbox.setAlignment(Qt.AlignRight)
        self.x_steps_spinbox.setRange(2, 99)
        self.x_steps_spinbox.setValue(self.x_steps)
        x_steps_label.setBuddy(self.x_steps_spinbox)
        y_limit_label = QLabel("Y &Limits:")
        self.y_limit_spinbox = QDoubleSpinBox()
        self.y_limit_spinbox.setAlignment(Qt.AlignRight)
        self.y_limit_spinbox.setSuffix(" mm")
        self.y_limit_spinbox.setRange(10, 1000.0)
        self.y_limit_spinbox.setSingleStep(1)
        self.y_limit_spinbox.setValue(self.y_limit)
        y_limit_label.setBuddy(self.y_limit_spinbox)
        y_steps_label = QLabel("&Y Tick Steps:")
        self.y_steps_spinbox = QSpinBox()
        self.y_steps_spinbox.setAlignment(Qt.AlignRight)
        self.y_steps_spinbox.setRange(2, 99)
        self.y_steps_spinbox.setValue(self.y_steps)
        y_steps_label.setBuddy(self.y_steps_spinbox)

        buttonbox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        self.setWindowTitle("Barrel Cam Editor - Edit Properties")

        cam_setting_grid = QGridLayout()
        cam_setting_grid.addWidget(speed_label, 0, 0)
        cam_setting_grid.addWidget(self.speed_spinbox, 0, 1)
        cam_setting_grid.addWidget(radius_label, 0, 2)
        cam_setting_grid.addWidget(self.radius_spinbox, 0, 3)

        if len(self.cam) > 0:
            cam_label = QLabel("&Cam:")
            self.cam_combobox = QComboBox()
            cam_label.setBuddy(self.cam_combobox)

            for camProfile in self.cam:
                self.cam_combobox.addItem(camProfile.label())
                self.colors.append(camProfile.color())
                self.heights.append(camProfile.height())
                self.depths.append(camProfile.depth())

            self.color_label = QLabel()
            self.color_label.setPixmap(self.new_pixmap(80, 25))

            height_label = QLabel("&Height:")
            self.height_spinbox = QDoubleSpinBox()
            self.height_spinbox.setAlignment(Qt.AlignRight)
            self.height_spinbox.setSuffix(" mm")
            self.height_spinbox.setRange(10, 100.0)
            self.height_spinbox.setSingleStep(0.5)
            self.height_spinbox.setValue(self.heights[self.cam_combobox.currentIndex()])
            height_label.setBuddy(self.height_spinbox)

            depth_label = QLabel("&Depth:")
            self.depth_spinbox = QDoubleSpinBox()
            self.depth_spinbox.setAlignment(Qt.AlignRight)
            self.depth_spinbox.setSuffix(" mm")
            self.depth_spinbox.setRange(10, 100.0)
            self.depth_spinbox.setSingleStep(0.5)
            self.depth_spinbox.setValue(self.depths[self.cam_combobox.currentIndex()])
            depth_label.setBuddy(self.depth_spinbox)

            color_button = QPushButton("&Color...")

            cam_setting_grid.addWidget(cam_label, 1, 0)
            cam_setting_grid.addWidget(self.cam_combobox, 1, 1)
            cam_setting_grid.addWidget(self.color_label, 1, 2)
            cam_setting_grid.addWidget(color_button, 1, 3)
            cam_setting_grid.addWidget(height_label, 2, 0)
            cam_setting_grid.addWidget(self.height_spinbox, 2, 1)
            cam_setting_grid.addWidget(depth_label, 2, 2)
            cam_setting_grid.addWidget(self.depth_spinbox, 2, 3)

            self.cam_combobox.currentIndexChanged.connect(self.update)
            color_button.clicked.connect(self.update_color)
            self.height_spinbox.valueChanged.connect(self.update_height)
            self.depth_spinbox.valueChanged.connect(self.update_depth)

        limits_setting_grid = QGridLayout()
        limits_setting_grid.addWidget(self.acc_checkbox, 0, 0)
        limits_setting_grid.addWidget(self.acc_limit_label, 0, 1)
        limits_setting_grid.addWidget(self.acc_limit_spinbox, 0, 2)
        limits_setting_grid.addWidget(self.min_distance_checkbox, 1, 0)
        limits_setting_grid.addWidget(self.min_distance_label, 1, 1)
        limits_setting_grid.addWidget(self.min_distance_spinbox, 1, 2)
        limits_setting_grid.addWidget(self.max_distance_checkbox, 2, 0)
        limits_setting_grid.addWidget(self.max_distance_label, 2, 1)
        limits_setting_grid.addWidget(self.max_distance_spinbox, 2, 2)

        stp_setting_grid = QGridLayout()
        stp_setting_grid.addWidget(pitch_label, 0, 0)
        stp_setting_grid.addWidget(self.pitch_spinbox, 0, 1)

        grid_setting_grid = QGridLayout()
        grid_setting_grid.addWidget(x_steps_label, 0, 0)
        grid_setting_grid.addWidget(self.x_steps_spinbox, 0, 1)
        grid_setting_grid.addWidget(y_limit_label, 1, 0)
        grid_setting_grid.addWidget(self.y_limit_spinbox, 1, 1)
        grid_setting_grid.addWidget(y_steps_label, 2, 0)
        grid_setting_grid.addWidget(self.y_steps_spinbox, 2, 1)

        cam_setting_widget.setLayout(cam_setting_grid)
        limits_setting_widget.setLayout(limits_setting_grid)
        stp_setting_widget.setLayout(stp_setting_grid)
        grid_setting_widget.setLayout(grid_setting_grid)

        tab_widget.addTab(cam_setting_widget, "&Cam")
        tab_widget.addTab(limits_setting_widget, "&Limits")
        tab_widget.addTab(stp_setting_widget, "&STP Settings")
        tab_widget.addTab(grid_setting_widget, "&Grid")

        layout = QVBoxLayout()
        layout.addWidget(tab_widget)
        layout.addSpacing(30)
        layout.addWidget(buttonbox)

        self.setLayout(layout)

        self.acc_checkbox.stateChanged.connect(self.update_limits)
        self.min_distance_checkbox.stateChanged.connect(self.update_limits)
        self.max_distance_checkbox.stateChanged.connect(self.update_limits)
        self.update_limits()

        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

    def new_pixmap(self, width, height):
        """
        Creates a new pixmap with the self.color
        """

        pixmap = QPixmap(width, height)
        painter = QPainter(pixmap)
        brush = QBrush(self.colors[self.cam_combobox.currentIndex()], Qt.SolidPattern)
        painter.fillRect(pixmap.rect(), brush)
        return pixmap

    def update(self):
        """
        Updates the dialog
        """

        self.color_label.setPixmap(self.new_pixmap(80, 25))
        self.height_spinbox.setValue(self.heights[self.cam_combobox.currentIndex()])
        self.depth_spinbox.setValue(self.depths[self.cam_combobox.currentIndex()])

    def update_color(self):
        """
        Updates the color of the pixmap
        """

        color = QColorDialog.getColor(self.colors[self.cam_combobox.currentIndex()], self)
        if color.isValid():
            self.colors[self.cam_combobox.currentIndex()] = color
            self.color_label.setPixmap(self.new_pixmap(80, 25))

    def update_depth(self):
        """
        Updates the depths values
        """

        self.depths[self.cam_combobox.currentIndex()] = self.depth_spinbox.value()

    def update_height(self):
        """
        Updates the heights values
        """

        self.heights[self.cam_combobox.currentIndex()] = self.height_spinbox.value()

    def update_limits(self):
        """
        Updates the limits dialog
        """

        self.acc_limit_label.setEnabled(self.acc_checkbox.isChecked())
        self.acc_limit_spinbox.setDisabled(not self.acc_checkbox.isChecked())
        self.min_distance_label.setEnabled(self.min_distance_checkbox.isChecked())
        self.min_distance_spinbox.setDisabled(not self.min_distance_checkbox.isChecked())
        self.max_distance_label.setEnabled(self.max_distance_checkbox.isChecked())
        self.max_distance_spinbox.setDisabled(not self.max_distance_checkbox.isChecked())

    #def update_label(self):
    #    """
    #    Updates the label color
    #    """
    #
    #    self.color_label.setPixmap(self.new_pixmap(80, 25))

    def cam_settings(self):
        """
        Returns the cam settings
        """

        cam = copy.deepcopy(self.cam)
        cam.set_speed(self.speed_spinbox.value())
        cam.set_radius(self.radius_spinbox.value())
        if len(self.cam) > 0:
            for i, cam_profile in enumerate(cam):
                cam_profile.set_color(self.colors[i])
                cam_profile.set_depth(self.depths[i])
                cam_profile.set_height(self.heights[i])

        return cam

    def grid_settings(self):
        """
        Returns a list of scene settings
        """

        return self.x_steps_spinbox.value() + 1, self.y_limit_spinbox.value(), self.y_steps_spinbox.value() + 1


class GraphsDlg(QDialog):
    """
    Dialogs that shows the profiles' graphs
    """

    def __init__(self, widget, toolbar=None, parent=None):
        """
        Constructor for the dialogs
        """

        super(GraphsDlg, self).__init__(parent)

        self.printer = QPrinter(QPrinter.HighResolution)
        self.printer.setPageOrientation(QPageLayout.Landscape)
        self.printer.setPageMargins(QMarginsF(10, 10, 10, 10), QPageLayout.Point)

        self.setWindowTitle("Barrel Cam Editor - Graphs")
        self.setWindowFlags(self.windowFlags() |
                            Qt.WindowSystemMenuHint |
                            Qt.WindowMinMaxButtonsHint)

        print_button = QPushButton("Print...")
        close_button = QPushButton("Close")

        layout = QVBoxLayout()
        if toolbar is not None:
            layout.addWidget(toolbar)
        self.widget = widget
        layout.addWidget(self.widget)

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(print_button)
        buttons_layout.addWidget(close_button)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

        print_button.clicked.connect(self.printGraphs)
        close_button.clicked.connect(self.close)

    def printGraphs(self):
        """
        Prints the graphs
        """

        dialog = QPrintDialog(self.printer)
        if dialog.exec_():
            painter = QPainter(self.printer)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)
            pixmap = QPixmap.grabWidget(self.widget)
            painter.drawPixmap(self.printer.pageRect(), pixmap)
