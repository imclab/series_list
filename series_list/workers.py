from PySide.QtCore import QThread, Signal, QObject, Slot
from .loaders.series import EZTVLoader
from .models import SeriesEntry


class SeriesListWorker(QObject):
    """Series list worker"""
    need_series = Signal(int, unicode, int)
    received = Signal(SeriesEntry, int)

    def __init__(self, *args, **kwargs):
        super(SeriesListWorker, self).__init__(*args, **kwargs)
        self.loader = EZTVLoader()
        self.need_series.connect(self._get_series)

    @Slot(int, unicode, int)
    def _get_series(self, page, filters, tick):
        """Get series"""
        for episode in self.loader.get_series(page, filters):
            self.received.emit(episode, tick)


class SeriesListWorkerThread(QThread):
    """Series list worker"""

    def __init__(self):
        super(SeriesListWorkerThread, self).__init__()
        self.receiver = SeriesListWorker()
        self.receiver.moveToThread(self)


class PosterWorker(QObject):
    """Poster worker"""
    need_poster = Signal(SeriesEntry, int)
    received = Signal(SeriesEntry, int)

    def __init__(self, *args, **kwargs):
        super(PosterWorker, self).__init__(*args, **kwargs)
        self.need_poster.connect(self._get_poster)

    @Slot(SeriesEntry, int)
    def _get_poster(self, episode, tick):
        """Get poster for episode"""
        episode.load_poster()
        self.received.emit(episode, tick)


class PosterWorkerThread(QThread):
    """Poster worker"""

    def __init__(self):
        super(PosterWorkerThread, self).__init__()
        self.receiver = PosterWorker()
        self.receiver.moveToThread(self)


class SubtitleWorker(QObject):
    """Subtitle worker"""
    need_subtitle = Signal(SeriesEntry, int)
    received = Signal(SeriesEntry, int)

    def __init__(self, *args, **kwargs):
        super(SubtitleWorker, self).__init__(*args, **kwargs)
        self.need_subtitle.connect(self._get_subtitle)

    @Slot(SeriesEntry, int)
    def _get_subtitle(self, episode, tick):
        """Get subtitle for episode"""
        episode.load_subtitle()
        self.received.emit(episode, tick)


class SubtitleWorkerThread(QThread):
    """Poster worker"""

    def __init__(self):
        super(SubtitleWorkerThread, self).__init__()
        self.receiver = SubtitleWorker()
        self.receiver.moveToThread(self)
