from dataclasses import dataclass, field

@dataclass
class Playlist:
    YTDL_OPTIONS: dict = field(default_factory=dict)
    isPlaylist: dict = field(default_factory=dict)
    playlistURL: dict = field(default_factory=dict)
    playlistStart: dict = field(default_factory=dict)
    playlistEnd: dict = field(default_factory=dict)
    currentPlaylist: dict = field(default_factory=dict)