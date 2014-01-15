import sys
import subprocess
from PySide.QtCore import Signal, QTimer
from PySide.QtGui import QApplication
from ..workers.downloads import DownloadsWorkerThread
from ..widgets.series_window import SeriesWindow
from ..widgets.series_entry import SeriesEntryWidget
from ..loaders import library
from ..models import SeriesEntry
from ..utils import ticked
from ..settings import config
from ..lib.actors import Actor, current_actor
from ..lib.async import async, proxy


class SeriesListApp(QApplication):
    """Series list application"""
    downloaded = Signal(SeriesEntry)
    download_progress = Signal(SeriesEntry, float)

    def init(self, window):
        """Init application"""
        self.window = window
        self.tick = 0
        self._filter = ''
        self._init_workers()
        self._init_events()
        self._load_episodes()

    def _init_workers(self):
        """Init worker"""
        self.downloads_worker = DownloadsWorkerThread()
        self.downloads_worker.start()

    def _init_events(self):
        """Init events"""
        self.window.series_widget.need_more.connect(self._load_episodes)
        self.window.filter_widget.filter_changed.connect(self._filter_changed)
        self.downloads_worker.downloaded.connect(self._downloaded)
        self.downloads_worker.download_progress.connect(self._download_progress)
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: current_actor().loop_tick())
        self.timer.start(50)

    def _can_load_episodes(self, page):
        if not library.series.can_change_page_with_filter:
            if page > 0 and self._filter:
                self.window.series_widget.no_new_data()
                return False
        return True

    @async
    def _load_episodes(self, page=0):
        """Load episodes"""
        if self._can_load_episodes(page):
            tick = self.tick
            episodes = yield proxy.episodes.get_episodes(
                page=page, filters=self._filter,
            )
            if not len(episodes):
                self._nothing_received(tick)
            for episode in episodes:
                self._episode_received(
                    SeriesEntry.get_or_create(**episode), tick,
                )

    @ticked
    def _episode_received(self, episode, tick):
        """Episode received"""
        entry = SeriesEntryWidget.get_or_create(episode)
        self.window.series_widget.add_entry(entry)
        episode.load_poster()
        episode.load_subtitle()

    @ticked
    def _nothing_received(self, tick):
        """Nothing received"""
        self.window.series_widget.no_new_data()

    @ticked
    def _something_wrong(self, message, tick):
        """handle faults"""
        self.window.series_widget.something_wrong(message)

    def _downloaded(self, episode, tick):
        """Downloaded"""
        self.downloaded.emit(episode)

    def _download_progress(self, episode, value):
        """Download progress"""
        self.download_progress.emit(episode, value)

    def need_download(self, episode):
        """Send need_subtitle to worker"""
        self.downloads_worker.need_download.emit(episode, self.tick)

    def _filter_changed(self, value):
        """Filter changed"""
        self.window.series_widget.clear()
        self.tick += 1
        self._filter = value
        self._load_episodes()


class GuiActor(Actor):
    use_nowait = True
    self_loop = True

    def run(self):
        super(GuiActor, self).run()
        library.import_all()
        app = SeriesListApp(sys.argv)
        subprocess.call(['mkdir', '-p', config.download_path])
        window = SeriesWindow()
        window.show()
        app.init(window)
        app.exec_()
