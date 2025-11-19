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

from numpy import arctan, linspace, pi
from PySide6.QtCore import QPoint, QRect, QRectF, Qt, Signal, QPointF
from PySide6.QtGui import QBrush, QFont, QFontMetrics, QPainter, QPen, QPainterPath
from PySide6.QtWidgets import QGraphicsItem, QGraphicsView, QGraphicsScene, QSizePolicy, QTableWidget, QTableWidgetItem

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from BarrelCam import camcmd, camdlg

OFFSET = 1


class CamPointItem(QGraphicsItem):
    """
    Draws on screen the points of a cam
    """

    def __init__(self, cam_point, cam_profile_item, scene):
        """
        CamPointItem Constructor
        """

        super(CamPointItem, self).__init__()

        self.cam_point = cam_point
        self.parent = cam_profile_item
        self.width = 30
        scene.clearSelection()
        self.rect = QRect(-self.width, -self.width, 2 * self.width, 2 * self.width)
        self.position = QPoint(self.cam_point.angle() * self.parent.angle_steps,
                               self.cam_point.displacement() * self.parent.displacement_steps)
        self.setPos(self.position)
        self.setFlags(
            QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptedMouseButtons(Qt.LeftButton)

        scene.addItem(self)

    def boundingRect(self):
        """
        Defines the item borders
        """

        return self.rect

    def itemChange(self, change, value):

        if change == QGraphicsItem.ItemPositionChange:

            min_angle = 1 * self.parent.angle_steps
            max_angle = (360 - 1) * self.parent.angle_steps
            angle = self.cam_point.angle()

            prev_point = self.parent.get_profile().get_prev_point(self.cam_point)
            if prev_point is not None:
                min_angle = (prev_point.angle() + 1) * self.parent.angle_steps
            next_point = self.parent.get_profile().get_next_point(self.cam_point)
            if next_point is not None:
                max_angle = (next_point.angle() - 1) * self.parent.angle_steps
            if angle == 360:
                value.setX(360 * self.parent.angle_steps)
            else:
                if value.x() < min_angle:
                    value.setX(min_angle)
                if value.x() > max_angle:
                    value.setX(max_angle)

            if value.y() < 0:
                value.setY(0)

            self.scene().parent.undo_stack.push(camcmd.PointMoveCommand(self.scene(), self, value, False,
                                                                        "Cam Point Moved"))

        return QGraphicsItem.itemChange(self, change, value)

    def mouseDoubleClickEvent(self, event):
        dlg = camdlg.CamPointDlg(self.parent.get_profile(), self.cam_point, parent=self.scene().parent)
        if dlg.exec():
            self.scene().parent.undo_stack.push(camcmd.PointEditCommand(self.scene().parent, self.parent.get_profile(),
                                                self.cam_point, dlg.point(), "Cam Point Edited"))

    def paint(self, painter, option, widget):

        pen = QPen()
        pen.setColor(Qt.black)
        pen_width = 1 / option.levelOfDetailFromTransform(painter.worldTransform())

        if self.isSelected():
            brush = QBrush()
            brush.setStyle(Qt.SolidPattern)
            brush.setColor(Qt.yellow)
            pen.setColor(Qt.red)
            painter.setBrush(brush)
        pen.setWidth(pen_width)
        painter.setPen(pen)
        painter.drawEllipse(self.rect.adjusted(10, 10, -10, -10))
        painter.drawLine(-self.width, 0, self.width, 0)
        painter.drawLine(0, -self.width, 0, self.width)

    def point(self):
        """
        Returns the cam_point
        """

        return self.cam_point


class CamProfileItem(QGraphicsItem):
    """
    Draws on screen the scheme of a cam displacement diagram
    """

    def __init__(self, cam_profile, scene):
        """
        Creates the profile lines
        """

        super(CamProfileItem, self).__init__()

        self.cam_profile = cam_profile
        self.scene = scene
        self.scene.clearSelection()
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.scene.addItem(self)
        self.setZValue(-1)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.angle_steps = self.scene.parent.cam.angle_steps()
        self.displacement_steps = self.scene.parent.cam.displacement_steps()
        self.color = cam_profile.color()

    def boundingRect(self):
        """
        Defines the item borders
        """

        return QRectF(0, (self.cam_profile.min_displacement() - 8) * self.displacement_steps,
                      360 * self.angle_steps,
                      (self.cam_profile.max_displacement() - self.cam_profile.min_displacement() + 12)
                      * self.displacement_steps)

    def get_profile(self):
        """
        Returns the cam profile
        """

        return self.cam_profile

    def mouseDoubleClickEvent(self, event):
        """
        Edits the cam_profile with a double click
        """

        dlg = camdlg.CamProfileEditDlg(self.get_profile(), parent=self.scene.parent)
        if dlg.exec():
            if dlg.update_cam_profile():
                self.scene.parent.undo_stack.push(camcmd.CamEditCommand(self.scene.parent, self.get_profile(),
                                                  dlg.edited_cam_profile(), "Cam Profile Edited"))

    def paint(self, painter, option, widget):
        """
        Draws on screen the scheme of a cam displacement diagram
        """

        pen = QPen()
        pen_width = 1.5 / option.levelOfDetailFromTransform(painter.worldTransform())
        if self.isSelected():
            pen.setColor(Qt.red)
        else:
            pen.setColor(self.cam_profile.color())
        pen.setWidth(pen_width)
        painter.setPen(pen)

        polyline = self.cam_profile.polyline(False, self.angle_steps)
        i = 0

        while i < len(polyline) - 1:
            painter.drawLine(polyline[i][0] * self.angle_steps, polyline[i][1] * self.displacement_steps,
                             polyline[i + 1][0] * self.angle_steps, polyline[i + 1][1] * self.displacement_steps)
            i += 1

        label_font = QFont()
        label_font.setPointSizeF(5 * self.angle_steps)
        label_font.setBold(True)
        painter.setFont(label_font)
        if self.cam_profile[-1].displacement() > self.cam_profile[0].displacement():
            y_position = self.displacement_steps * (self.cam_profile[-1].displacement() + 6)
        else:
            y_position = self.displacement_steps * (self.cam_profile[-1].displacement() - 2)

        painter.drawText(OFFSET, y_position, self.cam_profile.label())

    def shape(self):
        """
        Define the shape of the CamProfileItem

        :return: QPainterPath representing the shape
        """

        shape_increase = 3
        path = QPainterPath()
        polyline = self.cam_profile.polyline(False, self.angle_steps)

        if self.cam_profile[-1].displacement() > self.cam_profile[0].displacement():
            y_position = self.displacement_steps * (self.cam_profile[-1].displacement() + 6)
        else:
            y_position = self.displacement_steps * (self.cam_profile[-1].displacement() - 2)

        label_font = QFont()
        label_font.setPointSizeF(5 * self.angle_steps)
        label_font.setBold(True)
        font_metrics = QFontMetrics(label_font)

        path.addRect(OFFSET,
                     y_position - font_metrics.boundingRect(self.cam_profile.label()).height(),
                     font_metrics.boundingRect(self.cam_profile.label()).width(),
                     font_metrics.boundingRect(self.cam_profile.label()).height())

        i = 0
        while i < len(polyline) - 1:
            path.addRect(polyline[i][0] * self.angle_steps,                                                       #x
                         (polyline[i][1] - shape_increase) * self.displacement_steps,                             #y
                         (polyline[i + 1][0] - polyline[i][0]) * self.angle_steps,                                #w
                         (polyline[i + 1][1] - polyline[i][1] + 2 * shape_increase) * self.displacement_steps)    #h
            i += 1

        return path


class CamScene(QGraphicsScene):
    """
    Creates the main_window for the graphics representation of the cam
    """

    camChanged = Signal()
    pointChanged = Signal()

    def __init__(self, parent=None):
        """
        Constructor for the main_window
        """

        super(CamScene, self).__init__(parent)

        self.parent = parent
        self.__x_steps = 9
        self.__y_limit = 100
        self.__y_steps = 9

        self.angle_steps = self.parent.cam.angle_steps()
        self.displacement_steps = self.parent.cam.displacement_steps()

        self.update_scene()

    def add_grid(self):
        """
        Adds a grid to the Scene
        """

        tick_font = QFont()
        tick_font.setPointSizeF(1.5 * self.angle_steps)
        font_metrics = QFontMetrics(tick_font)
        tick_pen = QPen(Qt.DotLine)
        self.addRect(0, -OFFSET, 360 * self.angle_steps, OFFSET + (self.__y_limit * self.displacement_steps), tick_pen)

        for x in linspace(0, 360, self.__x_steps, endpoint=True):
            text = self.addText("{0:.0f}°".format(x), tick_font)
            if x < 360:
                text.setPos(x * self.angle_steps, - OFFSET - font_metrics.boundingRect("360°").height())
            else:
                text.setPos((x * self.angle_steps) - font_metrics.boundingRect("360°").width(),
                            - OFFSET - font_metrics.boundingRect("360°").height())
            if 0 < x < 360:
                self.addLine(x * self.angle_steps, -2, x * self.angle_steps, self.__y_limit * self.displacement_steps,
                             tick_pen)
        for y in linspace(0, self.__y_limit, self.__y_steps, endpoint=True):
            text = self.addText("{0:.0f} mm".format(y), tick_font)
            text.setRotation(270)
            if y == 0:
                text.setPos(-font_metrics.boundingRect("0 mm").height(), font_metrics.boundingRect("0 mm").width())
            else:
                text.setPos(-font_metrics.boundingRect("200 mm").height(), (y * self.displacement_steps))
            if 0 < y < self.__y_limit:
                self.addLine(0, y * self.displacement_steps, 360 * self.angle_steps, y * self.displacement_steps,
                             tick_pen)

    def modified(self):
        """
        Sets the cam modified and update the main_window
        """

        cam = self.parent.cam
        max_displacement = cam.max_displacement()
        self.setSceneRect(0, 0, 360 * self.angle_steps, (max_displacement + OFFSET) * self.displacement_steps)
        cam.set_dirty(True)
        self.pointChanged.emit()

    def get_x_steps(self):
        """
        Returns the number X steps for the main_window
        """

        return self.__x_steps

    def get_y_limit(self):
        """
        Returns the Y limit for the main_window
        """

        return self.__y_limit

    def get_y_steps(self):
        """
        Returns the number Y steps for the main_window
        """

        return self.__y_steps

    def set_x_steps(self, x_steps):
        """
        Sets the X tick step for the main_window
        """

        self.__x_steps = x_steps
        self.update_scene()

    def set_y_limit(self, y_limit):
        """
        Sets the Y limit for the main_window
        """

        self.__y_limit = y_limit
        self.update_scene()

    def set_y_steps(self, y_steps):
        """
        Sets the Y tick step for the main_window
        """

        self.__y_steps = y_steps
        self.update_scene()

    def update_scene(self):
        """
        Populates the main_window with profiles and points
        """

        self.clear()

        self.add_grid()

        if len(self.parent.cam) > 0:
            self.setSceneRect(0, 0, 360 * self.angle_steps, (self.parent.cam.max_displacement() + OFFSET)
                              * self.displacement_steps)

            for cam_profile in self.parent.cam:
                cam_profile_item = CamProfileItem(cam_profile, self)

                for point in cam_profile:
                    CamPointItem(point, cam_profile_item, self)


class CamView(QGraphicsView):
    """
    Creates the view for the graphics representation of the cam
    """

    viewResized = Signal(int)

    def __init__(self, parent=None):
        """
        Constructor for the view
        """

        super(CamView, self).__init__(parent)

        self.parent = parent
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.last_wheel_event_time = 0

    def mouseDoubleClickEvent(self, event):
        """
        Zoom all on left button double click
        """

        if event.button() == Qt.MiddleButton:
            self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
            self.viewResized.emit(self.sceneRect())

        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        """
        Ignore right mouse clicks
        """

        if event.buttons() == Qt.LeftButton:
            return QGraphicsView.mousePressEvent(self, event)

    def wheelEvent(self, event):
        """
        Zooms the view with mouse wheel
        """

        factor = pow(1.41, (-event.angleDelta().y() / 240.0))
        self.scale(factor, factor)
        self.viewResized.emit(factor)


class GraphsWidget(FigureCanvas):
    """
    Class to represent the FigureCanvas widget
    """

    def __init__(self, cam):
        """
        Constructor for the graphs
        """

        self.cam = cam
        self.speed = self.cam.speed() * 6 * pi / 180  # rad/s
        self.radius = self.cam.radius()
        self.figure = Figure()
        self.figure.patch.set_facecolor('white')

        FigureCanvas.__init__(self, self.figure)

        self.updateGraphs()

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def updateGraphs(self):
        """
        Plots the graphs
        """

        self.figure.clf()
        profiles_plot = self.figure.add_subplot(221)
        first_derivative_plot = self.figure.add_subplot(223)
        second_derivative_plot = self.figure.add_subplot(224)
        if len(self.cam) > 1:
            distances_plot = self.figure.add_subplot(222)
            plots = [profiles_plot, distances_plot, first_derivative_plot, second_derivative_plot]
        else:
            plots = [profiles_plot, first_derivative_plot, second_derivative_plot]

        for cam_profile in self.cam:
            polyline = cam_profile.polyline(True)
            x = [xi[0] for xi in polyline]
            y = [-xi[1] for xi in polyline]
            profiles_plot.plot(x, y, label=cam_profile.label(), color=cam_profile.color().getRgbF())
            profiles_plot.set_ylabel('Displacement $[mm]$')
            first_derivative = cam_profile.first_derivative()
            x = [xi[0] for xi in first_derivative]
            y = [(180 / pi) * arctan((xi[1]) / self.radius) for xi in first_derivative]
            first_derivative_plot.plot(x, y, label=cam_profile.label(), color=cam_profile.color().getRgbF())
            first_derivative_plot.set_ylabel('Slope [°]')
            second_derivative = cam_profile.second_derivative()
            x = [xi[0] for xi in second_derivative]
            y = [(self.speed ** 2) * xi[1] / 1000 for xi in second_derivative]
            second_derivative_plot.plot(x, y, label=cam_profile.label(), color=cam_profile.color().getRgbF())
            second_derivative_plot.set_ylabel('Acceleration $[m/s^2]$')
        if len(self.cam) > 1:
            for i, cam_profile in enumerate(self.cam):
                polyline = cam_profile.polyline(True)
                x = [xi[0] for xi in polyline]
                if i > 0:
                    differences = [y[1] - y0[j] for j, y in enumerate(polyline)]
                    y_min = min(differences)
                    x_min = x[differences.index(y_min)]
                    y_max = max(differences)
                    x_max = x[differences.index(y_max)]
                    distances_plot.plot(x, differences, label=cam_profile.label(), color=cam_profile.color().getRgbF())

                    x_max_disp = -50
                    if x_max < 180:
                        x_max_disp = +50

                    x_min_disp = -50
                    if x_min < 180:
                        x_min_disp = +50

                    distances_plot.annotate('Max = {0:0.2f}'.format(y_max),
                                           xy=(x_max, y_max), xytext=(x_max + x_max_disp, y_max + 3),
                                           arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"))
                    distances_plot.annotate('Min = {0:0.2f}'.format(y_min),
                                           xy=(x_min, y_min), xytext=(x_min + x_min_disp, y_min - 4),
                                           arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"))
                    distances_plot.scatter([x_max, x_min], [y_max, y_min])
                else:
                    y0 = [xi[1] for xi in polyline]
                distances_plot.set_ylabel('Distances $[mm]$')

        for plot in plots:
            plot.set_xlim([0.0, 360.0])
            plot.set_xticks(linspace(0, 360, 7, endpoint=True))
            plot.grid(True)
            plot.set_xlabel('Angle [°]')
            # plot.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3, ncol=2, mode="expand", borderaxespad=0.)
            # plot.legend(loc='upper left')


class TableCamWidget(QTableWidget):
    """
    Creates  a table representing the cam
    """

    def __init__(self, profile, parent=None):
        """
        Constructor for the table
        """

        super(TableCamWidget, self).__init__(parent)

        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setAlternatingRowColors(True)
        self.profile = profile
        self.update()

    def update(self):
        """
        Create a table and populate it.
        """

        self.clearSelection()
        self.setRowCount(len(self.profile))
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Angle", "Displacement", "Law"])
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        for row, cam_point in enumerate(self.profile):
            angle = QTableWidgetItem(str(cam_point.angle()))
            displacement = QTableWidgetItem(str(cam_point.displacement()))
            law = QTableWidgetItem(cam_point.law_description())
            self.setItem(row, 0, angle)
            self.setItem(row, 1, displacement)
            self.setItem(row, 2, law)
        self.resizeColumnsToContents()
