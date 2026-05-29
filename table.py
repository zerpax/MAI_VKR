from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QInputDialog, QTableView, 
    QDialog, QListWidget, QLineEdit, QListWidgetItem
)


class ClassSelectionDialog(QDialog):
    def __init__(self, model, exclude_id=None):
        super().__init__()

        self.model = model
        self.selected_id = None

        self.setWindowTitle("Select Target Class")

        self.layout = QVBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search class...")
        self.layout.addWidget(self.search)

        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)

        self.setLayout(self.layout)

        self.all_classes = [
            (nid, data["label"])
            for nid, data in self.model.get_all_nodes()
            if data.get("type") == "class" and nid != exclude_id
        ]

        self.populate_list(self.all_classes)

 
        self.search.textChanged.connect(self.filter_list)
        self.list_widget.itemDoubleClicked.connect(self.select_item)

    def populate_list(self, items):
        self.list_widget.clear()

        for nid, label in items:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, nid)
            self.list_widget.addItem(item)

    def filter_list(self, text):
        text = text.lower()

        filtered = [
            (nid, label)
            for nid, label in self.all_classes
            if text in label.lower()
        ]

        self.populate_list(filtered)

    def select_item(self, item):
        self.selected_id = item.data(Qt.ItemDataRole.UserRole)
        self.accept()



class ClassesTableModel(QAbstractTableModel):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.pending_changes = {}  

    def flags(self, index):
        return (
            Qt.ItemFlag.ItemIsSelectable |
            Qt.ItemFlag.ItemIsEnabled |
            Qt.ItemFlag.ItemIsEditable
        )
    
    def get_classes(self):
        return [
            (node_id, data)
            for node_id, data in self.model.get_all_nodes()
            if data.get("type") == "class"
        ]

    def rowCount(self, parent=None):
        return len(self.get_classes())

    def columnCount(self, parent=None):
        return 1 

    def data(self, index, role):
        if not index.isValid():
            return None

        nodes = self.get_classes()
        node_id, data = nodes[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            label = data.get("label")
            return self.pending_changes.get(node_id, label)

        if role == Qt.ItemDataRole.UserRole:
            return node_id

        return None

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return ["Label"][section]

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole:
            nodes = self.get_classes()
            node_id, _ = nodes[index.row()]

            self.pending_changes[node_id] = value
            self.dataChanged.emit(index, index)
            return True
        return False
    
    def apply_changes(self):
        for node_id, new_label in self.pending_changes.items():
            self.model.set_label(node_id, new_label)
        self.pending_changes.clear()

class AttributesTableModel(QAbstractTableModel):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.current_node_id = None
        self.pending_changes = {}  

    def set_node(self, node_id):
        self.current_node_id = node_id
        self.layoutChanged.emit()

    def get_attributes(self):
        if self.current_node_id is None:
            return []

        neighbors = self.model.get_neighbors(self.current_node_id)

        return [
            (n, self.model.get_node(n).get("label", ""))
            for n in neighbors
            if self.model.get_node(n).get("type") == "attribute"
        ]

    def rowCount(self, parent=None):
        return len(self.get_attributes())

    def columnCount(self, parent=None):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None

        attr_id, label = self.get_attributes()[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            return self.pending_changes.get(attr_id, label)

        if role == Qt.ItemDataRole.UserRole:
            return attr_id

        return None

    def flags(self, index):
        return (
            Qt.ItemFlag.ItemIsSelectable |
            Qt.ItemFlag.ItemIsEnabled |
            Qt.ItemFlag.ItemIsEditable
        )

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole:
            attr_id, _ = self.get_attributes()[index.row()]
            self.pending_changes[attr_id] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def apply_changes(self):
        for attr_id, new_label in self.pending_changes.items():
            self.model.set_label(attr_id, new_label)
        self.pending_changes.clear()

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return "Attributes"

class RelationsTableModel(QAbstractTableModel):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.current_node_id = None
        self.pending_changes = {}  

    def set_node(self, node_id):
        self.current_node_id = node_id
        self.layoutChanged.emit()

    def get_relations(self):
        if self.current_node_id is None:
            return []

        neighbors = self.model.get_neighbors(self.current_node_id)
        result = []

        for n in neighbors:
            data = self.model.get_node(n)

            if data.get("type") == "relation":
                rel_label = data.get("label", "")

                for target in self.model.get_neighbors(n):
                    if target == self.current_node_id:
                        continue

                    target_data = self.model.get_node(target)
                    if target_data.get("type") == "class":
                        result.append((n, rel_label, target, target_data.get("label", "")))

        return result

    def rowCount(self, parent=None):
        return len(self.get_relations())

    def columnCount(self, parent=None):
        return 2

    def data(self, index, role):
        if not index.isValid():
            return None

        rel_id, rel_label, target_id, target_label = self.get_relations()[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return self.pending_changes.get(rel_id, rel_label)
            elif index.column() == 1:
                return target_label

        if role == Qt.ItemDataRole.UserRole:
            return rel_id

        return None

    def flags(self, index):
        base_flags = (
            Qt.ItemFlag.ItemIsSelectable |
            Qt.ItemFlag.ItemIsEnabled
        )

        if index.column() == 0:
            return base_flags | Qt.ItemFlag.ItemIsEditable

        return base_flags

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole and index.column() == 0:
            rel_id, _, _, _ = self.get_relations()[index.row()]
            self.pending_changes[rel_id] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def apply_changes(self):
        for rel_id, new_label in self.pending_changes.items():
            self.model.set_label(rel_id, new_label)
        self.pending_changes.clear()

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return ["Relation", "Target Class"][section]



class TableView(QWidget):
    def __init__(self, model):
        super().__init__()

        self.model = model

        self.nodes_view = QTableView()
        self.attributes_view = QTableView()
        self.relations_view = QTableView()

        self.nodes_model = ClassesTableModel(model)
        self.attributes_model = AttributesTableModel(model)
        self.relations_model = RelationsTableModel(model)

        self.nodes_view.setModel(self.nodes_model)
        self.attributes_view.setModel(self.attributes_model)
        self.relations_view.setModel(self.relations_model)

        self.nodes_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.nodes_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.nodes_view.selectionModel().selectionChanged.connect(self.on_node_selected)

        self.attributes_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.attributes_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.attributes_view.selectionModel().selectionChanged.connect(self.on_attribute_selected)

        self.relations_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.relations_view.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.relations_view.selectionModel().selectionChanged.connect(self.on_relation_selected)

        self.add_class_btn = QPushButton("Add Class")
        self.delete_class_btn = QPushButton("Delete Class")

        self.add_attr_btn = QPushButton("Add Attribute")
        self.delete_attr_btn = QPushButton("Delete Attribute")
        
        self.add_rel_btn = QPushButton("Add Relation")
        self.delete_rel_btn = QPushButton("Delete Relation")

        self.apply_changes_btn = QPushButton("Apply Changes")
        
        self.delete_class_btn.setEnabled(False)
        self.add_attr_btn.setEnabled(False)
        self.delete_attr_btn.setEnabled(False)
        self.add_rel_btn.setEnabled(False)
        self.delete_rel_btn.setEnabled(False)

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Classes"))
        left_layout.addWidget(self.nodes_view)
        left_layout.addWidget(self.add_class_btn)
        left_layout.addWidget(self.delete_class_btn)
        left_layout.addWidget(self.apply_changes_btn)


        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Attributes"))
        right_layout.addWidget(self.attributes_view)

        attr_buttons = QHBoxLayout()
        attr_buttons.addWidget(self.add_attr_btn)
        attr_buttons.addWidget(self.delete_attr_btn)
        right_layout.addLayout(attr_buttons)

        right_layout.addWidget(QLabel("Relations"))
        right_layout.addWidget(self.relations_view)

        rel_buttons = QHBoxLayout()
        rel_buttons.addWidget(self.add_rel_btn)
        rel_buttons.addWidget(self.delete_rel_btn)
        right_layout.addLayout(rel_buttons)

        layout = QHBoxLayout()
        layout.addLayout(left_layout)
        layout.addLayout(right_layout)

        self.setLayout(layout)

        self.selected_node_id = None
        self.selected_attribute_id = None
        self.selected_relation_id = None 

        self.add_class_btn.clicked.connect(self.add_class)
        self.delete_class_btn.clicked.connect(self.delete_class)
        self.add_attr_btn.clicked.connect(self.add_attribute)
        self.delete_attr_btn.clicked.connect(self.delete_attribute)
        self.add_rel_btn.clicked.connect(self.add_relation)
        self.delete_rel_btn.clicked.connect(self.delete_relation)

        self.model.node_added.connect(self.refresh)
        self.model.node_removed.connect(self.refresh)
        self.model.node_updated.connect(self.refresh)
        self.model.edge_added.connect(self.refresh)
        self.model.edge_removed.connect(self.refresh)

        self.model.model_reset.connect(self.refresh)

        self.apply_changes_btn.clicked.connect(self.apply_changes)

        


    def on_node_selected(self, selected, deselected):
        indexes = self.nodes_view.selectionModel().selectedRows()

        if not indexes:
            self.selected_node_id = None
            self.delete_class_btn.setEnabled(False)
            self.add_attr_btn.setEnabled(False)
            self.attributes_model.set_node(None)
            self.relations_model.set_node(None)
            return

        index = indexes[0]
        node_id = index.data(Qt.ItemDataRole.UserRole)

        self.selected_node_id = node_id

        self.delete_class_btn.setEnabled(True)
        self.add_attr_btn.setEnabled(True)
        self.add_rel_btn.setEnabled(True)

        self.attributes_model.set_node(node_id)
        self.relations_model.set_node(node_id)

    def on_attribute_selected(self, selected, deselected):
        indexes = self.attributes_view.selectionModel().selectedRows()

        if not indexes:
            self.selected_attribute_id = None
            self.delete_attr_btn.setEnabled(False)
            return

        index = indexes[0]
        self.selected_attribute_id = index.data(Qt.ItemDataRole.UserRole)

        self.delete_attr_btn.setEnabled(True)

    def on_relation_selected(self, selected, deselected):
        indexes = self.relations_view.selectionModel().selectedRows()

        if not indexes:
            self.selected_relation_id = None
            self.delete_rel_btn.setEnabled(False)
            return

        index = indexes[0]
        self.selected_relation_id = index.data(Qt.ItemDataRole.UserRole)

        self.delete_rel_btn.setEnabled(True)


    def add_class(self):
        text, ok = QInputDialog.getText(self, "New Class", "Enter class name:")
        if not ok or not text:
            return

        self.model.add_node("class", text)
        

    def delete_class(self):
        if self.selected_node_id is None:
            return

        self.model.remove_node(self.selected_node_id)

        self.attributes_model.set_node(None)
        self.relations_model.set_node(None)
        
        self.selected_node_id = None

        self.nodes_view.selectionModel().clearSelection()



    def add_attribute(self):
        if self.selected_node_id is None:
            return

        text, ok = QInputDialog.getText(self, "New Attribute", "Enter attribute name:")
        if not ok or not text:
            return

        attr_id = self.model.add_node("attribute", text)
        self.model.add_edge(self.selected_node_id, attr_id)

    def delete_attribute(self):
        if self.selected_attribute_id is None:
            return

        self.model.remove_node(self.selected_attribute_id)
        self.selected_attribute_id = None

        self.delete_attr_btn.setEnabled(False)


    def add_relation(self):
        if self.selected_node_id is None:
            return


        dialog = ClassSelectionDialog(self.model, exclude_id=self.selected_node_id)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        target_id = dialog.selected_id

        if target_id is None:
            return


        rel_name, ok = QInputDialog.getText(self, "Relation Name", "Enter relation name:")
        if not ok or not rel_name:
            return


        rel_id = self.model.add_node("relation", rel_name)

        


        self.model.add_edge(self.selected_node_id, rel_id)
        self.model.add_edge(rel_id, target_id)


    def delete_relation(self):
        if not hasattr(self, "selected_relation_id") or self.selected_relation_id is None:
            return

        self.model.remove_node(self.selected_relation_id)

        self.selected_relation_id = None


        self.delete_rel_btn.setEnabled(False)




        

    def refresh(self):
        if self.selected_node_id is not None:
            if self.model.get_node(self.selected_node_id) is None:
                self.selected_node_id = None

                self.attributes_model.set_node(None)
                self.relations_model.set_node(None)

                self.delete_class_btn.setEnabled(False)
                self.add_attr_btn.setEnabled(False)
                self.add_rel_btn.setEnabled(False)


        self.nodes_model.layoutChanged.emit()
        self.attributes_model.layoutChanged.emit()
        self.relations_model.layoutChanged.emit()

    def apply_changes(self):
        self.nodes_model.apply_changes()
        self.attributes_model.apply_changes()
        self.relations_model.apply_changes()