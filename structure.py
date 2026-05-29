from PyQt6.QtCore import QObject, pyqtSignal
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
import networkx as nx
import json
import math
import random
import shutil

Base = declarative_base()


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True)
    type = Column(String)
    label = Column(String)
    x = Column(Float, nullable=True)
    y = Column(Float, nullable=True)


class Edge(Base):
    __tablename__ = "edges"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("nodes.id"))
    target_id = Column(Integer, ForeignKey("nodes.id"))




class OntologyModel(QObject):
    node_added = pyqtSignal(int)
    node_removed = pyqtSignal(int)
    node_updated = pyqtSignal(int)

    edge_added = pyqtSignal(int, int)
    edge_removed = pyqtSignal(int, int)
    
    model_reset = pyqtSignal()

    def __init__(self, db_path=None):
        super().__init__()

        self.db_path = None 
        if db_path is None:
            self.engine = create_engine("sqlite:///:memory:")
        else:
            self.engine = create_engine(f"sqlite:///{db_path}")

        Base.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()



    def add_node(self, node_type, label, pos=None):
        node = Node(type=node_type, label=label)

        if pos:
            node.x, node.y = pos

        self.session.add(node)
        self.session.commit()

        self.node_added.emit(node.id)
        return node.id

    def remove_node(self, node_id):
        node = self.session.get(Node, node_id)
        if not node:
            return


        if node.type == "class":
            neighbors = self.get_neighbors(node_id)

            for n_id in neighbors:
                n = self.session.get(Node, n_id)
                if not n:
                    continue

                if n.type in ("relation", "attribute"):
                    self.remove_node(n_id)


        self.session.query(Edge).filter(
            (Edge.source_id == node_id) |
            (Edge.target_id == node_id)
        ).delete()

        self.session.delete(node)
        self.session.commit()

        self.node_removed.emit(node_id)



    def add_edge(self, source_id, target_id, relation_type=None):
        if self.has_edge(source_id, target_id):
            return

        edge = Edge(source_id=source_id, target_id=target_id)
        self.session.add(edge)
        self.session.commit()

        self.edge_added.emit(source_id, target_id)

    def remove_edge(self, source_id, target_id):
        edge = self.session.query(Edge).filter(
            ((Edge.source_id == source_id) & (Edge.target_id == target_id)) |
            ((Edge.source_id == target_id) & (Edge.target_id == source_id))
        ).first()

        if not edge:
            return

        self.session.delete(edge)
        self.session.commit()

        self.edge_removed.emit(source_id, target_id)


        for node_id in (source_id, target_id):
            node = self.session.get(Node, node_id)
            if not node:
                continue

            if node.type == "relation":
                neighbors = self.get_neighbors(node_id)

                class_count = sum(
                    1 for n in neighbors
                    if self.get_node(n)["type"] == "class"
                )

                if class_count < 2:
                    self.remove_node(node_id)


    def get_all_nodes(self):
        nodes = self.session.query(Node).all()

        result = []
        for n in nodes:
            result.append((n.id, {
                "type": n.type,
                "label": n.label,
                "pos": (n.x, n.y) if n.x is not None else None
            }))
        return result

    def get_node(self, node_id):
        n = self.session.get(Node, node_id)
        if not n:
            return None

        return {
            "type": n.type,
            "label": n.label,
            "pos": (n.x, n.y) if n.x is not None else None
        }

    def get_all_edges(self):
        edges = self.session.query(Edge).all()
        return [(e.source_id, e.target_id) for e in edges]

    def has_edge(self, source_id, target_id):
        return self.session.query(Edge).filter(
            ((Edge.source_id == source_id) & (Edge.target_id == target_id)) |
            ((Edge.source_id == target_id) & (Edge.target_id == source_id))
        ).first() is not None

    def get_neighbors(self, node_id):
        edges = self.session.query(Edge).filter(
            (Edge.source_id == node_id) |
            (Edge.target_id == node_id)
        ).all()

        neighbors = []
        for e in edges:
            if e.source_id == node_id:
                neighbors.append(e.target_id)
            else:
                neighbors.append(e.source_id)

        return neighbors

    def has_node(self, node_id):
        return self.session.get(Node, node_id) is not None



    def update_node(self, node_id, **kwargs):
        node = self.session.get(Node, node_id)
        if not node:
            return False

        for k, v in kwargs.items():
            if k == "label":
                node.label = v

        self.session.commit()
        self.node_updated.emit(node_id)
        return True

    def set_label(self, node_id, new_label):
        return self.update_node(node_id, label=new_label)

    def set_position(self, node_id, x, y):
        node = self.session.get(Node, node_id)
        if not node:
            return False

        node.x = x
        node.y = y
        self.session.commit()
        return True


    def save_to_file(self, file_path):
        self.session.commit()

        dest_engine = create_engine(f"sqlite:///{file_path}")
        Base.metadata.create_all(dest_engine)

        with self.engine.connect() as source_conn:
            with dest_engine.connect() as dest_conn:
                source_db = source_conn.connection.dbapi_connection
                dest_db = dest_conn.connection.dbapi_connection
                
                source_db.backup(dest_db)
        
        self.db_path = file_path

    def load_from_file(self, db_path):
        self.session.close()
        self.engine.dispose()

        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        
        Base.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self._emit_full_reload()    
    


    def _build_nx_graph(self):
        g = nx.Graph()
        for node_id, _ in self.get_all_nodes():
            g.add_node(node_id)
        for s, t in self.get_all_edges():
            g.add_edge(s, t)
        return g

    def auto_layout(self):
        nodes = self.get_all_nodes()
        if not nodes:
            return

        g = self._build_nx_graph()

        pos = {}
        fixed = []

        for node_id, data in nodes:
            node_pos = data.get("pos")

            if node_pos is not None and node_pos != (0, 0):
                x, y = node_pos
                pos[node_id] = (x / 500, y / 500)
                fixed.append(node_id)

        new_pos = nx.spring_layout(
            g,
            pos=pos if pos else None,
            fixed=fixed if fixed else None,
            seed=42
        )

        scale = 500

        for node_id, (x, y) in new_pos.items():
            if node_id not in pos:
                self.set_position(node_id, x * scale, y * scale)
                self.node_updated.emit(node_id)

    def place_near_neighbors(self, node_id):
        neighbors = self.get_neighbors(node_id)

        if not neighbors:
            self.set_position(
                node_id,
                random.randint(-100, 100),
                random.randint(-100, 100)
            )
            self.node_updated.emit(node_id)
            return

        positions = []
        for n in neighbors:
            data = self.get_node(n)
            if data and data.get("pos"):
                positions.append(data["pos"])

        if not positions:
            self.set_position(node_id, 0, 0)
            self.node_updated.emit(node_id)
            return

        avg_x = sum(p[0] for p in positions) / len(positions)
        avg_y = sum(p[1] for p in positions) / len(positions)

        angle = random.uniform(0, 2 * math.pi)
        radius = 500

        x = avg_x + radius * math.cos(angle)
        y = avg_y + radius * math.sin(angle)

        self.set_position(node_id, x, y)
        self.node_updated.emit(node_id)

    def auto_layout_near_neighbors(self):
        nodes = self.get_all_nodes()
        
        if not nodes:
            return

        for node_id, data in nodes:
            if data.get("pos") is None:
                self.place_near_neighbors(node_id)

    def load_database(self, db_path):
        self.session.close()

        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self._emit_full_reload()

    def _emit_full_reload(self):
        self.model_reset.emit()