#!/usr/bin/env python
"""
BinManager

The main program interface for the package. BinPack manages
creation and ranking of bins and returns layout dictionaries
for packed bins.

"""
from typing import List, Union, Callable, Optional, Any
from . import item
from . import shelf
from . import guillotine
from . import maximal_rectangles
from . import skyline

# Type Aliases:
Algorithm = Union[shelf.Sheet, guillotine.Guillotine, maximal_rectangles.MaximalRectangle]


class BinManager:
    """
    Interface Class.
    """
    def __init__(self, bin_width: int = 8,
                 bin_height: int = 4,
                 bin_algo: str = 'bin_best_fit',
                 pack_algo: str = 'guillotine',
                 heuristic: str ='default',
                 split_heuristic: str = 'default',
                 sorting: bool = True,
                 rotation: bool = True,
                 rectangle_merge: bool = True,
                 wastemap: bool = True) -> None:
        self.bin_width = bin_width
        self.bin_height = bin_height
        self.items = [] # type: List[item.Item]
        self.bin_count = 0

        if bin_algo == 'bin_best_fit':
            self.bin_sel_algo = self._bin_best_fit
        elif bin_algo == 'bin_first_fit':
            self.bin_sel_algo =  self._bin_first_fit
        self.heuristic = heuristic
        self.algorithm = pack_algo

        self.split_heuristic = split_heuristic
        self.sorting = sorting
        self.rotation = rotation
        self.rectangle_merge = rectangle_merge
        self.wastemap = wastemap

        defaultBin = self._bin_factory() 
        self.bins = [defaultBin]


    def add_items(self, *items: item.Item) -> None:
        for item in items:
            self.items.append(item)
        if self.sorting:
            self.items.sort(key=lambda el: el.width*el.height, reverse=True)


    def _bin_factory(self) -> Any:
        """
        Returns a bin with the specificed algorithm,
        heuristic, and dimensions
        """
        if self.algorithm == 'guillotine':
            return guillotine.Guillotine(self.bin_width, self.bin_height, self.rotation,
                                         self.rectangle_merge, self.split_heuristic)
        elif self.algorithm == 'shelf':
            return shelf.Sheet(self.bin_width, self.bin_height, self.rotation, self.wastemap)
        elif self.algorithm == 'maximal_rectangle':
            return maximal_rectangles.MaximalRectangle(self.bin_width, self.bin_height, self.rotation)
        elif self.algorithm == 'skyline':
            return skyline.Skyline(self.bin_width, self.bin_height, self.rotation)
        raise ValueError('Error: No such Algorithm')


    def _bin_first_fit(self, item: item.Item) -> None:
        """
        Insert into the first bin that fits the item
        """
        result = False
        for binn in self.bins:
            result = binn.insert(item, self.heuristic)
            if result:
                break
        if not result:
            self.bins.append(self._bin_factory())
            self.bins[-1].insert(item, self.heuristic)


    def _bin_best_fit(self, item: item.Item) -> bool:
        """
        Insert into the bin that best fits the item
        """

        # Ensure item can theoretically fit the bin
        item_fits = False
        if item.width <= self.bin_width or item.height >= self.bin_height:
            item_fits = True
        if self.rotation and (item.height <= self.bin_width or item.width >= self.bin_height):
            item_fits = True
        if not item_fits:
            raise ValueError("Error! item too big for bin")

        if self.algorithm == 'skyline':
            best_bin = None
            best_y = float('inf')
            for binn in self.bins:
                for i, seg in enumerate(binn.skyline):
                    fits, y = binn.check_fit(item.width, item.height, i)
                    if fits and y < best_y:
                        best_y = y
                        best_bin = binn
                    fits, y = binn.check_fit(item.height, item.width, i)
                    if fits and y < best_y:
                        best_y = y
                        best_bin = binn
            if best_bin:
                return best_bin.insert(item, self.heuristic)

        if self.algorithm == 'guillotine' or self.algorithm == 'maximal_rectangle':
            best_rect = None 
            best_bin_index = None 
            for i, binn in enumerate(self.bins):
                best_in_bin = None
                for rect in binn.freerects:
                    if binn.item_fits_rect(item, rect):
                        best_in_bin = rect
                        break
                if not best_in_bin:
                    continue
                if not best_rect:
                    best_rect = best_in_bin
                    best_bin_index = i
                elif best_in_bin.area < best_rect.area:
                    best_rect = best_in_bin
                    best_bin_index = i

            if best_rect:
                return self.bins[i].insert(item, self.heuristic)

        if self.algorithm == 'shelf':
            best_area = float('inf')
            best_bin = None
            for i, binn in enumerate(self.bins):
                area = None
                for shelf in binn.shelves:
                    if binn.item_fits_shelf(item, shelf):
                        area = shelf.area
                        break
                if ((item.width <= binn.x and 
                     item.height <= binn.available_height) or
                    (item.height <= binn.x and 
                     item.width <= binn.available_height)):
                    area = binn.x * binn.available_height

                if area and area < best_area:
                    best_area = area
                    best_bin = binn
            if best_bin:
                return best_bin.insert(item, self.heuristic)

        self.bins.append(self._bin_factory())
        self.bins[-1].insert(item, self.heuristic)
        return True


    def execute(self) -> None:
        """
        Loop over all items and attempt insertion
        """
        for item in self.items:
            self.bin_sel_algo(item)
