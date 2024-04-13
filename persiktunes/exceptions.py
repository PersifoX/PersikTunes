"""
### Exceptions module `main`

This module contains all the exceptions used in PersikTunes.
"""


class PersikTunesException(Exception):
    """Base of all PersikTunes exceptions."""


class NodeException(Exception):
    """Base exception for nodes."""


class NodeCreationError(NodeException):
    """There was a problem while creating the node."""


class NodeConnectionFailure(NodeException):
    """There was a problem while connecting to the node."""


class NodeConnectionClosed(NodeException):
    """The node's connection is closed."""

    pass


class NodeRestException(NodeException):
    """A request made using the node's REST uri failed"""

    pass


class NodeNotAvailable(PersikTunesException):
    """The node is currently unavailable."""

    pass


class NoNodesAvailable(PersikTunesException):
    """There are no nodes currently available."""

    pass


class TrackInvalidPosition(PersikTunesException):
    """An invalid position was chosen for a track."""

    pass


class TrackLoadError(PersikTunesException):
    """There was an error while loading a track."""

    pass


class FilterInvalidArgument(PersikTunesException):
    """An invalid argument was passed to a filter."""

    pass


class FilterTagInvalid(PersikTunesException):
    """An invalid tag was passed or PersikTunes was unable to find a filter tag"""

    pass


class FilterTagAlreadyInUse(PersikTunesException):
    """A filter with a tag is already in use by another filter"""

    pass


class QueueException(Exception):
    """Base PersikTunes queue exception."""

    pass


class QueueFull(QueueException):
    """Exception raised when attempting to add to a full Queue."""

    pass


class QueueEmpty(QueueException):
    """Exception raised when attempting to retrieve from an empty Queue."""

    pass


class LavalinkVersionIncompatible(PersikTunesException):
    """Lavalink version is incompatible. Must be using Lavalink > 3.7.0 to avoid this error."""

    pass
