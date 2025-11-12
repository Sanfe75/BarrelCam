# BarrelCam Editor
#
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

import os
import platform
import PySide6
import sys

from PySide6.QtCore import QEvent, QFile, QFileInfo, QMargins, QSettings, Qt
from PySide6.QtGui import QAction, QIcon, QKeySequence, QPageLayout, QPainter, QUndoStack
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import QApplication, QDockWidget, QFileDialog, QInputDialog, QMainWindow, QMessageBox, QSpinBox,\
    QTabWidget

from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

sys.path.insert(0, '.')

import qrcresources

from BarrelCam import camcmd, camdata, camdlg, camwidget

__author__ = 'simone.sanfelici'
__version__ = "0.9.1"


class BarrelCamEditor(QMainWindow):
    """
    GUI for editing barrel Cams
    """

    copied_items = []
    instances = []
    next_id = 1
    recent_files = []

    def __init__(self, file_name=None, parent=None):
        """
        Main Window Constructor
        """

        super(BarrelCamEditor, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        BarrelCamEditor.instances.append(self)

        self.undo_stack = QUndoStack()
        self.undo_stack.canUndoChanged.connect(self.update_ui)
        self.undo_stack.canRedoChanged.connect(self.update_ui)
        self.cam = camdata.Cam()
        self.selected_points = []
        self.selected_cams = []

        if file_name is None:
            self.cam.set_file_name("Unnamed-{0}".format(BarrelCamEditor.next_id))
            BarrelCamEditor.next_id += 1
            self.cam.set_dirty(False)
        else:
            _, message = self.cam.load(file_name)
            self.statusBar().showMessage(message, 5000)

        self.view = camwidget.CamView(self)
        self.view.viewResized.connect(self.update_zoom)
        self.scene = camwidget.CamScene(self)
        self.scene.selectionChanged.connect(self.update_ui)
        self.scene.pointChanged.connect(self.update_widgets)
        self.view.setScene(self.scene)
        self.setCentralWidget(self.view)
        self.view.setContextMenuPolicy(Qt.ActionsContextMenu)

        self.printer = QPrinter(QPrinter.HighResolution)
        self.printer.setPageOrientation(QPageLayout.Landscape)
        self.printer.setPageMargins(QMargins(10, 10, 10, 10), QPageLayout.Point)

        self.graphs_widget = None

        #table_dock_widget = QDockWidget("Table View", self)
        #table_dock_widget.setObjectName("TableDockWidget")
        #table_dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        #self.table_widget = camwidget.TableCamWidget(self.cam)
        #table_dock_widget.setWidget(self.table_widget)
        #self.addDockWidget(Qt.LeftDockWidgetArea, table_dock_widget)

        tab_dock_widget = QDockWidget("Tab View", self)
        tab_dock_widget.setObjectName("TabDockWidget")
        tab_dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        #self.tab_widget = camwidget.TabCamWidget(self.cam)
        self.tab_widget = QTabWidget()
        tab_dock_widget.setWidget(self.tab_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, tab_dock_widget)

        status = self.statusBar()
        status.setSizeGripEnabled(False)

        # Actions Creation
        file_new_action = self.create_action("&New...", self.file_new, QKeySequence.New, "file_new",
                                             "Create a new Cam file")
        file_open_action = self.create_action("&Open...", self.file_open, QKeySequence.Open,
                                              "file_open", "Open a Resource collection file")
        file_close_action = self.create_action("&Close", self.close, QKeySequence.Close,
                                               "file_close", "Close this editor")
        file_save_action = self.create_action("&Save", self.file_save, QKeySequence.Save,
                                              "file_save", "Save the Resource collection file")
        file_save_as_action = self.create_action("&Save as...", self.file_save_as, QKeySequence.SaveAs,
                                                 "file_save_as", "Save the Resource collection using a new name")
        file_save_all_action = self.create_action("Save A&ll", self.file_save_all, icon="file_save_all",
                                                  tip="Save all the Resource collections")
        file_export_2DDXF_action = self.create_action("Export &2D DXF...", self.file_export_2D, icon="file_export_2d",
                                                      tip="Export 2D DXF")
        #file_export_3DDXF_action = self.create_action("Export &3D DXF...", self.file_export_3D, icon="file_export_3d",
        #                                              tip="Export 3D DXF")
        #file_export_2DCSV_action = self.create_action("Export &2D CSV...", self.file_export_2DCSV,
        #                                              icon="file_export_2d", tip="Export 2D CSV")
        file_export_3DSTP_action = self.create_action("Export &3D STP...", self.file_export_3DSTP,
                                                      icon="file_export_3d", tip="Export 3D STP")
        file_print_action = self.create_action("&Print", self.file_print, QKeySequence.Print, "file_print",
                                               "Print the cam scheme")
        file_quit_action = self.create_action("&Quit", self.file_quit, "Ctrl+Q",
                                              "file_quit", "Close the application")
        self.edit_undo_action = self.create_action("Undo", self.undo_stack.undo, QKeySequence.Undo, "edit_undo",
                                                   "Undo last command")
        self.edit_redo_action = self.create_action("Redo", self.undo_stack.redo, QKeySequence.Redo, "edit_redo",
                                                   "Redo last undone command")
        self.edit_cut_action = self.create_action("Cut", self.edit_cut, QKeySequence.Cut, "edit_cut",
                                                  "Cut selected profiles")
        self.edit_copy_action = self.create_action("&Copy", self.edit_copy, QKeySequence.Copy, "edit_copy",
                                                   "Copy selected profiles")
        self.edit_paste_action = self.create_action("Paste", self.edit_paste, QKeySequence.Paste, "edit_paste",
                                                    "Paste copied profiles")
        self.edit_mirror_action = self.create_action("&Mirror the Cam", self.edit_mirror, "Ctrl+M", "edit_mirror",
                                                     "Mirror all the profiles")
        edit_cam_add_action = self.create_action("&Add Cam profile", self.edit_cam_add, "Ctrl+A", "edit_cam_add",
                                                 "Add a cam profile")
        self.edit_cam_edit_action = self.create_action("E&dit Cam profile", self.edit_cam_edit, "Ctrl+D",
                                                       "edit_cam_edit",
                                                       "Edit a cam profile")
        self.edit_cam_move_action = self.create_action("Mov&e Cam Profile", self.edit_cam_move, "Ctrl+E",
                                                       "edit_cam_move",
                                                       "Move a cam profile")
        self.edit_point_add_action = self.create_action("Add P&oint", self.edit_point_add, "Ctrl+O", "edit_point_add",
                                                        "Add a point to the selected cam")
        self.edit_point_edit_action = self.create_action("Ed&it Point", self.edit_point_edit, "Ctrl+I",
                                                         "edit_point_edit",
                                                         "Edit the selected cam point")
        self.edit_delete_action = self.create_action("Delete", self.edit_delete, "Delete", "edit_delete",
                                                     "Delete the selected items")
        view_zoom_all_action = self.create_action("Zoom &All", self.view_zoom_all, "Ctrl+A", "view_zoom_all",
                                                  "Zoom to fit")
        view_zoom_action = self.create_action("&Zoom...", self.view_zoom, "Ctrl+Z", "view_zoom",
                                              "Zoom the view")
        self.view_graphs_action = self.create_action("&Graphs", self.view_graphs, "Ctrl+G", "view_graphs",
                                                     "Show the graphs for the cam profiles")
        view_settings_action = self.create_action("&Settings", self.settings, "Ctrl+S", "view_settings",
                                                  "Edit settings")
        self.window_arrange_horizontal_action = self.create_action("Tile &Horizontally", self.window_arrange_horizontal,
                                                                   "Alt+H", "window_arrange_horizontal",
                                                                   "Arrange the windows horizontally")
        self.window_arrange_vertical_action = self.create_action("Tile &Vertically", self.window_arrange_vertical,
                                                                 "Alt+V", "window_arrange_vertical",
                                                                 "Arrange the windows vertically")
        help_about_action = self.create_action("About Barrel Cam Editor", self.help_about, icon="help_about")

        # Menus Creation
        self.file_menu = self.menuBar().addMenu("&File")
        export_menu = self.file_menu.addMenu(QIcon(":/file_export.png"), "&Export")
        #self.add_actions(export_menu, (file_export_2DDXF_action, file_export_3DDXF_action, file_export_2DCSV_action,
        #                               file_export_3DCSV_action))
        self.add_actions(export_menu, (file_export_2DDXF_action, file_export_3DSTP_action))
        self.file_menu_actions = (file_new_action, file_open_action, file_close_action, None, file_save_action,
                                  file_save_as_action, file_save_all_action, None, export_menu, None, file_print_action,
                                  file_quit_action)
        self.file_menu.aboutToShow.connect(self.update_file_menu)

        edit_menu = self.menuBar().addMenu("&Edit")
        self.add_actions(edit_menu, (self.edit_undo_action, self.edit_redo_action, None, self.edit_cut_action,
                                     self.edit_copy_action, self.edit_paste_action, None, edit_cam_add_action,
                                     self.edit_cam_edit_action, self.edit_cam_move_action, self.edit_mirror_action,
                                     None, self.edit_point_add_action, self.edit_point_edit_action, None,
                                     self.edit_delete_action))

        view_menu = self.menuBar().addMenu("&View")
        self.add_actions(view_menu,
                         (view_zoom_all_action, view_zoom_action, None, self.view_graphs_action, view_settings_action))

        self.window_menu = self.menuBar().addMenu("&Window")
        self.window_menu.aboutToShow.connect(self.update_window_menu)

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(help_about_action)

        self.zoom_spinbox = QSpinBox()
        self.zoom_spinbox.setRange(1, 1000)
        self.zoom_spinbox.setSuffix(" %")
        self.zoom_spinbox.setValue(100)
        self.zoom_spinbox.setSingleStep(10)
        self.zoom_spinbox.setToolTip("Zoom the view")
        self.zoom_spinbox.setStatusTip(self.zoom_spinbox.toolTip())
        self.zoom_spinbox.setKeyboardTracking(False)
        self.zoom_spinbox.valueChanged.connect(self.resize_view)

        # ToolBars Creation
        file_toolbar = self.addToolBar("File")
        file_toolbar.setObjectName("FileToolBar")
        self.add_actions(file_toolbar, (file_new_action, file_open_action, file_save_action))

        edit_toolbar = self.addToolBar("Edit")
        edit_toolbar.setObjectName("EditToolBar")
        self.add_actions(edit_toolbar, (self.edit_undo_action, self.edit_redo_action, None, edit_cam_add_action,
                                        self.edit_cam_edit_action, self.edit_cam_move_action, self.edit_mirror_action,
                                        None, self.edit_point_add_action, self.edit_point_edit_action, None,
                                        self.edit_delete_action))

        view_toolbar = self.addToolBar("View")
        view_toolbar.setObjectName("ViewToolBar")
        self.add_actions(view_toolbar,
                         (self.view_graphs_action, view_settings_action, None, view_zoom_all_action, None))
        view_toolbar.addWidget(self.zoom_spinbox)

        # Contest Menu Creation
        self.add_actions(self.view,
                         (self.edit_cut_action, self.edit_copy_action, self.edit_paste_action, edit_cam_add_action,
                          self.edit_cam_edit_action, self.edit_cam_move_action, self.edit_mirror_action,
                          self.edit_point_add_action, self.edit_point_edit_action, self.edit_delete_action))

        self.update_status("Ready")
        self.load_settings()
        self.update_ui()
        self.update_widgets()
        self.update_file_menu()
        self.update_window_menu()

    @staticmethod
    def add_actions(target, actions):
        """Add the given actions to the target.

        Add the given actions to the target, the actions are a list or tuple, if an element is None
        the function add a separator to the target.

        Parameters:
        target (object): the target of the add_actions
        actions (list): the list of actions to add
        """

        for action in actions:
            if action is None:
                target.addSeparator()
            elif isinstance(action, QAction):
                target.addAction(action)
            else:
                target.addMenu(action)

    @staticmethod
    def add_recent_file(file_name):
        """
        Updates the recent file list
        """

        if file_name is None:
            return
        if file_name in BarrelCamEditor.recent_files:
            BarrelCamEditor.recent_files.remove(file_name)
        BarrelCamEditor.recent_files[0:0] = [file_name]
        while len(BarrelCamEditor.recent_files) > 9:
            BarrelCamEditor.recent_files.pop()

#    def changeEvent(self, event):
#        """
#        Updates the UI when the window raise
#        """
#        print(int(QEvent.ActivationChange))
#        if event.type() == 99:
#            self.update_ui()

    @staticmethod
    def check_opened(file_name):
        """
        Checks if file_name is already opened (taking it from the
        action for recent files list. If it is opened show
        the existing window, otherwise opens a new one
        """

        for window in BarrelCamEditor.instances:
            if window.cam.file_name() == file_name:
                window.activateWindow()
                window.raise_()
                return True

        BarrelCamEditor.add_recent_file(file_name)
        return False

    def closeEvent(self, event):
        """
        Closes the window, saves application state and recent Files
        """

        if self.ok_to_continue():
            self.scene.clear()
            settings = QSettings()
            if BarrelCamEditor.recent_files:
                settings.setValue("RecentFiles", BarrelCamEditor.recent_files)
            settings.setValue("Geometry", self.saveGeometry())
            settings.setValue("MainWindow/State", self.saveState())
            settings.setValue("Scene/x_steps", self.scene.get_x_steps())
            settings.setValue("Scene/y_limit", self.scene.get_y_limit())
            settings.setValue("Scene/y_steps", self.scene.get_y_steps())
            BarrelCamEditor.instances.remove(self)
        else:
            event.ignore()

    def create_action(self, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False, signal="triggered"):
        """Create the actions for the interface.

        Parameters:
        text (str): the name of the action
        slot (func): the slot for the action
        shortcut (str): the shortcut
        icon (str): the icon file name without ext
        tip (str): the tooltip for the action
        checkable (bool): if checkable
        signal (str): the signal type

        Return:
        QAction: the action created
        """

        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/{0}.png".format(icon)))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            if signal == "triggered":
                action.triggered.connect(slot)
            if signal == "toggled":
                action.toggled[bool].connect(slot)
        if checkable:
            action.setCheckable(checkable)
        return action

    def edit_cam_add(self):
        """
        Adds a cam
        """

        dlg = camdlg.CamProfileDlg(self)
        if dlg.exec():
            self.undo_stack.push(camcmd.CamAddCommand(self, dlg.cam_profile(), "Cam Profile Added"))

    def edit_cam_edit(self):
        """
        Edits the selected cam
        """

        cam_profile = self.selected_cams[0].get_profile()
        dlg = camdlg.CamProfileEditDlg(cam_profile, parent=self)
        if dlg.exec():
            if dlg.update_cam_profile():
                self.undo_stack.push(camcmd.CamEditCommand(self, cam_profile, dlg.edited_cam_profile(),
                                                           "Cam Profile Edited"))

    def edit_cam_move(self):
        """
        Translates the selected cams
        """

        cam_profiles = [selected_cam.get_profile() for selected_cam in self.selected_cams]
        dlg = camdlg.CamProfileMoveDlg(cam_profiles, parent=self)
        if dlg.exec():
            translation = dlg.move()
            if translation != 0:
                self.undo_stack.push(camcmd.CamMoveCommand(self, cam_profiles, translation, "Cam Profile Moved"))

    def edit_copy(self):
        """
        Copies the selected profiles
        """

        BarrelCamEditor.copied_items = []
        for camProfileItem in self.selected_cams:
            BarrelCamEditor.copied_items.append(camProfileItem.get_profile())

        self.update_ui()

    def edit_cut(self):
        """
        Cuts the selected profiles
        """

        BarrelCamEditor.copied_items = []
        self.edit_copy()
        self.selected_points = []
        self.edit_delete("Cut")

    def edit_delete(self, action_text):
        """
        Deletes the selected points
        """

        if not action_text:
            action_text = "Delete"
        item_text = "item" if (len(self.selected_points) + len(self.selected_cams)) == 1 else "items"

        reply = QMessageBox.question(self, "Barrel Cam Editor - {0}".format(action_text),
                                     "{0} the selected {1}?".format(action_text, item_text),
                                     QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        if reply == QMessageBox.Cancel:
            return False
        elif reply == QMessageBox.Yes:

            point_list = []
            profile_list = []
            for point_item in self.selected_points:
                cam_profile = point_item.parent.get_profile()
                point = point_item.point()
                if point.angle() != 360:
                    point_list.append((point, cam_profile))
            for cam_item in self.selected_cams:
                cam_profile = cam_item.get_profile()
                profile_list.append(cam_profile)
            self.undo_stack.push(camcmd.EditDeleteCommand(self, profile_list, point_list,
                                                          "{0} deleted".format(item_text.title())))

    def edit_mirror(self):
        """
        Mirrors all the cam profiles
        """

        reply = QMessageBox.question(self, "Barrel Cam Editor - Mirror", "Do you want to mirror all the profiles?",
                                     QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        if reply == QMessageBox.Yes:
            self.undo_stack.push(camcmd.CamMirrorCommand(self, "Cam Mirrored"))

    def edit_paste(self):
        """
        Pastes the copied profiles
        """

        for cam_profile in BarrelCamEditor.copied_items:
            self.undo_stack.push(camcmd.CamAddCommand(self, cam_profile, "Cam Profile Pasted"))

    def edit_point_add(self):
        """
        Adds a point to the selected cam
        """

        cam_profile = self.selected_cams[0].get_profile()
        dlg = camdlg.CamPointDlg(cam_profile, parent=self)
        if dlg.exec():
            self.undo_stack.push(camcmd.PointAddCommand(self, cam_profile, dlg.point(), "Cam Point Added"))

    def edit_point_edit(self):
        """
        Edits the selected point
        """

        if len(self.selected_points) == 1:
            cam_point = self.selected_points[0].point()
            cam_profile = self.selected_points[0].parent.get_profile()
            dlg = camdlg.CamPointDlg(cam_profile, cam_point, parent=self)
            if dlg.exec():
                self.undo_stack.push(camcmd.PointEditCommand(self, cam_profile, cam_point, dlg.point(),
                                                             "Cam Point Edited"))
        elif len(self.selected_points) > 1:
            point_list = []
            for point_item in self.selected_points:
                cam_profile = point_item.parent.get_profile()
                point = point_item.point()
                point_list.append((point, cam_profile))
            dlg = camdlg.CamPointMoveDlg(point_list, parent=self)
            if dlg.exec():
                delta_angle, delta_displacement = dlg.move()
                if delta_angle != 0 or delta_displacement != 0:
                    self.undo_stack.push(
                        camcmd.PointsMoveCommand(self, point_list, delta_angle, delta_displacement, "Cam Points Moved"))

    def edit_point_table(self):
        """
        Edits the point corresponding to the selected row
        """

        table = self.tab_widget.currentWidget()
        table_index = self.tab_widget.currentIndex()
        cam_profile = self.cam[table_index]
        indexes = [selected.row() for selected in table.selectionModel().selectedRows()]
        cam_point = cam_profile[indexes[0]]
        dlg = camdlg.CamPointDlg(cam_profile, cam_point, parent=self)
        if dlg.exec():
            self.undo_stack.push(camcmd.PointEditCommand(self, cam_profile, cam_point, dlg.point(),
                                                         "Cam Point Edited"))

    def file_export_2D(self):
        """
        Exports a 2d DXF
        """

        if len(self.cam) == 0:
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setWindowTitle("Error")
            error_dialog.setText("Impossible to export the file.")
            error_dialog.setInformativeText("You need at least 1 profile to save to DXF file.")
            error_dialog.setStandardButtons(QMessageBox.Ok)
            error_dialog.exec()
            return

        directory = self.cam.file_name()[:-4] + ".dxf"
        file_name = QFileDialog.getSaveFileName(self, "Barrel Cam Editor - Export the cam file",
                                                directory, "DXF file (*.dxf)")[0]
        if file_name:
            extension = file_name[-4:].lower()
            if extension != ".dxf":
                file_name += ".dxf"
            self.cam.save_2D_DXF(file_name)

    #def file_export_3D(self):
    #    """
    #    Exports a 3d DXF
    #    """

        #pass
        # directory = self.file_name[:-4] + ".dxf"
        # file_name = QFileDialog.getSaveFileName(self, "Barrel Cam Editor - Export the cam file",
        #                                       directory, "DXF file (*.dxf)")
        # if file_name:
        #    extension = file_name[-4:].lower()
        #    if extension != ".dxf":
        #        file_name += ".dxf"
        #    self.cam.save3DDXF(file_name)

    def file_export_3DSTP(self):
        """
        Exports a 2d CSV
        """

        if len(self.cam) == 0:
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setWindowTitle("Error")
            error_dialog.setText("Impossible to export the file.")
            error_dialog.setInformativeText("You need at least 1 profile to save to STP file.")
            error_dialog.setStandardButtons(QMessageBox.Ok)
            error_dialog.exec()
            return

        directory = self.cam.file_name()[:-4] + ".stp"
        file_name = QFileDialog.getSaveFileName(self, "Barrel Cam Editor - Export the cam file", directory,
                                                "STP file (*.stp)")[0]
        if file_name:
            extension = file_name[-4:].lower()
            if extension != ".stp":
                file_name += ".stp"
            self.cam.save_3D_STP(file_name)

    #def file_export_3DCSV(self):
    #    """
    #    Exports a 3d CSV
    #    """

    #    pass
        # directory = self.file_name[:-4] + ".csv"
        # file_name = QFileDialog.getSaveFileName(self, "Barrel Cam Editor - Export the cam file",
        #                                       directory, "CSV file (*.csv)")
        # if file_name:
        #    extension = file_name[-4:].lower()
        #    if extension != ".csv":
        #        file_name += ".csv"
        #    self.cam.save3DCSV(file_name)

    @staticmethod
    def file_new():
        """Create a new file.
        """

        BarrelCamEditor().show()

    def file_open(self):
        """Create the dialog to select and then open a cam file.
        """

        path = QFileInfo(self.cam.file_name()).path() if not self.cam.file_name().startswith("Unnamed") else "."
        file_name, ext = QFileDialog.getOpenFileName(self, "Barrel Cam Editor - Load Barrel Cam",
                                                     path, "Barrel Cam file (*.cam)")
        if file_name:
            self.load_file(file_name)

    def file_print(self):
        """
        Prints the cam profiles
        """

        dialog = QPrintDialog(self.printer)
        if dialog.exec():
            painter = QPainter(self.printer)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)
            self.scene.clearSelection()
            self.scene.render(painter)

    @staticmethod
    def file_quit():
        """Close all the files and exit the application.
        """

        QApplication.closeAllWindows()

    def file_save(self):
        """Save a file.
        """

        if self.cam.file_name().startswith("Unnamed"):
            self.file_save_as()
        else:
            self.cam.save()
            self.update_status("Cam saved as {0}".format(QFileInfo(self.cam.file_name()).fileName()))
            return True

    def file_save_all(self):
        """Save all the files.
        """

        pass

    def file_save_as(self):
        """Create the dialog to save a new file.
        """

        file_name, ext = QFileDialog.getSaveFileName(self, "Barrel Cam Editor - Save the cam file",
                                                     self.cam.file_name(), "Cam file (*.cam)")
        if file_name:
            extension = file_name[-4:].lower()
            if extension != ".cam":
                file_name += ".cam"
            self.cam.set_file_name(file_name)
            self.file_save()

    def help_about(self):
        """Open the about message.
        """

        message = """<b>Barrel Cam Editor</b> v {0}
                     <p>Copyright &copy; Sanfe Ltd.
                     All rights reserved.
                     <p>This application can be used to create and
                     compile a resource collection file that can
                     be used in in python pyside6 projects.
                     <p> Python {1} - Qt {2} - PySide6 {3}
                      on {4}.<p> Icons by <a href='https://icons8.com'>Icons8</a>
                     """.format(__version__, platform.python_version(), PySide6.QtCore.__version__, PySide6.__version__,
                                platform.system())

        QMessageBox.about(self, "About Barrel Cam Editor", message)

    def load_file(self, file_name=None):
        """
        If the file is not already opened it opens a new MainWindow with file_name
        """

        if not file_name:
            action = self.sender()
            if isinstance(action, QAction):
                file_name = action.data()

        if not self.check_opened(file_name):
            if not self.cam.dirty() and self.cam.file_name().startswith("Unnamed"):
                self.cam.set_file_name(file_name)
                self.cam.load()
                self.update_status("Cam loaded from {0}".format(QFileInfo(self.cam.file_name()).fileName()))
                self.scene.update_scene()
                self.update_widgets()
                self.update_ui()
            else:
                BarrelCamEditor(file_name).show()

    def load_settings(self):
        """
        Loads the program settings
        """

        settings = QSettings()
        if settings.value("RecentFiles") is not None and BarrelCamEditor.recent_files == []:
            BarrelCamEditor.recent_files = settings.value("RecentFiles")
        if settings.value("Geometry") is not None:
            self.restoreGeometry(settings.value("Geometry"))
        if settings.value("MainWindow/State") is not None:
            self.restoreState(settings.value("MainWindow/State"))
        if settings.value("Scene/y_limit") is not None:
            y_limit = int(settings.value("Scene/y_limit"))
        else:
            y_limit = 200
        if settings.value("Scene/x_steps") is not None:
            x_steps = int(settings.value("Scene/x_steps"))
        else:
            x_steps = 2
        if settings.value("Scene/y_steps") is not None:
            y_steps = int(settings.value("Scene/y_steps"))
        else:
            y_steps = 2
        if settings.value("Options/ortho") is not None:
            ortho = bool(settings.value("Options/ortho"))
        else:
            ortho = False

        self.scene.set_x_steps(x_steps)
        self.scene.set_y_limit(y_limit)
        self.scene.set_y_steps(y_steps)
        # self.scene.setOrtho(ortho)

    def ok_to_continue(self):
        """Create Dialog to continue.

        Return:
        bool: it is OK to continue
        """

        if self.cam.dirty():
            reply = QMessageBox.question(self, "BarrelCam Editor - Unsaved Changes", "Save unsaved changes?",
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return False
            elif reply == QMessageBox.Yes:
                result = self.file_save()
                return result
        return True

    def raise_window(self):
        """Raise and make active editor_to_rise
        """

        title = self.sender().text().split(maxsplit=1)[1]
        for editor in BarrelCamEditor.instances:
            if editor.windowTitle()[:-3] == title:
                editor.activateWindow()
                editor.raise_()
                break

    def resize_view(self, percent=None):
        """
        Resizes the views to the given percent
        """

        if percent is None:
            percent = self.zoom_spinbox.value()
        factor = percent / 100
        matrix = self.view.transform()
        matrix.reset()
        matrix.scale(factor, factor)
        self.view.setTransform(matrix)

    def settings(self):
        """
        Shows settings dialog
        """

        dlg = camdlg.CamSettings(self.cam, self)
        if dlg.exec():
            cam = dlg.cam_settings()

            equals = True
            if cam.speed() != self.cam.speed() or cam.radius() != self.cam.radius():
                equals = False
            for i, cam_profile in enumerate(self.cam):
                if cam_profile.color() != cam[i].color():
                    equals = False
                if cam_profile.depth() != cam[i].depth() or cam_profile.height() != cam[i].height():
                    equals = False
            if not equals:
                self.undo_stack.push(camcmd.CamCommand(self, self.cam, cam, "Cam Edited"))
            x_steps, y_limit, y_steps = dlg.grid_settings()
            self.scene.set_x_steps(x_steps)
            self.scene.set_y_limit(y_limit)
            self.scene.set_y_steps(y_steps)

    def update_file_menu(self):
        """
        Dynamically creates the file menu
        """

        self.file_menu.clear()
        # self.exportMenu.clear()
        self.add_actions(self.file_menu, self.file_menu_actions[:-2])
        self.file_menu.addSeparator()
        # self.exportMenu = self.fileMenu.addMenu(QIcon(":/fileexport.png"), "&Export")
        # self.addActions(self.exportMenu, self.exportMenuActions)
        self.file_menu.addSeparator()
        self.file_menu.addActions(self.file_menu_actions[-2:-1])
        recent_files = []
        try:
            for filename in BarrelCamEditor.recent_files:
                if QFile.exists(filename):
                    recent_files.append(filename)
        except AttributeError:
            pass

        if recent_files:
            self.file_menu.addSeparator()
            for i, filename in enumerate(recent_files):
                action = QAction(QIcon(":/icon.png"), "&{0} {1}".format(i + 1, QFileInfo(filename).fileName()), self)
                action.setData(filename)
                action.triggered[()].connect(self.load_file)
                self.file_menu.addAction(action)
        self.file_menu.addSeparator()
        self.file_menu.addActions(self.file_menu_actions[-1:])

#    def update_selection(self):
#        """
#        Update the selections for table and scene
#        """

#        self.selected_points = []
#        self.selected_cams = []
#        self.scene.clearSelection()

    def update_status(self, message=None):
        """
        Updates the statusbar and the window title
        """

        self.statusBar().showMessage(message, 5000)
        self.setWindowTitle("Barrel Cam Editor - {0}[*]".format(QFileInfo(self.cam.file_name()).fileName()))
        self.setWindowModified(self.cam.dirty())
        self.printer.setDocName(QFileInfo(self.cam.file_name()).fileName())

    def update_ui(self):
        """
        Dynamically enable the actions depending on the selected items
        """

        self.selected_points = []
        self.selected_cams = []

        file_name_exist = (file_name := self.cam.file_name()) is not None

        self.setWindowTitle("Barrel Cam Editor - {0}[*]".format(os.path.basename(file_name)))
        self.setWindowModified(self.cam.dirty())

        for item in self.scene.selectedItems():
            if isinstance(item, camwidget.CamPointItem):
                self.selected_points.append(item)
            if isinstance(item, camwidget.CamProfileItem):
                self.selected_cams.append(item)
        '''table = self.tab_widget.currentWidget()
            if table:
                table_index = self.tab_widget.currentIndex()
                #resources = self.collection[table_index]
                indexes = [selected.row() for selected in table.selectionModel().selectedRows()]
                print(indexes)'''

        self.edit_cam_move_action.setEnabled(len(self.selected_cams) > 0)
        self.edit_mirror_action.setEnabled(len(self.cam) > 0)
        self.edit_cam_edit_action.setEnabled(len(self.selected_cams) == 1)
        self.edit_point_add_action.setEnabled(len(self.selected_cams) == 1)
        self.edit_point_edit_action.setEnabled(len(self.selected_points) > 0)
        self.edit_delete_action.setEnabled(self.selected_points != [] or self.selected_cams != [])
        self.edit_cut_action.setEnabled(len(self.selected_cams) > 0)
        self.edit_copy_action.setEnabled(len(self.selected_cams) > 0)
        self.edit_paste_action.setEnabled(len(BarrelCamEditor.copied_items) > 0)
        self.edit_undo_action.setEnabled(self.undo_stack.canUndo())
        self.edit_redo_action.setEnabled(self.undo_stack.canRedo())
        self.view_graphs_action.setEnabled(len(self.cam) > 0)

    def update_widgets(self):
        """
        Updates the widgets when the cam changes
        """

        self.scene.update()
        self.tab_widget.clear()
        for profile in self.cam:
            table = camwidget.TableCamWidget(profile)
            #table.selectionModel().selectionChanged.connect(self.update_selection)
            table.itemDoubleClicked.connect(self.edit_point_table)
            self.tab_widget.addTab(table, QIcon(":/profile.png"), profile.label())
        if self.graphs_widget is not None:
            self.graphs_widget.updateGraphs()
            self.graphs_widget.figure.canvas.draw()

    def update_window_menu(self):
        """Update the window menu dynamically.
        """

        self.window_menu.clear()
        menu = self.window_menu
        if len(BarrelCamEditor.instances) > 1:
            self.add_actions(menu, (self.window_arrange_horizontal_action, self.window_arrange_vertical_action, None))
        i = 1
        for editor in BarrelCamEditor.instances:
            title = editor.windowTitle()[:-3]
            shortcut = ""
            if i == 10:
                menu.addSeparator()
                menu = menu.addMenu("&More")
            if i < 10:
                shortcut = "&{0} ".format(i)
            elif i < 36:
                shortcut = "&{0} ".format(chr(i + ord("@") - 9))
            action = menu.addAction("{0}{1}".format(shortcut, title))
            action.triggered.connect(self.raise_window)
            i += 1

    def update_zoom(self):
        """
        Updates the zoomSpinBox percent
        """

        self.zoom_spinbox.setValue(self.view.transform().m11() * 100)

    def view_graphs(self):
        """
        Shows the graphs for the cam profiles
        """

        graphs_widget = camwidget.GraphsWidget(self.cam)
        graphs_toolbar = NavigationToolbar(graphs_widget, self)
        dlg = camdlg.GraphsDlg(graphs_widget, graphs_toolbar, self)
        dlg.show()

    def view_zoom(self):
        """
        Sets the Zoom level
        """

        percent, ok = QInputDialog.getInt(self, "Barrel Cam - Zoom", "Percent:", self.zoom_spinbox.value(), 0, 400, 10)
        if ok:
            self.zoom_spinbox.setValue(percent)

    def view_zoom_all(self):
        """
        Zooms all the Scene
        """

        self.view.fitInView(self.view.sceneRect(), Qt.KeepAspectRatio)
        self.zoom_spinbox.setValue(self.view.transform().m11() * 100)

    def window_arrange_horizontal(self):
        """Arrange the open windows horizontally.
        """

        size = self.screen().geometry()
        top = size.top()
        left = size.left()
        height = size.height() // len(BarrelCamEditor.instances)
        width = size.width()
        for instance in BarrelCamEditor.instances:
            instance.showNormal()
            instance.move(left, top)
            instance.resize(width, height)
            top += height

    def window_arrange_vertical(self):
        """Arrange the open windows vertically.
        """

        size = self.screen().geometry()
        top = size.top()
        left = size.left()
        height = size.height()
        width = size.width() // len(BarrelCamEditor.instances)
        for instance in BarrelCamEditor.instances:
            instance.showNormal()
            instance.move(left, top)
            instance.resize(width, height)
            left += width


if __name__ == "__main__":
    APP = QApplication(sys.argv)
    APP.setOrganizationName("Sanfe Ltd.")
    APP.setOrganizationDomain("sanfe.com")
    APP.setApplicationName("BarrelCam Editor")
    APP.setWindowIcon(QIcon(":/icon.png"))
    if len(sys.argv) > 1 and str(sys.argv[1]) == "-reset":
        QSettings().clear()
    MAIN_WINDOW = BarrelCamEditor()
    MAIN_WINDOW.show()
    APP.exec()
