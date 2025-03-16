import os
import shutil
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon, QResizeEvent
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

from config import load_config, save_config
from database import SessionLocal, engine
from models import Base, Category, Mod
from translations import TRANSLATIONS

# Create tables
Base.metadata.create_all(bind=engine)


class ModDialog(QDialog):
    def __init__(self, parent=None, mod=None):
        super().__init__(parent)
        # If editing an existing mod, ensure dependencies are loaded before UI setup
        if mod:
            with SessionLocal() as db:
                # Make sure mod is attached to the current session and dependencies are loaded
                self.mod = db.merge(mod)
                # Force loading of all relationships to avoid detached instance errors
                _ = self.mod.dependencies
                _ = self.mod.categories
                # Store necessary attributes to avoid detached instance issues
                self.mod_name = self.mod.name
                self.mod_filename = self.mod.filename
                self.mod_is_translated = self.mod.is_translated
                self.mod_client_required = self.mod.client_required
                self.mod_server_required = self.mod.server_required
                self.mod_notes = self.mod.notes
                self.mod_id = self.mod.id
                # Store dependencies and categories for later use
                self.mod_dependencies = [d.name for d in self.mod.dependencies]
                self.mod_categories = [c.name for c in self.mod.categories] if self.mod.categories else []
        else:
            self.mod = None
            self.mod_dependencies = []
            self.mod_categories = []

        self.last_selected_file = None
        self.translations = parent.translations if parent else TRANSLATIONS["en"]
        self.setWindowTitle(self.translations["add_edit_mod_title"])
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Module name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel(self.translations["label_module_name"]))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # File selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel(self.translations["label_module_file"]))
        self.filename_edit = QLineEdit()
        # If in edit mode, allow editing file name
        if self.mod:
            self.filename_edit.setReadOnly(False)
        else:
            self.filename_edit.setReadOnly(True)
            browse_button = QPushButton(self.translations["button_browse"])
            browse_button.clicked.connect(self.browse_file)
            file_layout.addWidget(browse_button)
        file_layout.addWidget(self.filename_edit)
        layout.addLayout(file_layout)

        # Categories
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel(self.translations["label_category"]))
        self.category_combo = QComboBox()
        self.load_categories()
        category_layout.addWidget(self.category_combo)
        manage_category_button = QPushButton(self.translations["menu_manage_categories"])
        manage_category_button.clicked.connect(self.manage_categories)
        category_layout.addWidget(manage_category_button)
        layout.addLayout(category_layout)

        # Options
        self.is_translated = QCheckBox(self.translations["check_translated"])
        self.client_required = QCheckBox(self.translations["check_client_required"])
        self.server_required = QCheckBox(self.translations["check_server_required"])
        layout.addWidget(self.is_translated)
        layout.addWidget(self.client_required)
        layout.addWidget(self.server_required)

        # Notes
        notes_layout = QVBoxLayout()
        notes_layout.addWidget(QLabel(self.translations["label_notes"]))
        self.notes_edit = QLineEdit()
        notes_layout.addWidget(self.notes_edit)
        layout.addLayout(notes_layout)

        # Dependencies
        dependency_label = QLabel(self.translations["label_dependencies"])
        layout.addWidget(dependency_label)

        # Create horizontal layout for lists and buttons
        lists_layout = QHBoxLayout()

        # Available modules list
        available_layout = QVBoxLayout()
        available_layout.addWidget(QLabel(self.translations["label_available_modules"]))
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
                background-color: #1976D2;  /* Use dark blue for selection background */
                color: white;
            }
            QListWidget::item:selected:!active {
                background-color: #42A5F5;  /* Use medium blue when not active */
                color: white;
            }
            QListWidget::item:hover {
                background-color: #E3F2FD;  /* Use very light blue for hover */
                color: black;  /* Use black text for hover */
            }
        """)
        available_layout.addWidget(self.available_list)
        lists_layout.addLayout(available_layout)

        # Buttons
        button_layout = QVBoxLayout()
        button_layout.addStretch()
        add_button = QPushButton(">>")
        add_button.clicked.connect(self.add_dependencies)
        remove_button = QPushButton("<<")
        remove_button.clicked.connect(self.remove_dependencies)
        # Set button style
        button_style = """
            QPushButton {
                padding: 4px 8px;
                background-color: #E3F2FD;
                border: 1px solid #90CAF9;
                border-radius: 4px;
                min-width: 40px;
                color: #1976D2;  /* Use dark blue for text color */
                font-weight: bold;  /* Bold text */
            }
            QPushButton:hover {
                background-color: #BBDEFB;
                color: #1565C0;  /* Use darker blue on hover */
            }
            QPushButton:pressed {
                background-color: #90CAF9;
                color: #0D47A1;  /* Use darkest blue when pressed */
            }
        """
        add_button.setStyleSheet(button_style)
        remove_button.setStyleSheet(button_style)
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        button_layout.addStretch()
        lists_layout.addLayout(button_layout)

        # Selected modules list
        selected_layout = QVBoxLayout()
        selected_layout.addWidget(QLabel(self.translations["label_selected"]))
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
                background-color: #1976D2;  /* Use dark blue for selection background */
                color: white;
            }
            QListWidget::item:selected:!active {
                background-color: #42A5F5;  /* Use medium blue when not active */
                color: white;
            }
            QListWidget::item:hover {
                background-color: #E3F2FD;  /* Use very light blue for hover */
                color: black;  /* Use black text for hover */
            }
        """)
        selected_layout.addWidget(self.selected_list)
        lists_layout.addLayout(selected_layout)

        layout.addLayout(lists_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton(self.translations["button_save"])
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton(self.translations["button_cancel"])
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Set module attributes first if editing an existing module
        if self.mod:
            self.name_edit.setText(self.mod_name)
            self.filename_edit.setText(self.mod_filename)
            self.is_translated.setChecked(self.mod_is_translated)
            self.client_required.setChecked(self.mod_client_required)
            self.server_required.setChecked(self.mod_server_required)
            self.notes_edit.setText(self.mod_notes)

            # Set categories
            if self.mod_categories:
                category_name = self.mod_categories[0]
                index = self.category_combo.findText(category_name)
                if index >= 0:
                    self.category_combo.setCurrentIndex(index)

        # Load mods after setting all attributes to ensure dependencies are preserved
        self.load_mods()

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.translations["dialog_choose_mod"],
            "",
            self.translations["dialog_mod_filter"],
        )
        if file_path:
            # Store selected file path
            self.last_selected_file = file_path
            # Get file name
            filename = os.path.basename(file_path)
            self.filename_edit.setText(filename)

            # Always update module name when file is changed
            # This allows the name to be updated even when switching between different files
            name = os.path.splitext(filename)[0].replace("_", " ")
            self.name_edit.setText(name)

    def load_categories(self):
        with SessionLocal() as db:
            # Ensure "Uncategorized" category exists
            uncategorized = db.query(Category).filter(Category.name == self.translations["label_uncategorized"]).first()
            if not uncategorized:
                uncategorized = Category(name=self.translations["label_uncategorized"])
                db.add(uncategorized)
                db.commit()

            # Load all categories ordered by name (case-insensitive)
            from sqlalchemy.sql import func

            categories = db.query(Category).order_by(func.lower(Category.name)).all()
            self.category_combo.clear()
            for category in categories:
                self.category_combo.addItem(category.name)

            # If no category is selected, default to "Uncategorized"
            if self.category_combo.count() > 0 and not self.mod:
                uncategorized_index = self.category_combo.findText(self.translations["label_uncategorized"])
                if uncategorized_index >= 0:
                    self.category_combo.setCurrentIndex(uncategorized_index)

    def load_mods(self):
        with SessionLocal() as db:
            # Get all mods ordered by name (case-insensitive)
            from sqlalchemy.sql import func

            mods = db.query(Mod).order_by(func.lower(Mod.name)).all()
            self.available_list.clear()
            self.selected_list.clear()

            for mod in mods:
                # Don't show self as dependency option
                if self.mod and mod.id == self.mod_id:
                    continue

                # If in edit mode and module is a dependency, add to selected list
                if self.mod and mod.name in self.mod_dependencies:
                    self.selected_list.addItem(mod.name)
                else:
                    # Otherwise add to available list
                    self.available_list.addItem(mod.name)

    def add_dependencies(self):
        # Move selected items from available list to selected list
        for item in self.available_list.selectedItems():
            self.available_list.takeItem(self.available_list.row(item))
            self.selected_list.addItem(item.text())

    def remove_dependencies(self):
        # Move selected items from selected list back to available list
        for item in self.selected_list.selectedItems():
            self.selected_list.takeItem(self.selected_list.row(item))
            self.available_list.addItem(item.text())

    def manage_categories(self):
        dialog = CategoryManagerDialog(self)
        if dialog.exec():
            self.load_categories()  # Reload category list

    def accept(self):
        name = self.name_edit.text()
        filename = self.filename_edit.text()
        notes = self.notes_edit.text()

        if not name or not filename:
            QMessageBox.warning(
                self,
                self.translations["title_error"],
                self.translations["msg_name_file_empty"],
            )
            return

        # Ensure file name has .jar extension
        if not filename.lower().endswith(".jar"):
            filename = filename + ".jar"
            self.filename_edit.setText(filename)

        # Create mods directory (if not exists)
        mods_dir = Path("mods")
        mods_dir.mkdir(exist_ok=True)

        with SessionLocal() as db:
            if self.mod:
                # Update existing module
                mod = db.query(Mod).filter(Mod.id == self.mod_id).first()
                if not mod:
                    QMessageBox.critical(
                        self, self.translations["title_error"], self.translations["msg_module_not_found"]
                    )
                    return

                mod.name = name
                mod.filename = filename
                mod.is_translated = self.is_translated.isChecked()
                mod.client_required = self.client_required.isChecked()
                mod.server_required = self.server_required.isChecked()
                mod.notes = notes

                # Update categories
                selected_category = self.category_combo.currentText()
                if selected_category:
                    category = db.query(Category).filter(Category.name == selected_category).first()
                    if category:
                        mod.categories = [category]

                # Update dependencies
                dependencies = []
                for i in range(self.selected_list.count()):
                    item = self.selected_list.item(i)
                    if item:  # Ensure item is not None
                        dependency = db.query(Mod).filter(Mod.name == item.text()).first()
                        if dependency:
                            dependencies.append(dependency)
                mod.dependencies = dependencies

                # Rename file
                old_path = mods_dir / self.mod_filename
                new_path = mods_dir / filename
                try:
                    if old_path != new_path:  # Only rename when filename actually changes
                        if new_path.exists():
                            QMessageBox.warning(
                                self,
                                self.translations["title_error"],
                                self.translations["msg_file_exists"].format(filename),
                            )
                            return
                        old_path.rename(new_path)
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        self.translations["title_error"],
                        self.translations["msg_error_rename_file"].format(str(e)),
                    )
                    return

            else:
                target_path = mods_dir / filename
                try:
                    source_path = self.last_selected_file
                    if not source_path:
                        QMessageBox.warning(
                            self,
                            self.translations["title_warning"],
                            self.translations["msg_choose_module_file"],
                        )
                        return
                    shutil.copy2(source_path, target_path)
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        self.translations["title_error"],
                        self.translations["msg_error_copy_file"].format(str(e)),
                    )
                    return

                # Add module
                mod = Mod(
                    name=name,
                    filename=filename,
                    is_translated=self.is_translated.isChecked(),
                    client_required=self.client_required.isChecked(),
                    server_required=self.server_required.isChecked(),
                    notes=notes,
                )

                # Set categories
                selected_category = self.category_combo.currentText()
                if selected_category:
                    category = db.query(Category).filter(Category.name == selected_category).first()
                    if category:
                        mod.categories = [category]

                # Set dependencies
                dependencies = []
                for i in range(self.selected_list.count()):
                    item = self.selected_list.item(i)
                    if item:  # Ensure item is not None
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
        self.translations = parent.translations if parent else TRANSLATIONS["en"]
        self.setWindowTitle(
            self.translations["add_category_title"] if not category else self.translations["edit_category_title"]
        )
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Category name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel(self.translations["label_category_name"]))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton(self.translations["button_save"])
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton(self.translations["button_cancel"])
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
        self.translations = parent.translations if parent else TRANSLATIONS["en"]
        self.setWindowTitle(self.translations["manage_categories_title"])
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.category_list = QListWidget()
        layout.addWidget(self.category_list)

        # Buttons
        button_layout = QHBoxLayout()

        add_button = QPushButton(self.translations["button_add"])
        add_button.clicked.connect(self.add_category)
        button_layout.addWidget(add_button)

        # Add edit button
        edit_button = QPushButton(self.translations["button_edit"])
        edit_button.clicked.connect(self.edit_category)
        button_layout.addWidget(edit_button)

        delete_button = QPushButton(self.translations["button_delete"])
        delete_button.clicked.connect(self.delete_category)
        button_layout.addWidget(delete_button)

        close_button = QPushButton(self.translations["button_close"])
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Load initial categories
        self.load_categories()

    def load_categories(self):
        """Load categories from database"""
        self.category_list.clear()
        with SessionLocal() as db:
            # Ensure default category exists
            default_category = (
                db.query(Category).filter(Category.name == self.translations["label_uncategorized"]).first()
            )
            if not default_category:
                default_category = Category(name=self.translations["label_uncategorized"])
                db.add(default_category)
                db.commit()

            # Load all categories ordered by name (case-insensitive)
            from sqlalchemy.sql import func

            categories = db.query(Category).order_by(func.lower(Category.name)).all()
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
            QMessageBox.warning(
                self,
                self.translations["title_warning"],
                self.translations["msg_select_category"],
            )
            return

        # Do not allow editing "Default"
        if current_item.text() == self.translations["label_uncategorized"]:
            QMessageBox.warning(
                self,
                self.translations["title_warning"],
                self.translations["msg_cannot_edit_uncategorized"],
            )
            return

        with SessionLocal() as db:
            # Get the category to edit
            category = db.query(Category).filter(Category.name == current_item.text()).first()
            if not category:
                QMessageBox.warning(self, self.translations["title_error"], self.translations["msg_module_not_found"])
                return

            # Create dialog with the category
            dialog = CategoryDialog(self, category)
            if dialog.exec():
                new_name = dialog.get_category_name()
                if new_name and new_name != category.name:
                    # Check if the new name already exists
                    existing = db.query(Category).filter(Category.name == new_name).first()
                    if existing:
                        QMessageBox.warning(
                            self,
                            self.translations["title_error"],
                            self.translations["msg_category_exists"].format(new_name),
                        )
                        return

                    # Update category name
                    category.name = new_name
                    db.commit()

                    # Reload categories
                    self.load_categories()

                    # Signal that changes were made
                    self.accept()

                    # Reload mods in the main window to show updated category names
                    from typing import cast

                    parent = cast(MainWindow, self.parent())
                    if isinstance(parent, MainWindow):
                        parent.load_mods()

    def delete_category(self):
        current_item = self.category_list.currentItem()
        if not current_item:
            QMessageBox.warning(
                self,
                self.translations["title_warning"],
                self.translations["msg_select_category"],
            )
            return

        # Do not allow deleting "Default"
        if current_item.text() == self.translations["label_uncategorized"]:
            QMessageBox.warning(
                self,
                self.translations["title_warning"],
                self.translations["msg_cannot_delete_uncategorized"],
            )
            return

        reply = QMessageBox.question(
            self,
            self.translations["title_confirm_delete"],
            self.translations["msg_confirm_delete_category"].format(current_item.text()),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            with SessionLocal() as db:
                # Get the category to delete
                category = db.query(Category).filter(Category.name == current_item.text()).first()
                if category:
                    # Get the "Default" category
                    default_category = (
                        db.query(Category).filter(Category.name == self.translations["label_uncategorized"]).first()
                    )

                    if default_category:
                        # Get all mods in this category
                        mods_to_update = db.query(Mod).filter(Mod.categories.any(id=category.id)).all()

                        # Move all mods to "Default"
                        for mod in mods_to_update:
                            # Remove all existing categories
                            mod.categories.clear()
                            # Add default category
                            mod.categories.append(default_category)

                        # Commit the changes to mods
                        db.commit()

                    # Delete the category
                    db.delete(category)
                    db.commit()

                    # Reload categories
                    self.load_categories()

                    # Signal that changes were made by accepting the dialog
                    self.accept()

                    # Reload mods in the main window
                    from typing import cast

                    parent = cast(MainWindow, self.parent())
                    if isinstance(parent, MainWindow):
                        parent.load_mods()

    def closeEvent(self, event):  # noqa: N802
        """Override close event to notify parent to reload mods"""
        super().closeEvent(event)
        # Signal that changes were made by accepting the dialog
        self.accept()


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.translations = parent.translations if parent else TRANSLATIONS["en"]
        self.setWindowTitle(self.translations["about_title"])
        self.setup_ui()
        # Remove the ? button from the title bar
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

    def setup_ui(self):
        layout = QVBoxLayout()

        # Create a QLabel for the content
        content_label = QLabel(self.translations["about_content"])
        content_label.setOpenExternalLinks(True)  # Enable clicking links
        content_label.setTextFormat(Qt.TextFormat.RichText)  # Enable HTML formatting
        layout.addWidget(content_label)

        # Add OK button
        button_layout = QHBoxLayout()
        ok_button = QPushButton(self.translations["button_close"])
        ok_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Load saved language from config
        self.config = load_config()
        self.current_language = self.config.get("language", "en")
        self.translations = TRANSLATIONS[self.current_language]  # Translation dictionary
        self.setWindowTitle(self.translations["main_window_title"])
        # Set window icon
        icon_path = Path(__file__).parent.parent / "static" / "mmdm-icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        else:
            print(f"Warning: Icon file not found at {icon_path}")
            # Try to create static directory if it doesn't exist
            static_dir = Path(__file__).parent.parent / "static"
            static_dir.mkdir(exist_ok=True)
        # Set default window size
        self.resize(800, 600)
        self.setup_ui()
        self.load_mods()

    def setup_ui(self):
        # Set menu bar
        menubar: QMenuBar | None = self.menuBar()
        if not menubar:
            return

        # File menu
        file_menu: QMenu | None = menubar.addMenu(self.translations["menu_file"])
        if not file_menu:
            return
        add_mod_action: QAction | None = file_menu.addAction(self.translations["menu_add_mod"])
        if add_mod_action:
            add_mod_action.triggered.connect(self.add_mod)
        edit_mod_action: QAction | None = file_menu.addAction(self.translations["menu_edit_mod"])
        if edit_mod_action:
            edit_mod_action.triggered.connect(self.edit_mod)
        delete_mod_action: QAction | None = file_menu.addAction(self.translations["menu_delete_mod"])
        if delete_mod_action:
            delete_mod_action.triggered.connect(self.delete_mod)
        file_menu.addSeparator()
        exit_action: QAction | None = file_menu.addAction(self.translations["menu_exit"])
        if exit_action:
            exit_action.triggered.connect(self.close)

        # Management menu
        manage_menu: QMenu | None = menubar.addMenu(self.translations["menu_manage"])
        if not manage_menu:
            return
        add_category_action: QAction | None = manage_menu.addAction(self.translations["menu_add_category"])
        if add_category_action:
            add_category_action.triggered.connect(self.add_category)
        manage_categories_action: QAction | None = manage_menu.addAction(self.translations["menu_manage_categories"])
        if manage_categories_action:
            manage_categories_action.triggered.connect(self.manage_categories)

        # Export menu
        export_menu: QMenu | None = menubar.addMenu(self.translations["menu_export"])
        if export_menu:
            export_client_action: QAction | None = export_menu.addAction(self.translations["menu_export_client"])
            if export_client_action:
                export_client_action.triggered.connect(lambda: self.export_mods("client"))

            export_server_action: QAction | None = export_menu.addAction(self.translations["menu_export_server"])
            if export_server_action:
                export_server_action.triggered.connect(lambda: self.export_mods("server"))

            export_menu.addSeparator()

            export_json_action: QAction | None = export_menu.addAction(self.translations["menu_export_json"])
            if export_json_action:
                export_json_action.triggered.connect(self.export_json)

            export_dep_tree_action: QAction | None = export_menu.addAction(self.translations["menu_export_dep_tree"])
            if export_dep_tree_action:
                export_dep_tree_action.triggered.connect(self.export_dependency_tree)

            import_json_action: QAction | None = export_menu.addAction(self.translations["menu_import_json"])
            if import_json_action:
                import_json_action.triggered.connect(self.import_json)

        # Language menu
        language_menu: QMenu | None = menubar.addMenu(self.translations["menu_language"])
        if language_menu:
            english_action: QAction = QAction("English", self)
            english_action.setCheckable(True)
            english_action.setChecked(self.current_language == "en")
            english_action.triggered.connect(lambda: self.change_language("en"))
            language_menu.addAction(english_action)

            chinese_action: QAction = QAction("繁體中文", self)
            chinese_action.setCheckable(True)
            chinese_action.setChecked(self.current_language == "zh_TW")
            chinese_action.triggered.connect(lambda: self.change_language("zh_TW"))
            language_menu.addAction(chinese_action)

            language_menu.triggered.connect(
                lambda action: self.update_language_menu(action, [english_action, chinese_action])
            )

        # About menu
        about_action: QAction = QAction(self.translations["menu_about"], self)
        about_action.triggered.connect(self.show_about)
        menubar.addAction(about_action)

        # Main content area
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Toolbar (button row)
        button_layout = QHBoxLayout()

        # Add module button
        add_button = QPushButton(self.translations["menu_add_mod"])
        add_button.clicked.connect(self.add_mod)
        button_layout.addWidget(add_button)

        # Edit module button
        edit_button = QPushButton(self.translations["menu_edit_mod"])
        edit_button.clicked.connect(self.edit_mod)
        button_layout.addWidget(edit_button)

        # Delete module button
        delete_button = QPushButton(self.translations["menu_delete_mod"])
        delete_button.clicked.connect(self.delete_mod)
        button_layout.addWidget(delete_button)

        # Separator
        button_layout.addStretch()

        # Expand/collapse button
        self.expand_button = QPushButton(self.translations["button_expand_deps"])
        self.expand_button.setCheckable(True)
        self.expand_button.clicked.connect(self.toggle_dependencies)
        button_layout.addWidget(self.expand_button)

        # Separator
        button_layout.addStretch()

        # Manage categories button
        manage_categories_button = QPushButton(self.translations["menu_manage_categories"])
        manage_categories_button.clicked.connect(self.manage_categories)
        button_layout.addWidget(manage_categories_button)

        layout.addLayout(button_layout)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel(self.translations["label_search"]))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.filter_mods)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)

        # Module list
        self.mod_table = QTableWidget()
        self.mod_table.setColumnCount(8)
        self.update_table_headers()
        self.mod_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.mod_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # Set table to auto-adjust width
        header = self.mod_table.horizontalHeader()
        if header:
            # Set all columns resizable
            for i in range(self.mod_table.columnCount()):
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            # Monitor column width changes
            header.sectionResized.connect(self.update_column_ratios)

        # Set double-click event
        self.mod_table.doubleClicked.connect(self.edit_mod)
        # Set text wrapping
        self.mod_table.setWordWrap(True)
        # Set selection style
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

        # Status bar
        status_bar: QStatusBar | None = self.statusBar()
        if status_bar:
            status_bar.showMessage(self.translations["msg_ready"])

    def update_table_headers(self):
        """Update table headers with current language"""
        self.mod_table.setHorizontalHeaderLabels(
            [
                self.translations["header_module_name"],
                self.translations["header_category"],
                self.translations["header_translated"],
                self.translations["header_client"],
                self.translations["header_server"],
                self.translations["header_dependencies"],
                self.translations["header_filename"],
                self.translations["header_notes"],
            ]
        )

    def update_language_menu(self, triggered_action: QAction, actions: list[QAction]) -> None:
        """Update language menu checkmarks"""
        for action in actions:
            if action != triggered_action:
                action.setChecked(False)

    def change_language(self, language: str) -> None:
        """Change the application language"""
        if language != self.current_language:
            self.current_language = language
            self.translations = TRANSLATIONS[language]
            # Save language setting to config
            self.config["language"] = language
            save_config(self.config)
            self.retranslate_ui()

    def retranslate_ui(self) -> None:
        """Update all UI elements with new language"""
        # Update window title
        self.setWindowTitle(self.translations["main_window_title"])

        # Update menu items
        menubar = self.menuBar()
        if menubar:
            # Update regular menus
            menus = menubar.findChildren(QMenu)
            for menu in menus:
                if menu.title() in ["File", "檔案"]:
                    menu.setTitle(self.translations["menu_file"])
                elif menu.title() in ["Manage", "管理"]:
                    menu.setTitle(self.translations["menu_manage"])
                elif menu.title() in ["Export", "匯出"]:
                    menu.setTitle(self.translations["menu_export"])
                elif menu.title() in ["Language", "語言"]:
                    menu.setTitle(self.translations["menu_language"])

                # Update menu actions
                for action in menu.actions():
                    if action.text() in ["Add Module", "新增模組"]:
                        action.setText(self.translations["menu_add_mod"])
                    elif action.text() in ["Edit Module", "編輯模組"]:
                        action.setText(self.translations["menu_edit_mod"])
                    elif action.text() in ["Delete Module", "刪除模組"]:
                        action.setText(self.translations["menu_delete_mod"])
                    elif action.text() in ["Add Category", "新增分類"]:
                        action.setText(self.translations["menu_add_category"])
                    elif action.text() in ["Manage Categories", "管理分類"]:
                        action.setText(self.translations["menu_manage_categories"])
                    elif action.text() in ["Export Client Mods", "匯出客戶端模組"]:
                        action.setText(self.translations["menu_export_client"])
                    elif action.text() in ["Export Server Mods", "匯出伺服端模組"]:
                        action.setText(self.translations["menu_export_server"])
                    elif action.text() in ["Export to JSON", "匯出至JSON"]:
                        action.setText(self.translations["menu_export_json"])
                    elif action.text() in ["Export Dependency Tree", "匯出依賴樹"]:
                        action.setText(self.translations["menu_export_dep_tree"])
                    elif action.text() in ["Import from JSON", "從JSON匯入"]:
                        action.setText(self.translations["menu_import_json"])

            # Update About action
            for action in menubar.actions():
                if action.text() in ["About", "關於"]:
                    action.setText(self.translations["menu_about"])

        # Update buttons
        for button in self.findChildren(QPushButton):
            if button == self.expand_button:
                button.setText(
                    self.translations["button_expand_deps"]
                    if not button.isChecked()
                    else self.translations["button_collapse_deps"]
                )
            elif button.text() in ["Add Module", "新增模組"]:
                button.setText(self.translations["menu_add_mod"])
            elif button.text() in ["Edit Module", "編輯模組"]:
                button.setText(self.translations["menu_edit_mod"])
            elif button.text() in ["Delete Module", "刪除模組"]:
                button.setText(self.translations["menu_delete_mod"])
            elif button.text() in ["Manage Categories", "管理分類"]:
                button.setText(self.translations["menu_manage_categories"])

        # Update labels
        for label in self.findChildren(QLabel):
            if label.text() in ["Search:", "搜尋:"]:
                label.setText(self.translations["label_search"])

        # Update table headers
        self.update_table_headers()

        # Update status bar
        status_bar = self.statusBar()
        if status_bar:
            current_text = status_bar.currentMessage()
            if current_text in ["Ready", "就緒"]:
                status_bar.showMessage(self.translations["msg_ready"])
            elif "Total" in current_text or "共" in current_text:
                count = len([i for i in range(self.mod_table.rowCount()) if not self.mod_table.isRowHidden(i)])
                status_bar.showMessage(self.translations["msg_total_mods"].format(count))

        # Refresh table contents
        self.load_mods()

    def update_column_ratios(self):
        """Update column width ratios"""
        header = self.mod_table.horizontalHeader()
        if header:
            total_width = sum(header.sectionSize(i) for i in range(self.mod_table.columnCount()))
            if total_width > 0:
                self.column_ratios = [header.sectionSize(i) / total_width for i in range(self.mod_table.columnCount())]

    def resizeEvent(self, a0: QResizeEvent | None) -> None:  # noqa: N802 (This is special method of Qt)
        if a0 is not None:
            super().resizeEvent(a0)
            # When window size changes, adjust all column widths proportionally
            header = self.mod_table.horizontalHeader()
            viewport = self.mod_table.viewport()
            if header and viewport and hasattr(self, "column_ratios"):
                # Temporarily disconnect width change monitoring to avoid circular updates
                header.sectionResized.disconnect(self.update_column_ratios)
                # Adjust each column width based on stored ratios
                new_total_width = viewport.width()
                for i, ratio in enumerate(self.column_ratios):
                    new_width = int(new_total_width * ratio)
                    header.resizeSection(i, new_width)
                # Reconnect width change monitoring
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
        self.expand_button.setText(
            self.translations["button_collapse_deps"] if is_expanded else self.translations["button_expand_deps"]
        )
        self.load_mods()  # Reload module list to update display

    def load_mods(self):
        with SessionLocal() as db:
            # Get all mods ordered by name (case-insensitive)
            from sqlalchemy.sql import func

            mods = db.query(Mod).order_by(func.lower(Mod.name)).all()
            self.mod_table.setRowCount(len(mods))
            is_expanded = self.expand_button.isChecked()

            for i, mod in enumerate(mods):
                # Create table items and set them as non-editable
                name_item = QTableWidgetItem(mod.name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.mod_table.setItem(i, 0, name_item)

                # Sort categories by name (case-insensitive)
                category_item = QTableWidgetItem(", ".join(sorted([c.name for c in mod.categories], key=str.lower)))
                category_item.setFlags(category_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.mod_table.setItem(i, 1, category_item)

                translated_item = QTableWidgetItem(
                    self.translations["msg_yes"] if mod.is_translated else self.translations["msg_no"]
                )
                translated_item.setFlags(translated_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.mod_table.setItem(i, 2, translated_item)

                client_item = QTableWidgetItem(
                    self.translations["msg_yes"] if mod.client_required else self.translations["msg_no"]
                )
                client_item.setFlags(client_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.mod_table.setItem(i, 3, client_item)

                server_item = QTableWidgetItem(
                    self.translations["msg_yes"] if mod.server_required else self.translations["msg_no"]
                )
                server_item.setFlags(server_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.mod_table.setItem(i, 4, server_item)

                # Show dependencies based on expand state
                if is_expanded:
                    # Sort dependencies by name (case-insensitive) and format with bullet points
                    dependencies_text = (
                        "\n".join(f"• {d.name}" for d in sorted(mod.dependencies, key=lambda x: x.name.lower()))
                        if mod.dependencies
                        else ""
                    )
                else:
                    # Sort dependencies by name (case-insensitive) and join with commas
                    dependencies_text = ", ".join(
                        d.name for d in sorted(mod.dependencies, key=lambda x: x.name.lower())
                    )

                dependency_item = QTableWidgetItem(dependencies_text)
                dependency_item.setFlags(dependency_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                # Set text alignment to left and vertically top
                dependency_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
                self.mod_table.setItem(i, 5, dependency_item)

                filename_item = QTableWidgetItem(mod.filename)
                filename_item.setFlags(filename_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.mod_table.setItem(i, 6, filename_item)

                notes_item = QTableWidgetItem(mod.notes or "")
                notes_item.setFlags(notes_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.mod_table.setItem(i, 7, notes_item)

                # Adjust row height
                if is_expanded and mod.dependencies:
                    # Each dependency item should be at least 30 pixels high
                    row_height = 30 * len(mod.dependencies)
                    self.mod_table.setRowHeight(i, max(30, row_height))
                else:
                    self.mod_table.setRowHeight(i, 30)

            # Update status bar
            status_bar: QStatusBar | None = self.statusBar()
            if status_bar:
                status_bar.showMessage(self.translations["msg_total_mods"].format(len(mods)))

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
                self.load_mods()  # Reload module list to update categories

    def edit_mod(self):
        # Get selected row
        current_row = self.mod_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(
                self,
                self.translations["title_warning"],
                self.translations["msg_select_module"],
            )
            return

        # Get module name
        name_item = self.mod_table.item(current_row, 0)
        if not name_item:
            QMessageBox.warning(
                self,
                self.translations["title_error"],
                self.translations["msg_unable_get_name"],
            )
            return

        mod_name = name_item.text()
        if not mod_name:
            QMessageBox.warning(
                self,
                self.translations["title_error"],
                self.translations["msg_name_empty"],
            )
            return

        # Get module from database
        with SessionLocal() as db:
            mod = db.query(Mod).filter(Mod.name == mod_name).first()
            if not mod:
                QMessageBox.warning(
                    self,
                    self.translations["title_error"],
                    self.translations["msg_module_not_found"],
                )
                return

            # Open edit dialog
            dialog = ModDialog(self, mod)
            if dialog.exec():
                self.load_mods()  # Reload module list

    def delete_mod(self):
        # Get selected row
        current_row = self.mod_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(
                self,
                self.translations["title_warning"],
                self.translations["msg_select_module"],
            )
            return

        # Get module name
        name_item = self.mod_table.item(current_row, 0)
        if not name_item:
            QMessageBox.warning(
                self,
                self.translations["title_error"],
                self.translations["msg_unable_get_name"],
            )
            return

        mod_name = name_item.text()
        if not mod_name:
            QMessageBox.warning(
                self,
                self.translations["title_error"],
                self.translations["msg_name_empty"],
            )
            return

        with SessionLocal() as db:
            mod = db.query(Mod).filter(Mod.name == mod_name).first()
            if not mod:
                QMessageBox.warning(
                    self,
                    self.translations["title_error"],
                    self.translations["msg_module_not_found"],
                )
                return

            # Check if other modules depend on this module
            dependent_mods = db.query(Mod).filter(Mod.dependencies.any(id=mod.id)).all()
            if dependent_mods:
                # If there are dependencies, show warning message and list modules that depend on this one
                dependent_names = ", ".join([m.name for m in dependent_mods])
                QMessageBox.warning(
                    self,
                    self.translations["title_unable_delete"],
                    self.translations["msg_unable_delete"].format(mod_name, dependent_names),
                )
                return

            # Confirm whether to delete
            reply = QMessageBox.question(
                self,
                self.translations["title_confirm_delete"],
                self.translations["msg_confirm_delete_mod"].format(mod_name),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Delete file
                try:
                    file_path = Path("mods") / mod.filename
                    if file_path.exists():
                        file_path.unlink()
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        self.translations["title_error"],
                        self.translations["msg_error_delete_file"].format(str(e)),
                    )
                    return

                # Delete from database
                db.delete(mod)
                db.commit()
                self.load_mods()  # Reload module list

    def export_mods(self, mod_type: str):
        """Export mods to client_mods or server_mods folder based on type."""
        import shutil
        from pathlib import Path

        # Create export directory if it doesn't exist
        export_dir = Path(f"{mod_type}_mods")
        export_dir.mkdir(exist_ok=True)

        # Get mods based on type
        with SessionLocal() as db:
            if mod_type == "client":
                mods = db.query(Mod).filter(Mod.client_required.is_(True)).all()
            else:  # server
                mods = db.query(Mod).filter(Mod.server_required.is_(True)).all()

            if not mods:
                QMessageBox.information(
                    self, self.translations["title_error"], self.translations["msg_no_mods_found"].format(mod_type)
                )
                return

            # Copy mod files to export directory
            success_count = 0
            errors = []

            for mod in mods:
                source_path = Path("mods") / mod.filename
                if not source_path.exists():
                    errors.append(f"File not found: {source_path}")
                    continue

                try:
                    # Copy the file to the export directory
                    shutil.copy2(source_path, export_dir / source_path.name)
                    success_count += 1
                except Exception as e:
                    errors.append(self.translations["msg_error_copy_file"].format(str(e)))

            # Show result message
            if success_count > 0:
                success_msg = self.translations["msg_export_success"].format(success_count, export_dir)
                if errors:
                    success_msg += "\n\n" + "\n".join(errors)
                QMessageBox.information(self, self.translations["title_export_success"], success_msg)
            else:
                error_msg = self.translations["msg_export_failed"].format("\n".join(errors))
                QMessageBox.critical(self, self.translations["title_error"], error_msg)

    def export_json(self):
        """Export all categories and mods data to a JSON file."""
        import json

        # Ask for save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self.translations["dialog_json_export"],
            "manual-mmdm.json",
            self.translations["dialog_json_filter"],
        )

        if not file_path:
            return

        # Add .json extension if not present
        if not file_path.lower().endswith(".json"):
            file_path += ".json"

        try:
            with SessionLocal() as db:
                # Get all categories ordered by name (case-insensitive)
                from sqlalchemy.sql import func

                categories = db.query(Category).order_by(func.lower(Category.name)).all()
                categories_data = []

                for category in categories:
                    categories_data.append({"name": category.name})

                # Get all mods ordered by name (case-insensitive)
                mods = db.query(Mod).order_by(func.lower(Mod.name)).all()
                mods_data = []

                for mod in mods:
                    # Get category names (sorted case-insensitive)
                    category_names = sorted([c.name for c in mod.categories], key=str.lower)

                    # Get dependency names (sorted case-insensitive)
                    dependency_names = sorted([d.name for d in mod.dependencies], key=str.lower)

                    mods_data.append(
                        {
                            "name": mod.name,
                            "filename": mod.filename,
                            "is_translated": mod.is_translated,
                            "client_required": mod.client_required,
                            "server_required": mod.server_required,
                            "notes": mod.notes,
                            "categories": category_names,
                            "dependencies": dependency_names,
                        }
                    )

                # Create export data
                export_data = {"categories": categories_data, "mods": mods_data}

                # Save to file
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=4)

                QMessageBox.information(
                    self,
                    self.translations["title_export_success"],
                    self.translations["msg_json_export_success"].format(file_path),
                )

        except Exception as e:
            QMessageBox.critical(
                self, self.translations["title_error"], self.translations["msg_json_export_failed"].format(str(e))
            )

    def export_dependency_tree(self):
        """Export mods dependency tree in formats similar to Python package managers."""
        # Ask for save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self.translations["dialog_dep_tree_export"],
            "dependency-tree.txt",
            self.translations["dialog_txt_filter"],
        )

        if not file_path:
            return

        # Add .txt extension if not present
        if not file_path.lower().endswith(".txt"):
            file_path += ".txt"

        try:
            with SessionLocal() as db:
                # Get all mods ordered by name (case-insensitive)
                from sqlalchemy.sql import func

                mods = db.query(Mod).order_by(func.lower(Mod.name)).all()

                # Build dependency tree
                output_text = ""

                # Header
                output_text += "Dependency Tree:\n"
                output_text += "=" * 50 + "\n\n"

                # Hierarchical dependency tree section
                output_text += "# Hierarchical Dependencies\n"

                # Find root mods (not dependencies of any other mod)
                all_dependencies = set()
                for mod in mods:
                    for dep in mod.dependencies:
                        all_dependencies.add(dep.name)

                root_mods = []
                for mod in mods:
                    if mod.name not in all_dependencies:
                        root_mods.append(mod)

                # If no root mods found, use all mods
                if not root_mods:
                    root_mods = mods

                # Sort root mods by name
                root_mods = sorted(root_mods, key=lambda x: x.name.lower())

                # Generate tree for each root mod
                for mod in root_mods:
                    output_text += f"{mod.name}\n"
                    for i, dep in enumerate(sorted(mod.dependencies, key=lambda x: x.name.lower())):
                        is_last = i == len(mod.dependencies) - 1
                        prefix = "└── " if is_last else "├── "
                        output_text += f"  {prefix}{dep.name}\n"

                        # Generate full tree for each dependency
                        tree_output = ""
                        tree_output = self._generate_dependency_tree(dep, tree_output, [mod.name], 1)
                        output_text += tree_output

                # Add flat dependencies list section
                output_text += "\n\n# Flat Dependencies List\n"
                for mod in sorted(mods, key=lambda x: x.name.lower()):
                    deps = sorted([d.name for d in mod.dependencies], key=str.lower)
                    output_text += f"{mod.name}"
                    if deps:
                        output_text += f" (dependencies: {', '.join(deps)})"
                    output_text += "\n"

                # Save to file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(output_text)

                QMessageBox.information(
                    self,
                    self.translations["title_export_success"],
                    self.translations["msg_dep_tree_export_success"].format(file_path),
                )

        except Exception as e:
            QMessageBox.critical(
                self, self.translations["title_error"], self.translations["msg_dep_tree_export_failed"].format(str(e))
            )

    def _generate_dependency_tree(self, mod, output, visited, level):
        """Recursively generate dependency tree for a mod."""
        # Prevent circular dependencies
        if mod.name in visited:
            indent = "  " * (level + 1)
            output += f"{indent}└── {mod.name} (circular dependency)\n"
            return output

        # Add this mod to visited list
        visited = visited + [mod.name]

        # Sort dependencies by name (case-insensitive)
        dependencies = sorted(mod.dependencies, key=lambda x: x.name.lower())

        for i, dep in enumerate(dependencies):
            indent = "  " * (level + 1)
            is_last = i == len(dependencies) - 1

            if is_last:
                prefix = "└── "
            else:
                prefix = "├── "

            output += f"{indent}{prefix}{dep.name}\n"

            # Recursively process dependencies
            with SessionLocal() as db:
                # Ensure dependency is attached to session
                dep = db.merge(dep)
                # Force loading dependencies to avoid detached instance errors
                _ = dep.dependencies
                # Call recursively with the updated visited list
                self._generate_dependency_tree(dep, output, visited, level + 1)

        return output

    def import_json(self):
        """Import categories and mods data from a JSON file."""
        import json
        from pathlib import Path

        # Ask for file location
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.translations["dialog_json_import"],
            "",
            self.translations["dialog_json_filter"],
        )

        if not file_path:
            return

        # Confirm import
        confirm = QMessageBox.question(
            self,
            self.translations["title_confirm_import"],
            self.translations["msg_json_import_confirm"],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            # Load JSON data
            with open(file_path, encoding="utf-8") as f:
                import_data = json.load(f)

            # Create mods directory if it doesn't exist
            mods_dir = Path("mods")
            mods_dir.mkdir(exist_ok=True)

            with SessionLocal() as db:
                # Clear existing data
                db.query(Mod).delete()
                db.query(Category).delete()
                db.commit()

                # Import categories
                categories = {}
                for category_data in import_data.get("categories", []):
                    category = Category(name=category_data["name"])
                    db.add(category)
                    db.flush()  # Flush to get ID
                    categories[category.name] = category

                # Ensure "Uncategorized" category exists
                if "Uncategorized" not in categories:
                    uncategorized = Category(name="Uncategorized")
                    db.add(uncategorized)
                    db.flush()
                    categories["Uncategorized"] = uncategorized

                # Import mods
                mods = {}
                for mod_data in import_data.get("mods", []):
                    mod = Mod(
                        name=mod_data["name"],
                        filename=mod_data["filename"],
                        is_translated=mod_data.get("is_translated", False),
                        client_required=mod_data.get("client_required", True),
                        server_required=mod_data.get("server_required", True),
                        notes=mod_data.get("notes", ""),
                    )

                    # Add categories
                    mod_categories = []
                    for category_name in mod_data.get("categories", []):
                        if category_name in categories:
                            mod_categories.append(categories[category_name])

                    if mod_categories:
                        mod.categories = mod_categories
                    else:
                        # If no categories, add to Uncategorized
                        mod.categories = [categories["Uncategorized"]]

                    db.add(mod)
                    db.flush()  # Flush to get ID
                    mods[mod.name] = mod

                # Set dependencies
                for mod_data in import_data.get("mods", []):
                    mod = mods.get(mod_data["name"])  # type: ignore
                    if mod:
                        dependencies = []
                        for dep_name in mod_data.get("dependencies", []):
                            if dep_name in mods:
                                dependencies.append(mods[dep_name])
                        mod.dependencies = dependencies

                db.commit()

                # Reload mods
                self.load_mods()

                QMessageBox.information(
                    self,
                    self.translations["title_import_success"],
                    self.translations["msg_json_import_success"].format(
                        len(import_data.get("categories", [])), len(import_data.get("mods", []))
                    ),
                )

        except Exception as e:
            QMessageBox.critical(
                self, self.translations["title_error"], self.translations["msg_json_import_failed"].format(str(e))
            )

    def show_about(self):
        """Show about dialog"""
        dialog = AboutDialog(self)
        dialog.exec()

    def showEvent(self, event):  # noqa: N802 (This is special method of Qt)
        """When window is shown, set initial column widths"""
        super().showEvent(event)
        header = self.mod_table.horizontalHeader()
        viewport = self.mod_table.viewport()
        if header and viewport:
            # Set all columns initial equal width
            total_width = viewport.width()
            column_width = total_width // self.mod_table.columnCount()
            for i in range(self.mod_table.columnCount()):
                header.resizeSection(i, column_width)
            # Store initial column width ratios
            self.update_column_ratios()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
