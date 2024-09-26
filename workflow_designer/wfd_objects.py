from dataclasses import dataclass

NODEPROPS = ['FillColor', 'TextColor', 'Text', 'LabelEdit', 'Alignment', 'DrawColor', 'Shadow']
NODEATTRIBS = ['Font', 'LayoutNode', 'Shape']
LINKPROPS = ['DrawColor', 'Shadow', 'DashStyle']
LINKATTRIBS = ['LayoutLink', 'Point']

class Rect:
    def __init__(self, left: float, top: float, width: float, height: float):
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
    
@dataclass
class Link:
    linkProps: dict
    linkAttribs: dict[dict]
