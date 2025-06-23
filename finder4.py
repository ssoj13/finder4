#!/usr/bin/env python
"""
Random-Seed Column Browser
- Maintains a global selection (list of selected items) used as seed.
- Displays the current path in a QLineEdit (e.g. "/foo/bar").
- Maximum number of columns equals the number of generator functions supplied.
- Generator functions return a list of strings.
- The user can type a path (slash-separated) and hit Enter to update the selection.
- UI initialization is handled in init_ui().
- The main entry point is defined as a static method of the class.
- Widget size and current path are saved/restored using QSettings.
"""
import hashlib
import random
import string
import sys

from PySide6 import QtCore, QtWidgets


class FinderBrowser(QtWidgets.QWidget):
	COLUMN_WIDTH = 120

	def __init__(self, fn, parent=None):
		"""
			 :param fn: List of generator functions. Each function takes the current seed (a list of strings)
		and returns a list of strings.
		The number of functions sets the maximum number of columns.
			 :param parent: Parent widget.
		"""
		super().__init__(parent)
		self.key_actions = {QtCore.Qt.Key_Escape: self.close}
		# Global selection used as seed (list of selected strings).
		self.selection = []
		# Generator functions.
		self.fns = fn
		# List to hold column widgets.
		self.columns = []
		# QSettings instance.
		self.settings = QtCore.QSettings("MyCompany", "RandomSeedColumnBrowser")
		# Initialize the UI.
		self.init_ui()
		# Load saved settings (size and path).
		self.load_settings()
		# Build the initial columns.
		self.refresh()

	def init_ui(self):
		"""Initialize the UI components."""
		self.setWindowTitle("Random-Seed Column Browser")
		self.resize(800, 600)
		self.vlayout = QtWidgets.QVBoxLayout(self)
		self.vlayout.setContentsMargins(5, 5, 5, 5)
		self.vlayout.setSpacing(5)
		# LineEdit to display the current path.
		self.path_lineedit = QtWidgets.QLineEdit()
		self.path_lineedit.setReadOnly(False)
		self.vlayout.addWidget(self.path_lineedit)
		self.path_lineedit.returnPressed.connect(self._on_path_entered)
		self.path_lineedit.setText(self.get_path())
		# Container for the columns.
		self.columns_container = QtWidgets.QWidget()
		self.hlayout = QtWidgets.QHBoxLayout(self.columns_container)
		self.hlayout.setContentsMargins(0, 0, 0, 0)
		self.hlayout.setSpacing(1)
		self.hlayout.setAlignment(QtCore.Qt.AlignLeft)
		self.vlayout.addWidget(self.columns_container)

	def get_path(self):
		"""Return the current selection as a filesystem-like path (e.g. "/foo/bar")."""
		if not self.selection:
			return "/"
		return "/" + "/".join(self.selection)

	def set_selection_from_path(self, path_str):
		"""
		Accept a slash-separated path and update the selection.
		For example, "/foo/bar" becomes ["foo", "bar"]. An empty or "/" path resets the selection.
		"""
		if path_str.startswith("/"):
			path_str = path_str[1:]
		if not path_str:
			self.selection = []
		else:
			self.selection = [seg for seg in path_str.split("/") if seg]

	def refresh(self):
		"""
		Rebuild all columns based on the current selection.
		For each column index i:
		  - Use the generator function at index i with seed = self.selection[:i].
		  - Create a column (QListWidget) and select the item matching self.selection[i] (if any).
		If the number of selected items is less than the number of generators, add one extra column.
		"""
		# Remove any existing columns.
		while self.columns:
			widget = self.columns.pop()
			self.hlayout.removeWidget(widget)
			widget.deleteLater()
		# Rebuild columns for each already selected item.
		for i in range(len(self.selection)):
			seed = self.selection[:i]
			options = self.fns[i](seed)
			list_widget = QtWidgets.QListWidget()
			list_widget.setFixedWidth(self.COLUMN_WIDTH)
			list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
			for option in options:
				item = QtWidgets.QListWidgetItem(option)
				list_widget.addItem(item)
			# Try to find and select the item matching the selection.
			for idx in range(list_widget.count()):
				if list_widget.item(idx).text() == self.selection[i]:
					list_widget.setCurrentRow(idx)
					break
			list_widget.itemClicked.connect(lambda item, idx=i: self._on_click(idx, item))
			self.hlayout.addWidget(list_widget)
			self.columns.append(list_widget)
		# If we haven't reached the maximum columns, add one more.
		if len(self.selection) < len(self.fns):
			seed = self.selection[:]
			options = self.fns[len(self.selection)](seed)
			list_widget = QtWidgets.QListWidget()
			list_widget.setFixedWidth(self.COLUMN_WIDTH)
			list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
			for option in options:
				item = QtWidgets.QListWidgetItem(option)
				list_widget.addItem(item)
			list_widget.itemClicked.connect(lambda item, idx=len(self.selection): self._on_click(idx, item))
			self.hlayout.addWidget(list_widget)
			self.columns.append(list_widget)
		# Update the path display.
		self.path_lineedit.setText(self.get_path())

	def _on_click(self, col_index, item):
		"""
		When an item is clicked:
		  - Update the selection to be the current selection up to col_index plus the clicked item.
		  - Rebuild the columns.
		"""
		self.selection = self.selection[:col_index] + [item.text()]
		self.refresh()

	def _on_path_entered(self):
		"""Handle the user pressing Enter in the path line edit."""
		path_str = self.path_lineedit.text()
		self.set_selection_from_path(path_str)
		self.refresh()

	def keyPressEvent(self, event):
		"""
		Handle key press events by looking up the key in the keys dictionary.
		If the key is found, the corresponding action is executed.
		Otherwise, the default keyPressEvent is called.
		"""
		if event.key() in self.key_actions:
			action = self.key_actions[event.key()]
			action()
			event.accept()
		else:
			super().keyPressEvent(event)

	@staticmethod
	def rand_strlist(seed_list, n=5, m=8, count=10):
		"""
		Generate a list of random strings using a list of strings as a seed.
		The seed list is joined into a single string, hashed, and used to seed the random generator.
		Each string has a random length between n and m (defaults: 5 and 8).
		:param seed_list: List of strings used as seed.
		:param n: Minimum string length.
		:param m: Maximum string length.
		:param count: Number of strings to generate.
		:return: List of random strings.
		"""
		if not isinstance(seed_list, list):
			seed_list = [str(seed_list)]
		seed_str = "".join(seed_list)
		seed_int = int(hashlib.sha256(seed_str.encode("utf-8")).hexdigest(), 16) % (2**32)
		random.seed(seed_int)
		result = []
		for _ in range(count):
			length = random.randint(n, m)
			s = "".join(random.choices(string.ascii_letters + string.digits, k=length))
			result.append(s)
		return result

	def load_settings(self):
		"""Restore widget size and current path from QSettings."""
		size = self.settings.value("size")
		if size:
			self.resize(size)
		saved_path = self.settings.value("path", "/")
		self.path_lineedit.setText(saved_path)
		self.set_selection_from_path(saved_path)

	def save_settings(self):
		"""Save widget size and current path to QSettings."""
		self.settings.setValue("size", self.size())
		self.settings.setValue("path", self.get_path())

	def closeEvent(self, event):
		"""Override closeEvent to save settings."""
		self.save_settings()
		event.accept()

	@staticmethod
	def test():
		"""Main entry point."""
		app = QtWidgets.QApplication(sys.argv)

		def gen_random_entries(seed):
			if not isinstance(seed, list):
				seed = [str(seed)]
			return FinderBrowser.rand_strlist(seed, n=5, m=8, count=10)

		# Provide a list of generator functions (one per column).
		fn_list = [gen_random_entries] * 7
		widget = FinderBrowser(fn=fn_list)
		widget.show()
		sys.exit(app.exec())


if __name__ == "__main__":
	FinderBrowser.test()
