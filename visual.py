from PyQt6.QtWidgets import (
    QWidget, QGraphicsView,
    QGraphicsItem, QGraphicsTextItem, QMenu, QInputDialog, 
)
from PyQt6.QtGui import QBrush, QPen, QPolygonF, QPainterPath, QPainterPathStroker
from PyQt6.QtCore import Qt, QRectF, QPointF, QLineF

import structure
import math


class OntologyItem(QGraphicsItem):
    def __init__(self, node_id, model, text="Item"):
        super().__init__()

        self.model = model 
        self.node_id = node_id
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        )

        self.text = QGraphicsTextItem(text, self)
        self.text.setDefaultTextColor(Qt.GlobalColor.black)
        self.arrows = []
        
        self.setZValue(1)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.menu = QMenu()

        delete_action = self.menu.addAction("Delete Element")
        delete_action.triggered.connect(self.delete)

        self.label = text

        self._zoom = 0
        self._zoom_min = -10
        self._zoom_max = 10

    def center_text(self):
        rect = self.boundingRect()
        text_rect = self.text.boundingRect()

        x = rect.center().x() - text_rect.width() / 2
        y = rect.center().y() - text_rect.height() / 2
        self.text.setPos(x, y)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for arrow in self.arrows:
                arrow.update_positions()

            if self.model and self.node_id is not None:
                pos = self.pos()
                self.model.set_position(self.node_id, pos.x(), pos.y())
        return super().itemChange(change, value)

    def contextMenuEvent(self, event):
        self.menu.exec(event.screenPos())

    def delete(self):
        if self.model and self.node_id is not None:
            self.model.remove_node(self.node_id)

    def mouseDoubleClickEvent(self, event):
        new_text, ok = QInputDialog.getText(
            None,
            "Edit Name",
            "Enter new name:",
            text=self.text.toPlainText()
        )

        if ok and new_text:
            self.model.set_label(self.node_id, new_text)
            
            self.text.setPlainText(new_text)
            self.center_text()
            self.label = new_text

        super().mouseDoubleClickEvent(event)

class ClassItem(OntologyItem):
    def __init__(self, node_id, model, text="Class"):
        super().__init__(node_id, model, text)
        self.rect = QRectF(0, 0, 120, 60)
        self.center_text()

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget=None):
        if self.isSelected():
            painter.setBrush(QBrush(Qt.GlobalColor.yellow))
            pen = QPen(Qt.GlobalColor.blue, 3)
        else:
            painter.setBrush(QBrush(Qt.GlobalColor.white))
            pen = QPen(Qt.GlobalColor.black, 2)

        painter.setPen(pen)
        painter.drawRect(self.rect)

class AttributeItem(OntologyItem):
    def __init__(self, node_id, model, text="Attribute"):
        super().__init__(node_id, model, text)
        self.rect = QRectF(0, 0, 100, 50)
        self.center_text()

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget=None):
        if self.isSelected():
            painter.setBrush(QBrush(Qt.GlobalColor.yellow))
            pen = QPen(Qt.GlobalColor.blue, 3)
        else:
            painter.setBrush(QBrush(Qt.GlobalColor.white))
            pen = QPen(Qt.GlobalColor.black, 2)

        painter.setPen(pen)
        painter.drawEllipse(self.rect)

class RelationItem(OntologyItem):
    def __init__(self, node_id, model, text="Relation"):
        super().__init__(node_id, model, text)
        self.rect = QRectF(0, 0, 120, 60)
        self.center_text()

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget=None):
        w = self.rect.width()
        h = self.rect.height()

        polygon = QPolygonF([
            QPointF(w / 2, 0),   # top Center
            QPointF(w, h / 2),   # right Center
            QPointF(w / 2, h),   # bottom Center
            QPointF(0, h / 2)    # left Center
        ])

        if self.isSelected():
            painter.setBrush(QBrush(Qt.GlobalColor.yellow))
            pen = QPen(Qt.GlobalColor.blue, 3)
        else:
            painter.setBrush(QBrush(Qt.GlobalColor.white))
            pen = QPen(Qt.GlobalColor.black, 2)

        painter.setPen(pen)

        
        painter.drawPolygon(polygon)

class Arrow(QGraphicsItem):
    def __init__(self, start_item, end_item, model):
        super().__init__()
        
        self.model = model
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)

        self.start_item = start_item
        self.end_item = end_item

        start_item.arrows.append(self)
        end_item.arrows.append(self)

        self.start_point = QPointF()
        self.end_point = QPointF()

        self.setZValue(0)

        self.update_positions()

        self.menu = QMenu()

        delete_action = self.menu.addAction("Delete Connection")
        delete_action.triggered.connect(self.delete)

    def boundingRect(self):
        extra = 5
        rect = QRectF(self.start_point, self.end_point).normalized()
        return rect.adjusted(-extra, -extra, extra, extra)
    
    def shape(self):
        path = QPainterPath()
        path.moveTo(self.start_point)
        path.lineTo(self.end_point)

        stroker = QPainterPathStroker()
        stroker.setWidth(10) 

        return stroker.createStroke(path)

    def paint(self, painter, option, widget=None):
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.drawLine(self.start_point, self.end_point)

        line = QLineF(self.start_point, self.end_point)

        if line.length() == 0:
            return

        arrow_size = 20

        p2 = (self.start_point + self.end_point) / 2

        angle = math.radians(-line.angle())

        angle1 = angle + math.radians(150)
        angle2 = angle + math.radians(210)

        p1 = QPointF(
            p2.x() + arrow_size * math.cos(angle1),
            p2.y() + arrow_size * math.sin(angle1)
        )

        p3 = QPointF(
            p2.x() + arrow_size * math.cos(angle2),
            p2.y() + arrow_size * math.sin(angle2)
        )

        painter.setBrush(Qt.GlobalColor.black)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(QPolygonF([p2, p1, p3]))
        
    def update_positions(self):
        self.prepareGeometryChange()

        self.start_point = self.start_item.sceneBoundingRect().center()
        self.end_point = self.end_item.sceneBoundingRect().center()

        self.update()

    def contextMenuEvent(self, event):
        self.menu.exec(event.screenPos())

    def delete(self):
        if self.model:
            self.model.remove_edge(
                self.start_item.node_id,
                self.end_item.node_id
            )

        if self.start_item and self in self.start_item.arrows:
            self.start_item.arrows.remove(self)

        if self.end_item and self in self.end_item.arrows:
            self.end_item.arrows.remove(self)

        if self.scene():
            self.scene().removeItem(self)

class GraphicsView(QGraphicsView):
    def __init__(self, scene, model):
        super().__init__(scene)

        self.model = model

        self.node_items = {}
        self.edge_items = {}

        self.menu = QMenu()
        self.add_class_action = self.menu.addAction("Add Class")
        self.add_attr_action = self.menu.addAction("Add Attribute")
        self.add_rel_action = self.menu.addAction("Add Relation")

        self.connection_start = None

        # connect signals
        self.model.node_added.connect(self.on_node_added)
        self.model.node_removed.connect(self.on_node_removed)
        self.model.node_updated.connect(self.on_node_updated)

        self.model.edge_added.connect(self.on_edge_added)
        self.model.edge_removed.connect(self.on_edge_removed)
        self.model.model_reset.connect(self.load_from_model)

        #enable smooth rendering
        self.setRenderHint(self.renderHints())

        # panning
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        self._panning = False
        self._pan_start = None

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self._zoom = 0
        self._zoom_min = -50
        self._zoom_max = 50

        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
         
    def create_node(self, node_type, position):
        text, ok = QInputDialog.getText(self, f"New {node_type}", "Enter name:")
        if not ok or not text:
            return

        self.model.add_node(
            node_type,
            text,
            pos=(position.x(), position.y())
        )

    def contextMenuEvent(self, event):
        
        scene_pos = self.mapToScene(event.pos())        

        item = self.itemAt(event.pos())
        selected_items = self.scene().selectedItems()
        if len(selected_items) >= 1:
            menu = QMenu()
            delete_action = menu.addAction("Delete Selected")
            action = menu.exec(event.globalPos())

            if action == delete_action:
                self.delete_selected()
            return

        if item:
            super().contextMenuEvent(event)
            return

        if item:
            super().contextMenuEvent(event)
            return

        selected = self.menu.exec(event.globalPos())

        if selected == self.add_class_action:
            self.create_node("class", scene_pos)

        elif selected == self.add_attr_action:
            self.create_node("attribute", scene_pos)

        elif selected == self.add_rel_action:
            self.create_node("relation", scene_pos)

    def addClass(self, position):
        text, ok = QInputDialog.getText(self, "New Class", "Enter class name:")
        if not ok or not text:
            return  # user cancelled

        node_id = self.model.add_node(
            "class", 
            text,
            pos=(position.x(), position.y())
        )

        new_class = ClassItem(node_id, self.model, text)
        new_class.setPos(position)
        self.scene().addItem(new_class)

    def addAttribute(self, position):
        text, ok = QInputDialog.getText(self, "New Attribute", "Enter attribute name:")
        if not ok or not text:
            return
        
        node_id = self.model.add_node(
            "attribute", 
            text,
            pos=(position.x(), position.y())
        )

        item = AttributeItem(node_id, self.model, text)
        item.setPos(position)
        self.scene().addItem(item)

    def addRelation(self, position):
        text, ok = QInputDialog.getText(self, "New Relation", "Enter relation name:")
        if not ok or not text:
            return

        node_id = self.model.add_node(
            "relation", 
            text,
            pos=(position.x(), position.y())
        )

        item = RelationItem(node_id, self.model, text)
        item.setPos(position)
        self.scene().addItem(item)

    def get_ontology_item(self, item):
        while item and not isinstance(item, OntologyItem):
            item = item.parentItem()
        return item

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            item = self.get_ontology_item(item)

            if item:
                self._last_press_pos = event.pos()
                super().mousePressEvent(event)
            else:
                self._panning = True
                self._pan_start = event.pos()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                return

        else:
                super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:

            if getattr(self, "_panning", False):
                self._panning = False
                self.setCursor(Qt.CursorShape.ArrowCursor)
                return

            release_pos = event.pos()
            press_pos = getattr(self, "_last_press_pos", None)

            if press_pos and (release_pos - press_pos).manhattanLength() < 5:
                item = self.itemAt(release_pos)
                item = self.get_ontology_item(item)
                if item:
                    self.handle_connection(item)

        super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):

        if self._panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()

            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            return

        super().mouseMoveEvent(event)

    def handle_connection(self, item):
        if self.connection_start is None:
            self.connection_start = item
            self.connection_start.setSelected(True)
            return

        if self.connection_start == item:
            self.connection_start.setSelected(False)
            self.connection_start = None
            return

        if not self.model.has_edge(self.connection_start.node_id, item.node_id):
            self.model.add_edge(
                self.connection_start.node_id,
                item.node_id
            )

        self.connection_start.setSelected(False)
        self.connection_start = None

    def create_item(self, node_id, data):
        node_type = data["type"]
        label = data["label"]

        if node_type == "class":
            return ClassItem(node_id, self.model, label)

        elif node_type == "attribute":
            return AttributeItem(node_id, self.model, label)

        elif node_type == "relation":
            return RelationItem(node_id, self.model, label)        

    def load_from_model(self):
        self.scene().clear()
        self.node_items.clear()
        self.edge_items.clear()

        for node_id, _ in self.model.get_all_nodes():
            self.on_node_added(node_id)

        for src, tgt in self.model.get_all_edges():
            self.on_edge_added(src, tgt)

    def on_node_added(self, node_id):
        
        data = self.model.get_node(node_id)

        item = self.create_item(node_id, data)

        pos = data.get("pos", (0, 0))
        if(pos is None):
            pos = (0, 0)
        item.setPos(pos[0], pos[1])
        self.scene().addItem(item)        
        self.node_items[node_id] = item

    def on_node_removed(self, node_id):
        if node_id in self.node_items:
            item = self.node_items.pop(node_id)

            # remove arrows attached
            for arrow in item.arrows[:]:
                arrow.delete()

            self.scene().removeItem(item)

    def on_node_updated(self, node_id):
        item = self.node_items.get(node_id)
        data = self.model.get_node(node_id)

        if not item or not data:
            return

        # update label
        label = data.get("label", "")
        item.text.setPlainText(label)
        item.center_text()

        # update position 
        pos = data.get("pos")
        if pos:
            item.setPos(pos[0], pos[1])

    def on_edge_added(self, source_id, target_id):
        start_item = self.node_items.get(source_id)
        end_item = self.node_items.get(target_id)

        if not start_item or not end_item:
            return

        arrow = Arrow(start_item, end_item, self.model)
        self.scene().addItem(arrow)
        self.edge_items[(source_id, target_id)] = arrow

    def on_edge_removed(self, src, tgt):
        key = (src, tgt)
        rev_key = (tgt, src)

        arrow = self.edge_items.pop(key, None) or self.edge_items.pop(rev_key, None)

        if arrow:
            if arrow.start_item and arrow in arrow.start_item.arrows:
                arrow.start_item.arrows.remove(arrow)

            if arrow.end_item and arrow in arrow.end_item.arrows:
                arrow.end_item.arrows.remove(arrow)

            if arrow.scene():
                self.scene().removeItem(arrow)

    

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0 and self._zoom < self._zoom_max:
            factor = 1.15
            self._zoom += 1
        elif event.angleDelta().y() < 0 and self._zoom > self._zoom_min:
            factor = 1 / 1.15
            self._zoom -= 1
        else:
            return

        self.scale(factor, factor)

    def delete_selected(self):
        selected_items = self.scene().selectedItems()

        for item in selected_items:
            item = self.get_ontology_item(item)
            if isinstance(item, OntologyItem):
                if item.model and item.node_id is not None:
                    self.model.remove_node(item.node_id)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected()
            return
        super().keyPressEvent(event)