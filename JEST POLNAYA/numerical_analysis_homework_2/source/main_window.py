import sys, os
from PyQt5.QtWidgets import QMessageBox
import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import QtGui, QtWidgets, QtCore, uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPalette, QColor
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from Integrator.integrator import Integrator
from worker import Worker
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class ErrorPlotWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("График погрешности")
        self.setGeometry(100, 100, 600, 400)

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.setCentralWidget(self.canvas)
        
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.addToolBar(self.toolbar)

    def plot_errors(self, xs, er1s, er2s):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(xs, er1s, 'r--', label='E1')
        ax.plot(xs, er2s, 'b--', label='E2')
        ax.legend(loc='upper right')
        ax.set_title('Глобальные погрешности')
        ax.set_xlabel("x")
        ax.set_ylabel("Погрешность")
        self.canvas.draw()

class Main_window(QtWidgets.QMainWindow):
    def show_info(self, initial_v1, initial_v2, final_v1, final_v2, max_e1, max_e2, min_e1, min_e2, total_steps, boundary_layer_steps, post_boundary_layer_steps):
        info = f"""
        Начальные численные решения: v1 = {initial_v1:.6e}, v2 = {initial_v2:.6e}
        Конечные численные решения: v1 = {final_v1:.6e}, v2 = {final_v2:.6e}
        Максимальное значение E1: {max_e1:.6e}
        Максимальное значение E2: {max_e2:.6e}
        Минимальное значение E1: {min_e1:.6e}
        Минимальное значение E2: {min_e2:.6e}
        Всего шагов: {total_steps}
        """
        QMessageBox.information(self, "Справка", info)                                  
    def __init__(self) -> None:
        super(Main_window, self).__init__()
        script_dir = os.path.dirname(os.path.realpath(__file__))
        uic.loadUi(
            os.path.abspath(os.path.join(script_dir, os.pardir))  # Parent directory
            + os.path.sep
            + "resources"
            + os.path.sep
            + "main_window.ui",
            self,
        )
        self.addToolBar(NavigationToolbar(self.plot.canvas, self))
        self.setWindowIcon(QtGui.QIcon(
            os.path.abspath(os.path.join(script_dir, os.pardir))  # Parent directory
            + os.path.sep
            + "resources"
            + os.path.sep
            + "icon.png"))
        pixmap = QPixmap(
            os.path.abspath(os.path.join(script_dir, os.pardir))  # Parent directory
            + os.path.sep
            + "resources"
            + os.path.sep
            + "system.png"
        )

        self.error_plot_btn = QtWidgets.QPushButton("График погрешности", self)
        self.error_plot_btn.setGeometry(10, 10, 150, 30)  # x, y, width, height
        self.error_plot_btn.clicked.connect(self.show_error_plot)
        

        self.system_label.setPixmap(pixmap)
        self.system_label.setMask(pixmap.mask())
        self.threadpool = QtCore.QThreadPool()
        self.row_index = 0

        self.plot_btn.clicked.connect(self.on_plot_btn_click)

    def insert_table_row(self, row_index, row):
        self.table.insertRow(row_index)
        self.row_index = row_index

        for index, item in enumerate(row):
            self.table.setItem(row_index, index, QtWidgets.QTableWidgetItem(
                f"{item:.6e}"))

    def thread_complete(self, points_to_plot):
        self.plot.canvas.axes[0].clear()
        self.plot.canvas.axes[0].plot(points_to_plot.xs, points_to_plot.v_1s, 'y')
        self.plot.canvas.axes[0].plot(points_to_plot.xs, points_to_plot.v_2s, 'b')
        self.plot.canvas.axes[0].legend(('v1(x)', 'v2(x)'),loc='upper right')
        self.plot.canvas.axes[0].set_title('Численное решение')
        self.plot.canvas.axes[0].set_xlabel("x")
        self.plot.canvas.axes[0].set_ylabel("v1(x)/v2(x)")

        self.plot.canvas.axes[1].clear()
        self.plot.canvas.axes[1].plot(points_to_plot.xs, points_to_plot.u_1s, 'y')
        self.plot.canvas.axes[1].plot(points_to_plot.xs, points_to_plot.u_2s, 'b')
        self.plot.canvas.axes[1].legend(('u1(x)', 'u2(x)'),loc='upper right')
        self.plot.canvas.axes[1].set_title('Истинное решение')
        self.plot.canvas.axes[1].set_xlabel("x")
        self.plot.canvas.axes[1].set_ylabel("u1(x)/u2(x)")
        self.plot.canvas.draw()

        self.table.setVerticalHeaderLabels((str(i) for i in range(self.row_index + 1)))

    def on_plot_btn_click(self) -> None:
        # Clear output table
        while (self.table.rowCount() > 0):
                self.table.removeRow(0)

        step = float(self.step_text_box.text())
        x_max = float(self.x_max_text_box.text())
        eps = float(self.eps_text_box.text())
        step_control_flag = self.step_control_check_box.isChecked()

        worker = Worker(step, x_max, eps, step_control_flag)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.insert_table_row.connect(self.insert_table_row)

        self.threadpool.start(worker)

    def show_error_plot(self):
        xs, er1s, er2s = self.get_error_data()
        if xs:
            if not hasattr(self, 'error_window') or self.error_window is None:
                self.error_window = ErrorPlotWindow()
            self.error_window.plot_errors(xs, er1s, er2s)
            self.error_window.show()
        else:
            QtWidgets.QMessageBox.warning(self, "Предупреждение", "Сначала выполните расчет!")

    def get_error_data(self):
        xs = []
        er1s = []
        er2s = []
        for row in range(self.table.rowCount()):
            xs.append(float(self.table.item(row, 0).text()))
            er1s.append(float(self.table.item(row, 5).text()))
            er2s.append(float(self.table.item(row, 6).text()))
        return xs, er1s, er2s


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)

    # Force the style to be the same on all OSs:
    app.setStyle("Fusion")

    # Now use a palette to switch to dark colors:
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(85, 132, 117))
    palette.setColor(QPalette.WindowText, Qt.black)
    palette.setColor(QPalette.Base, QColor(50,100,100))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase,  QColor(100, 132, 152))
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(100, 132, 152))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(100, 132, 152))
    app.setPalette(palette)

    window = Main_window()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
