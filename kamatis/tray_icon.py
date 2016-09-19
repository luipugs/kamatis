from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QMenu,
    QSystemTrayIcon,
    )


class TrayIcon(QSystemTrayIcon):

    def __init__(self, parent):
        super(TrayIcon, self).__init__(parent)
        self.__app = QApplication.instance()
        self.__app.state_changed.connect(self.__on_app_state_changed)
        self.__app.period_changed.connect(self.__on_period_changed)
        self.__app.timer_updated.connect(self.__on_timer_updated)
        self.__app.period_progressed.connect(self.__on_period_progressed)

        self.__state_actions_dict = {
            'STOPPED': (self.__app.start, 'Start'),
            'RUNNING': (self.__app.pause, 'Pause'),
            'PAUSED': (self.__app.resume, 'Resume'),
            }

        self.__init_icon()

        menu = QMenu()
        menu.aboutToShow.connect(self.__populate_menu)
        self.setContextMenu(menu)

        self.activated.connect(self.__on_activated)

    def __init_icon(self):
        self.__icon_template = ':/kamatis-{}.png'
        self.__period_step = 0
        self.__set_icon()

    def __set_normal_icon(self):
        self.__icon_template = ':/kamatis-{}.png'
        self.__set_icon()

    def __set_paused_icon(self):
        self.__icon_template = ':/kamatis-paused-{}.png'
        self.__set_icon()

    def __set_icon(self):
        icon = QIcon(self.__icon_template.format(self.__period_step))
        self.setIcon(icon)

    def __on_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.__on_trigger()

    def __on_app_state_changed(self, new_state):
        self.__app_state = new_state
        self.__on_trigger, _ = self.__state_actions_dict[new_state]
        pause_str = ' - paused'

        if new_state == 'STOPPED':
            self.__set_period_str('')
            self.__init_icon()
        elif new_state == 'RUNNING':
            self.__set_period_str(self.__period_str.replace(pause_str, ''))
            self.__set_normal_icon()
        elif new_state == 'PAUSED':
            self.__set_period_str('{}{}'.format(self.__period_str, pause_str))
            self.__set_paused_icon()

    def __on_period_changed(self, new_period):
        self.__set_period_str(new_period.capitalize())

    def __on_timer_updated(self, message):
        timeout = 3000
        app_name = self.__app.applicationName()
        self.showMessage(app_name, message, msecs=timeout)

    def __on_period_progressed(self, progress):
        self.__period_step = progress
        self.__set_icon()

    def __on_quit(self):
        self.__app.quit()

    def __set_period_str(self, period_str):
        self.__period_str = period_str
        text = '{}\n{}'.format(self.__app.applicationName(), period_str)
        self.setToolTip(text.strip())

    def __populate_menu(self):
        menu = self.contextMenu()
        menu.clear()

        on_trigger, text = self.__state_actions_dict[self.__app_state]
        action = menu.addAction(text)
        action.triggered.connect(on_trigger)

        if self.__app_state in ('RUNNING', 'PAUSED'):
            remaining_time = self.__app.get_remaining_time()
            remaining_text = self.__get_remaining_text(remaining_time)

            reset = menu.addAction('Reset')
            reset.triggered.connect(self.__app.reset)

            menu.addSeparator()
            period = menu.addAction(self.__period_str)
            period.setEnabled(False)
            min_sec = menu.addAction(remaining_text)
            min_sec.setEnabled(False)

        menu.addSeparator()
        settings = menu.addAction('Settings')
        settings.triggered.connect(self.__app.settings_window.show)

        menu.addSeparator()
        quit = menu.addAction('Quit')
        quit.triggered.connect(self.__on_quit)

    def __get_remaining_text(self, msecs):
        secs = int(msecs / 1000)
        mins, secs = divmod(secs, 60)
        hours, mins = divmod(mins, 60)
        time_str = '{:02d}:{:02d} to go'.format(mins, secs)
        if hours:
            time_str = '{:02d}:{}'.format(hours, time_str)
        return time_str
