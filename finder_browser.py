#!/usr/bin/env python
"""
Finder-like Filesystem Browser using PySide6
This application creates a main window with a column-based view
similar to macOS Finder. At the top a QLineEdit displays the full
path of the current selection. The leftmost column shows the contents
of a root folder. When you click an item, all columns to its right
are removed, and if the item is a directory, a new column is appended
that shows its contents.
Usage:
	python finder_browser.py
"""
import os
import sys

from PySide6 import QtCore, QtGui, QtWidgets


class FinderBrowser(QtWidgets.QMainWindow):
	COLUMN_WIDTH = 250

	def __init__(self, root_path=None, parent=None):
		"""
	  :param root_path: Optional. The root path to display. If not provided,
		the filesystem root is used.
	  :param parent: Parent widget.
		"""
		super().__init__(parent)
		self.setWindowTitle("Finder-like Filesystem Browser")
		self.resize(800, 600)
		# Use filesystem root if no root path provided.
		if root_path is None:
			root_path = os.path.abspath(os.sep)
		self.root_path = root_path
		# List to store column widgets.
		self.columns = []
		# Create a central widget with a vertical layout.
		central = QtWidgets.QWidget()
		self.setCentralWidget(central)
		self.vlayout = QtWidgets.QVBoxLayout(central)
		self.vlayout.setContentsMargins(5, 5, 5, 5)
		self.vlayout.setSpacing(5)
		# Create and add a QLineEdit to display the full path.
		self.path_lineedit = QtWidgets.QLineEdit()
		self.path_lineedit.setReadOnly(True)
		self.vlayout.addWidget(self.path_lineedit)
		# Create a container widget for the columns with a horizontal layout.
		self.columns_container = QtWidgets.QWidget()
		self.hlayout = QtWidgets.QHBoxLayout(self.columns_container)
		self.hlayout.setContentsMargins(0, 0, 0, 0)
		self.hlayout.setSpacing(1)
		# Align columns to the left.
		self.hlayout.setAlignment(QtCore.Qt.AlignLeft)
		self.vlayout.addWidget(self.columns_container)
		# Add the first column (root).
		self._add_column(self.root_path)

	def _add_column(self, path):
		"""
		Create a new column (a QListWidget) that shows the contents of the directory at 'path'
		and add it to the horizontal layout.
		"""
		list_widget = QtWidgets.QListWidget()
		list_widget.setFixedWidth(self.COLUMN_WIDTH)
		list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
		# Populate the list_widget with directory contents.
		self._populate_list_widget(list_widget, path)
		# Connect the item click signal; capture the column index.
		index = len(self.columns)
		list_widget.itemClicked.connect(lambda item, idx=index: self._on_item_clicked(idx, item))
		self.hlayout.addWidget(list_widget)
		self.columns.append(list_widget)
		# Update the path display.
		self.path_lineedit.setText(path)

	def _populate_list_widget(self, list_widget, path):
		"""
		List the contents of 'path' and add each entry to the given list widget.
		Each QListWidgetItem stores the full path in Qt.UserRole.
		"""
		list_widget.clear()
		# Set tooltip for extra info.
		list_widget.setToolTip(path)
		try:
			entries = os.listdir(path)
		except PermissionError:
			item = QtWidgets.QListWidgetItem("Permission Denied")
			list_widget.addItem(item)
			return
		# Sort entries so that directories appear first.
		entries.sort(key=lambda name: (not os.path.isdir(os.path.join(path, name)), name.lower()))
		# If not at the filesystem root, add an entry for the parent folder.
		if os.path.abspath(path) != os.path.abspath(os.sep):
			parent_item = QtWidgets.QListWidgetItem("..")
			parent_item.setData(QtCore.Qt.UserRole, os.path.abspath(os.path.join(path, os.pardir)))
			parent_item.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowUp))
			list_widget.addItem(parent_item)
		for name in entries:
			full_path = os.path.join(path, name)
			item = QtWidgets.QListWidgetItem(name)
			item.setData(QtCore.Qt.UserRole, full_path)
			if os.path.isdir(full_path):
				icon = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)
			else:
				icon = self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon)
			item.setIcon(icon)
			list_widget.addItem(item)

	def _on_item_clicked(self, column_index, item):
		"""
		Called when an item in one of the columns is clicked.
		Remove any columns to the right of column_index and, if the item represents
		a directory, add a new column showing its contents.
		"""
		# Remove columns to the right.
		while len(self.columns) > column_index + 1:
			widget = self.columns.pop()
			self.hlayout.removeWidget(widget)
			widget.deleteLater()
		# Get the full path from the item.
		path = item.data(QtCore.Qt.UserRole)
		if not path:
			return
		# Update the path display.
		self.path_lineedit.setText(path)
		if os.path.isdir(path):
			# Add a new column for the directory.
			self._add_column(path)


def main():
	app = QtWidgets.QApplication(sys.argv)
	browser = FinderBrowser()
	browser.show()
	sys.exit(app.exec())


if __name__ == "__main__":
	main()
