from PyQt5.QtCore import (
    pyqtSignal,
    QUrl,
    )
from PyQt5.QtGui import QIcon
from PyQt5.QtMultimedia import (
    QMediaContent,
    QMediaPlayer,
    )
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialogButtonBox,
    QFormLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QWidget,
    )

from kamatis.ext.pyqtconfig import RECALCULATE_ALL
from kamatis.sound_combo_box import SoundComboBox


class SettingsWidget(QWidget):

    def __init__(self, parent):
        super(SettingsWidget, self).__init__(parent)
        self.__app = QApplication.instance()
        self.__settings = self.__app.settings
        self.__sound_settings_keys = self.__app.sound_settings.keys()
        self.__default_settings = self.__app.default_settings
        self.__orig_settings = self.__get_app_settings()

        player = QMediaPlayer(self)
        player.stateChanged.connect(self.__on_player_state_change)
        player.mediaStatusChanged.connect(self.__on_player_status_change)
        self.__player = player

        self.setLayout(QFormLayout())
        self.__populate_layout()

        self.__settings.updated.connect(self.__on_update_settings)
        self.parent().changes_confirmed.connect(self.__on_changes_confirmed)

    def __populate_layout(self):
        layout = self.layout()

        work_length_spin_box = QSpinBox(self)
        work_length_spin_box.setMinimum(1)
        work_length_spin_box.setSuffix(' mins')
        work_length_spin_box.setToolTip('Length of the work period')
        self.__settings.add_handler('work', work_length_spin_box)
        layout.addRow('&Work:', work_length_spin_box)

        short_break_length_spin_box = QSpinBox(self)
        short_break_length_spin_box.setMinimum(1)
        short_break_length_spin_box.setSuffix(' mins')
        text = 'Length of the short break period'
        short_break_length_spin_box.setToolTip(text)
        self.__settings.add_handler('short_break', short_break_length_spin_box)
        layout.addRow('&Short break:', short_break_length_spin_box)

        long_break_length_spin_box = QSpinBox(self)
        long_break_length_spin_box.setMinimum(1)
        long_break_length_spin_box.setSuffix(' mins')
        text = 'Length of the long break period'
        long_break_length_spin_box.setToolTip(text)
        self.__settings.add_handler('long_break', long_break_length_spin_box)
        layout.addRow('&Long break:', long_break_length_spin_box)

        cycle_length_spin_box = QSpinBox(self)
        cycle_length_spin_box.setMinimum(1)
        cycle_length_spin_box.setSuffix(' periods')
        text = 'How many work + short break periods before taking a long break'
        cycle_length_spin_box.setToolTip(text)
        self.__settings.add_handler('cycle', cycle_length_spin_box)
        layout.addRow('&Cycle length:', cycle_length_spin_box)

        autostart_check_box = QCheckBox(self)
        application_name = QApplication.applicationName()
        text = 'Autostart {} on login'.format(application_name)
        autostart_check_box.setToolTip(text)
        self.__settings.add_handler('autostart', autostart_check_box)
        layout.addRow('&Autostart:', autostart_check_box)

        sound_combo_box = SoundComboBox(self)
        sound_combo_box.currentIndexChanged.connect(self.__on_choose_sound)
        self.__sound_combo_box = sound_combo_box
        layout.addRow('&Play sound:', self.__sound_combo_box)

        self.__test_sound_button = QPushButton('Test sound', self)
        self.__test_sound_button.clicked.connect(self.__on_test_sound_clicked)
        layout.addRow(self.__test_sound_button)

        self.__sound_combo_box.select_default()

        button_box = self.__get_buttons()
        layout.addRow(button_box)

    def __get_buttons(self):
        button_box = QDialogButtonBox(self)

        save = button_box.addButton(QDialogButtonBox.Save)
        save.clicked.connect(self.__on_save)

        self.__reset = button_box.addButton(QDialogButtonBox.Reset)
        self.__reset.clicked.connect(self.__on_reset)

        cancel = button_box.addButton(QDialogButtonBox.Cancel)
        cancel.clicked.connect(self.__on_cancel)

        self.__default = button_box.addButton(QDialogButtonBox.RestoreDefaults)
        self.__default.clicked.connect(self.__on_default)

        return button_box

    def __on_choose_sound(self, index):
        sound_file_path = self.__sound_combo_box.currentData()
        enabled = sound_file_path not in self.__app.NO_SOUND_VALS
        self.__test_sound_button.setEnabled(enabled)
        if enabled:
            media_content = QMediaContent(QUrl.fromLocalFile(sound_file_path))
            self.__player.setMedia(media_content)

    def __on_test_sound_clicked(self, checked):
        if self.__player.state() == QMediaPlayer.StoppedState:
            self.__player.play()
        else:
            self.__player.stop()

    def __on_player_status_change(self, status):
        if status == QMediaPlayer.InvalidMedia:
            self.__show_unplayable_warning()
            self.__sound_combo_box.restore_previous_choice()

    def __on_player_state_change(self, state):
        if state == QMediaPlayer.PlayingState:
            self.__sound_combo_box.setEnabled(False)
            self.__test_sound_button.setText('Stop test')
        else:
            self.__sound_combo_box.setEnabled(True)
            self.__test_sound_button.setText('Test sound')

    def __on_update_settings(self):
        self.__new_settings = self.__get_app_settings()
        has_pending_changes = self.__orig_settings != self.__new_settings
        self.__reset.setEnabled(has_pending_changes)
        default_enabled = self.__default_settings != self.__new_settings
        self.__default.setEnabled(default_enabled)

    def __on_save(self):
        self.__orig_settings = self.__new_settings
        QApplication.instance().save_settings()
        self.parent().close()

    def __on_reset(self):
        self.__settings.set_many(self.__orig_settings)

    def __on_cancel(self):
        self.__on_reset()
        self.parent().close()

    def __on_default(self):
        self.__settings.set_many(self.__default_settings)

    def __get_app_settings(self):
        # Don't manage sound combo box settings.
        app_settings = self.__settings.as_dict()
        for key in self.__sound_settings_keys:
            app_settings.pop(key)
        return app_settings

    def __on_changes_confirmed(self, button):
        if button == QMessageBox.Save:
            self.__on_save()
        else:
            self.__on_cancel()

    def __show_unplayable_warning(self):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('File cannot be played')
        text = 'File is unplayable. It will be removed from the list.'
        msg_box.setText(text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def has_pending_changes(self):
        return self.__orig_settings != self.__new_settings

    def showEvent(self, event):
        # Emit signal to set enabled status of reset and default buttons.
        self.__settings.updated.emit(RECALCULATE_ALL)
        return super(SettingsWidget, self).showEvent(event)


class SettingsWindow(QMainWindow):

    changes_confirmed = pyqtSignal(int)
    settings_set = pyqtSignal()

    def __init__(self):
        super(SettingsWindow, self).__init__()
        application_name = QApplication.applicationName()
        self.setWindowTitle('{} Settings'.format(application_name))
        self.setWindowIcon(QIcon(':/kamatis.svg'))

        self.__settings_widget = SettingsWidget(self)
        self.setCentralWidget(self.__settings_widget)

    def showEvent(self, event):
        # Show settings window in center of screen.
        desktop = QApplication.desktop()
        width = desktop.width()
        height = desktop.height()
        x = (width - self.width()) / 2
        y = (height - self.height()) / 2
        self.move(x, y)
        return super(SettingsWindow, self).showEvent(event)

    def closeEvent(self, event):
        if self.__settings_widget.has_pending_changes():
            self.__confirm_changes()
        self.settings_set.emit()
        return super(SettingsWindow, self).closeEvent(event)

    def __confirm_changes(self):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('Unsaved changes')
        text = 'Some settings were changed. Do you want to save your changes?'
        msg_box.setText(text)
        msg_box.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
        msg_box.setDefaultButton(QMessageBox.Save)
        ret = msg_box.exec_()
        self.changes_confirmed.emit(ret)
