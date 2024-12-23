from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

plt.style.use('bmh')


class Mpl_widget(QtWidgets.QWidget):
    def __init__(self, parent=None):

        QtWidgets.QWidget.__init__(self, parent)

        self.canvas = FigureCanvas(Figure(tight_layout=True))

        vertical_layout = QtWidgets.QVBoxLayout()
        vertical_layout.addWidget(self.canvas)

        self.canvas.axes = self.canvas.figure.add_subplot(211), self.canvas.figure.add_subplot(212)
        self.setLayout(vertical_layout)
