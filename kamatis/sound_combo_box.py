from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    )
import os


class SoundComboBox(QComboBox):

    def __init__(self, parent):
        super(SoundComboBox, self).__init__(parent)
        app = QApplication.instance()
        self.__settings = app.settings

        self.__max_recent = 5  # Save the last 5 sound files chosen.
        self.__num_default_entries = len(app.default_sound_entries)
        self.__max_entries = self.__max_recent + self.__num_default_entries

        self.__mapper_items = list()

        self.__search_dir = self.__settings.get('search_dir')
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setToolTip('Sound to play at the end of each period')
        self.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.__init_entries()
        self.__prev_value = self.currentData()
        self.activated.connect(self.__on_activated)

    def __init_entries(self):
        entries = self.__settings.get('sound_entries')
        for index, entry in enumerate(entries):
            text, data = entry
            self.insert_item(index, text, data)
        self.__on_entries_updated()

    def __on_activated(self, index):
        data = self.currentData()
        if data != 'CHOOSE':
            self.__prev_value = data
            return

        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setViewMode(QFileDialog.Detail)
        dialog.setDirectory(self.__search_dir)
        if not dialog.exec_():
            return

        sound_file_path = dialog.selectedFiles()[0]
        self.__search_dir, sound_file_name = os.path.split(sound_file_path)
        self.__set_settings('search_dir', self.__search_dir)
        if self.count() == self.__max_entries:
            self.remove_item(self.__max_recent - 1)

        self.insert_item(0, sound_file_name, sound_file_path)
        # XXX: Setting current index sets the value of handled key in
        # ConfigManager to the text instead of the data. So would have to
        # select again manually. Seems to have been fixed?
        self.setCurrentIndex(0)
        self.__on_entries_updated()

        # Resize settings window to show full name of chosen sound file.
        parent = self.parent()
        grandparent = parent.parent()
        parent.resize(parent.sizeHint())
        grandparent.resize(grandparent.sizeHint())

    def select_default(self):
        self.currentIndexChanged.emit(self.currentIndex())

    def restore_previous_choice(self):
        self.remove_item(self.currentIndex())
        self.__set_settings('chosen_sound', self.__prev_value)
        self.__on_entries_updated()

    def insert_item(self, index, text, data):
        if not text and data == 'SEPARATOR':
            self.insertSeparator(index)
        else:
            super(SoundComboBox, self).insertItem(index, text, data)
        self.__mapper_items.insert(index, (text, data))

    def remove_item(self, index):
        super(SoundComboBox, self).removeItem(index)
        self.__mapper_items.pop(index)

    def __set_settings(self, key, value):
        self.__settings.set(key, value)
        QApplication.instance().save_sound_settings()

    def __on_entries_updated(self):
        mapper_dict = dict(self.__mapper_items)
        self.__settings.add_handler('chosen_sound', self, mapper=mapper_dict)
        self.__set_settings('sound_entries', self.__mapper_items)
