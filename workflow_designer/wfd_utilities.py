import math

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QPainter

# Inspired by https://forum.qt.io/topic/109749/how-to-create-an-arrow-in-qt/6
# Probably worth converting all to Q primitives (QPointF, QLineF, etc.)
def drawArrow(painter: QPainter, srcPoint: tuple, dstPoint: tuple, headSize: int = 5):
    dx = srcPoint[0] - dstPoint[0]
    dy = srcPoint[1] - dstPoint[1]

    angle = math.atan2(-dy, dx)

    arrowP1X = dstPoint[0] + math.sin(angle + (math.pi / 3)) * headSize
    arrowP1Y = dstPoint[1] + math.cos(angle + (math.pi / 3)) * headSize
    
    arrowP2X = dstPoint[0] + math.sin(angle + math.pi - (math.pi / 3)) * headSize
    arrowP2Y = dstPoint[1] + math.cos(angle + math.pi - (math.pi / 3)) * headSize

    painter.drawLine(
            srcPoint[0],
            srcPoint[1],
            dstPoint[0],
            dstPoint[1]
        )

    pointList = [
            QPoint(dstPoint[0], dstPoint[1]),
            QPoint(arrowP1X, arrowP1Y),
            QPoint(arrowP2X, arrowP2Y)
        ]
    painter.drawPolygon(pointList, Qt.OddEvenFill)
    
