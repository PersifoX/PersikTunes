"""
### Queue module `main`

This module contains all the queue used in PersikTunes.
"""

from __future__ import annotations

import random
from copy import copy
from typing import Iterable, Iterator, List, Optional, Union

from .enums import LoopMode
from .exceptions import QueueEmpty, QueueException, QueueFull

# from .objects import Track
from .models import Track


class Queue(Iterable[Track]):
    """Queue for PersikTunes. This queue takes PersikTunes.Track as an input and includes looping and shuffling."""

    def __init__(
        self,
        max_size: Optional[int] = None,
        *,
        overflow: bool = True,
        return_exceptions: bool = False,
        loose_mode: bool = False,
    ):
        """
        ### Init method:

        ```py
        self.max_size: Optional[int] "max size of the queue"
        self._current_item: Optional[Track] "current item in the queue"
        self._queue: List[Track] "list of items in the queue"
        self._overflow: bool "if True, allows queue to grow beyond max_size"
        self._loop_mode: Optional[LoopMode] "One of None, LoopMode.QUEUE, LoopMode.TRACK"
        self._return_exceptions: bool "if True, exceptions will raised instead of returning None (in some cases)"
        self._primary: Optional[Track] "Primary track. After track ends, queue will be resumed"
        self._loose_mode: bool "If True, queue will not stop when track ends"
        ```
        """
        self.max_size: Optional[int] = max_size
        "max size of the queue"
        self._current_item: Optional[Track] = None
        "current item in the queue"
        self._queue: List[Track] = []
        "list of items in the queue"
        self._overflow: bool = overflow
        "if True, allows queue to grow beyond max_size"
        self._loop_mode: Optional[LoopMode] = None
        "One of None, LoopMode.QUEUE, LoopMode.TRACK"
        self._return_exceptions: bool = return_exceptions
        "if True, exceptions will raised instead of returning None (in some cases)"
        self._primary: Optional[Track] = None
        "Primary track. After track ends, queue will be resumed"
        self._loose_mode: bool = loose_mode
        "If True, queue will not stop when track ends"

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Overwritten iterable methods

    def __str__(self) -> str:
        """String showing all Track objects appearing as a list."""
        return str(list(f"'{t}'" for t in self))

    def __repr__(self) -> str:
        """Official representation with max_size and member count."""
        return (
            f"<{self.__class__.__name__} max_size={self.max_size} members={self.count}>"
        )

    def __bool__(self) -> bool:
        """Treats the queue as a bool, with it evaluating True when it contains members."""
        return bool(self.count)

    def __call__(self, item: Track) -> None:
        """Allows the queue instance to be called directly in order to add a member."""
        self.put(item)

    def __len__(self) -> int:
        """Return the number of members in the queue."""
        return self.count

    def __getitem__(self, index: int) -> Track:
        """Returns a member at the given position.
        Does not remove item from queue.
        """
        if not isinstance(index, int):
            raise ValueError("'int' type required.'")

        return self._queue[index]

    def __setitem__(self, index: int, item: Track) -> None:
        """Inserts an item at given position."""
        if not isinstance(index, int):
            raise ValueError("'int' type required.'")

        self.put_at_index(index, item)

    def __delitem__(self, index: int) -> None:
        """Delete item at given position."""
        self._queue.__delitem__(index)

    def __iter__(self) -> Iterator[Track]:
        """Iterate over members in the queue.
        Does not remove items when iterating.
        """
        return self._queue.__iter__()

    def __reversed__(self) -> Iterator[Track]:
        """Iterate over members in reverse order."""
        return self._queue.__reversed__()

    def __contains__(self, item: Track) -> bool:
        """Check if an item is a member of the queue."""
        return item in self._queue

    def __add__(self, other: Iterable[Track]) -> Queue:
        """Return a new queue containing all members.
        The new queue will have the same max_size as the original.
        """
        if not isinstance(other, Iterable):
            raise TypeError(
                f"Adding with the '{type(other)}' type is not supported.",
            )

        new_queue = self.copy()
        new_queue.extend(other)
        return new_queue

    def __iadd__(self, other: Union[Iterable[Track], Track]) -> Queue:
        """Add items to queue."""
        if isinstance(other, Track):
            self.put(other)
            return self

        if isinstance(other, Iterable):
            self.extend(other)
            return self

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Private methods

    def _get(self) -> Track:
        return (
            self._queue.pop(0)
            if self._loop_mode
            else self._queue[self._index(self._current_item) + 1]
        )

    def _drop(self) -> Track:
        return self._queue.pop()

    def _index(self, item: Track) -> int:
        return self._queue.index(item)

    def _put(self, item: Track) -> None:
        self._queue.append(item)

    def _insert(self, index: int, item: Track) -> None:
        self._queue.insert(index, item)

    def _remove(self, item: Track) -> None:
        self._queue.remove(item)

    def _get_item(self, item: Union[Track, int]) -> Track:
        if isinstance(item, Track):
            return item

        return self._queue[item]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # static methods

    @staticmethod
    def _check_track(item: Track) -> Track:
        if not isinstance(item, Track):
            raise TypeError("Only PersikTunes.Track objects are supported.")

        return item

    @classmethod
    def _check_track_container(cls, iterable: Iterable) -> List[Track]:
        iterable = list(iterable)
        for item in iterable:
            cls._check_track(item)

        return iterable

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # properties

    @property
    def count(self) -> int:
        """Returns queue member count."""
        return len(self._queue)

    @property
    def is_empty(self) -> bool:
        """Returns True if queue has no members."""
        return not bool(self.count)

    @property
    def is_full(self) -> bool:
        """Returns True if queue item count has reached max_size."""
        return False if self.max_size is None else self.count >= self.max_size

    @property
    def is_looping(self) -> bool:
        """Returns True if the queue is looping either a track or the queue"""
        return bool(self._loop_mode)

    @property
    def loop_mode(self) -> Optional[LoopMode]:
        """Returns the LoopMode enum set in the queue object"""
        return self._loop_mode

    @property
    def loose_mode(self) -> bool:
        """Returns True if the loose_mode enabled or the queue"""
        return self._loose_mode

    @property
    def size(self) -> int:
        """Returns the amount of items in the queue"""
        return len(self._queue)

    @property
    def primary(self) -> Optional[Track]:
        """Returns the primary item of the queue"""
        return self._primary

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # public methods

    def get_queue(self) -> List:
        """Returns the queue as a List"""
        return self._queue

    def get(self) -> Track:
        """Alias for `next()` with additional check LoopMode, primary and loose_mode."""

        if self._loop_mode == LoopMode.TRACK and self._current_item:
            return self._current_item

        return self.next()

    def next(self):
        """Return next immediately available item in queue if any.
        Raises QueueEmpty if no items in queue.
        """
        if self.is_empty:
            if self._return_exceptions:
                raise QueueEmpty("No items in the queue.")
            else:
                return

        try:
            self._current_item = self._get()

        except:
            if self._loop_mode.value == "queue":
                self._current_item = self._queue[0]

                return self._current_item

    def prev(self):
        """Return prevision immediately available item in queue if any.
        Raises QueueEmpty if no items in queue.
        """
        if self.is_empty:
            if self._return_exceptions:
                raise QueueEmpty("No items in the queue.")
            else:
                return

        if not self._current_item or self._current_item not in self._queue:
            self._current_item = self._queue[0]

        elif not self.find_position(self._current_item):
            return

        else:
            self._current_item = self._queue[self.find_position(self._current_item) - 1]

        return self._current_item

    def pop(self, index=-1) -> Track:
        """Return item from queue.
        Raises QueueEmpty if no items in queue.
        """
        if self.is_empty:
            if self._return_exceptions:
                raise QueueEmpty("No items in the queue.")
            else:
                return

        return self._queue.pop(index)

    def remove(self, item: Union[Track, int]) -> None:
        """
        Removes a item within the queue.
        Raises ValueError if item is not in queue.
        """
        item = self._get_item(item)

        if item == self._current_item:
            self._current_item = self._queue[self.find_position(self._current_item) - 1]
        return self._remove(self._check_track(item))

    def find_position(self, item: Track) -> int:
        """Find the position a given item within the queue.
        Raises ValueError if item is not in queue.
        """
        return self._index(self._check_track(item))

    def put(self, item: Track) -> None:
        """Put the given item into the back of the queue."""
        if self.is_full:
            if not self._overflow:
                if self._return_exceptions:
                    raise QueueFull(
                        f"Queue max_size of {self.max_size} has been reached.",
                    )
                else:
                    return

            self._drop()

        return self._put(self._check_track(item))

    def put_at_index(self, index: int, item: Track) -> None:
        """Put the given item into the queue at the specified index."""
        if self.is_full:
            if not self._overflow:
                if self._return_exceptions:
                    raise QueueFull(
                        f"Queue max_size of {self.max_size} has been reached.",
                    )
                else:
                    return

            self._drop()

        return self._insert(index, self._check_track(item))

    def put_at_front(self, item: Track) -> None:
        """Put the given item into the front of the queue."""
        if self.is_full:
            if not self._overflow:
                if self._return_exceptions:
                    raise QueueFull(
                        f"Queue max_size of {self.max_size} has been reached.",
                    )
                else:
                    return

            self._drop()

        return self.put_at_index(0, item)

    def put_list(self, item: List[Track]) -> None:
        """Put the given list into the back of the queue."""
        if self.is_full:
            if not self._overflow:
                if self._return_exceptions:
                    raise QueueFull(
                        f"Queue max_size of {self.max_size} has been reached.",
                    )
                else:
                    return

            for _ in range(item.__len__()):
                self._drop()

        [self._check_track(track) for track in item]
        self._queue += item

    def extend(self, iterable: Iterable[Track], *, atomic: bool = True) -> None:
        """
        Add the members of the given iterable to the end of the queue.
        If atomic is set to True, no tracks will be added upon any exceptions.
        If atomic is set to False, as many tracks will be added as possible.
        When overflow is enabled for the queue, `atomic=True` won't prevent dropped items.
        """
        if atomic:
            iterable = self._check_track_container(iterable)

            if not self._overflow and self.max_size is not None:
                new_len = len(iterable)

                if (new_len + self.count) > self.max_size:
                    if self._return_exceptions:
                        raise QueueFull(
                            f"Queue has {self.count}/{self.max_size} items, "
                            f"cannot add {new_len} more.",
                        )
                    else:
                        return

        for item in iterable:
            self.put(item)

    def copy(self) -> Queue:
        """Create a copy of the current queue including it's members."""
        new_queue = self.__class__(max_size=self.max_size)
        new_queue._queue = copy(self._queue)

        return new_queue

    def clear(self) -> None:
        """Remove all items from the queue."""
        self._queue.clear()

    def set_loop_mode(self, mode: LoopMode | None) -> None:
        """
        Sets the loop mode of the queue.
        Takes the LoopMode enum as an argument.
        """
        self._loop_mode = mode

    def shuffle(self) -> None:
        """Shuffles the queue."""
        random.shuffle(self._queue)

        self._queue.remove(self._current_item)
        self._insert(0, self._current_item)

    def clear_track_filters(self) -> None:
        """Clears all filters applied to tracks"""
        for track in self._queue:
            track.filters = None

    def jump(self, item: Union[Track, int]) -> Track:
        """
        Jumps to the item specified in the queue from the current position.
        """
        if self._loop_mode == LoopMode.TRACK:
            if self._return_exceptions:
                raise QueueException(
                    "Jumping the queue whilst looping a track is not allowed."
                )
            else:
                return

        if self._get_item(item) in self._queue:
            self._current_item = self._get_item(item)

        else:
            if self._return_exceptions:
                raise QueueException("Item not found in Queue.")
            else:
                return

        return self._current_item

    def move(self, item: Union[Track, int], index: int) -> None:
        """
        Move item in the queue.
        """

        if self.is_empty:
            if self._return_exceptions:
                raise QueueEmpty("No items in the queue.")
            else:
                return

        item = self._get_item(item)

        if item in self._queue:
            self._remove(item)
            self._insert(index, item)

    def set_primary(self, item: Track) -> None:
        """
        Set the primary item of the queue.
        """
        self._primary = self._check_track(item)
