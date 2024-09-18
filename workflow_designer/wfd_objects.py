from dataclasses import dataclass

NODEPROPS = ['FillColor', 'TextColor', 'Text']
NODEATTRIBS = ['Font', 'LayoutNode']
LINKPROPS = ['DrawColor']
LINKATTRIBS = ['LayoutLink', 'Point']

class Rect:
    def __init__(self, left: int, top: int, width: int, height: int):
        self.left = left
        self.top = top
        self.width = width
        self.height = height

        self.rx = width / 2
        self.ry = height / 2
        self.cx = left + self.rx
        self.cy = top + self.ry

@dataclass
class Node:
    nodeRect: Rect
    nodeProps: dict
    nodeAttribs: dict[dict]
    
