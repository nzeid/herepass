"""
Copyright (c) 2022 Nader G. Zeid

This file is part of HerePass.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with HerePass. If not, see <https://www.gnu.org/licenses/gpl.html>.
"""

import gc
import math
import re
import secrets
import string
from pathlib import Path
from threading import Thread

from kivy import require as kivy_require
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.bubble import Bubble
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.filechooser import FileChooserController, FileChooserIconView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import escape_markup

from herepass import Group, HerePass, herepass_version

kivy_require("2.1.0")
Config.set("input", "mouse", "mouse,disable_multitouch")


class HerePassUI(App):
    def build(self):
        class HerePassFileChooser(FileChooserIconView):
            def on_selection(widget_1, widget_2, selections):
                if len(selections):
                    selected = selections[0]
                else:
                    selected = widget_1.path
                selected = Path(selected)
                if (
                    hasattr(widget_1, "assert_file")
                    and widget_1.assert_file
                    and not selected.is_file()
                ):
                    widget_1.target_label.color = data.error_font_color
                    widget_1.target_label.text = "You must a select a file!"
                    widget_1.has_errors = True
                elif (
                    hasattr(widget_1, "ensure_dir")
                    and widget_1.ensure_dir
                    and not selected.is_dir()
                ):
                    widget_1.target_label.color = data.font_color
                    widget_1.target_label.text = str(selected.parent)
                    widget_1.has_errors = False
                else:
                    widget_1.target_label.color = data.font_color
                    widget_1.target_label.text = str(selected)
                    widget_1.has_errors = False

        class ClosureData:
            pass

        data = ClosureData()

        def update_background_rectangle(widget, value):
            if isinstance(widget, RelativeLayout):
                widget.background_rectangle.pos = (0, 0)
            else:
                widget.background_rectangle.pos = widget.pos
            widget.background_rectangle.size = widget.size

        def set_background_color(widget, color):
            with widget.canvas.before:
                Color(color[0], color[1], color[2], color[3])
                if isinstance(widget, RelativeLayout):
                    widget.background_rectangle = Rectangle(
                        pos=(0, 0), size=widget.size
                    )
                else:
                    widget.background_rectangle = Rectangle(
                        pos=widget.pos, size=widget.size
                    )
            widget.bind(
                pos=update_background_rectangle, size=update_background_rectangle
            )

        def rectify_height(widget):
            min_height = widget.size_hint_min_y
            widget.target_height = dp(0)
            if (
                len(widget.children)
                and not isinstance(widget, FileChooserController)
                and not (
                    isinstance(widget, BoxLayout) and widget.orientation == "horizontal"
                )
                and not hasattr(widget, "target_height_disabled")
            ):
                for child in widget.children:
                    rectify_height(child)
                    widget.target_height += child.target_height
            else:
                widget.target_height += min_height
            if hasattr(widget, "padding") and not isinstance(widget, TextInput):
                if len(widget.padding) == 1:
                    widget.target_height += widget.padding * 2
                elif len(widget.padding) == 2:
                    widget.target_height += widget.padding[1] * 2
                else:
                    widget.target_height += widget.padding[1] + widget.padding[3]
            widget.size_hint_min_y = widget.target_height
            if hasattr(widget, "target_height_as_max") and widget.target_height_as_max:
                widget.size_hint_max_y = widget.target_height

        def sync_height(widget, moment=-1):
            target_widget = widget
            while target_widget.parent and hasattr(
                target_widget.parent, "target_height"
            ):
                target_widget = target_widget.parent
            widget_id = str(id(target_widget)) + " " + str(moment)
            if widget_id not in data.sync_height_tracker:
                data.sync_height_tracker[widget_id] = True

                def trigger_rectify_height(delta):
                    rectify_height(target_widget)
                    del data.sync_height_tracker[widget_id]

                Clock.schedule_once(trigger_rectify_height, moment)

        def generate_v_spacer(dp_height):
            return Widget(size_hint_min_y=dp(dp_height), size_hint_max_y=dp(dp_height))

        def generate_h_spacer(dp_width):
            return Widget(size_hint_min_x=dp(dp_width), size_hint_max_x=dp(dp_width))

        def generate_titled_separator(label, height):
            height = dp(height)
            separator = BoxLayout(
                orientation="horizontal",
                size_hint_min_y=height,
                size_hint_max_y=height,
            )
            dp_width = 2
            dp_label_space = 16
            # Left:
            left_line = generate_v_spacer(dp_width)
            set_background_color(left_line, data.line_gray)
            left_line_frame = AnchorLayout(
                anchor_x="center",
                anchor_y="center",
            )
            left_line_frame.add_widget(left_line)
            # Right:
            right_line = generate_v_spacer(dp_width)
            set_background_color(right_line, data.line_gray)
            right_line_frame = AnchorLayout(
                anchor_x="center",
                anchor_y="center",
            )
            right_line_frame.add_widget(right_line)
            # Label:
            separator_label = Label(
                text=label,
                halign="center",
                valign="middle",
                color=data.font_color_gray,
                font_size=dp(20),
            )

            def adjust_width(widget, value):
                width = value[0]
                separator_label.size_hint_min_x = width
                separator_label.size_hint_max_x = width

            separator_label.bind(texture_size=adjust_width)
            # Separator:
            separator.add_widget(left_line_frame)
            separator.add_widget(generate_h_spacer(dp_label_space))
            separator.add_widget(separator_label)
            separator.add_widget(generate_h_spacer(dp_label_space))
            separator.add_widget(right_line_frame)
            return separator

        def generate_separator(height):
            height = dp(height)
            separator = AnchorLayout(
                anchor_x="center",
                anchor_y="center",
                size_hint_min_y=height,
                size_hint_max_y=height,
            )
            separator.target_height_disabled = True
            line = generate_v_spacer(2)
            set_background_color(line, data.line_gray)
            separator.add_widget(line)
            return separator

        def set_text_input_enter(text_input, on_enter):
            def trigger_on_enter(widget):
                Clock.schedule_once(on_enter, 0)

            text_input.bind(on_text_validate=trigger_on_enter)

        def adjust_file_chooser_elements(widget, entry_widget, parent):
            entry_widget.children[0].color = data.font_color
            entry_widget.children[1].color = data.font_color

        def generate_button(text, height, font_size):
            button = Button(
                text=text,
                halign="center",
                valign="middle",
                size_hint_min_y=height,
                size_hint_max_y=height,
                font_size=font_size,
                bold=True,
                shorten=True,
            )
            button.bind(size=button.setter("text_size"))
            return button

        def flush_encrypted():
            data.current_file_handle.seek(0)
            data.current_file_handle.write(data.herepass.to_encrypted_json())
            data.current_file_handle.truncate()
            data.current_file_handle.flush()

        def adjust_text_size_width(widget, value):
            widget.text_size[0] = value

        def adjust_size_hint_y(widget, value):
            widget.size_hint_min_y = value[1]
            widget.size_hint_max_y = value[1]
            sync_height(widget)

        def lock_to_text_height(widget):
            adjust_text_size_width(widget, widget.width)
            adjust_size_hint_y(widget, widget.texture_size)
            widget.bind(width=adjust_text_size_width)
            widget.bind(texture_size=adjust_size_hint_y)

        def generate_sized_text_input(
            text,
            font_size,
            font_color,
            secret,
            multiline,
            editable,
            box,
            label=None,
            label_font_color=None,
        ):
            output = TextInput(
                size_hint_min_y=0,
                size_hint_max_y=0,
                foreground_color=font_color,
                font_name="Roboto-Regular.ttf",
                font_size=font_size,
                password=secret,
            )
            # When "password" is True, "text" assignment must be delayed:
            output.text = text

            if multiline:
                output.multiline = True
                output.do_wrap = True
                output.write_tab = True
            else:
                output.multiline = False
                output.do_wrap = False
                output.write_tab = False

                if not box:
                    output.padding = (0, output.padding[1], 0, output.padding[3])
                    output.border = (0, output.border[1], 0, output.border[3])

                    def adjust_text_input_width(first=None, second=None):
                        width = output._lines_labels[0].width
                        output.size_hint_min_x = width
                        output.size_hint_max_x = width

                    Clock.schedule_once(adjust_text_input_width, 0)
                    output.bind(text=adjust_text_input_width)

            if editable:
                output.readonly = False
                output.cursor_blink = True
            else:
                output.readonly = True
                output.cursor_blink = False
                output.cursor_width = 0
                if secret:
                    output.disabled = True

            if not box:
                output.background_color = (0, 0, 0, 0)

            if label:
                output.herepass_labeled = False

                def adjust_text_input_label(widget, focussed):
                    if focussed:
                        if output.herepass_labeled:
                            output.herepass_labeled = False
                            output.text = ""
                            output.font_name = "Roboto-Regular.ttf"
                            output.foreground_color = font_color
                    else:
                        if not output.text:
                            output.herepass_labeled = True
                            output.font_name = "Roboto-Italic.ttf"
                            output.foreground_color = label_font_color
                            output.text = label

                adjust_text_input_label(output, False)
                output.bind(focus=adjust_text_input_label)

            def adjust_text_input_height(first=None, second=None):
                height = (
                    (len(output._lines) * output.line_height)
                    + output.padding[1]
                    + output.padding[3]
                )
                output.size_hint_min_y = height
                output.size_hint_max_y = height

            def adjust_text_input_height_and_sync(first=None, second=None):
                adjust_text_input_height(first, second)
                sync_height(output)

            Clock.schedule_once(adjust_text_input_height, 0)
            sync_height(output, 0)
            output.bind(minimum_height=adjust_text_input_height_and_sync)
            return output

        def flash_popup(text, confirm_label, cancel_label, confirm_action):
            space_width = 20
            font_size = dp(18)
            button_height = dp(40)
            popup = ModalView(
                background_color=(0, 0, 0, 0), background="", auto_dismiss=False
            )
            popup_layout = ScrollView()
            popup_frame = AnchorLayout(
                anchor_x="center",
                anchor_y="top",
                size_hint_min_x=dp(400),
            )
            popup_frame.target_height = None
            popup_page = BoxLayout(
                orientation="vertical",
                size_hint_max_x=dp(600),
                padding=dp(space_width),
            )
            popup_page.target_height = None
            popup_page.target_height_as_max = True
            popup_label = Label(
                halign="left",
                valign="top",
                text=text,
                font_size=font_size,
                markup=True,
            )
            lock_to_text_height(popup_label)
            popup_confirm = generate_button(confirm_label, button_height, font_size)

            def confirm_popup(widget):
                popup.dismiss(animation=False)
                confirm_action()

            popup_confirm.bind(on_release=confirm_popup)
            popup_cancel = generate_button(cancel_label, button_height, font_size)

            def dismiss_popup(widget):
                popup.dismiss(animation=False)

            popup_cancel.bind(on_release=dismiss_popup)
            popup_page.add_widget(popup_label)
            popup_page.add_widget(generate_v_spacer(space_width))
            popup_page.add_widget(popup_confirm)
            popup_page.add_widget(generate_v_spacer(space_width))
            popup_page.add_widget(popup_cancel)
            popup_frame.add_widget(popup_page)
            popup_layout.add_widget(popup_frame)
            popup.add_widget(popup_layout)
            popup.open(animation=False)
            sync_height(popup_frame)

        def build_entry_view(group_entry, parent_widget):
            entry_view = BoxLayout(
                orientation="horizontal",
                size_hint_min_y=dp(40),
                size_hint_max_y=dp(40),
            )
            entry_view_spacer = generate_v_spacer(20)

            entry_label_scroller = ScrollView()
            entry_label_frame = AnchorLayout(anchor_x="right", anchor_y="top")
            entry_label = generate_sized_text_input(
                group_entry.get("label"),
                dp(18),
                data.font_color,
                False,
                False,
                False,
                False,
            )
            entry_label.halign = "center"
            entry_label_scroller.add_widget(entry_label_frame)
            entry_label_frame.add_widget(entry_label)

            def set_entry_label_frame_width(widget, width):
                entry_label_frame.size_hint_min_x = width

            entry_label.bind(width=set_entry_label_frame_width)
            entry_view.add_widget(entry_label_scroller)

            entry_view.add_widget(generate_h_spacer(6))

            secret_input = group_entry.get("secret")
            entry_content = generate_sized_text_input(
                "******" if secret_input else group_entry.get("content"),
                dp(18),
                data.font_color,
                secret_input,
                False,
                False,
                True,
            )
            entry_view.add_widget(entry_content)
            entry_view.add_widget(generate_h_spacer(6))

            entry_copy_button = generate_button("Copy", dp(40), dp(18))
            entry_copy_button.size_hint_min_x = dp(60)
            entry_copy_button.size_hint_max_x = dp(60)

            def copy_entry_content(widget):
                Clipboard.copy(group_entry.get("content"))

            entry_copy_button.bind(on_release=copy_entry_content)
            entry_view.add_widget(entry_copy_button)

            entry_view.add_widget(generate_h_spacer(6))

            if secret_input:
                entry_reveal_button = generate_button("Show", dp(40), dp(18))
                entry_reveal_button.size_hint_min_x = dp(60)
                entry_reveal_button.size_hint_max_x = dp(60)
                entry_reveal_button.herepass_revealed = False

                def reveal_entry_secret(widget):
                    if widget.herepass_revealed:
                        widget.herepass_revealed = False
                        widget.text = "Show"
                        entry_content.text = "******"
                        entry_content.cursor = (0, 0)
                        entry_content.password = True
                        entry_content.disabled = True
                    else:
                        widget.herepass_revealed = True
                        widget.text = "Hide"
                        entry_content.disabled = False
                        entry_content.password = False
                        entry_content.text = group_entry.get("content")
                        entry_content.cursor = (0, 0)

                entry_reveal_button.bind(on_release=reveal_entry_secret)
                entry_view.add_widget(entry_reveal_button)
            else:
                entry_view.add_widget(generate_h_spacer(60))

            parent_widget.add_widget(entry_view)
            parent_widget.add_widget(entry_view_spacer)
            # Don't forget to sync height later!
            return {"label_scroller": entry_label_scroller, "label": entry_label}

        def build_entry_form(group_entry, secret, parent_widget, rendered):
            entry_form = BoxLayout(
                orientation="horizontal",
                size_hint_min_y=dp(40),
                size_hint_max_y=dp(40),
            )
            entry_form.herepass_deleted = False
            entry_form_spacer = generate_v_spacer(20)
            entry_label = generate_sized_text_input(
                group_entry.get("label") if group_entry else "",
                dp(18),
                data.font_color,
                False,
                False,
                True,
                True,
                "Label",
                data.font_color_gray,
            )
            entry_form.add_widget(entry_label)
            entry_form.add_widget(generate_h_spacer(6))

            secret_input = group_entry.get("secret") if group_entry else secret
            if group_entry:
                initial_value = group_entry.get("content")
            else:
                if secret_input:
                    initial_value = "".join(
                        secrets.choice(data.alphanumeric) for i in range(16)
                    )
                else:
                    initial_value = ""

            entry_content = generate_sized_text_input(
                initial_value,
                dp(18),
                data.font_color,
                secret_input,
                False,
                True,
                True,
                "******" if secret_input else "Detail",
                data.font_color_gray,
            )

            entry_form.add_widget(entry_content)
            entry_form.add_widget(generate_h_spacer(6))
            entry_delete_button = generate_button("Delete", dp(40), dp(18))
            entry_delete_button.size_hint_min_x = dp(90)
            entry_delete_button.size_hint_max_x = dp(90)

            def delete_entry_form(widget):
                parent_widget.remove_widget(entry_form)
                parent_widget.remove_widget(entry_form_spacer)
                sync_height(parent_widget)
                entry_form.herepass_deleted = True

            entry_delete_button.bind(on_release=delete_entry_form)
            entry_form.add_widget(entry_delete_button)
            parent_widget.add_widget(entry_form)
            parent_widget.add_widget(entry_form_spacer)
            if rendered:
                sync_height(parent_widget)
            return (
                group_entry,
                {
                    "label": entry_label,
                    "content": entry_content,
                    "form": entry_form,
                },
            )

        def build_subgroup_view(subgroup, subgroup_parent_groups, parent_widget):
            def view_subgroup(widget):
                rebuild_group_page(subgroup, subgroup_parent_groups, False)

            subgroup_button = generate_button(subgroup.get("label"), dp(40), dp(18))
            subgroup_button.bind(on_release=view_subgroup)
            parent_widget.add_widget(subgroup_button)

        def build_subgroup_form(subgroup, parent_widget, rendered):
            subgroup_form = BoxLayout(
                orientation="horizontal",
                size_hint_min_y=dp(40),
                size_hint_max_y=dp(40),
            )
            subgroup_form.herepass_deleted = False
            subgroup_form_spacer = generate_v_spacer(20)
            subgroup_label = generate_sized_text_input(
                subgroup.get("label") if subgroup else "",
                dp(18),
                data.font_color,
                False,
                False,
                True,
                True,
                "Label",
                data.font_color_gray,
            )
            subgroup_form.add_widget(subgroup_label)
            subgroup_form.add_widget(generate_h_spacer(6))
            subgroup_delete_button = generate_button("Delete", dp(40), dp(18))
            subgroup_delete_button.size_hint_min_x = dp(90)
            subgroup_delete_button.size_hint_max_x = dp(90)

            def delete_subgroup_form(widget):
                parent_widget.remove_widget(subgroup_form)
                parent_widget.remove_widget(subgroup_form_spacer)
                sync_height(parent_widget)
                subgroup_form.herepass_deleted = True

            subgroup_delete_button.bind(on_release=delete_subgroup_form)
            subgroup_form.add_widget(subgroup_delete_button)
            parent_widget.add_widget(subgroup_form)
            parent_widget.add_widget(subgroup_form_spacer)
            if rendered:
                sync_height(parent_widget)
            return (
                subgroup,
                {
                    "label": subgroup_label,
                    "form": subgroup_form,
                },
            )

        def build_breadcrumbs(parent_groups):
            height = 22
            sep_height = 2
            if not len(parent_groups):
                placeholder = generate_v_spacer(height + (2 * sep_height))
                set_background_color(placeholder, data.bar_bg_color)
                return placeholder

            breadcrumb_list = []
            i = 0
            text = ""
            current_groups = []
            for parent_group in parent_groups:
                label = escape_markup(parent_group.get("label"))
                label = "[ref=" + str(i) + "][u]" + label + "[/u][/ref]"
                text += label + "  /  "
                breadcrumb = ClosureData()
                breadcrumb.target_group = parent_group
                breadcrumb.parent_groups = current_groups.copy()
                breadcrumb_list.append(breadcrumb)
                i += 1
                current_groups.append(parent_group)
            text = text[0:-5]
            breadcrumbs = Label(
                text=text,
                halign="left",
                size_hint_min_y=dp(height),
                size_hint_max_y=dp(height),
                color=data.font_color,
                font_size=dp(18),
                padding_x=dp(6),
                shorten=True,
                markup=True,
            )
            breadcrumbs.bind(size=breadcrumbs.setter("text_size"))

            def trigger_rebuild(widget, ref):
                breadcrumb = breadcrumb_list[int(ref)]
                rebuild_group_page(
                    breadcrumb.target_group, breadcrumb.parent_groups, False
                )

            breadcrumbs.bind(on_ref_press=trigger_rebuild)

            set_background_color(breadcrumbs, data.bar_bg_color)

            breadcrumbs_wrapper = BoxLayout(
                orientation="vertical",
            )
            separator = generate_v_spacer(sep_height)
            set_background_color(separator, data.bar_bg_color)
            breadcrumbs_wrapper.add_widget(separator)

            breadcrumbs_wrapper.add_widget(breadcrumbs)

            separator = generate_v_spacer(sep_height)
            set_background_color(separator, data.bar_bg_color)
            breadcrumbs_wrapper.add_widget(separator)

            return breadcrumbs_wrapper

        def build_group_search_page(target_group):
            # The actual page:
            group_page = BoxLayout(
                orientation="vertical",
                padding=dp(20),
                size_hint_min_y=0,
                size_hint_max_y=0,
                size_hint_max_x=dp(600),
            )
            group_page.target_height = None
            group_page.target_height_as_max = True

            search_bar = BoxLayout(
                orientation="horizontal",
                size_hint_min_y=dp(40),
                size_hint_max_y=dp(40),
            )
            search_input = generate_sized_text_input(
                "",
                dp(18),
                data.font_color,
                False,
                False,
                True,
                True,
                "Search...",
                data.font_color_gray,
            )
            search_bar.add_widget(search_input)
            search_bar.add_widget(generate_h_spacer(6))
            search_button = generate_button("Search", dp(40), dp(18))
            search_button.size_hint_min_x = dp(80)
            search_button.size_hint_max_x = dp(80)

            search_results = BoxLayout(
                orientation="vertical",
                size_hint_min_y=0,
                size_hint_max_y=0,
                size_hint_y=None,
                height=0,
            )

            def trigger_search(widget):
                search_phrase = search_input.text.strip()
                search_input.text = search_phrase
                search_results.clear_widgets()
                search_results.size_hint_y = 1
                if search_input.herepass_labeled or not search_phrase:
                    message = Label(
                        text="You must enter a search phrase.",
                        halign="left",
                        size_hint_min_y=dp(22),
                        size_hint_max_y=dp(22),
                        color=data.error_font_color,
                        font_size=dp(18),
                        shorten=True,
                    )
                    message.bind(size=message.setter("text_size"))
                    search_results.add_widget(generate_v_spacer(20))
                    search_results.add_widget(message)
                    sync_height(search_results, -1)
                    return
                matched = target_group.search(search_phrase)
                found = False
                for lineage in matched:
                    if not lineage[-1].get("deleted"):
                        found = True
                        break
                if found:
                    search_results.add_widget(generate_v_spacer(20))
                    search_results.add_widget(generate_separator(2))
                    for lineage in matched:
                        subgroup = lineage.pop()
                        if subgroup.get("deleted"):
                            continue
                        search_results.add_widget(generate_v_spacer(20))
                        build_subgroup_view(subgroup, lineage, search_results)
                    search_results.add_widget(generate_v_spacer(20))
                    search_results.add_widget(generate_separator(2))
                else:
                    message = Label(
                        text="Nothing found.",
                        halign="left",
                        size_hint_min_y=dp(22),
                        size_hint_max_y=dp(22),
                        color=data.font_color,
                        font_size=dp(18),
                        shorten=True,
                    )
                    message.bind(size=message.setter("text_size"))
                    search_results.add_widget(generate_v_spacer(20))
                    search_results.add_widget(message)
                sync_height(search_results, -1)

            search_button.bind(on_release=trigger_search)
            set_text_input_enter(search_input, trigger_search)

            search_bar.add_widget(search_button)

            cancel_button = generate_button("Cancel", dp(40), dp(18))
            cancel_button.size_hint_min_x = dp(80)
            cancel_button.size_hint_max_x = dp(80)

            def load_group(widget):
                rebuild_group_page(target_group, [], False)

            cancel_button.bind(on_release=load_group)
            search_bar.add_widget(generate_h_spacer(6))
            search_bar.add_widget(cancel_button)

            group_page.add_widget(search_bar)
            group_page.add_widget(search_results)

            def replace_widgets(delta):
                """
                It's necessary to delay widget replacement to frame 0 so that
                sync_height doesn't cause flickering.
                """
                data.main_frame.remove_widget(data.current_page)
                data.current_page = group_page
                gc.collect()

            show_main_layout(None)
            data.main_frame.add_widget(group_page)
            Clock.schedule_once(replace_widgets, 0)
            sync_height(group_page, 0)

        def rebuild_group_page(target_group, parent_groups, editable):
            # The root group cannot be deleted:
            if (
                data.edit_allowed
                and not len(parent_groups)
                and target_group.get("deleted")
            ):
                target_group.set("deleted", False)
                flush_encrypted()

            # Separate groups and entries:
            subgroups = []
            entries = []
            for subitem in target_group.get("entries"):
                if subitem.get("deleted"):
                    continue
                if isinstance(subitem, Group):
                    subgroups.append(subitem)
                else:
                    entries.append(subitem)

            # Pair elements:
            pairs = {
                "label": None,
                "description": None,
                "entries": [],
                "subgroups": [],
            }

            # The actual page:
            group_page = BoxLayout(
                orientation="vertical",
                padding=dp(20),
                size_hint_min_y=0,
                size_hint_max_y=0,
                size_hint_max_x=dp(600),
            )
            group_page.target_height = None
            group_page.target_height_as_max = True

            if editable:
                group_label = generate_sized_text_input(
                    target_group.get("label"),
                    dp(36),
                    data.font_color,
                    False,
                    True,
                    True,
                    True,
                    "Label",
                    data.font_color_gray,
                )
                pairs["label"] = (target_group, group_label)
            else:
                # Control bar:
                control_bar = BoxLayout(
                    orientation="horizontal",
                    size_hint_min_y=dp(40),
                    size_hint_max_y=dp(40),
                )

                # Back or Close button:
                if len(parent_groups):

                    def load_parent_group(widget):
                        rebuild_group_page(parent_groups.pop(), parent_groups, False)

                    back_button = generate_button("Back", dp(40), dp(18))
                    back_button.bind(on_release=load_parent_group)
                    control_bar.add_widget(back_button)
                else:
                    exit_button = generate_button("Close", dp(40), dp(18))
                    exit_button.bind(on_release=show_start_page)
                    control_bar.add_widget(exit_button)

                # Search button:
                root_group = parent_groups[0] if len(parent_groups) else target_group

                def load_group_search_page(widget):
                    build_group_search_page(root_group)

                search_button = generate_button("Search", dp(40), dp(18))
                search_button.bind(on_release=load_group_search_page)
                control_bar.add_widget(generate_h_spacer(10))
                control_bar.add_widget(search_button)

                # Edit button:
                if data.edit_allowed:

                    def load_group_editing(widget):
                        rebuild_group_page(target_group, parent_groups, True)

                    edit_button = generate_button("Edit", dp(40), dp(18))
                    edit_button.bind(on_release=load_group_editing)
                    control_bar.add_widget(generate_h_spacer(10))
                    control_bar.add_widget(edit_button)

                group_page.add_widget(control_bar)
                group_page.add_widget(generate_v_spacer(10))
                # Breadcrumbs:
                group_page.add_widget(build_breadcrumbs(parent_groups))
                group_page.add_widget(generate_v_spacer(10))
                # Group label:
                group_label = generate_sized_text_input(
                    target_group.get("label"),
                    dp(36),
                    data.font_color,
                    False,
                    True,
                    False,
                    False,
                )
            group_label.halign = "center"
            group_page.add_widget(group_label)

            if editable:
                group_page.add_widget(generate_v_spacer(10))
                group_description = generate_sized_text_input(
                    target_group.get("description") or "",
                    dp(18),
                    data.font_color,
                    False,
                    True,
                    True,
                    True,
                    "Details",
                    data.font_color_gray,
                )
                group_page.add_widget(group_description)
                pairs["description"] = (target_group, group_description)
            else:
                if target_group.get("description"):
                    group_page.add_widget(generate_v_spacer(10))
                    group_description = generate_sized_text_input(
                        target_group.get("description"),
                        dp(18),
                        data.font_color,
                        False,
                        True,
                        False,
                        False,
                    )
                    group_page.add_widget(group_description)

            if editable:
                entry_forms = BoxLayout(
                    orientation="vertical",
                    size_hint_min_y=0,
                    size_hint_max_y=0,
                )
                entry_forms.add_widget(generate_titled_separator("Entries", 60))
                entry_forms.target_height = None
                entry_forms.target_height_as_max = True
                group_page.add_widget(entry_forms)

                for entry in entries:
                    if not entry.get("deleted"):
                        pairs["entries"].append(
                            build_entry_form(entry, None, entry_forms, False)
                        )

                entry_add_buttons = BoxLayout(
                    orientation="horizontal",
                    size_hint_min_y=dp(40),
                    size_hint_max_y=dp(40),
                )

                def add_detail_form(widget):
                    pairs["entries"].append(
                        build_entry_form(None, False, entry_forms, True)
                    )

                entry_detail_button = generate_button("Add Detail", dp(40), dp(18))
                entry_detail_button.bind(on_release=add_detail_form)
                entry_add_buttons.add_widget(entry_detail_button)

                entry_add_buttons.add_widget(generate_h_spacer(10))

                def add_secret_form(widget):
                    pairs["entries"].append(
                        build_entry_form(None, True, entry_forms, True)
                    )

                entry_secret_button = generate_button("Add Secret", dp(40), dp(18))
                entry_secret_button.bind(on_release=add_secret_form)
                entry_add_buttons.add_widget(entry_secret_button)

                group_page.add_widget(entry_add_buttons)

                subgroup_forms = BoxLayout(
                    orientation="vertical",
                    size_hint_min_y=0,
                    size_hint_max_y=0,
                )
                subgroup_forms.add_widget(generate_titled_separator("Subgroups", 60))
                subgroup_forms.target_height = None
                subgroup_forms.target_height_as_max = True
                group_page.add_widget(subgroup_forms)

                for subgroup in subgroups:
                    if not subgroup.get("deleted"):
                        pairs["subgroups"].append(
                            build_subgroup_form(subgroup, subgroup_forms, False)
                        )

                def add_subgroup_form(widget):
                    pairs["subgroups"].append(
                        build_subgroup_form(None, subgroup_forms, True)
                    )

                group_add_button = generate_button("Add Subgroup", dp(40), dp(18))
                group_add_button.bind(on_release=add_subgroup_form)
                group_page.add_widget(group_add_button)
            else:
                if not (len(subgroups) or len(entries)):
                    group_page.add_widget(generate_v_spacer(20))
                    text = "There are currently no subgroups or entries."
                    if data.edit_allowed:
                        text += " Edit to add."
                    empty_alert = Label(
                        text=text,
                        size_hint_min_y=0,
                        color=data.font_color_gray,
                        font_size=dp(18),
                        italic=True,
                    )
                    group_page.add_widget(empty_alert)

                    def trigger_lock_to_text_height(delta):
                        lock_to_text_height(empty_alert)

                    Clock.schedule_once(trigger_lock_to_text_height, 0)
                else:
                    if len(entries):
                        group_page.add_widget(generate_v_spacer(24))
                        entry_views = []
                        for entry in entries:
                            if not entry.get("deleted"):
                                entry_views.append(build_entry_view(entry, group_page))

                        # Remove the last spacer:
                        group_page.remove_widget(group_page.children[0])

                        def justify_label_column(delta):
                            max_width = 0
                            for entry_view in entry_views:
                                current_width = (
                                    entry_view["label"]._lines_labels[0].width
                                )
                                current_width += dp(4)
                                if current_width > max_width:
                                    max_width = current_width
                            for entry_view in entry_views:
                                entry_view["label_scroller"].size_hint_max_x = max_width

                        Clock.schedule_once(justify_label_column, 0)
                    if len(subgroups):
                        if len(entries):
                            group_page.add_widget(generate_separator(42))
                        else:
                            group_page.add_widget(generate_separator(30))
                            group_page.add_widget(generate_v_spacer(6))
                        subgroup_parent_groups = parent_groups.copy()
                        subgroup_parent_groups.append(target_group)
                        for subgroup in subgroups:
                            if not subgroup.get("deleted"):
                                build_subgroup_view(
                                    subgroup, subgroup_parent_groups, group_page
                                )
                                group_page.add_widget(generate_v_spacer(20))
                        # Remove the last spacer:
                        group_page.remove_widget(group_page.children[0])

            if editable:
                group_page.add_widget(generate_separator(42))

                def validate_input(widget):
                    # Check label:
                    label = pairs["label"][1].text.strip()
                    pairs["label"][1].text = label
                    if pairs["label"][1].herepass_labeled or (not label):
                        show_error_bubble(
                            pairs["label"][1], "You must choose a label.", True
                        )
                        return
                    # Check description:
                    description = pairs["description"][1].text.strip()
                    pairs["description"][1].text = description
                    if pairs["description"][1].herepass_labeled or (not description):
                        description = None
                    # Check entries:
                    for pair in pairs["entries"]:
                        if not pair[1]["form"].herepass_deleted:
                            entry_label = pair[1]["label"].text.strip()
                            pair[1]["label"].text = entry_label
                            if pair[1]["label"].herepass_labeled or (not entry_label):
                                show_error_bubble(
                                    pair[1]["label"], "You must enter a label.", False
                                )
                                return
                            if pair[1]["content"].herepass_labeled or not len(
                                pair[1]["content"].text
                            ):
                                show_error_bubble(
                                    pair[1]["content"],
                                    "Please enter something.",
                                    False,
                                )
                                return
                    # Check subgroups:
                    for pair in pairs["subgroups"]:
                        if not pair[1]["form"].herepass_deleted:
                            subgroup_label = pair[1]["label"].text.strip()
                            pair[1]["label"].text = subgroup_label
                            if pair[1]["label"].herepass_labeled or (
                                not subgroup_label
                            ):
                                show_error_bubble(
                                    pair[1]["label"], "You must enter a label.", False
                                )
                                return
                    # Popup message:
                    popup_msg = ""
                    # Prompt label:
                    if pairs["label"][0].get("label") != label:
                        popup_msg += "[b]Label[/b][i] will change from [/i][b]"
                        popup_msg += escape_markup(pairs["label"][0].get("label"))
                        popup_msg += "[/b][i] to [/i][b]"
                        popup_msg += escape_markup(label)
                        popup_msg += "[/b][i].[/i]\n\n"
                    # Prompt description:
                    if pairs["description"][0].get("description") != description:
                        if pairs["description"][0].get("description") is None:
                            popup_msg += "[b]Description[/b][i] will be added.[/i]"
                        elif description is None:
                            popup_msg += "[b]Description[/b][i] will be deleted.[/i]"
                        else:
                            popup_msg += "[b]Description[/b][i] will change.[/i]"
                        popup_msg += "\n\n"
                    # Prompt entries:
                    entry_msg = ""
                    for pair in pairs["entries"]:
                        if pair[0]:
                            if pair[1]["form"].herepass_deleted:
                                entry_msg += "[b]Entry[/b][i] labeled [/i][b]"
                                entry_msg += escape_markup(pair[0].get("label"))
                                entry_msg += "[/b][i] will be deleted.[/i]\n"
                            else:
                                if pair[0].get("content") != pair[1]["content"].text:
                                    entry_msg += "[b]Entry[/b][i] labeled [/i][b]"
                                    entry_msg += escape_markup(pair[0].get("label"))
                                    entry_msg += "[/b][i] will change.[/i]\n"
                                if pair[0].get("label") != pair[1]["label"].text:
                                    entry_msg += "[b]Entry[/b][i] labeled [/i][b]"
                                    entry_msg += escape_markup(pair[0].get("label"))
                                    entry_msg += "[/b][i] will be renamed to [/i][b]"
                                    entry_msg += escape_markup(pair[1]["label"].text)
                                    entry_msg += "[/b][i].[/i]\n"
                        else:
                            if not pair[1]["form"].herepass_deleted:
                                entry_msg += "[b]Entry[/b][i] labeled [/i][b]"
                                entry_msg += escape_markup(pair[1]["label"].text)
                                entry_msg += "[/b][i] will be added.[/i]"
                                entry_msg += "\n"
                    if entry_msg:
                        popup_msg += entry_msg
                        popup_msg += "\n"
                    group_msg = ""
                    for pair in pairs["subgroups"]:
                        if pair[0]:
                            if pair[1]["form"].herepass_deleted:
                                group_msg += "[b]Subgroup[/b][i] labeled [/i][b]"
                                group_msg += escape_markup(pair[0].get("label"))
                                group_msg += "[/b][i] will be deleted.[/i]\n"
                            else:
                                if pair[0].get("label") != pair[1]["label"].text:
                                    group_msg += "[b]Subgroup[/b][i] labeled [/i][b]"
                                    group_msg += escape_markup(pair[0].get("label"))
                                    group_msg += "[/b][i] will be renamed to [/i][b]"
                                    group_msg += escape_markup(pair[1]["label"].text)
                                    group_msg += "[/b][i].[/i]\n"
                        else:
                            if not pair[1]["form"].herepass_deleted:
                                group_msg += "[b]Subgroup[/b][i] labeled [/i][b]"
                                group_msg += escape_markup(pair[1]["label"].text)
                                group_msg += "[/b][i] will be added.[/i]"
                                group_msg += "\n"
                    if group_msg:
                        popup_msg += group_msg
                        popup_msg += "\n"

                    if not popup_msg:
                        popup_msg += "[i]No changes were made.[/i]\n\n"

                    def save_and_load_group():
                        # Save label:
                        if pairs["label"][0].get("label") != label:
                            pairs["label"][0].set("label", label)
                        # Save description:
                        if pairs["description"][0].get("description") != description:
                            pairs["description"][0].set("description", description)
                        # Save entries:
                        for pair in pairs["entries"]:
                            if pair[0]:
                                if pair[1]["form"].herepass_deleted:
                                    pair[0].set("deleted", True)
                                else:
                                    if pair[0].get("label") != pair[1]["label"].text:
                                        pair[0].set("label", pair[1]["label"].text)
                                    if (
                                        pair[0].get("content")
                                        != pair[1]["content"].text
                                    ):
                                        pair[0].set("content", pair[1]["content"].text)
                                    if (
                                        pair[0].get("secret")
                                        != pair[1]["content"].password
                                    ):
                                        pair[0].set(
                                            "secret", pair[1]["content"].password
                                        )
                            else:
                                if not pair[1]["form"].herepass_deleted:
                                    target_group.add_entry(
                                        pair[1]["label"].text,
                                        pair[1]["content"].text,
                                        pair[1]["content"].password,
                                    )
                        # Save subgroups:
                        for pair in pairs["subgroups"]:
                            if pair[0]:
                                if pair[1]["form"].herepass_deleted:
                                    pair[0].set("deleted", True)
                                else:
                                    if pair[0].get("label") != pair[1]["label"].text:
                                        pair[0].set("label", pair[1]["label"].text)
                            else:
                                if not pair[1]["form"].herepass_deleted:
                                    target_group.add_group(pair[1]["label"].text, None)
                        #
                        flush_encrypted()
                        rebuild_group_page(target_group, parent_groups, False)

                    # Popup:
                    flash_popup(popup_msg, "Confirm", "Cancel", save_and_load_group)

                save_button = generate_button("Save", dp(40), dp(18))
                group_page.add_widget(save_button)
                save_button.bind(on_release=validate_input)
                group_page.add_widget(generate_v_spacer(20))

                def load_group(widget):
                    rebuild_group_page(target_group, parent_groups, False)

                cancel_button = generate_button("Cancel", dp(40), dp(18))
                cancel_button.bind(on_release=load_group)
                group_page.add_widget(cancel_button)

                group_page.add_widget(generate_v_spacer(20))
                group_page.add_widget(generate_separator(2))
            else:
                if len(subgroups):
                    group_page.add_widget(generate_v_spacer(20))
                    group_page.add_widget(generate_separator(2))

            def replace_widgets(delta):
                """
                It's necessary to delay widget replacement to frame 0 so that
                sync_height doesn't cause flickering.
                """
                data.main_frame.remove_widget(data.current_page)
                data.current_page = group_page
                gc.collect()

            show_main_layout(None)
            data.main_frame.add_widget(group_page)
            Clock.schedule_once(replace_widgets, 0)
            sync_height(group_page, 0)

        def generate_checkbox(text, dp_font_size, checked):
            font_size = dp(dp_font_size)
            height = dp(dp_font_size + math.ceil(dp_font_size / 3))
            row = BoxLayout(
                orientation="horizontal", size_hint_min_y=height, size_hint_max_y=height
            )
            checkbox_wrapper = AnchorLayout(
                anchor_x="center",
                anchor_y="center",
                size_hint_min_x=dp(24),
                size_hint_max_x=dp(24),
            )
            checkbox = CheckBox(color=data.font_color_gray, active=checked)
            checkbox_wrapper.add_widget(checkbox)
            row.add_widget(checkbox_wrapper)
            row.add_widget(generate_h_spacer(6))
            label = Label(
                text="[ref=0]" + escape_markup(text) + "[/ref]",
                halign="left",
                valign="middle",
                size_hint_min_y=height,
                size_hint_max_y=height,
                color=data.font_color,
                font_size=font_size,
                shorten=True,
                markup=True,
            )
            label.bind(size=label.setter("text_size"))

            def toggle_checkbox(widget, ref):
                checkbox.active = not checkbox.active

            label.bind(on_ref_press=toggle_checkbox)
            row.add_widget(label)
            return {"row": row, "checkbox": checkbox}

        def build_enter_password_page():
            data.enter_password_page = BoxLayout(
                orientation="vertical",
                padding=dp(20),
                size_hint_max_x=dp(600),
            )
            data.enter_password_page.target_height = None
            data.enter_password_page.target_height_as_max = True

            height = dp(24)
            data.enter_password_label = Label(
                text="Your selected file:",
                halign="left",
                size_hint_min_y=height,
                size_hint_max_y=height,
                color=data.font_color,
                font_size=dp(20),
            )
            data.enter_password_label.bind(
                size=data.enter_password_label.setter("text_size")
            )
            data.enter_password_page.add_widget(data.enter_password_label)

            data.enter_password_page.add_widget(generate_v_spacer(20))

            height = dp(24)
            data.enter_password_path_label = Label(
                text="",
                halign="left",
                size_hint_min_y=height,
                size_hint_max_y=height,
                color=data.font_color,
                font_size=dp(20),
                bold=True,
                shorten=True,
            )
            data.enter_password_path_label.bind(
                size=data.enter_password_path_label.setter("text_size")
            )
            data.enter_password_page.add_widget(data.enter_password_path_label)

            data.enter_password_page.add_widget(generate_v_spacer(20))

            height = dp(24)
            data.enter_password_label = Label(
                text="Enter the password:",
                halign="left",
                size_hint_min_y=height,
                size_hint_max_y=height,
                color=data.font_color,
                font_size=dp(20),
            )
            data.enter_password_label.bind(
                size=data.enter_password_label.setter("text_size")
            )
            data.enter_password_page.add_widget(data.enter_password_label)

            data.enter_password_page.add_widget(generate_v_spacer(20))

            data.enter_password_input_frame = AnchorLayout(
                anchor_x="left",
                anchor_y="center",
            )
            data.enter_password_page.add_widget(data.enter_password_input_frame)

            data.enter_password_input = BoxLayout(
                orientation="vertical", size_hint_max_x=dp(300)
            )
            data.enter_password_input_frame.add_widget(data.enter_password_input)

            height = dp(40)
            font_size = dp(20)
            data.enter_password_text_input = TextInput(
                size_hint_min_y=height,
                size_hint_max_y=height,
                padding=(dp(6), dp(6), dp(6), dp(3)),
                font_size=font_size,
                multiline=False,
                write_tab=False,
                password=True,
            )
            data.enter_password_input.add_widget(data.enter_password_text_input)

            data.enter_password_page.add_widget(generate_v_spacer(20))

            checkbox = generate_checkbox("Allow changes?", 18, False)
            data.enter_password_page.add_widget(checkbox["row"])
            data.edit_allowed_checkbox = checkbox["checkbox"]

            data.enter_password_page.add_widget(generate_v_spacer(20))

            data.enter_password_load = generate_button("Load", dp(40), dp(18))
            data.enter_password_page.add_widget(data.enter_password_load)
            data.enter_password_load.bind(on_release=load_for_group_page)

            set_text_input_enter(data.enter_password_text_input, load_for_group_page)

            data.enter_password_page.add_widget(generate_v_spacer(20))

            data.enter_password_cancel = generate_button("Cancel", dp(40), dp(18))
            data.enter_password_page.add_widget(data.enter_password_cancel)
            data.enter_password_cancel.bind(on_release=show_start_page)

            # Don't forget to rectify heights!
            sync_height(data.enter_password_page)

        def build_choose_password_page():
            data.choose_password_page = BoxLayout(
                orientation="vertical",
                padding=dp(20),
                size_hint_max_x=dp(600),
            )
            data.choose_password_page.target_height = None
            data.choose_password_page.target_height_as_max = True

            height = dp(24)
            data.choose_password_label = Label(
                text="Your new file:",
                halign="left",
                size_hint_min_y=height,
                size_hint_max_y=height,
                color=data.font_color,
                font_size=dp(20),
            )
            data.choose_password_label.bind(
                size=data.choose_password_label.setter("text_size")
            )
            data.choose_password_page.add_widget(data.choose_password_label)

            data.choose_password_page.add_widget(generate_v_spacer(20))

            height = dp(24)
            data.choose_password_path_label = Label(
                text="",
                halign="left",
                size_hint_min_y=height,
                size_hint_max_y=height,
                color=data.font_color,
                font_size=dp(20),
                bold=True,
                shorten=True,
            )
            data.choose_password_path_label.bind(
                size=data.choose_password_path_label.setter("text_size")
            )
            data.choose_password_page.add_widget(data.choose_password_path_label)

            data.choose_password_page.add_widget(generate_v_spacer(20))

            height = dp(24)
            data.choose_password_label = Label(
                text="Choose a strong password:",
                halign="left",
                size_hint_min_y=height,
                size_hint_max_y=height,
                color=data.font_color,
                font_size=dp(20),
            )
            data.choose_password_label.bind(
                size=data.choose_password_label.setter("text_size")
            )
            data.choose_password_page.add_widget(data.choose_password_label)

            data.choose_password_page.add_widget(generate_v_spacer(20))

            data.choose_password_input_frame = AnchorLayout(
                anchor_x="left",
                anchor_y="center",
            )
            data.choose_password_page.add_widget(data.choose_password_input_frame)

            data.choose_password_input = BoxLayout(
                orientation="vertical", size_hint_max_x=dp(300)
            )
            data.choose_password_input_frame.add_widget(data.choose_password_input)

            height = dp(40)
            font_size = dp(20)
            data.choose_password_first_input = TextInput(
                size_hint_min_y=height,
                size_hint_max_y=height,
                padding=(dp(6), dp(6), dp(6), dp(3)),
                font_size=font_size,
                multiline=False,
                write_tab=False,
                password=True,
            )

            data.choose_password_input.add_widget(data.choose_password_first_input)

            data.choose_password_input.add_widget(generate_v_spacer(20))

            height = dp(40)
            font_size = dp(20)
            data.choose_password_second_input = TextInput(
                size_hint_min_y=height,
                size_hint_max_y=height,
                padding=(dp(6), dp(6), dp(6), dp(3)),
                font_size=font_size,
                multiline=False,
                write_tab=False,
                password=True,
            )
            data.choose_password_input.add_widget(data.choose_password_second_input)

            data.choose_password_page.add_widget(generate_v_spacer(20))

            data.choose_password_create = generate_button("Create", dp(40), dp(18))
            data.choose_password_page.add_widget(data.choose_password_create)
            data.choose_password_create.bind(on_release=create_for_group_page)

            set_text_input_enter(
                data.choose_password_first_input, create_for_group_page
            )
            set_text_input_enter(
                data.choose_password_second_input, create_for_group_page
            )

            data.choose_password_page.add_widget(generate_v_spacer(20))

            data.choose_password_cancel = generate_button("Cancel", dp(40), dp(18))
            data.choose_password_page.add_widget(data.choose_password_cancel)
            data.choose_password_cancel.bind(on_release=show_start_page)

            # Don't forget to rectify heights!
            sync_height(data.choose_password_page)

        def clear_password_fields():
            data.choose_password_first_input.text = ""
            data.choose_password_second_input.text = ""
            data.enter_password_text_input.text = ""

        def build_file_load_layout():
            data.file_load_layout = AnchorLayout(
                anchor_x="center",
                anchor_y="top",
                size_hint_min_x=dp(300),
            )
            data.file_load_layout.target_height = None

            data.file_load_page = BoxLayout(
                orientation="vertical",
                padding=dp(20),
                size_hint_max_x=dp(600),
                size_hint_max_y=dp(600),
            )
            data.file_load_page.target_height = None
            data.file_load_layout.add_widget(data.file_load_page)

            height = dp(24)
            data.file_load_label = Label(
                text="Select the encrypted file:",
                halign="left",
                size_hint_min_y=height,
                size_hint_max_y=height,
                color=data.font_color,
                font_size=dp(20),
                shorten=True,
            )
            data.file_load_label.bind(size=data.file_load_label.setter("text_size"))
            data.file_load_page.add_widget(data.file_load_label)

            data.file_load_page.add_widget(generate_v_spacer(20))

            home_path = str(Path.home())
            data.file_load_chooser = HerePassFileChooser(
                size_hint_min_y=dp(200),
                dirselect=True,
                multiselect=False,
                path=home_path,
            )
            data.file_load_page.add_widget(data.file_load_chooser)
            data.file_load_chooser.bind(on_entry_added=adjust_file_chooser_elements)

            data.file_load_page.add_widget(generate_v_spacer(20))

            height = dp(24)
            data.file_load_path_label = Label(
                text="Select an encrypted file.",
                halign="left",
                size_hint_min_y=height,
                size_hint_max_y=height,
                color=data.font_color,
                font_size=dp(20),
                shorten=True,
            )
            data.file_load_path_label.bind(
                size=data.file_load_path_label.setter("text_size")
            )
            data.file_load_page.add_widget(data.file_load_path_label)

            data.file_load_chooser.target_label = data.file_load_path_label
            data.file_load_chooser.assert_file = True
            data.file_load_chooser.has_errors = True

            data.file_load_page.add_widget(generate_v_spacer(20))

            data.file_load_continue = generate_button("Continue", dp(40), dp(18))
            data.file_load_page.add_widget(data.file_load_continue)
            data.file_load_continue.bind(on_release=show_enter_password_page)

            data.file_load_page.add_widget(generate_v_spacer(20))

            data.file_load_cancel = generate_button("Cancel", dp(40), dp(18))
            data.file_load_page.add_widget(data.file_load_cancel)
            data.file_load_cancel.bind(on_release=show_start_page)

            # Don't forget to rectify heights!
            sync_height(data.file_load_page)

        def build_file_create_layout():
            data.file_create_layout = AnchorLayout(
                anchor_x="center",
                anchor_y="top",
                size_hint_min_x=dp(300),
            )
            data.file_create_layout.target_height = None

            data.file_create_page = BoxLayout(
                orientation="vertical",
                padding=dp(20),
                size_hint_max_x=dp(600),
                size_hint_max_y=dp(600),
            )
            data.file_create_page.target_height = None
            data.file_create_layout.add_widget(data.file_create_page)

            height = dp(24)
            data.file_create_label = Label(
                text="Select the new file's directory:",
                halign="left",
                size_hint_min_y=height,
                size_hint_max_y=height,
                color=data.font_color,
                font_size=dp(20),
                shorten=True,
            )
            data.file_create_label.bind(size=data.file_create_label.setter("text_size"))
            data.file_create_page.add_widget(data.file_create_label)

            data.file_create_page.add_widget(generate_v_spacer(20))

            home_path = str(Path.home())
            data.file_create_chooser = HerePassFileChooser(
                size_hint_min_y=dp(200),
                dirselect=True,
                multiselect=False,
                path=home_path,
            )
            data.file_create_page.add_widget(data.file_create_chooser)
            data.file_create_chooser.bind(on_entry_added=adjust_file_chooser_elements)

            data.file_create_page.add_widget(generate_v_spacer(20))

            height = dp(24)
            data.file_create_path_label = Label(
                text=data.file_create_chooser.path,
                halign="left",
                size_hint_min_y=height,
                size_hint_max_y=height,
                color=data.font_color,
                font_size=dp(20),
                shorten=True,
            )
            data.file_create_path_label.bind(
                size=data.file_create_path_label.setter("text_size")
            )
            data.file_create_page.add_widget(data.file_create_path_label)

            data.file_create_chooser.target_label = data.file_create_path_label
            data.file_create_chooser.ensure_dir = True
            data.file_create_chooser.has_errors = False

            data.file_create_page.add_widget(generate_v_spacer(20))

            data.file_create_name_form = BoxLayout(
                orientation="horizontal", size_hint_min_y=dp(40), size_hint_max_y=dp(40)
            )
            data.file_create_page.add_widget(data.file_create_name_form)

            font_size = dp(20)
            data.file_create_name_input = TextInput(
                padding=(dp(6), dp(6), dp(6), dp(3)),
                font_size=font_size,
                multiline=False,
                write_tab=False,
            )
            data.file_create_name_form.add_widget(data.file_create_name_input)
            data.file_create_name_label = Label(
                text=data.file_suffix,
                halign="left",
                valign="top",
                padding=(0, dp(6)),
                size_hint_x=0.6,
                color=data.font_color,
                font_size=font_size,
            )
            data.file_create_name_label.bind(
                size=data.file_create_name_label.setter("text_size")
            )
            data.file_create_name_form.add_widget(data.file_create_name_label)

            data.file_create_page.add_widget(generate_v_spacer(20))

            data.file_create_continue = generate_button("Continue", dp(40), dp(18))
            data.file_create_page.add_widget(data.file_create_continue)
            data.file_create_continue.bind(on_release=show_choose_password_page)

            set_text_input_enter(data.file_create_name_input, show_choose_password_page)

            data.file_create_page.add_widget(generate_v_spacer(20))

            data.file_create_cancel = generate_button("Cancel", dp(40), dp(18))
            data.file_create_page.add_widget(data.file_create_cancel)
            data.file_create_cancel.bind(on_release=show_start_page)

            # Don't forget to rectify heights!
            sync_height(data.file_create_page)

        def build_start_page():
            data.start_page = BoxLayout(
                orientation="vertical",
                padding=dp(20),
                size_hint_max_x=dp(600),
            )
            data.start_page.target_height = None
            data.start_page.target_height_as_max = True

            data.start_page.add_widget(
                Label(
                    text="HerePass",
                    size_hint_min_y=dp(42),
                    size_hint_max_y=dp(42),
                    color=data.font_color,
                    font_size=dp(36),
                )
            )

            data.start_page.add_widget(
                Label(
                    text="Version " + herepass_version,
                    size_hint_min_y=dp(18),
                    size_hint_max_y=dp(18),
                    color=data.font_color,
                    font_size=dp(16),
                    bold=True,
                )
            )

            data.start_page.add_widget(generate_v_spacer(30))

            data.create_file_button = generate_button(
                "Create a New File", dp(50), dp(20)
            )
            data.start_page.add_widget(data.create_file_button)
            data.create_file_button.bind(on_release=show_file_create_layout)

            data.start_page.add_widget(generate_v_spacer(30))

            data.load_file_button = generate_button(
                "Load an Existing File", dp(50), dp(20)
            )
            data.start_page.add_widget(data.load_file_button)
            data.load_file_button.bind(on_release=show_file_load_layout)

            # Don't forget to rectify heights!
            sync_height(data.start_page)

        def build_main_layout():
            data.main_layout = ScrollView()
            data.main_frame = AnchorLayout(
                anchor_x="center",
                anchor_y="top",
                size_hint_min_x=dp(400),
            )
            data.main_frame.target_height = None
            data.main_layout.add_widget(data.main_frame)

        def anchor_error_bubble(a=None, b=None):
            pos = data.error_widget.to_window(data.error_widget.x, data.error_widget.y)
            data.error_bubble.x = pos[0]
            if data.error_bubble_below:
                data.error_bubble.y = pos[1] - data.error_bubble.height + dp(4)
            else:
                data.error_bubble.y = pos[1] + data.error_widget.height - dp(4)

        def adjust_error_bubble_height(widget, texture_size):
            data.error_bubble.height = texture_size[1] + data.error_bubble_padding
            data.error_bubble_label.height = texture_size[1]
            anchor_error_bubble()

        def destroy_error_bubble(a=None, b=None, c=None, d=None, e=None):
            if data.error_bubble:
                data.window.unbind(on_touch_down=destroy_error_bubble)
                Window.unbind(on_keyboard=destroy_error_bubble)
                data.window.remove_widget(data.error_bubble)
                data.error_bubble_label.unbind(texture_size=adjust_error_bubble_height)
                data.window.unbind(size=anchor_error_bubble, pos=anchor_error_bubble)
                data.error_bubble_label = None
                data.error_bubble = None
                data.error_widget = None

        def show_error_bubble(widget, message, below):
            font_size = dp(16)
            bubble_width = dp(260)
            text_width = bubble_width - data.error_bubble_padding
            destroy_error_bubble()
            if isinstance(data.main_layout, ScrollView):
                data.main_layout.scroll_to(widget, dp(60), False)
            data.error_widget = widget
            if below:
                data.error_bubble = Bubble(
                    size_hint=(None, None),
                    width=bubble_width,
                    arrow_pos="top_mid",
                )
            else:
                data.error_bubble = Bubble(
                    size_hint=(None, None),
                    width=bubble_width,
                )
            data.error_bubble_below = below
            data.window.bind(size=anchor_error_bubble, pos=anchor_error_bubble)
            data.error_bubble_label = Label(
                text=message,
                halign="center",
                color=data.light_error_font_color,
                bold=True,
                font_size=font_size,
                width=text_width,
                text_size=(text_width, None),
            )
            data.error_bubble_label.bind(texture_size=adjust_error_bubble_height)
            data.error_bubble.add_widget(data.error_bubble_label)
            data.window.add_widget(data.error_bubble)
            data.window.bind(on_touch_down=destroy_error_bubble)
            Window.bind(on_keyboard=destroy_error_bubble)

        def disable_create_button(delta=None):
            data.choose_password_create.unbind(on_release=create_for_group_page)
            data.choose_password_create.disabled = True
            data.choose_password_create.text = "Encrypting new file..."

        def enable_create_button(delta=None):
            data.choose_password_create.text = "Create"
            data.choose_password_create.disabled = False
            data.choose_password_create.bind(on_release=create_for_group_page)

        def disable_load_button(delta=None):
            data.enter_password_load.unbind(on_release=load_for_group_page)
            data.enter_password_load.disabled = True
            data.enter_password_load.text = "Decrypting selected file..."

        def enable_load_button(delta=None):
            data.enter_password_load.text = "Load"
            data.enter_password_load.disabled = False
            data.enter_password_load.bind(on_release=load_for_group_page)

        def load_and_decrypt():
            data.herepass = HerePass()
            data.current_file_handle.seek(0)
            try:
                data.herepass.from_encrypted_json(
                    data.passphrase, data.current_file_handle.read()
                )
                data.herepass_error = None
            except Exception as error:
                del data.herepass
                data.herepass_error = str(error).strip()
            del data.passphrase

        def end_load_and_decrypt(delta):
            if not data.load_thread.is_alive():
                Clock.unschedule(data.load_thread_monitor)
                del data.load_thread_monitor
                del data.load_thread
                # Sync with group page:
                Clock.schedule_once(enable_load_button, 0)
                #
                if data.herepass_error is None:
                    data.edit_allowed = data.edit_allowed_checkbox.active
                    if data.edit_allowed:
                        try:
                            new_file_handle = open(data.current_file, "rb+")
                        except OSError:
                            show_error_bubble(
                                data.enter_password_load,
                                "Unable to edit the selected file!",
                                False,
                            )
                            return
                        data.current_file_handle.close()
                        data.current_file_handle = new_file_handle
                    data.edit_allowed_checkbox.active = False
                    rebuild_group_page(data.herepass.group, [], False)
                    return
                show_error_bubble(
                    data.enter_password_load,
                    "Decryption error: " + data.herepass_error,
                    False,
                )

        def begin_load_and_decrypt(delta):
            data.load_thread = Thread(target=load_and_decrypt)
            data.load_thread.start()
            data.load_thread_monitor = Clock.schedule_interval(
                end_load_and_decrypt, 0.125
            )

        def load_for_group_page(widget):
            if not data.enter_password_text_input.text:
                show_error_bubble(
                    data.enter_password_text_input,
                    "Please enter a password!",
                    False,
                )
                return
            data.passphrase = data.enter_password_text_input.text
            clear_password_fields()
            disable_load_button()
            Clock.schedule_once(begin_load_and_decrypt)

        def create_and_encrypt():
            data.herepass = HerePass()
            try:
                data.herepass.create(data.passphrase)
                data.herepass_error = None
            except Exception as error:
                del data.herepass
                data.herepass_error = str(error).strip()
            del data.passphrase
            if data.herepass_error is None:
                flush_encrypted()

        def end_create_and_encrypt(delta):
            if not data.create_thread.is_alive():
                Clock.unschedule(data.create_thread_monitor)
                del data.create_thread_monitor
                del data.create_thread
                # Sync with group page:
                Clock.schedule_once(enable_create_button, 0)
                #
                if data.herepass_error is None:
                    data.edit_allowed = True
                    rebuild_group_page(data.herepass.group, [], False)
                    return
                show_error_bubble(
                    data.choose_password_create,
                    "Encryption error: " + data.herepass_error,
                    False,
                )

        def begin_create_and_encrypt(delta):
            data.create_thread = Thread(target=create_and_encrypt)
            data.create_thread.start()
            data.create_thread_monitor = Clock.schedule_interval(
                end_create_and_encrypt, 0.125
            )

        def create_for_group_page(widget):
            if (
                data.choose_password_first_input.text
                != data.choose_password_second_input.text
            ):
                show_error_bubble(
                    data.choose_password_first_input,
                    "The passwords entered must match!",
                    False,
                )
                return
            if len(data.choose_password_first_input.text) < 6:
                show_error_bubble(
                    data.choose_password_first_input,
                    "A password must be at least\n6 characters long!",
                    False,
                )
                return
            data.passphrase = data.choose_password_first_input.text
            clear_password_fields()
            disable_create_button()
            Clock.schedule_once(begin_create_and_encrypt)

        def clean_up_current_file():
            if data.current_file_handle:
                data.current_file_handle.close()
                data.current_file_handle = None
            if data.current_file:
                if not data.current_file.stat().st_size:
                    data.current_file.unlink()
                data.current_file = None

        def show_enter_password_page(widget):
            if data.file_load_chooser.has_errors:
                return
            target_file = Path(data.file_load_path_label.text)
            file_size = target_file.stat().st_size
            three_mb = 3145728
            if file_size > three_mb:
                show_error_bubble(
                    data.file_load_path_label, "The selected file is too large!", False
                )
                return
            clean_up_current_file()
            data.current_file = target_file
            try:
                data.current_file_handle = open(data.current_file, "rb")
            except OSError:
                show_error_bubble(
                    data.file_load_path_label,
                    "Unable to open the selected file!",
                    False,
                )
                data.current_file = None
                data.current_file_handle = None
                return
            data.enter_password_path_label.text = str(data.current_file)
            show_main_layout(widget)
            if data.current_page != data.enter_password_page:
                data.main_frame.remove_widget(data.current_page)
                data.main_frame.add_widget(data.enter_password_page)
                data.current_page = data.enter_password_page
                sync_height(data.enter_password_page)

        def show_choose_password_page(widget):
            if data.file_create_chooser.has_errors:
                return
            new_file_name = re.sub(
                data.whitespace_regex, " ", data.file_create_name_input.text
            )
            new_file_name = new_file_name.strip()
            data.file_create_name_input.text = new_file_name
            if not len(new_file_name):
                show_error_bubble(
                    data.file_create_name_input, "Choose a file name!", False
                )
                return
            clean_up_current_file()
            data.current_file = Path(data.file_create_path_label.text) / (
                new_file_name + data.file_suffix
            )
            try:
                data.current_file_handle = open(data.current_file, "xb")
            except OSError as error:
                if isinstance(error, FileExistsError):
                    message = "The file already exists!"
                else:
                    message = "Unable to create the file!"
                show_error_bubble(data.file_create_name_input, message, False)
                data.current_file = None
                data.current_file_handle = None
                return
            data.choose_password_path_label.text = str(data.current_file)
            show_main_layout(widget)
            if data.current_page != data.choose_password_page:
                data.main_frame.remove_widget(data.current_page)
                data.main_frame.add_widget(data.choose_password_page)
                data.current_page = data.choose_password_page
                sync_height(data.choose_password_page)

        def show_file_load_layout(widget):
            if data.current_layout != data.file_load_layout:
                data.file_load_chooser._update_files()
                data.window.remove_widget(data.main_layout)
                data.window.add_widget(data.file_load_layout)
                data.current_layout = data.file_load_layout

        def show_file_create_layout(widget):
            if data.current_layout != data.file_create_layout:
                data.file_create_chooser._update_files()
                data.window.remove_widget(data.main_layout)
                data.window.add_widget(data.file_create_layout)
                data.current_layout = data.file_create_layout

        def show_start_page(widget):
            show_main_layout(widget)
            if data.current_page != data.start_page:
                clear_password_fields()
                clean_up_current_file()
                data.main_frame.remove_widget(data.current_page)
                data.main_frame.add_widget(data.start_page)
                data.current_page = data.start_page
                sync_height(data.start_page)

        def show_main_layout(widget):
            if data.current_layout != data.main_layout:
                data.window.remove_widget(data.current_layout)
                data.window.add_widget(data.main_layout)
                data.current_layout = data.main_layout

        self.title = "HerePass"
        self.clean_up_current_file = clean_up_current_file
        data.background_color = (0.98, 0.98, 0.98, 1)
        data.font_color = (0, 0, 0, 1)
        data.font_color_gray = (0.4, 0.4, 0.4, 1)
        data.error_font_color = (1, 0, 0, 1)
        data.light_error_font_color = (1, 0.4, 0.4, 1)
        data.line_gray = (0.7, 0.7, 0.7, 1)
        data.bar_bg_color = (0.85, 0.85, 0.85, 1)
        data.file_suffix = ".enc.json"
        data.whitespace_regex = r"\s+"
        data.error_widget = None
        data.error_bubble_padding = dp(20)
        data.error_bubble = None
        data.error_bubble_below = False
        data.error_bubble_label = None
        data.current_file = None
        data.current_file_handle = None
        data.sync_height_tracker = {}
        data.edit_allowed = False
        data.alphanumeric = string.ascii_letters + string.digits

        data.window = FloatLayout()
        set_background_color(data.window, data.background_color)

        build_enter_password_page()
        build_choose_password_page()
        build_file_load_layout()
        build_file_create_layout()
        build_start_page()
        build_main_layout()

        data.current_layout = data.main_layout
        data.current_page = data.start_page
        data.main_frame.add_widget(data.start_page)
        data.window.add_widget(data.main_layout)
        sync_height(data.start_page)

        return data.window
