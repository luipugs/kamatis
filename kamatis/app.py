from PyQt5.QtCore import (
    pyqtSignal,
    QStandardPaths,
    QTimer,
    QUrl,
    )
from PyQt5.QtMultimedia import (
    QMediaContent,
    QMediaPlayer,
    )
from PyQt5.QtWidgets import QApplication
from textwrap import dedent
import os
import signal
import sys

from kamatis import res  # noqa
from kamatis.ext.pyqtconfig import (
    ConfigManager,
    QSettingsManager,
    )
from kamatis.settings_window import SettingsWindow
from kamatis.tray_icon import TrayIcon


class Kamatis(QApplication):

    __application_name = 'Kamatis'
    __desktop_file_entry = '''
        [Desktop Entry]
        Version=1.0
        Type=Application
        Name={0}
        GenericName={0}
        Comment=Launch {0}
        Icon={1}
        Categories=Utility;Qt;
        Exec={1}
        Terminal=false
        '''.format(__application_name, __application_name.lower())

    state_changed = pyqtSignal(str)
    period_changed = pyqtSignal(str)
    timer_updated = pyqtSignal(str)
    period_progressed = pyqtSignal(int)

    NO_SOUND_VALS = (
        'NO_SOUND',
        'SEPARATOR',
        'CHOOSE',
        )

    def __init__(self, *args):
        super(Kamatis, self).__init__(*args)
        self.setOrganizationName('Fumisoft')
        self.setApplicationName(self.__application_name)

        self.__player = QMediaPlayer(self)

        self.__period_steps = 12
        self.period_changed.connect(self.__start_timer)
        self.period_changed.connect(self.__start_progress_timer)

        self.__work_timer = QTimer(self)
        self.__work_timer.setSingleShot(True)
        self.__work_timer.timeout.connect(self.__start_break)
        self.__work_timer.timeout.connect(self.__play_sound)

        self.__break_timer = QTimer(self)
        self.__break_timer.setSingleShot(True)
        self.__break_timer.timeout.connect(self.__start_work)
        self.__break_timer.timeout.connect(self.__play_sound)

        self.__progress_timer = QTimer(self)
        self.__break_timer.setSingleShot(True)
        self.__progress_timer.timeout.connect(self.__start_progress_timer)

        self.__saved_settings = QSettingsManager()
        self.__load_default_settings()
        self.settings = ConfigManager()
        self.settings.set_defaults(self.__saved_settings.as_dict())

        self.settings_window = SettingsWindow()
        self.settings_window.settings_set.connect(self.__apply_settings)

        self.__tray_icon = TrayIcon(self)
        self.__tray_icon.show()

        self.__init_state()

    def __init_state(self):
        self.__apply_settings()
        self.__set_state('STOPPED')
        self.__period_counter = 0
        self.__progress = -1

    def __set_state(self, new_state):
        self.__state = new_state
        self.state_changed.emit(new_state)

    def __set_period(self, new_period):
        self.__period = new_period
        length = self.__saved_settings.get(new_period.replace(' ', '_'))
        # Length is saved in minutes but QTimer accepts milliseconds.
        self.__timer_length = length * 60 * 1000
        self.period_changed.emit(new_period)

    def __load_default_settings(self):
        location_type = QStandardPaths.MusicLocation
        music_dir = QStandardPaths.standardLocations(location_type)[0]

        self.default_sound_entries = [
            ('No sounds', 'NO_SOUND'),
            (None, 'SEPARATOR'),
            ('Choose...', 'CHOOSE'),
            ]

        self.sound_settings = {
            'search_dir': music_dir,
            'sound_entries': self.default_sound_entries,
            }

        self.default_settings = {
            'chosen_sound': 'NO_SOUND',
            'work': 25,
            'short_break': 5,
            'long_break': 15,
            'cycle': 4,
            'autostart': True,
            }

        self.__saved_settings.set_defaults(self.sound_settings)
        self.__saved_settings.set_defaults(self.default_settings)

    def __apply_settings(self):
        self.__set_autostart()
        self.__load_sound_file()
        self.__set_cycle_length()

    def __set_autostart(self):
        autostart_dir = os.path.expanduser('~/.config/autostart')
        file_name = '{}.desktop'.format(self.__application_name.lower())
        file_path = os.path.join(autostart_dir, file_name)

        if self.__saved_settings.get('autostart'):
            with open(file_path, 'w') as f:
                f.write(dedent(self.__desktop_file_entry).lstrip())
            return

        try:
            os.unlink(file_path)
        except OSError as err:
            if err.errno == 2:  # File does not exist, ignore.
                return
            raise

    def __load_sound_file(self):
        sound_file_path = self.__saved_settings.get('chosen_sound')
        if sound_file_path in self.NO_SOUND_VALS:
            sound_file_path = ''
        media_content = QMediaContent(QUrl.fromLocalFile(sound_file_path))
        self.__player.setMedia(media_content)

    def __set_cycle_length(self):
        self.__cycle_length = self.__saved_settings.get('cycle')

    def __start_work(self):
        self.__current_timer = self.__work_timer
        self.__set_period('work')

    def __start_break(self):
        self.__current_timer = self.__break_timer
        if self.__period_counter < self.__cycle_length:
            self.__period_counter += 1
            self.__set_period('short break')
        else:
            self.__period_counter = 0
            self.__set_period('long break')

    def __start_timer(self, period):
        message = '{} started'.format(period.capitalize())
        self.__current_timer.setInterval(self.__timer_length)
        self.__current_timer.start()
        self.timer_updated.emit(message)

    def __pause_timer(self):
        message = '{} paused'.format(self.__period.capitalize())
        self.__remaining = self.__current_timer.remainingTime()
        self.__progress_remaining = self.__progress_timer.remainingTime()
        self.__current_timer.stop()
        self.__progress_timer.stop()
        self.timer_updated.emit(message)

    def __resume_timer(self):
        message = '{} resumed'.format(self.__period.capitalize())
        self.__current_timer.setInterval(self.__remaining)
        self.__current_timer.start()
        self.__progress_timer.setInterval(self.__progress_remaining)
        self.__progress_timer.start()
        self.timer_updated.emit(message)

    def __play_sound(self):
        self.__player.play()

    def __start_progress_timer(self, *args):
        self.__progress = (self.__progress + 1) % self.__period_steps
        self.period_progressed.emit(self.__progress)
        progress_length = self.__timer_length / self.__period_steps
        self.__progress_timer.setInterval(progress_length)
        self.__progress_timer.start()

    def save_settings(self):
        new_settings = self.settings.as_dict()
        self.__saved_settings.set_many(new_settings)

    def save_sound_settings(self):
        for key in self.sound_settings.iterkeys():
            self.__saved_settings.set(key, self.settings.get(key))

    def start(self):
        self.__set_state('RUNNING')
        self.__start_work()

    def pause(self):
        self.__set_state('PAUSED')
        self.__pause_timer()

    def resume(self):
        self.__set_state('RUNNING')
        self.__resume_timer()

    def reset(self):
        message = 'Current session stopped. Will reset on restart.'
        self.__current_timer.stop()
        self.__progress_timer.stop()
        self.__init_state()
        self.__tray_icon.showMessage(self.__application_name, message)

    def get_remaining_time(self):
        if self.__state == 'PAUSED':
            return self.__remaining
        return self.__current_timer.remainingTime()


def __sigint_handler(*args):
    QApplication.quit()


def main():
    signal.signal(signal.SIGINT, __sigint_handler)
    app = Kamatis(sys.argv)
    timer = QTimer(app)
    timer.start(500)
    timer.timeout.connect(lambda: None)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
