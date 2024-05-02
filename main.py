import sys

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel

from logic import constants
from logic.constants import PAINT_AREA_OFFSET_X, PAINT_AREA_OFFSET_Y, CELL_SIZE, FPS, RANDOM_RATIO
from logic.grid import Grid
from logic.simulation import SimulationThread
from ui.main_window import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Conway's Game of Life")

        self.horizontalLayout.addWidget(self.widget)
        self.width = self.widget.width()
        self.height = self.widget.height()
        self.cell_size = CELL_SIZE
        self.widget_paint_area = Grid(self.width, self.height, self.cell_size)

        self.verticalLayout.addWidget(self.widget_paint_area)
        self.widget_control_panel.setFixedWidth(200)

        self.simulation = SimulationThread(show_gens_label=self.label_show_gens)
        self.simulation.sig[QLabel].connect(self.widget_paint_area.simulation)

        self.lineEdit_gens_per_sec.setText(f"{FPS}")
        self.lineEdit_cell_size.setText(f"{CELL_SIZE}")
        self.lineEdit_random_ratio.setText(f"{RANDOM_RATIO}")
        self.comboBox_board_pattern.addItem('有界模式')
        self.comboBox_board_pattern.addItem('甜甜圈模式')
        self.comboBox_board_pattern.setCurrentIndex(0)

        self.label_current_status.setText("准备就绪")
        self.checkBox_show_grid.setChecked(False)

    def resizeEvent(self, event):
        self.width = self.widget.width()
        self.height = self.widget.height()
        self.widget_paint_area.width = self.width // self.cell_size * self.cell_size
        self.widget_paint_area.height = self.height // self.cell_size * self.cell_size
        self.widget_paint_area.setFixedWidth(self.width)
        self.widget_paint_area.setFixedHeight(self.height)

    def closeEvent(self, event):
        self.simulation.flag = False
        self.simulation.wait()
        event.accept()

    def mouseMoveEvent(self, event):
        if self.widget_paint_area.running:
            return
        pos = event.position()
        row = (int(pos.y()) - PAINT_AREA_OFFSET_Y - 1) // self.cell_size
        col = (int(pos.x()) - PAINT_AREA_OFFSET_X - 1) // self.cell_size
        if (row, col) != self.widget_paint_area.last_toggled_cell:
            self.widget_paint_area.toggle_cell(row, col)
            self.widget_paint_area.update()

        in_area = PAINT_AREA_OFFSET_X < pos.x() < self.widget_paint_area.width + PAINT_AREA_OFFSET_X and PAINT_AREA_OFFSET_Y < pos.y() < self.widget_paint_area.height + PAINT_AREA_OFFSET_Y

        if (self.widget_paint_area.gens == 0 or self.widget_paint_area.gens == 1) and in_area:
            self.label_show_gens.setText("1")
            self.widget_paint_area.gens = 1

    def mousePressEvent(self, event):
        if self.widget_paint_area.running:
            return
        pos = event.position()
        row = (int(pos.y()) - PAINT_AREA_OFFSET_Y - 1) // self.cell_size
        col = (int(pos.x()) - PAINT_AREA_OFFSET_X - 1) // self.cell_size
        self.widget_paint_area.toggle_cell(row, col)
        self.widget_paint_area.update()

        in_area = PAINT_AREA_OFFSET_X < pos.x() < self.widget_paint_area.width + PAINT_AREA_OFFSET_X and PAINT_AREA_OFFSET_Y < pos.y() < self.widget_paint_area.height + PAINT_AREA_OFFSET_Y

        if (self.widget_paint_area.gens == 0 or self.widget_paint_area.gens == 1) and in_area:
            self.label_show_gens.setText("1")
            self.widget_paint_area.gens = 1

    @Slot()
    def on_comboBox_board_pattern_currentIndexChanged(self):
        if self.comboBox_board_pattern.currentText() == '有界模式':
            self.widget_paint_area.survival_world = constants.Flag.Grid.survival_world_border
        if self.comboBox_board_pattern.currentText() == '甜甜圈模式':
            self.widget_paint_area.survival_world = constants.Flag.Grid.survival_world_donut

    @Slot()
    def on_pushButton_next_step_clicked(self):
        if self.widget_paint_area.gens == 0:
            return
        self.widget_paint_area.running = False
        self.simulation.flag = False
        self.widget_paint_area.running = True
        self.widget_paint_area.simulation(label_show_gens=self.label_show_gens)
        self.widget_paint_area.running = False

    @Slot()
    def on_lineEdit_cell_size_editingFinished(self):
        if self.lineEdit_cell_size.text().isdigit():
            if int(self.lineEdit_cell_size.text()) > 100:
                self.cell_size = 100
                self.lineEdit_cell_size.setText("100")

            if int(self.lineEdit_cell_size.text()) < 5:
                self.cell_size = 5
                self.lineEdit_cell_size.setText("5")
            if 5 <= int(self.lineEdit_cell_size.text()) <= 100:
                self.cell_size = int(self.lineEdit_cell_size.text())
        else:
            try:
                if 5 <= float(self.lineEdit_cell_size.text()) <= 100:
                    self.cell_size = round(float(self.lineEdit_cell_size.text()), 0)
                    self.lineEdit_cell_size.setText(str(round(float(self.lineEdit_cell_size.text()))))
                    return
                if float(self.lineEdit_cell_size.text()) > 100:
                    self.cell_size = 100
                    self.lineEdit_cell_size.setText("100")
                    return
                if float(self.lineEdit_cell_size.text()) < 5:
                    self.cell_size = 5
                    self.lineEdit_cell_size.setText("5")
                    return
            except ValueError:
                self.cell_size = 10
                self.lineEdit_cell_size.setText("10")

        self.widget_paint_area.cell_size = self.cell_size
        self.widget_paint_area.rows = self.height // self.cell_size
        self.widget_paint_area.cols = self.width // self.cell_size
        self.widget_paint_area.cells = [[0 for _x in range(self.widget_paint_area.cols)] for _y in
                                        range(self.widget_paint_area.rows)]
        self.widget_paint_area.decorate_cells = [[0 for _x in range(self.widget_paint_area.cols)] for _y in
                                                 range(self.widget_paint_area.rows)]
        self.on_pushButton_stop_clicked()
        self.widget_paint_area.update()

    @Slot()
    def on_lineEdit_random_radio_editingFinished(self):
        try:
            if float(self.lineEdit_random_ratio.text()) >= 1:
                self.widget_paint_area.random_radio = 0.99
                self.lineEdit_random_ratio.setText("0.99")
            if float(self.lineEdit_random_ratio.text()) <= 0:
                self.widget_paint_area.random_radio = 0.01
                self.lineEdit_random_ratio.setText("0.01")
            if 0 < float(self.lineEdit_random_ratio.text()) < 1:
                self.widget_paint_area.random_radio = float(self.lineEdit_random_ratio.text())
        except ValueError:
            self.widget_paint_area.random_radio = 0.25
            self.lineEdit_random_ratio.setText("0.25")

    @Slot()
    def on_pushButton_clean_surface_clicked(self):
        self.widget_paint_area.clear()
        self.widget_paint_area.update()
        self.widget_paint_area.running = False
        self.simulation.flag = False
        self.simulation.quit()
        self.label_current_status.setText("已清空")
        self.widget_paint_area.gens = 0
        self.label_show_gens.setText("")

    @Slot()
    def on_pushButton_start_clicked(self):
        if self.widget_paint_area.gens == 0:
            return
        self.widget_paint_area.running = True
        self.simulation.start()
        self.label_current_status.setText("正在运行")

    @Slot()
    def on_pushButton_stop_clicked(self):
        self.widget_paint_area.running = False
        self.simulation.flag = False
        self.simulation.quit()
        self.label_current_status.setText("已停止")

    @Slot()
    def on_pushButton_random_gen_clicked(self):
        self.widget_paint_area.fill_random()
        self.label_show_gens.setText("1")
        self.widget_paint_area.gens = 1
        self.widget_paint_area.update()

    @Slot()
    def on_lineEdit_gens_per_sec_editingFinished(self):
        if self.lineEdit_gens_per_sec.text().isdigit():
            if int(self.lineEdit_gens_per_sec.text()) > 60:
                self.simulation.fps = 60
                self.lineEdit_gens_per_sec.setText("60")

            if int(self.lineEdit_gens_per_sec.text()) < 1:
                self.simulation.fps = 1
                self.lineEdit_gens_per_sec.setText("1")
            if 1 <= int(self.lineEdit_gens_per_sec.text()) <= 60:
                self.simulation.fps = int(self.lineEdit_gens_per_sec.text())

        else:
            try:
                if 60 >= float(self.lineEdit_gens_per_sec.text()) >= 0.5:
                    self.simulation.fps = round(float(self.lineEdit_gens_per_sec.text()), 0)
                    self.lineEdit_gens_per_sec.setText(str(round(float(self.lineEdit_gens_per_sec.text()))))
                    return

                if float(self.lineEdit_gens_per_sec.text()) > 60:
                    self.simulation.fps = 60
                    self.lineEdit_gens_per_sec.setText("60")
                    return
                if float(self.lineEdit_gens_per_sec.text()) < 0.5:
                    self.simulation.fps = 1
                    self.lineEdit_gens_per_sec.setText("1")
                    return
            except ValueError:
                self.simulation.fps = 12
                self.lineEdit_gens_per_sec.setText("12")

    @Slot()
    def on_checkBox_show_tail_stateChanged(self):
        self.widget_paint_area.show_tail = self.checkBox_show_tail.isChecked()

    @Slot()
    def on_pushButton_clear_tail_clicked(self):
        for row in range(self.widget_paint_area.rows):
            for col in range(self.widget_paint_area.cols):
                self.widget_paint_area.decorate_cells[row][col] &= ~constants.Flag.Grid.show_tail
        self.widget_paint_area.update()

    @Slot()
    def on_checkBox_trace_1_gen_stateChanged(self):
        self.widget_paint_area.show_traces_of_death = self.checkBox_trace_1_gen.isChecked()
        flag = False
        for row in range(self.widget_paint_area.rows):
            for col in range(self.widget_paint_area.cols):
                if self.widget_paint_area.decorate_cells[row][col] & constants.Flag.Grid.show_traces_of_death:
                    flag = True
                    break
            if flag:
                break
        if flag:
            return
        for row in range(self.widget_paint_area.rows):
            for col in range(self.widget_paint_area.cols):
                if self.widget_paint_area.cells[row][col]:
                    self.widget_paint_area.decorate_cells[row][col] |= constants.Flag.Grid.show_traces_of_death

    @Slot()
    def on_checkBox_show_grid_stateChanged(self):
        self.widget_paint_area.show_grid = self.checkBox_show_grid.isChecked()
        self.widget_paint_area.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())