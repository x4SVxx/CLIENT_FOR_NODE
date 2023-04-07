import websockets
import json
from PyQt5 import QtWidgets
import PyQt5.QtCore as QtCore
from PyQt5.Qt import *
import pyqtgraph as pg
from PIL import Image
import multiprocessing
import sys
import asyncio
import numpy as np

class Tag:
    def __init__(self, x, y, name):
        self.x = x
        self.y = y
        self.name = name
        self.text_name = None
        self.text_cords = None

class Window(QMainWindow):
    def __init__(self, log_list):
        super(Window, self).__init__()
        self.tags = []
        self.main_window_geometry()
        self.create_graphics()
        self.start_draw(log_list)

    def main_window_geometry(self):
        self.SCREEN_WIDTH = QApplication.desktop().width()
        self.SCREEN_HEIGHT = QApplication.desktop().height()
        self.window_width = int(self.SCREEN_WIDTH / 10 * 7)
        self.window_height = int(self.SCREEN_HEIGHT / 10 * 7)
        self.window_x = int(self.SCREEN_WIDTH / 2 - self.window_width / 2)
        self.window_y = int(self.SCREEN_HEIGHT / 2 - self.window_height / 2)

        self.setGeometry(self.window_x, self.window_y, self.window_width, self.window_height)
        self.setWindowTitle("Websocket client")

    def create_graphics(self):
        self.graph_width = self.window_width
        self.graph_height = self.window_height
        self.graph_widget = pg.PlotWidget(self)
        self.graph_widget.showGrid(x=True, y=True)
        self.graph_widget.setBackground("White")
        self.graph_widget.setGeometry(QtCore.QRect(0, 0, self.graph_width, self.graph_height))
        filename, filetype = QFileDialog.getOpenFileName(self, "SELECT A MAP", ".", "Images files (*.png *.jpg *.jpeg)")
        self.img = pg.ImageItem(np.flipud(np.array(Image.open(filename))).transpose([1, 0, 2]), name="map")
        self.img.setRect(QRect(int(filename.split()[2]), int(filename.split()[3]), int(filename.split()[4]), int(filename.split()[5].split(".")[0])))
        self.img.setZValue(-100)
        self.graph_widget.addItem(self.img)

    def start_draw(self, log_list):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(lambda: self.draw(log_list))
        self.timer.start(100)

    """Функция отрисовки меток"""
    def draw(self, log_list):
        if len(log_list) != 0:
            message = log_list.pop()
            check_tag_flag = False
            for tag in self.tags:
                if tag.name == message["data"]["ID"]:
                    check_tag_flag = True
                    for item in self.graph_widget.listDataItems():
                        if item.name() == tag.name:
                            tag.x = float(message["data"]["x"])
                            tag.y = float(message["data"]["y"])
                            item.setData([tag.x], [tag.y], pen=pg.mkPen(width=3, color='Red'), name=tag.name)
                            tag.text_name.setPos(tag.x, tag.y)
                            tag.text_cords.setPos(tag.x, tag.y)
                            tag.text_cords.setText("x= " + str(round(tag.x, 2)) + "   " + "y= " + str(round(tag.y, 2)))

            if not check_tag_flag:
                new_tag = Tag(float(message["data"]["x"]), float((message["data"]["y"])), message["data"]["ID"])
                self.graph_widget.addItem(pg.ScatterPlotItem([new_tag.x], [new_tag.y], pen=pg.mkPen(width=3, color='Red'), name=new_tag.name))
                self.tags.append(new_tag)

                new_tag.text_name = pg.TextItem(str(new_tag.name), color="Black")
                new_tag.text_name.setFont(QFont("Arial", 14))
                new_tag.text_name.setAnchor([0, 1])
                new_tag.text_name.setPos(new_tag.x, new_tag.y)
                self.graph_widget.addItem(new_tag.text_name)

                new_tag.text_cords = pg.TextItem("x= " + str(round(new_tag.x, 2)) + "   " + "y= " + str(round(new_tag.y, 2)), color="Black")
                new_tag.text_cords.setFont(QFont("Arial", 10))
                new_tag.text_cords.setPos(new_tag.x, new_tag.y)
                self.graph_widget.addItem(new_tag.text_cords)

async def client_handler(server_ip, server_port, log_list):
    url = f"ws://{server_ip}:{server_port}"
    async with websockets.connect(url, ping_interval=None) as ws:
        while True:
            message = json.loads(await ws.recv())
            print("MESSAGE FROM SERVER: " + str(message))
            if "data" in message and "type" in message["data"] and "ID" in message["data"] and "x" in message["data"] and "y" in message["data"]:
                if message["data"]["type"] == "tag":
                    log_list.append(message)

async def ws_config(log_list):
    server_ip = "127.0.0.1"
    server_port = "8000"
    loop = asyncio.get_event_loop()
    loop.run_until_complete(await client_handler(server_ip, server_port, log_list))

async def asyncio_start_ws(log_list):
    await ws_config(log_list)

def start_ws(log_list):
    asyncio.run(asyncio_start_ws(log_list))

def start_qt(log_list):
    app = QApplication(sys.argv)
    window = Window(log_list)
    window.show()
    app.exec_()

if __name__ == "__main__":
    manager = multiprocessing.Manager()
    log_list = manager.list()
    process_ws = multiprocessing.Process(name="start_ws", target=start_ws, args=(log_list,), daemon=True)
    process_ws.start()
    start_qt(log_list)


