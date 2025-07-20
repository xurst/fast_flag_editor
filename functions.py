import json
import os
import imgui
import pygame
import shutil
from typing import Dict, Any, List

AUTOSAVE_DELAY = 1000
UPDATE_CHECK_INTERVAL = 5000  # Check for new Roblox version every 5 seconds

class FastFlagEditorApp:
    def __init__(self):
        self.flags: Dict[str, Any] = {}
        self.flag_types: Dict[str, str] = {}
        self.filtered_flags: List[str] = []

        self.search_text = ""
        self.selected_flags: Dict[str, bool] = {}

        self.autosave_scheduled_time: float = -1.0
        self.last_update_check_time: float = 0.0

        self.show_add_popup = False
        self.show_edit_popup = False
        self.show_remove_popup = False
        self.show_refresh_popup = False
        self.show_import_popup = False
        self.show_export_popup = False
        self.show_error_popup = False
        self.show_rename_popup = False
        self.popup_rename_old_name = ""
        self.popup_rename_new_name = ""
        self.popup_edit_new_name = ""
        self.last_selected_index = -1

        self.popup_add_name = ""
        self.popup_add_type_idx = 0
        self.popup_add_value = ""
        self.popup_edit_name = ""
        self.popup_edit_type_idx = 0
        self.popup_edit_value = ""
        self.popup_import_text = ""
        self.popup_export_text = ""
        self.error_popup_title = ""
        self.error_popup_message = ""

        self.flag_type_options = ["bool", "int", "string"]

        self.known_latest_version_path = self.get_latest_roblox_version_with_player()

        self.flags_enabled = True

        self.load_flags()

    def update(self):
        """Called every frame to handle time-based logic."""
        # --- Autosave logic ---
        if self.autosave_scheduled_time > 0 and pygame.time.get_ticks() > self.autosave_scheduled_time:
            self.save_flags()
            self.autosave_scheduled_time = -1.0

        # --- Roblox update check logic ---
        current_time = pygame.time.get_ticks()
        if current_time - self.last_update_check_time > UPDATE_CHECK_INTERVAL:
            self.check_for_roblox_update()
            self.last_update_check_time = current_time

    def check_for_roblox_update(self):
        """Periodically checks for a new Roblox version and migrates flags if needed."""
        current_latest_path = self.get_latest_roblox_version_with_player()

        if current_latest_path and current_latest_path != self.known_latest_version_path:
            old_version_path = self.known_latest_version_path
            old_settings_path = os.path.join(old_version_path, "ClientSettings", "ClientAppSettings.json")

            self.trigger_error_popup(
                "Roblox Update Detected",
                f"New version found!\nFrom: {os.path.basename(old_version_path)}\nTo: {os.path.basename(current_latest_path)}"
            )

            if os.path.exists(old_settings_path):
                try:
                    new_settings_dir = os.path.join(current_latest_path, "ClientSettings")
                    os.makedirs(new_settings_dir, exist_ok=True)
                    new_settings_path = os.path.join(new_settings_dir, "ClientAppSettings.json")
                    shutil.copy2(old_settings_path, new_settings_path)
                    print(f"Successfully copied flags from {old_version_path} to {current_latest_path}")
                except Exception as e:
                    self.trigger_error_popup("Migration Error", f"Could not copy flags: {e}")

            # Update to the new path and reload
            self.known_latest_version_path = current_latest_path
            self.load_flags()


    def draw_ui(self):
        """Draws the entire application UI and handles popup logic."""
        viewport = imgui.get_main_viewport()
        imgui.set_next_window_position(*viewport.pos)
        imgui.set_next_window_size(*viewport.size)
        window_flags = imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS

        opened, _ = imgui.begin("MainApp", closable=False, flags=window_flags)
        if opened:

            available_width = imgui.get_content_region_available_width()
            button_count = 5
            button_spacing = imgui.get_style().item_spacing.x
            button_width = (available_width - (button_spacing * (button_count - 1))) / button_count

            toggle_label = "Disable Flags" if self.flags_enabled else "Enable Flags"
            if imgui.button(toggle_label):
                self.flags_enabled = not self.flags_enabled
                self.schedule_autosave()
            imgui.separator()
            if imgui.button("Add Flag", width=button_width): self.trigger_add_popup()
            imgui.same_line()
            if imgui.button("Remove Selected", width=button_width): self.trigger_remove_popup()
            imgui.same_line()
            if imgui.button("Refresh", width=button_width): self.trigger_refresh_popup()
            imgui.same_line()
            if imgui.button("Import", width=button_width): self.trigger_import_popup()
            imgui.same_line()
            if imgui.button("Export", width=button_width): self.trigger_export_popup()

            imgui.separator()

            imgui.text("Search:")
            imgui.same_line()
            search_available_width = imgui.get_content_region_available_width()
            imgui.set_next_item_width(search_available_width)
            changed, self.search_text = imgui.input_text("##search", self.search_text, 256)
            if changed: self.filter_flags()

            imgui.separator()

            table_flags = (imgui.TABLE_BORDERS |
                        imgui.TABLE_RESIZABLE |
                        imgui.TABLE_SCROLL_Y |
                        imgui.TABLE_SIZING_STRETCH_PROP)

            if imgui.begin_table("FlagsTable", 4, flags=table_flags):

                imgui.table_setup_column("Actions", init_width_or_weight=1.5)
                imgui.table_setup_column("Name",    init_width_or_weight=5.0)
                imgui.table_setup_column("Type",    init_width_or_weight=2.0)
                imgui.table_setup_column("Value",   init_width_or_weight=3.0)
                imgui.table_headers_row()

                for key in list(self.filtered_flags):
                    value = self.flags.get(key)

                    if value is None: continue

                    flag_type = self.flag_types.get(key, "string")

                    imgui.table_next_row()

                    imgui.table_next_column()
                    available_width = imgui.get_content_region_available_width()
                    button_width = (available_width - imgui.get_style().item_spacing.x) / 0.96

                    if imgui.button(f"Edit##{key}", width=button_width, height=0):
                        self.trigger_edit_popup(key)

                    imgui.table_next_column()
                    is_selected = self.selected_flags.get(key, False)

                    clicked, _ = imgui.selectable(key, is_selected)

                    if imgui.is_item_hovered() and imgui.is_mouse_double_clicked():
                        self.trigger_edit_popup(key)
                    elif clicked:
                        current_index = self.filtered_flags.index(key)

                        if imgui.get_io().key_shift and self.last_selected_index != -1:

                            start_index = min(self.last_selected_index, current_index)
                            end_index = max(self.last_selected_index, current_index)

                            if not imgui.get_io().key_ctrl:
                                self.selected_flags.clear()

                            for i in range(start_index, end_index + 1):
                                flag_key = self.filtered_flags[i]
                                self.selected_flags[flag_key] = True
                        elif imgui.get_io().key_ctrl:

                            self.selected_flags[key] = not is_selected
                            self.last_selected_index = current_index
                        else:

                            self.selected_flags.clear()
                            self.selected_flags[key] = True
                            self.last_selected_index = current_index

                    imgui.table_next_column()
                    imgui.text(flag_type)

                    imgui.table_next_column()
                    imgui.text(str(value))

                imgui.end_table()

            self.draw_add_popup()
            self.draw_rename_popup()
            self.draw_edit_popup()
            self.draw_remove_popup()
            self.draw_import_popup()
            self.draw_export_popup()
            self.draw_error_popup()
            self.draw_refresh_popup()

        imgui.end()

    def schedule_autosave(self):
        self.autosave_scheduled_time = pygame.time.get_ticks() + AUTOSAVE_DELAY

    def get_latest_roblox_version_with_player(self):
        """Find the latest Roblox version folder that contains RobloxPlayerBeta.exe."""
        try:
            versions_dir = os.path.join(os.environ["LOCALAPPDATA"], "Roblox", "Versions")
            if not os.path.exists(versions_dir):
                return None

            version_folders = [
                os.path.join(versions_dir, d)
                for d in os.listdir(versions_dir)
                if os.path.isdir(os.path.join(versions_dir, d))
            ]

            if not version_folders:
                return None

            version_folders.sort(key=os.path.getmtime, reverse=True)

            for folder in version_folders:
                exe_path = os.path.join(folder, "RobloxPlayerBeta.exe")
                if os.path.exists(exe_path):
                    return folder

            return None

        except Exception:
            return None

    def load_flags(self):
        if not self.known_latest_version_path:
            self.flags = {}
            self.flag_types = {}
            self.filter_flags()
            self.trigger_error_popup("Load Error", "Could not find Roblox version folder. Starting with no flags.")
            return

        settings_file_path = os.path.join(
            self.known_latest_version_path, "ClientSettings", "ClientAppSettings.json"
        )

        try:
            if os.path.exists(settings_file_path):
                with open(settings_file_path, "r") as f:
                    content = f.read()
                    if content.strip():
                        self.flags = json.loads(content)
                        self.flags_enabled = True
                    else: # File is empty, assume flags are disabled
                        self.flags_enabled = False
            else: # File doesn't exist, start fresh
                self.flags = {}
                self.flags_enabled = True

            self.flag_types = {}
            for key, value in self.flags.items():
                self.flag_types[key] = self._deduce_type(value)

            self.filter_flags()
        except Exception as e:
            self.trigger_error_popup("Error Loading Flags", f"Failed to load flags: {e}")

    def save_flags(self):
        if not self.known_latest_version_path:
            self.trigger_error_popup("Save Error", "Could not find Roblox version folder. Cannot save.")
            return

        try:
            dst_dir = os.path.join(self.known_latest_version_path, "ClientSettings")
            os.makedirs(dst_dir, exist_ok=True)

            dst_path = os.path.join(dst_dir, "ClientAppSettings.json")
            
            with open(dst_path, "w") as f:
                if self.flags_enabled:
                    json.dump(self.flags, f, indent=2)
                else:
                    # Write empty content to disable flags, but don't delete the file
                    f.write("{}")

        except Exception as e:
            self.trigger_error_popup("Error Saving Flags", f"Failed to save flags: {e}")

    def filter_flags(self):
        search_lower = self.search_text.lower()
        if not search_lower:
            self.filtered_flags = sorted(self.flags.keys())
        else:
            self.filtered_flags = sorted([k for k in self.flags if search_lower in k.lower()])
        # Deselect flags after filtering to avoid confusion
        self.selected_flags.clear()
        self.last_selected_index = -1

    def _deduce_type(self, value: Any) -> str:
        if isinstance(value, bool): return "bool"
        if isinstance(value, int): return "int"
        if isinstance(value, str):
            if value.lower() in ("true", "false"): return "bool"
            if value.isdigit() or (value.startswith("-") and value[1:].isdigit()): return "int"
        return "string"

    def _validate_value(self, flag_type: str, value: str) -> bool:
        if flag_type == "bool": return value.lower() in ("true", "false")
        if flag_type == "int":
            try: int(value); return True
            except ValueError: return False
        return True

    def _convert_value(self, flag_type: str, value: str) -> Any:
        if flag_type == "bool": return value.lower() == "true"
        if flag_type == "int": return int(value)
        return value

    def trigger_add_popup(self):
        self.popup_add_name, self.popup_add_value = "", ""
        self.popup_add_type_idx = 0
        self.show_add_popup = True

    def trigger_rename_popup(self, key: str):
        self.popup_rename_old_name = key
        self.popup_rename_new_name = key
        self.show_rename_popup = True

    def trigger_edit_popup(self, key: str):
        self.popup_edit_name = key
        self.popup_edit_new_name = key
        self.popup_edit_value = str(self.flags[key])
        try:
            self.popup_edit_type_idx = self.flag_type_options.index(self.flag_types[key])
        except (ValueError, KeyError):
            self.popup_edit_type_idx = self.flag_type_options.index("string")
        self.show_edit_popup = True

    def trigger_remove_popup(self):
        if not any(self.selected_flags.values()):
            self.trigger_error_popup("No Selection", "Please select one or more flags to remove.")
            return
        self.show_remove_popup = True

    def trigger_import_popup(self):
        self.popup_import_text = ""
        self.show_import_popup = True

    def trigger_refresh_popup(self):
        self.show_refresh_popup = True

    def trigger_export_popup(self):
        self.popup_export_text = json.dumps(self.flags, indent=2)
        self.show_export_popup = True

    def trigger_error_popup(self, title: str, message: str):
        self.error_popup_title = title
        self.error_popup_message = message
        self.show_error_popup = True

    def draw_add_popup(self):
        if self.show_add_popup:
            imgui.open_popup("Add Flag")
            self.show_add_popup = False

        if imgui.begin_popup_modal("Add Flag", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)[0]:
            _, self.popup_add_name = imgui.input_text("Name", self.popup_add_name, 256)
            _, self.popup_add_type_idx = imgui.combo("Type", self.popup_add_type_idx, self.flag_type_options)
            _, self.popup_add_value = imgui.input_text("Value", self.popup_add_value, 256)
            imgui.separator()
            if imgui.button("Add"):
                name, type_str, value_str = self.popup_add_name.strip(), self.flag_type_options[self.popup_add_type_idx], self.popup_add_value.strip()
                if not name:
                    self.trigger_error_popup("Invalid Input", "Flag name cannot be empty.")
                elif name in self.flags:
                    self.trigger_error_popup("Invalid Input", "A flag with this name already exists.")
                elif not self._validate_value(type_str, value_str):
                    self.trigger_error_popup("Invalid Input", f"Value '{value_str}' is not a valid {type_str}.")
                else:
                    self.flags[name] = self._convert_value(type_str, value_str)
                    self.flag_types[name] = type_str
                    self.filter_flags()
                    self.schedule_autosave()
                    imgui.close_current_popup()
            imgui.same_line()
            if imgui.button("Cancel"):
                imgui.close_current_popup()
            imgui.end_popup()

    def draw_rename_popup(self):
        if self.show_rename_popup:
            imgui.open_popup("Rename Flag")
            self.show_rename_popup = False

        if imgui.begin_popup_modal("Rename Flag", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)[0]:
            imgui.text(f"Renaming: {self.popup_rename_old_name}")
            _, self.popup_rename_new_name = imgui.input_text("New Name", self.popup_rename_new_name, 256)
            imgui.separator()
            if imgui.button("Rename"):
                new_name = self.popup_rename_new_name.strip()
                if not new_name:
                    self.trigger_error_popup("Invalid Input", "Flag name cannot be empty.")
                elif new_name == self.popup_rename_old_name:
                    imgui.close_current_popup()
                elif new_name in self.flags:
                    self.trigger_error_popup("Invalid Input", "A flag with this name already exists.")
                else:

                    self.flags[new_name] = self.flags.pop(self.popup_rename_old_name)
                    self.flag_types[new_name] = self.flag_types.pop(self.popup_rename_old_name)
                    if self.selected_flags.get(self.popup_rename_old_name, False):
                        self.selected_flags.pop(self.popup_rename_old_name, None)
                        self.selected_flags[new_name] = True
                    self.filter_flags()
                    self.schedule_autosave()
                    imgui.close_current_popup()
            imgui.same_line()
            if imgui.button("Cancel"):
                imgui.close_current_popup()
            imgui.end_popup()

    def draw_edit_popup(self):
        if self.show_edit_popup:
            imgui.open_popup("Edit Flag")
            self.show_edit_popup = False

        if imgui.begin_popup_modal("Edit Flag", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)[0]:
            _, self.popup_edit_new_name = imgui.input_text("Name", self.popup_edit_new_name, 256)
            _, self.popup_edit_type_idx = imgui.combo("Type", self.popup_edit_type_idx, self.flag_type_options)
            _, self.popup_edit_value = imgui.input_text("Value", self.popup_edit_value, 256)
            imgui.separator()
            if imgui.button("Update"):
                new_name = self.popup_edit_new_name.strip()
                type_str, value_str = self.flag_type_options[self.popup_edit_type_idx], self.popup_edit_value.strip()

                if not new_name:
                    self.trigger_error_popup("Invalid Input", "Flag name cannot be empty.")
                elif not self._validate_value(type_str, value_str):
                    self.trigger_error_popup("Invalid Input", f"Value '{value_str}' is not a valid {type_str}.")
                elif new_name != self.popup_edit_name and new_name in self.flags:
                    self.trigger_error_popup("Invalid Input", "A flag with this name already exists.")
                else:

                    if new_name != self.popup_edit_name:

                        self.flags.pop(self.popup_edit_name, None)
                        self.flag_types.pop(self.popup_edit_name, None)

                        if self.selected_flags.get(self.popup_edit_name, False):
                            self.selected_flags.pop(self.popup_edit_name, None)
                            self.selected_flags[new_name] = True

                    self.flags[new_name] = self._convert_value(type_str, value_str)
                    self.flag_types[new_name] = type_str
                    self.filter_flags()
                    self.schedule_autosave()
                    imgui.close_current_popup()
            imgui.same_line()
            if imgui.button("Cancel"):
                imgui.close_current_popup()
            imgui.end_popup()

    def draw_remove_popup(self):
        if self.show_remove_popup:
            imgui.open_popup("Confirm Removal")
            self.show_remove_popup = False

        if imgui.begin_popup_modal("Confirm Removal", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)[0]:
            keys_to_remove = [k for k, v in self.selected_flags.items() if v]
            imgui.text(f"Are you sure you want to remove {len(keys_to_remove)} flag(s)?")
            imgui.separator()
            if imgui.button("Yes, Remove"):
                for key in keys_to_remove:
                    self.flags.pop(key, None)
                    self.flag_types.pop(key, None)
                self.filter_flags()
                self.schedule_autosave()
                imgui.close_current_popup()
            imgui.same_line()
            if imgui.button("Cancel"):
                imgui.close_current_popup()
            imgui.end_popup()

    def draw_import_popup(self):
        if self.show_import_popup:
            imgui.open_popup("Import Flags")
            self.show_import_popup = False

        if imgui.begin_popup_modal("Import Flags", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)[0]:
            imgui.text("Paste JSON content below:")
            _, self.popup_import_text = imgui.input_text_multiline("##importjson", self.popup_import_text, -1, 300)
            imgui.separator()

            def perform_import(overwrite: bool):
                try:
                    imported_data = json.loads(self.popup_import_text.strip() or "{}")
                    if not isinstance(imported_data, dict):
                        raise TypeError("Imported JSON is not a dictionary.")

                    processed_data = {}
                    for key, value in imported_data.items():
                        if isinstance(value, str):
                            if value.lower() in ("true", "false"):
                                processed_data[key] = value.lower() == "true"
                            elif value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
                                processed_data[key] = int(value)
                            else:
                                processed_data[key] = value
                        else:
                            processed_data[key] = value

                    if overwrite:
                        self.flags.clear()
                        self.flag_types.clear()

                    self.flags.update(processed_data)

                    for key, value in processed_data.items():
                        self.flag_types[key] = self._deduce_type(value)

                    self.filter_flags()
                    self.schedule_autosave()
                    imgui.close_current_popup()

                    flag_count = len(processed_data)
                    action = "Overwritten" if overwrite else "Merged"
                    self.trigger_error_popup("Import Successful", f"{action} {flag_count} flag(s) successfully!")

                except json.JSONDecodeError as e:
                    self.trigger_error_popup("Import Error", f"Invalid JSON format: {str(e)}")
                except Exception as e:
                    self.trigger_error_popup("Import Error", f"Failed to import flags: {str(e)}")

            if imgui.button("Merge"):
                perform_import(overwrite=False)
            imgui.same_line()
            if imgui.button("Overwrite"):
                perform_import(overwrite=True)
            imgui.same_line()
            if imgui.button("Cancel"):
                imgui.close_current_popup()
            imgui.end_popup()

    def draw_refresh_popup(self):
        if self.show_refresh_popup:
            imgui.open_popup("Confirm Refresh")
            self.show_refresh_popup = False

        if imgui.begin_popup_modal("Confirm Refresh", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)[0]:
            imgui.text("Are you sure you want to refresh?")
            imgui.text("This will reload all flags from the file and")
            imgui.text("discard any unsaved changes.")
            imgui.separator()

            if imgui.button("Yes, Refresh"):
                self.load_flags()
                imgui.close_current_popup()
            imgui.same_line()
            if imgui.button("Cancel"):
                imgui.close_current_popup()
            imgui.end_popup()

    def draw_export_popup(self):
        if self.show_export_popup:
            imgui.open_popup("Export Flags")
            self.show_export_popup = False

        if imgui.begin_popup_modal("Export Flags", flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)[0]:
            imgui.text("Copy the JSON content below:")
            imgui.input_text_multiline("##exportjson", self.popup_export_text, -1, 300, flags=imgui.INPUT_TEXT_READ_ONLY)
            imgui.separator()
            if imgui.button("Copy to Clipboard"):
                imgui.set_clipboard_text(self.popup_export_text)
            imgui.same_line()
            if imgui.button("Close"):
                imgui.close_current_popup()
            imgui.end_popup()

    def draw_error_popup(self):
        if self.show_error_popup:
            imgui.open_popup(self.error_popup_title)
            self.show_error_popup = False

        if imgui.begin_popup_modal(self.error_popup_title, flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)[0]:
            imgui.text(self.error_popup_message)
            imgui.separator()
            if imgui.button("OK"):
                imgui.close_current_popup()
            imgui.end_popup()