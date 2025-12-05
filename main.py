import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLineEdit, QComboBox, QTextEdit, QFileDialog,
    QSpinBox, QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage, QClipboard
from PyQt5.QtCore import Qt


# ------------------------------------------------------------
# MAIN WINDOW WITH STACKED PAGES
# ------------------------------------------------------------

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Question Paper Builder - FalconE Tools")
        self.resize(900, 600)

        self.stack = QStackedWidget()

        # Pages
        self.page1 = StartPage(self)
        self.page2 = SectionPage(self)
        self.page3 = QuestionBuilderPage(self)

        # Add pages to stack
        self.stack.addWidget(self.page1)
        self.stack.addWidget(self.page2)
        self.stack.addWidget(self.page3)

        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)

    def go_to_page(self, index):
        self.stack.setCurrentIndex(index)


# ------------------------------------------------------------
# PAGE 1 — SCHOOL / EXAM / CLASS
# ------------------------------------------------------------

class StartPage(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        layout = QVBoxLayout()

        title = QLabel("Enter Basic Details")
        title.setStyleSheet("font-size: 26px; font-weight: bold;")
        layout.addWidget(title)

        self.school = QComboBox()
        self.school.addItems(["St. Vincent Pallotti", "National Public School", "Dummy School"])
        layout.addWidget(QLabel("School:"))
        layout.addWidget(self.school)

        self.exam = QComboBox()
        self.exam.addItems(["Unit Test I", "Unit Test II", "Mid Term", "Final Exam"])
        layout.addWidget(QLabel("Exam Type:"))
        layout.addWidget(self.exam)

        self.class_input = QLineEdit()
        self.class_input.setPlaceholderText("Enter class (e.g., 5A, 7, 10)")
        layout.addWidget(QLabel("Class:"))
        layout.addWidget(self.class_input)

        btn = QPushButton("Next → Section Page")
        btn.clicked.connect(self.go_next)
        layout.addWidget(btn)

        self.setLayout(layout)

    def go_next(self):
        if self.class_input.text().strip() == "":
            QMessageBox.warning(self, "Error", "Please enter the Class.")
            return
        self.main.go_to_page(1)


# ------------------------------------------------------------
# PAGE 2 — SELECT SECTION
# ------------------------------------------------------------

class SectionPage(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        layout = QVBoxLayout()
        title = QLabel("Choose Section")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        self.section = QComboBox()
        self.section.addItems(["Section A", "Section B", "Section C"])
        layout.addWidget(self.section)

        btn = QPushButton("Next → Build Questions")
        btn.clicked.connect(self.go_next)
        layout.addWidget(btn)

        self.setLayout(layout)

    def go_next(self):
        self.main.go_to_page(2)


# ------------------------------------------------------------
# PAGE 3 — QUESTION BUILDER
# ------------------------------------------------------------

class QuestionBuilderPage(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main

        layout = QVBoxLayout()

        title = QLabel("Build Question")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        # Question Type
        layout.addWidget(QLabel("Question Type:"))
        self.qtype = QComboBox()
        self.qtype.addItems(["General", "MCQ", "Match The Following"])
        self.qtype.currentIndexChanged.connect(self.update_form)
        layout.addWidget(self.qtype)

        # Question Input Fields
        self.question_number = QLineEdit()
        self.question_number.setPlaceholderText("Question Number (1,2,3...)")

        self.part_number = QLineEdit()
        self.part_number.setPlaceholderText("Part Number (I, II, III)")

        self.part_heading = QLineEdit()
        self.part_heading.setPlaceholderText("Part Heading (Fill in the blanks...)")

        layout.addWidget(self.question_number)
        layout.addWidget(self.part_number)
        layout.addWidget(self.part_heading)

        # ---- Dynamic Forms ----
        self.dynamic_area = QVBoxLayout()
        layout.addLayout(self.dynamic_area)

        # Insert Table Button
        table_btn = QPushButton("Insert Table")
        table_btn.clicked.connect(self.insert_table_dialog)
        layout.addWidget(table_btn)

        # Insert Image Button
        img_btn = QPushButton("Insert Image")
        img_btn.clicked.connect(self.insert_image)
        layout.addWidget(img_btn)

        # Display area for images
        self.image_label = QLabel()
        self.image_label.setFixedHeight(200)
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)

        self.setLayout(layout)

        # Build initial form
        self.update_form()

    # --------------------------------------------------------
    # DYNAMIC FORM HANDLER
    # --------------------------------------------------------
    def clear_dynamic_form(self):
        for i in reversed(range(self.dynamic_area.count())):
            widget = self.dynamic_area.itemAt(i).widget()
            if widget:
                widget.deleteLater()

    def update_form(self):
        self.clear_dynamic_form()

        qtype = self.qtype.currentText()

        if qtype == "General":
            txt = QTextEdit()
            txt.setPlaceholderText("Enter question text...")
            self.dynamic_area.addWidget(txt)

        elif qtype == "MCQ":
            self.options = []
            for opt in ["Option A", "Option B", "Option C", "Option D"]:
                box = QLineEdit()
                box.setPlaceholderText(opt)
                self.options.append(box)
                self.dynamic_area.addWidget(box)

        elif qtype == "Match The Following":
            label = QLabel("Enter pairs (Left Side = Right Side):")
            self.dynamic_area.addWidget(label)

            self.match_box = QTextEdit()
            self.match_box.setPlaceholderText("1. Apple = Fruit\n2. Car = Vehicle")
            self.dynamic_area.addWidget(self.match_box)

    # --------------------------------------------------------
    # ADD TABLE
    # --------------------------------------------------------
    def insert_table_dialog(self):
        rows, cols = 3, 3

        table = QTableWidget(rows, cols)
        table.setMaximumHeight(200)

        for r in range(rows):
            for c in range(cols):
                table.setItem(r, c, QTableWidgetItem(""))

        self.dynamic_area.addWidget(QLabel("Inserted Table:"))
        self.dynamic_area.addWidget(table)

    # --------------------------------------------------------
    # IMAGE INSERTION
    # --------------------------------------------------------
    def insert_image(self):
        choice = QMessageBox.question(
            self, "Insert Image",
            "Insert from clipboard?",
            QMessageBox.Yes | QMessageBox.No
        )

        if choice == QMessageBox.Yes:
            clipboard = QApplication.clipboard()
            img = clipboard.image()
            if img.isNull():
                QMessageBox.warning(self, "Error", "No image found in clipboard.")
                return
            self.image_label.setPixmap(QPixmap.fromImage(img).scaled(200, 200, Qt.KeepAspectRatio))

        else:
            path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg)")
            if path:
                self.image_label.setPixmap(QPixmap(path).scaled(200, 200, Qt.KeepAspectRatio))


# ------------------------------------------------------------
# RUN APP
# ------------------------------------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
