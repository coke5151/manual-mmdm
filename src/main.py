import os
import shutil
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QResizeEvent
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QStatusBar,
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
        self.last_selected_file = None
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
        # 如果是編輯模式，允許編輯檔案名稱
        if self.mod:
            self.filename_edit.setReadOnly(False)
        else:
            self.filename_edit.setReadOnly(True)
            browse_button = QPushButton("瀏覽...")
            browse_button.clicked.connect(self.browse_file)
            file_layout.addWidget(browse_button)
        file_layout.addWidget(self.filename_edit)
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
        dependency_label = QLabel("前置模組:")
        layout.addWidget(dependency_label)

        # 建立水平佈局來放置兩個列表和按鈕
        lists_layout = QHBoxLayout()

        # 可用模組列表
        available_layout = QVBoxLayout()
        available_layout.addWidget(QLabel("可用模組:"))
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.available_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #BDBDBD;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 4px;
                border-radius: 2px;
            }
            QListWidget::item:selected {
                background-color: #1976D2;  /* 使用深藍色作為選取背景 */
                color: white;
            }
            QListWidget::item:selected:!active {
                background-color: #42A5F5;  /* 未激活時使用中等深度的藍色 */
                color: white;
            }
            QListWidget::item:hover {
                background-color: #E3F2FD;  /* 滑鼠懸停時使用非常淺的藍色 */
                color: black;  /* 懸停時使用黑色文字 */
            }
        """)
        available_layout.addWidget(self.available_list)
        lists_layout.addLayout(available_layout)

        # 按鈕
        button_layout = QVBoxLayout()
        button_layout.addStretch()
        add_button = QPushButton(">>")
        add_button.clicked.connect(self.add_dependencies)
        remove_button = QPushButton("<<")
        remove_button.clicked.connect(self.remove_dependencies)
        # 設定按鈕樣式
        button_style = """
            QPushButton {
                padding: 4px 8px;
                background-color: #E3F2FD;
                border: 1px solid #90CAF9;
                border-radius: 4px;
                min-width: 40px;
                color: #1976D2;  /* 使用深藍色作為文字顏色 */
                font-weight: bold;  /* 文字加粗 */
            }
            QPushButton:hover {
                background-color: #BBDEFB;
                color: #1565C0;  /* 懸停時使用更深的藍色 */
            }
            QPushButton:pressed {
                background-color: #90CAF9;
                color: #0D47A1;  /* 按下時使用最深的藍色 */
            }
        """
        add_button.setStyleSheet(button_style)
        remove_button.setStyleSheet(button_style)
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        button_layout.addStretch()
        lists_layout.addLayout(button_layout)

        # 已選擇模組列表
        selected_layout = QVBoxLayout()
        selected_layout.addWidget(QLabel("已選擇:"))
        self.selected_list = QListWidget()
        self.selected_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.selected_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #BDBDBD;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 4px;
                border-radius: 2px;
            }
            QListWidget::item:selected {
                background-color: #1976D2;  /* 使用深藍色作為選取背景 */
                color: white;
            }
            QListWidget::item:selected:!active {
                background-color: #42A5F5;  /* 未激活時使用中等深度的藍色 */
                color: white;
            }
            QListWidget::item:hover {
                background-color: #E3F2FD;  /* 滑鼠懸停時使用非常淺的藍色 */
                color: black;  /* 懸停時使用黑色文字 */
            }
        """)
        selected_layout.addWidget(self.selected_list)
        lists_layout.addLayout(selected_layout)

        layout.addLayout(lists_layout)

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

        # 載入初始資料
        self.load_mods()  # 確保在新增和編輯模式都載入可用模組

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

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "選擇模組檔案", "", "Minecraft 模組檔案 (*.jar);;所有檔案 (*.*)"
        )
        if file_path:
            # 儲存選擇的檔案路徑
            self.last_selected_file = file_path
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
            self.available_list.clear()
            self.selected_list.clear()

            for mod in mods:
                # 不顯示自己作為前置選項
                if self.mod and mod.id == self.mod.id:
                    continue

                # 如果是編輯模式且該模組是前置模組，加入已選擇列表
                if self.mod and mod in self.mod.dependencies:
                    self.selected_list.addItem(mod.name)
                else:
                    # 否則加入可用列表
                    self.available_list.addItem(mod.name)

    def add_dependencies(self):
        # 將選中的項目從可用列表移到已選擇列表
        for item in self.available_list.selectedItems():
            self.available_list.takeItem(self.available_list.row(item))
            self.selected_list.addItem(item.text())

    def remove_dependencies(self):
        # 將選中的項目從已選擇列表移回可用列表
        for item in self.selected_list.selectedItems():
            self.selected_list.takeItem(self.selected_list.row(item))
            self.available_list.addItem(item.text())

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

        # 確保檔案名稱有 .jar 副檔名
        if not filename.lower().endswith(".jar"):
            filename = filename + ".jar"
            self.filename_edit.setText(filename)

        # 建立 mods 目錄（如果不存在）
        mods_dir = Path("mods")
        mods_dir.mkdir(exist_ok=True)

        with SessionLocal() as db:
            if self.mod:
                # 更新現有模組
                mod = db.merge(self.mod)  # 將模組合併到當前 session
                mod.name = name
                mod.filename = filename
                mod.is_translated = self.is_translated.isChecked()
                mod.client_required = self.client_required.isChecked()
                mod.server_required = self.server_required.isChecked()

                # 更新分類
                selected_category = self.category_combo.currentText()
                if selected_category:
                    category = db.query(Category).filter(Category.name == selected_category).first()
                    if category:
                        mod.categories = [category]

                # 更新前置模組
                dependencies = []
                for i in range(self.selected_list.count()):
                    item = self.selected_list.item(i)
                    if item:  # 確保 item 不是 None
                        dependency = db.query(Mod).filter(Mod.name == item.text()).first()
                        if dependency:
                            dependencies.append(dependency)
                mod.dependencies = dependencies

                # 重新命名檔案
                old_path = mods_dir / self.mod.filename
                new_path = mods_dir / filename
                try:
                    if old_path != new_path:  # 只有當檔名確實改變時才重新命名
                        if new_path.exists():
                            QMessageBox.warning(self, "錯誤", f"檔案 {filename} 已經存在")
                            return
                        old_path.rename(new_path)
                except Exception as e:
                    QMessageBox.critical(self, "錯誤", f"重新命名檔案時發生錯誤：{str(e)}")
                    return

            else:
                # 新增模式：複製檔案
                target_path = mods_dir / filename
                try:
                    source_path = self.last_selected_file
                    if not source_path:
                        QMessageBox.warning(self, "錯誤", "請選擇模組檔案")
                        return
                    shutil.copy2(source_path, target_path)
                except Exception as e:
                    QMessageBox.critical(self, "錯誤", f"複製檔案時發生錯誤：{str(e)}")
                    return

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
                dependencies = []
                for i in range(self.selected_list.count()):
                    item = self.selected_list.item(i)
                    if item:  # 確保 item 不是 None
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
        # 設定預設視窗大小
        self.resize(800, 600)
        self.setup_ui()
        self.load_mods()

    def setup_ui(self):
        # 設定選單列
        menubar: QMenuBar | None = self.menuBar()
        if not menubar:
            return

        # 檔案選單
        file_menu: QMenu | None = menubar.addMenu("檔案")
        if not file_menu:
            return
        add_mod_action: QAction | None = file_menu.addAction("新增模組")
        if add_mod_action:
            add_mod_action.triggered.connect(self.add_mod)
        edit_mod_action: QAction | None = file_menu.addAction("編輯模組")
        if edit_mod_action:
            edit_mod_action.triggered.connect(self.edit_mod)
        delete_mod_action: QAction | None = file_menu.addAction("刪除模組")
        if delete_mod_action:
            delete_mod_action.triggered.connect(self.delete_mod)
        file_menu.addSeparator()
        exit_action: QAction | None = file_menu.addAction("結束")
        if exit_action:
            exit_action.triggered.connect(self.close)

        # 管理選單
        manage_menu: QMenu | None = menubar.addMenu("管理")
        if not manage_menu:
            return
        add_category_action: QAction | None = manage_menu.addAction("新增分類")
        if add_category_action:
            add_category_action.triggered.connect(self.add_category)
        manage_categories_action: QAction | None = manage_menu.addAction("管理分類")
        if manage_categories_action:
            manage_categories_action.triggered.connect(self.manage_categories)

        # 主要內容區域
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 工具列（按鈕列）
        button_layout = QHBoxLayout()

        # 新增模組按鈕
        add_button = QPushButton("新增模組")
        add_button.clicked.connect(self.add_mod)
        button_layout.addWidget(add_button)

        # 編輯模組按鈕
        edit_button = QPushButton("編輯模組")
        edit_button.clicked.connect(self.edit_mod)
        button_layout.addWidget(edit_button)

        # 刪除模組按鈕
        delete_button = QPushButton("刪除模組")
        delete_button.clicked.connect(self.delete_mod)
        button_layout.addWidget(delete_button)

        # 分隔線
        button_layout.addStretch()

        # 展開/折疊按鈕
        self.expand_button = QPushButton("展開前置")
        self.expand_button.setCheckable(True)  # 使按鈕可以切換狀態
        self.expand_button.clicked.connect(self.toggle_dependencies)
        button_layout.addWidget(self.expand_button)

        # 分隔線
        button_layout.addStretch()

        # 管理分類按鈕
        manage_categories_button = QPushButton("管理分類")
        manage_categories_button.clicked.connect(self.manage_categories)
        button_layout.addWidget(manage_categories_button)

        layout.addLayout(button_layout)

        # 搜尋列
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜尋:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.filter_mods)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # 模組列表
        self.mod_table = QTableWidget()
        self.mod_table.setColumnCount(7)
        self.mod_table.setHorizontalHeaderLabels(["模組名稱", "分類", "已漢化", "客戶端", "伺服器", "前置", "檔案名稱"])
        self.mod_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.mod_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        # 設定表格自動調整寬度
        header = self.mod_table.horizontalHeader()
        if header:
            # 設定所有欄位都可以調整大小
            for i in range(self.mod_table.columnCount()):
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            # 監聽欄位寬度變化
            header.sectionResized.connect(self.update_column_ratios)

        # 設定雙擊事件
        self.mod_table.doubleClicked.connect(self.edit_mod)
        # 設定文字換行
        self.mod_table.setWordWrap(True)
        # 設定選取樣式
        self.mod_table.setStyleSheet("""
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #1976D2;
                color: white;
            }
            QTableWidget::item:selected:!active {
                background-color: #42A5F5;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #E3F2FD;
                color: black;
            }
        """)
        layout.addWidget(self.mod_table)

        # 狀態列
        status_bar: QStatusBar | None = self.statusBar()
        if status_bar:
            status_bar.showMessage("就緒")

    def update_column_ratios(self):
        """更新欄位寬度比例"""
        header = self.mod_table.horizontalHeader()
        if header:
            total_width = sum(header.sectionSize(i) for i in range(self.mod_table.columnCount()))
            if total_width > 0:
                self.column_ratios = [header.sectionSize(i) / total_width for i in range(self.mod_table.columnCount())]

    def resizeEvent(self, a0: QResizeEvent | None) -> None:  # noqa: N802 (This is special method of Qt)
        if a0 is not None:
            super().resizeEvent(a0)
            # 當視窗大小改變時，等比例調整所有欄位寬度
            header = self.mod_table.horizontalHeader()
            viewport = self.mod_table.viewport()
            if header and viewport and hasattr(self, "column_ratios"):
                new_total_width = viewport.width()
                # 暫時取消寬度變化的監聽，避免循環更新
                header.sectionResized.disconnect(self.update_column_ratios)
                # 根據儲存的比例調整每個欄位的寬度
                for i, ratio in enumerate(self.column_ratios):
                    new_width = int(new_total_width * ratio)
                    header.resizeSection(i, new_width)
                # 重新連接寬度變化的監聽
                header.sectionResized.connect(self.update_column_ratios)

    def filter_mods(self):
        search_text = self.search_edit.text().lower()
        for row in range(self.mod_table.rowCount()):
            show_row = False
            for col in range(self.mod_table.columnCount()):
                item = self.mod_table.item(row, col)
                if item and search_text in item.text().lower():
                    show_row = True
                    break
            self.mod_table.setRowHidden(row, not show_row)

    def manage_categories(self):
        dialog = CategoryManagerDialog(self)
        dialog.exec()

    def toggle_dependencies(self):
        is_expanded = self.expand_button.isChecked()
        self.expand_button.setText("折疊前置" if is_expanded else "展開前置")
        self.load_mods()  # 重新載入模組列表以更新顯示

    def load_mods(self):
        with SessionLocal() as db:
            mods = db.query(Mod).all()
            self.mod_table.setRowCount(len(mods))
            is_expanded = self.expand_button.isChecked()

            for i, mod in enumerate(mods):
                # 建立表格項目並設定為不可編輯
                name_item = QTableWidgetItem(mod.name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.mod_table.setItem(i, 0, name_item)

                category_item = QTableWidgetItem(", ".join(c.name for c in mod.categories))
                category_item.setFlags(category_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.mod_table.setItem(i, 1, category_item)

                translated_item = QTableWidgetItem("是" if mod.is_translated else "否")
                translated_item.setFlags(translated_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.mod_table.setItem(i, 2, translated_item)

                client_item = QTableWidgetItem("是" if mod.client_required else "否")
                client_item.setFlags(client_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.mod_table.setItem(i, 3, client_item)

                server_item = QTableWidgetItem("是" if mod.server_required else "否")
                server_item.setFlags(server_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.mod_table.setItem(i, 4, server_item)

                # 根據展開狀態顯示前置模組
                if is_expanded:
                    dependencies_text = "\n".join(f"• {d.name}" for d in mod.dependencies) if mod.dependencies else ""
                else:
                    dependencies_text = ", ".join(d.name for d in mod.dependencies)

                dependency_item = QTableWidgetItem(dependencies_text)
                dependency_item.setFlags(dependency_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                # 設定文字對齊方式為靠左對齊且垂直置頂
                dependency_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
                self.mod_table.setItem(i, 5, dependency_item)

                filename_item = QTableWidgetItem(mod.filename)
                filename_item.setFlags(filename_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.mod_table.setItem(i, 6, filename_item)

                # 調整行高
                if is_expanded and mod.dependencies:
                    # 每個依賴項目至少 30 像素高
                    row_height = 30 * len(mod.dependencies)
                    self.mod_table.setRowHeight(i, max(30, row_height))
                else:
                    self.mod_table.setRowHeight(i, 30)

            # 更新狀態列
            status_bar: QStatusBar | None = self.statusBar()
            if status_bar:
                status_bar.showMessage(f"共 {len(mods)} 個模組")

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

    def edit_mod(self):
        # 獲取選中的行
        current_row = self.mod_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "請先選擇一個模組")
            return

        # 獲取模組名稱
        name_item = self.mod_table.item(current_row, 0)
        if not name_item:
            QMessageBox.warning(self, "錯誤", "無法獲取模組名稱")
            return

        mod_name = name_item.text()
        if not mod_name:
            QMessageBox.warning(self, "錯誤", "模組名稱為空")
            return

        # 從資料庫中獲取模組
        with SessionLocal() as db:
            mod = db.query(Mod).filter(Mod.name == mod_name).first()
            if not mod:
                QMessageBox.warning(self, "錯誤", "找不到選擇的模組")
                return

            # 開啟編輯對話框
            dialog = ModDialog(self, mod)
            if dialog.exec():
                self.load_mods()  # 重新載入模組列表

    def delete_mod(self):
        # 獲取選中的行
        current_row = self.mod_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "警告", "請先選擇一個模組")
            return

        # 獲取模組名稱
        name_item = self.mod_table.item(current_row, 0)
        if not name_item:
            QMessageBox.warning(self, "錯誤", "無法獲取模組名稱")
            return

        mod_name = name_item.text()
        if not mod_name:
            QMessageBox.warning(self, "錯誤", "模組名稱為空")
            return

        with SessionLocal() as db:
            mod = db.query(Mod).filter(Mod.name == mod_name).first()
            if not mod:
                QMessageBox.warning(self, "錯誤", "找不到選擇的模組")
                return

            # 檢查是否有其他模組依賴此模組
            dependent_mods = db.query(Mod).filter(Mod.dependencies.any(id=mod.id)).all()
            if dependent_mods:
                # 如果有依賴，顯示警告訊息並列出依賴此模組的其他模組
                dependent_names = ", ".join([m.name for m in dependent_mods])
                QMessageBox.warning(
                    self,
                    "無法刪除",
                    f"無法刪除模組「{mod_name}」，因為以下模組依賴它：\n{dependent_names}",
                )
                return

            # 確認是否要刪除
            reply = QMessageBox.question(
                self,
                "確認刪除",
                f"確定要刪除模組「{mod_name}」嗎？\n注意：這將同時刪除模組檔案。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                # 刪除檔案
                try:
                    file_path = Path("mods") / mod.filename
                    if file_path.exists():
                        file_path.unlink()
                except Exception as e:
                    QMessageBox.critical(self, "錯誤", f"刪除檔案時發生錯誤：{str(e)}")
                    return

                # 從資料庫中刪除
                db.delete(mod)
                db.commit()
                self.load_mods()  # 重新載入模組列表

    def showEvent(self, event):  # noqa: N802 (This is special method of Qt)
        """當視窗顯示時設定初始欄位寬度"""
        super().showEvent(event)
        header = self.mod_table.horizontalHeader()
        viewport = self.mod_table.viewport()
        if header and viewport:
            # 設定所有欄位初始等寬
            total_width = viewport.width()
            column_width = total_width // self.mod_table.columnCount()
            for i in range(self.mod_table.columnCount()):
                header.resizeSection(i, column_width)
            # 儲存初始的欄位寬度比例
            self.update_column_ratios()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
