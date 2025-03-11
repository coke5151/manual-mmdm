"""Language resource file for the application."""

TRANSLATIONS = {
    "en": {
        # Window titles
        "main_window_title": "Minecraft Module Manager",
        "add_edit_mod_title": "Add/Edit Mod",
        "add_category_title": "Add Category",
        "edit_category_title": "Edit Category",
        "manage_categories_title": "Manage Categories",
        # Menu items
        "menu_file": "File",
        "menu_manage": "Manage",
        "menu_language": "Language",
        "menu_add_mod": "Add Module",
        "menu_edit_mod": "Edit Module",
        "menu_delete_mod": "Delete Module",
        "menu_exit": "Exit",
        "menu_add_category": "Add Category",
        "menu_manage_categories": "Manage Categories",
        # Buttons
        "button_browse": "Browse...",
        "button_save": "Save",
        "button_cancel": "Cancel",
        "button_close": "Close",
        "button_add": "Add",
        "button_edit": "Edit",
        "button_delete": "Delete",
        "button_expand_deps": "Expand Dependencies",
        "button_collapse_deps": "Collapse Dependencies",
        # Labels
        "label_module_name": "Module Name:",
        "label_module_file": "Module File:",
        "label_category": "Category:",
        "label_dependencies": "Dependencies:",
        "label_available_modules": "Available Modules:",
        "label_selected": "Selected:",
        "label_search": "Search:",
        "label_category_name": "Category Name:",
        "label_notes": "Notes:",
        "label_uncategorized": "Uncategorized",
        "msg_cannot_delete_uncategorized": "Cannot delete the Uncategorized category",
        # Table headers
        "header_module_name": "Module Name",
        "header_category": "Category",
        "header_translated": "Translated",
        "header_client": "Client",
        "header_server": "Server",
        "header_dependencies": "Dependencies",
        "header_filename": "File Name",
        "header_notes": "Notes",
        # Checkboxes
        "check_translated": "Translated",
        "check_client_required": "Client Required",
        "check_server_required": "Server Required",
        # Messages
        "msg_ready": "Ready",
        "msg_total_mods": "Total {} modules",
        "msg_select_module": "Please select a module",
        "msg_select_category": "Please select a category",
        "msg_unable_get_name": "Unable to get module name",
        "msg_name_empty": "Module name is empty",
        "msg_module_not_found": "Module not found",
        "msg_unable_delete": 'Unable to delete module "{}", because the following modules depend on it:\n{}',
        "msg_confirm_delete_mod": 'Are you sure you want to delete module "{}"?\n'
        + "Note: This will also delete the module file.",
        "msg_confirm_delete_category": 'Are you sure you want to delete category "{}"?\n'
        + "Note: This will remove all modules associated with this category.",
        "msg_error_delete_file": "Error deleting file: {}",
        "msg_name_file_empty": "Module name and file name cannot be empty",
        "msg_file_exists": "File {} already exists",
        "msg_error_rename_file": "Error renaming file: {}",
        "msg_choose_module_file": "Please choose module file",
        "msg_error_copy_file": "Error copying file: {}",
        "msg_yes": "Yes",
        "msg_no": "No",
        # Dialog titles
        "title_error": "Error",
        "title_warning": "Warning",
        "title_confirm_delete": "Confirm Delete",
        "title_unable_delete": "Unable to Delete",
        # File dialog
        "dialog_choose_mod": "Choose Module File",
        "dialog_mod_filter": "Minecraft Module Files (*.jar);;All Files (*.*)",
    },
    "zh_TW": {
        # Window titles
        "main_window_title": "Minecraft 模組管理器",
        "add_edit_mod_title": "新增/編輯模組",
        "add_category_title": "新增分類",
        "edit_category_title": "編輯分類",
        "manage_categories_title": "管理分類",
        # Menu items
        "menu_file": "檔案",
        "menu_manage": "管理",
        "menu_language": "語言",
        "menu_add_mod": "新增模組",
        "menu_edit_mod": "編輯模組",
        "menu_delete_mod": "刪除模組",
        "menu_exit": "結束",
        "menu_add_category": "新增分類",
        "menu_manage_categories": "管理分類",
        # Buttons
        "button_browse": "瀏覽...",
        "button_save": "儲存",
        "button_cancel": "取消",
        "button_close": "關閉",
        "button_add": "新增",
        "button_edit": "編輯",
        "button_delete": "刪除",
        "button_expand_deps": "展開相依性",
        "button_collapse_deps": "收合相依性",
        # Labels
        "label_module_name": "模組名稱:",
        "label_module_file": "模組檔案:",
        "label_category": "分類:",
        "label_dependencies": "相依性:",
        "label_available_modules": "可用模組:",
        "label_selected": "已選取:",
        "label_search": "搜尋:",
        "label_category_name": "分類名稱:",
        "label_notes": "備註:",
        "label_uncategorized": "無分類",
        "msg_cannot_delete_uncategorized": "無法刪除「無分類」分類",
        # Table headers
        "header_module_name": "模組名稱",
        "header_category": "分類",
        "header_translated": "已翻譯",
        "header_client": "客戶端",
        "header_server": "伺服器",
        "header_dependencies": "相依性",
        "header_filename": "檔案名稱",
        "header_notes": "備註",
        # Checkboxes
        "check_translated": "已翻譯",
        "check_client_required": "需要客戶端",
        "check_server_required": "需要伺服器",
        # Messages
        "msg_ready": "就緒",
        "msg_total_mods": "共 {} 個模組",
        "msg_select_module": "請先選擇一個模組",
        "msg_select_category": "請先選擇一個分類",
        "msg_unable_get_name": "無法獲取模組名稱",
        "msg_name_empty": "模組名稱為空",
        "msg_module_not_found": "找不到選擇的模組",
        "msg_unable_delete": "無法刪除模組「{}」，因為以下模組依賴它：\n{}",
        "msg_confirm_delete_mod": "確定要刪除模組「{}」嗎？\n注意：這將同時刪除模組檔案。",
        "msg_confirm_delete_category": "確定要刪除分類「{}」嗎？\n注意：這將移除所有模組與此分類的關聯。",
        "msg_error_delete_file": "刪除檔案時發生錯誤：{}",
        "msg_name_file_empty": "模組名稱和檔案名稱不能為空",
        "msg_file_exists": "檔案 {} 已經存在",
        "msg_error_rename_file": "重新命名檔案時發生錯誤：{}",
        "msg_choose_module_file": "請選擇模組檔案",
        "msg_error_copy_file": "複製檔案時發生錯誤：{}",
        "msg_yes": "是",
        "msg_no": "否",
        # Dialog titles
        "title_error": "錯誤",
        "title_warning": "警告",
        "title_confirm_delete": "確認刪除",
        "title_unable_delete": "無法刪除",
        # File dialog
        "dialog_choose_mod": "選擇模組檔案",
        "dialog_mod_filter": "Minecraft 模組檔案 (*.jar);;所有檔案 (*.*)",
    },
}
