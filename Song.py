from dataclasses import dataclass, field

@dataclass
class Song:
    autoplay: dict = field(default_factory=dict)
    musicQueue: dict = field(default_factory=dict)
    queueIndex: dict = field(default_factory=dict)
    vc: dict = field(default_factory=dict)