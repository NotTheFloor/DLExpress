import math

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QPainter, QPolygon, QPolygonF, QBrush
from PySide6.QtWidgets import QGraphicsItem, QGraphicsLineItem, QGraphicsPolygonItem

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
    
def addArrowToLineItem(graphicsItem: QGraphicsLineItem, headSize: int = 5):
    x1 = graphicsItem.line().x1()
    y1 = graphicsItem.line().y1()
    x2 = graphicsItem.line().x2()
    y2 = graphicsItem.line().y2()
    #dx = graphicsItem.line().dx.
    #dy = graphicsItem.line().dy
    dx = x2 - x1
    dy = y2 - y1

    angle = math.atan2(-dy, dx)

    arrowP1X = x2 + math.sin(angle + (math.pi / 6)) * headSize
    arrowP1Y = y2 + math.cos(angle + (math.pi / 6)) * headSize
    
    arrowP2X = x2 + math.sin(angle + math.pi - (math.pi / 6)) * headSize
    arrowP2Y = y2 + math.cos(angle + math.pi - (math.pi / 6)) * headSize

    pointList = [
            QPointF(x2, y2),
            QPointF(arrowP1X, arrowP1Y),
            QPointF(arrowP2X, arrowP2Y),
        ]
    
    polygon = QPolygonF(pointList)
    arrowItem = QGraphicsPolygonItem(polygon, graphicsItem)

    # Set same pen as line
    arrowItem.setPen(graphicsItem.pen())
    
    # Fill arrow with same color as pen
    arrowItem.setBrush(QBrush(graphicsItem.pen().color()))
    
    return arrowItem
