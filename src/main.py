import os
import shutil
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database import SessionLocal, engine
from models import Base, Category, Mod

# 建立資料表
Base.metadata.create_all(bind=engine)


class ModDialog(QDialog):
    def __init__(self, parent=None, mod=None):
        super().__init__(parent)
        self.mod = mod
        self.setWindowTitle("新增/編輯模組")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # 模組名稱
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("模組名稱:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 檔案選擇
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("模組檔案:"))
        self.filename_edit = QLineEdit()
        self.filename_edit.setReadOnly(True)
        file_layout.addWidget(self.filename_edit)
        browse_button = QPushButton("瀏覽...")
        browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_button)
        layout.addLayout(file_layout)

        # 分類
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("分類:"))
        self.category_combo = QComboBox()
        self.load_categories()
        category_layout.addWidget(self.category_combo)
        manage_category_button = QPushButton("管理分類...")
        manage_category_button.clicked.connect(self.manage_categories)
        category_layout.addWidget(manage_category_button)
        layout.addLayout(category_layout)

        # 選項
        self.is_translated = QCheckBox("已漢化")
        self.client_required = QCheckBox("需要客戶端")
        self.server_required = QCheckBox("需要伺服器")
        layout.addWidget(self.is_translated)
        layout.addWidget(self.client_required)
        layout.addWidget(self.server_required)

        # 前置模組
        dependency_layout = QVBoxLayout()
        dependency_layout.addWidget(QLabel("前置模組:"))
        self.dependency_list = QListWidget()
        self.load_mods()
        dependency_layout.addWidget(self.dependency_list)
        layout.addLayout(dependency_layout)

        # 按鈕
        button_layout = QHBoxLayout()
        save_button = QPushButton("儲存")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        if self.mod:
            self.name_edit.setText(self.mod.name)
            self.filename_edit.setText(self.mod.filename)
            self.is_translated.setChecked(self.mod.is_translated)
            self.client_required.setChecked(self.mod.client_required)
            self.server_required.setChecked(self.mod.server_required)

            # 設定分類
            if self.mod.categories:
                category_name = self.mod.categories[0].name
                index = self.category_combo.findText(category_name)
                if index >= 0:
                    self.category_combo.setCurrentIndex(index)

            # 設定前置模組
            for dependency in self.mod.dependencies:
                items = self.dependency_list.findItems(dependency.name, Qt.MatchFlag.MatchExactly)
                if items:
                    items[0].setSelected(True)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "選擇模組檔案", "", "Minecraft 模組檔案 (*.jar);;所有檔案 (*.*)"
        )
        if file_path:
            # 取得檔案名稱
            filename = os.path.basename(file_path)
            self.filename_edit.setText(filename)

            # 設定模組名稱（如果尚未設定）
            if not self.name_edit.text():
                # 移除副檔名並將底線替換為空格
                name = os.path.splitext(filename)[0].replace("_", " ")
                self.name_edit.setText(name)

    def load_categories(self):
        with SessionLocal() as db:
            categories = db.query(Category).all()
            self.category_combo.clear()
            for category in categories:
                self.category_combo.addItem(category.name)

    def load_mods(self):
        with SessionLocal() as db:
            mods = db.query(Mod).all()
            self.dependency_list.clear()
            for mod in mods:
                if mod != self.mod:
                    self.dependency_list.addItem(mod.name)

    def manage_categories(self):
        dialog = CategoryManagerDialog(self)
        if dialog.exec():
            self.load_categories()  # 重新載入分類列表

    def accept(self):
        name = self.name_edit.text()
        filename = self.filename_edit.text()

        if not name or not filename:
            QMessageBox.warning(self, "錯誤", "模組名稱和檔案名稱不能為空")
            return

        # 建立 mods 目錄（如果不存在）
        mods_dir = Path("mods")
        mods_dir.mkdir(exist_ok=True)

        # 複製檔案到 mods 目錄
        source_path = QFileDialog.getOpenFileName(
            self, "選擇模組檔案", "", "Minecraft 模組檔案 (*.jar);;所有檔案 (*.*)"
        )[0]

        if not source_path:
            QMessageBox.warning(self, "錯誤", "請選擇模組檔案")
            return

        target_path = mods_dir / filename
        try:
            shutil.copy2(source_path, target_path)
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"複製檔案時發生錯誤：{str(e)}")
            return

        with SessionLocal() as db:
            if self.mod:
                # 更新現有模組
                self.mod.name = name
                self.mod.filename = filename
                self.mod.is_translated = self.is_translated.isChecked()
                self.mod.client_required = self.client_required.isChecked()
                self.mod.server_required = self.server_required.isChecked()

                # 更新分類
                selected_category = self.category_combo.currentText()
                if selected_category:
                    category = db.query(Category).filter(Category.name == selected_category).first()
                    if category:
                        self.mod.categories = [category]

                # 更新前置模組
                selected_items = self.dependency_list.selectedItems()
                dependencies = []
                for item in selected_items:
                    dependency = db.query(Mod).filter(Mod.name == item.text()).first()
                    if dependency:
                        dependencies.append(dependency)
                self.mod.dependencies = dependencies
            else:
                # 新增模組
                mod = Mod(
                    name=name,
                    filename=filename,
                    is_translated=self.is_translated.isChecked(),
                    client_required=self.client_required.isChecked(),
                    server_required=self.server_required.isChecked(),
                )

                # 設定分類
                selected_category = self.category_combo.currentText()
                if selected_category:
                    category = db.query(Category).filter(Category.name == selected_category).first()
                    if category:
                        mod.categories = [category]

                # 設定前置模組
                selected_items = self.dependency_list.selectedItems()
                dependencies = []
                for item in selected_items:
                    dependency = db.query(Mod).filter(Mod.name == item.text()).first()
                    if dependency:
                        dependencies.append(dependency)
                mod.dependencies = dependencies

                db.add(mod)

            db.commit()
            super().accept()


class CategoryDialog(QDialog):
    def __init__(self, parent=None, category=None):
        super().__init__(parent)
        self.category = category
        self.setWindowTitle("新增分類" if not category else "編輯分類")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # 分類名稱
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("分類名稱:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 按鈕
        button_layout = QHBoxLayout()
        save_button = QPushButton("儲存")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        if self.category:
            self.name_edit.setText(self.category.name)

    def get_category_name(self):
        return self.name_edit.text()


class CategoryManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("管理分類")
        self.setup_ui()
        self.load_categories()

    def setup_ui(self):
        layout = QVBoxLayout()

        # 分類列表
        self.category_list = QListWidget()
        layout.addWidget(self.category_list)

        # 按鈕
        button_layout = QHBoxLayout()
        add_button = QPushButton("新增")
        add_button.clicked.connect(self.add_category)
        edit_button = QPushButton("編輯")
        edit_button.clicked.connect(self.edit_category)
        delete_button = QPushButton("刪除")
        delete_button.clicked.connect(self.delete_category)
        close_button = QPushButton("關閉")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_categories(self):
        with SessionLocal() as db:
            categories = db.query(Category).all()
            self.category_list.clear()
            for category in categories:
                self.category_list.addItem(category.name)

    def add_category(self):
        dialog = CategoryDialog(self)
        if dialog.exec():
            name = dialog.get_category_name()
            if name:
                with SessionLocal() as db:
                    category = Category(name=name)
                    db.add(category)
                    db.commit()
                self.load_categories()

    def edit_category(self):
        current_item = self.category_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "請先選擇一個分類")
            return

        with SessionLocal() as db:
            category = db.query(Category).filter(Category.name == current_item.text()).first()
            if category:
                dialog = CategoryDialog(self, category)
                if dialog.exec():
                    name = dialog.get_category_name()
                    if name:
                        category.name = name
                        db.commit()
                        self.load_categories()

    def delete_category(self):
        current_item = self.category_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "請先選擇一個分類")
            return

        reply = QMessageBox.question(
            self,
            "確認刪除",
            f"確定要刪除分類「{current_item.text()}」嗎？\n注意：這將移除所有模組與此分類的關聯。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            with SessionLocal() as db:
                category = db.query(Category).filter(Category.name == current_item.text()).first()
                if category:
                    db.delete(category)
                    db.commit()
                    self.load_categories()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minecraft 模組管理器")
        self.setup_ui()
        self.load_mods()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 工具列
        toolbar = QHBoxLayout()
        add_button = QPushButton("新增模組")
        add_button.clicked.connect(self.add_mod)
        add_category_button = QPushButton("新增分類")
        add_category_button.clicked.connect(self.add_category)
        toolbar.addWidget(add_button)
        toolbar.addWidget(add_category_button)
        layout.addLayout(toolbar)

        # 模組列表
        self.mod_table = QTableWidget()
        self.mod_table.setColumnCount(7)
        self.mod_table.setHorizontalHeaderLabels(["模組名稱", "分類", "已漢化", "客戶端", "伺服器", "前置", "檔案名稱"])
        layout.addWidget(self.mod_table)

    def load_mods(self):
        with SessionLocal() as db:
            mods = db.query(Mod).all()
            self.mod_table.setRowCount(len(mods))
            for i, mod in enumerate(mods):
                self.mod_table.setItem(i, 0, QTableWidgetItem(mod.name))
                self.mod_table.setItem(i, 1, QTableWidgetItem(", ".join(c.name for c in mod.categories)))
                self.mod_table.setItem(i, 2, QTableWidgetItem("是" if mod.is_translated else "否"))
                self.mod_table.setItem(i, 3, QTableWidgetItem("是" if mod.client_required else "否"))
                self.mod_table.setItem(i, 4, QTableWidgetItem("是" if mod.server_required else "否"))
                self.mod_table.setItem(i, 5, QTableWidgetItem(", ".join(d.name for d in mod.dependencies)))
                self.mod_table.setItem(i, 6, QTableWidgetItem(mod.filename))

    def add_mod(self):
        dialog = ModDialog(self)
        if dialog.exec():
            self.load_mods()

    def add_category(self):
        dialog = CategoryDialog(self)
        if dialog.exec():
            category_name = dialog.get_category_name()
            if category_name:
                with SessionLocal() as db:
                    category = Category(name=category_name)
                    db.add(category)
                    db.commit()
                    db.refresh(category)
                self.load_mods()  # 重新載入模組列表以更新分類


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
