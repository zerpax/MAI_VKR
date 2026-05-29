from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QGraphicsScene, QFileDialog, QTabWidget, QPushButton, QDialog, QVBoxLayout, QTextEdit
)
from analysis import OntologyAnalyzer
import visual, structure, table
import sys


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ontology Editor")
        self.setGeometry(100, 100, 800, 600)

        self.model = structure.OntologyModel()
        self.scene = QGraphicsScene()
        self.view = visual.GraphicsView(self.scene, self.model)

        self.setCentralWidget(self.view)

        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")

        save_action = file_menu.addAction("Save")
        load_action = file_menu.addAction("Load")

        save_action.triggered.connect(self.save_file)
        load_action.triggered.connect(self.load_file)

        self.tabs = QTabWidget()

        self.view = visual.GraphicsView(self.scene, self.model)
        self.table_view = table.TableView(self.model)

        self.tabs.addTab(self.view, "Graph")
        self.tabs.addTab(self.table_view, "Table")

        self.setCentralWidget(self.tabs)

        self.tabs.currentChanged.connect(self.on_tab_changed)

        self.scene.setSceneRect(-10000, -10000, 20000, 20000)

        analysis_menu = menu_bar.addMenu("Analysis")

        report_action = analysis_menu.addAction("Show Report")
        report_action.triggered.connect(self.show_report)
    def save_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save File", "", "SQLite Database (*.db);;All Files (*)")
        if filename:
            self.model.save_to_file(filename)
    
    def load_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open File", "", "SQLite Database (*.db);;All Files (*)")
        if filename:
            self.model.load_from_file(filename)
            self.view.load_from_model()

    def on_tab_changed(self, index):
        if index == 0:  
            # self.model.auto_layout_near_neighbors()
            pass

    def show_report(self):
        analyzer = OntologyAnalyzer(self.model)
        text = analyzer.generate_text_report()

        dialog = QDialog(self)
        dialog.setWindowTitle("Отчёт")

        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(text)

        layout.addWidget(text_edit)
        dialog.setLayout(layout)

        dialog.resize(600, 400)
        dialog.exec()

def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()