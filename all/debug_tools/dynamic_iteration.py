#! /usr/bin/env python
# -*- coding: utf-8 -*-

#
# Licensing
#
# Dynamic Iteration Data structures
# Copyright (C) 2018 Evandro Coan <https://github.com/evandrocoan>
#
#  Redistributions of source code must retain the above
#  copyright notice, this list of conditions and the
#  following disclaimer.
#
#  Redistributions in binary form must reproduce the above
#  copyright notice, this list of conditions and the following
#  disclaimer in the documentation and/or other materials
#  provided with the distribution.
#
#  Neither the name Evandro Coan nor the names of any
#  contributors may be used to endorse or promote products
#  derived from this software without specific prior written
#  permission.
#
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the
#  Free Software Foundation; either version 3 of the License, or ( at
#  your option ) any later version.
#
#  This program is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#  General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import copy

from debug_tools import getLogger

from debug_tools.utilities import emquote_string
from debug_tools.utilities import get_representation

# level 4 - Abstract Syntax Tree Parsing
log = getLogger( 127-4, __name__ )


class DynamicIterable(object):
    """
        Dynamically creates creates a unique iterable which can be used one time.

        Why have an __iter__ method in Python?
        https://stackoverflow.com/questions/36681312/why-have-an-iter-method-in-python
    """

    def __init__(self, data_container, iterable_access, empty_slots, end_index=None, filled_slots=set()):
        """
            Receives a iterable an initialize the object to start an iteration.

            @param `iterable_access` a function pointer to function which returns the next element given its index
            @param `end_index` it must be a list with one integer element
            @param `empty_slots` it must be a set with indexes of free place to put new elements
        """
        ## The current index used when iterating over this collection items
        self.current_index = -1

        ## List the empty free spots for old items, which should be skipped when iterating over
        self.empty_slots = empty_slots

        ## List the empty free spots for new items, which should be skipped when iterating over
        self.filled_slots = filled_slots

        ## The underlying container used to calculate this iterable length
        self.data_container = data_container

        ## The iterable access method to get the next item given a index
        if end_index is None:
            self.iterable_access = iterable_access

        else:
            self.iterable_access = lambda index: iterable_access( index ) if index < end_index[0] else self.stop_iteration( index )

    def __len__(self):
        """
            Return the total length of this container.
        """
        return len( self.data_container )

    def __iter__(self):
        """
            Resets the current index and return a copy if itself for iteration.
        """
        self.current_index = -1
        return self

    def __next__(self):
        """
            Called by Python automatically when iterating over this set and python wants to know the
            next element to iterate. Raises `StopIteration` when the iteration has been finished.

            How to make a custom object iterable?
            https://stackoverflow.com/questions/21665485/how-to-make-a-custom-object-iterable
            https://stackoverflow.com/questions/4019971/how-to-implement-iter-self-for-a-container-object-python
        """
        empty_slots = self.empty_slots
        current_index = self.current_index + 1
        filled_slots = self.filled_slots

        while current_index in empty_slots or current_index in filled_slots:
            current_index += 1

        try:
            self.current_index = current_index
            # log( 1, "current_index: %s", current_index )
            return self.iterable_access( current_index )

        except IndexError:
            raise StopIteration

    def stop_iteration(self, index):
        """
            Raise the exception `StopIteration` to stop the current iteration.
        """
        raise StopIteration

    def __str__(self):
        """
            Return a nice string representation of this iterable.
        """
        representation = []

        for item in self:
            representation.append( str( item ) )

        return "{%s}" % ( ", ".join( representation ) )


class DynamicIterationDict(object):
    """
        A `dict()` like object which allows to dynamically add and remove items while iterating over
        its elements as in `for element in dynamic_set`

        https://wiki.python.org/moin/TimeComplexity
        https://stackoverflow.com/questions/4014621/a-python-class-that-acts-like-dict
    """

    def __init__(self, initial=None, is_set=False, emquote=False, index=False):
        """
            Fully initializes and create a new dictionary.

            @param `initial` is a dictionary used to initialize it with new values.
        """

        ## Whether this collection elements are going to be used as a list, instead of dictionary
        self._is_set = is_set

        ## The list with the keys of this collection elements
        self.keys_list = list()

        ## The list with the elements of this collection
        self.values_list = list()

        ## Whether the keys of this dictionary should be emquoted when creating a string representation
        self._emquote_keys = emquote

        ## Whether the string representation of this collection will have item index attached to it
        self._add_index = index

        ## List the empty free spots for old items, used globally before the iteration starts
        self.empty_slots = set()

        ## List the empty free spots for old items, used globally after the iteration starts with `new_items_skip_count`
        self.filled_slots = set()

        ## A dictionary with the indexes of the elements in this collection
        self.items_dictionary = dict()

        ## Whether the iteration process is allowed to use new items added on the current iteration
        self.new_items_skip_count = 0

        ## A stack of `new_items_skip_count` which is required when the current iterator is called recursively
        self.new_items_skip_stack = []

        ## Holds the global maximum iterable index used when `new_items_skip_count` is set
        self.maximum_iterable_index = [0]

        if initial:

            if isinstance( initial, dict ):

                for key, value in initial.items():
                    self[key] = value

            else:
                self.fromkeys( initial )

    def __repr__(self):
        """
            Return a full representation of all public attributes of this object set state for
            debugging purposes.
        """
        return get_representation( self )

    def __str__(self):
        """
            Return a nice string representation of this collection.
        """
        keys_list = self.keys_list
        empty_slots = self.empty_slots
        representation = []

        if self._emquote_keys:
            get_key = lambda: emquote_string( key )

        else:
            get_key = lambda: key

        if self._add_index:
            get_index = lambda: "{}, {}".format( get_key(), index )

        else:
            get_index = get_key

        if self._is_set:
            return str( self.keys() )

        else:
            values_list = self.values_list

            for index in range( 0, len( keys_list ) ):

                if index not in empty_slots:
                    key = keys_list[index]
                    representation.append( "%s: %s" % ( get_index(), values_list[index] ) )

        return "{%s}" % ", ".join( representation )

    def __contains__(self, key):
        """
            Determines whether this dictionary contains or not a given `key`.
        """
        return key in self.items_dictionary

    def __len__(self):
        """
            Return the total length of this set.
        """
        return len( self.items_dictionary )

    def __call__(self, how_many_times=-1):
        """
            Return a iterable for the keys elements of this collection when calling its object as a
            function call.

            `how_many_times` is for how many iterations it should keep ignoring the new items.
        """
        return self.get_iterator( self.get_key, how_many_times )

    def __iter__(self):
        """
            Called by Python automatically when iterating over this set and python wants to start
            the iteration process.

            Why have an __iter__ method in Python?
            https://stackoverflow.com/questions/36681312/why-have-an-iter-method-in-python
        """
        return self.get_iterator( self.get_key )

    def __setitem__(self, key, value):
        """
            Given a `key` and `item` add it to this dictionary as a non yet iterated item, replacing
            the existent value. It a iteration is running, and the item was already iterated, then
            it will be updated on the `niterated_items` dict.
        """
        items_dictionary = self.items_dictionary

        if key in items_dictionary:
            item_index = items_dictionary[key]
            self.values_list[item_index] = value

        else:
            empty_slots = self.empty_slots
            values_list = self.values_list

            if empty_slots and self.new_items_skip_count > 0:
                free_slot = empty_slots.pop()
                self.filled_slots.add( free_slot )

                values_list[free_slot] = value
                self.keys_list[free_slot] = key

            else:
                free_slot = len( values_list )
                values_list.append( value )
                self.keys_list.append( key )

            self.items_dictionary[key] = free_slot

    def __getitem__(self, key):
        """
            Given a `key` returns its existent value.
        """
        # log( 1, "index: %s, key: %s", self.items_dictionary[key], key )
        return self.values_list[self.items_dictionary[key]]

    def __delitem__(self, key):
        """
            Given a `key` deletes if from this dict.
        """
        # log( 1, "key: %s, self: %s", key, self )
        items_dictionary = self.items_dictionary
        item_index = items_dictionary[key]

        self.empty_slots.add( item_index )
        del items_dictionary[key]

    def trim_indexes_sorted(self):
        """
            Fix the the outdated indexes on the internal lists after their dictionary removal,
            keeping the items original ordering O(n).
        """
        new_index = -1
        clean_keys = []
        clean_values = []

        values_list = self.values_list
        items_dictionary = self.items_dictionary

        for key, value_index in items_dictionary.items():
            new_index += 1
            items_dictionary[key] = new_index
            clean_keys.append( key )
            clean_values.append( values_list[value_index] )

        self.empty_slots.clear()
        self.keys_list = clean_keys
        self.values_list = clean_values

    def trim_indexes_unsorted(self):
        """
            Fix the the outdated indexes on the internal lists after their dictionary removal.
            keeping the items original ordering O(k), where `k` is length of `self.empty_slots`.
        """
        keys_list = self.keys_list
        values_list = self.values_list
        empty_slots = self.empty_slots
        last_slot = -1

        while empty_slots:
            empty_slot = empty_slots.pop()
            list_length = len( keys_list )
            key = keys_list.pop()

            keys_list[empty_slot] = key
            values_list[empty_slot] = values_list.pop()
            self.items_dictionary[key] = empty_slot

            if last_slot >= list_length:
                last_slot = last_slot

        if last_slot > -1:
            del keys_list[last_slot:]
            del values_list[last_slot:]

    def keys(self, how_many_times=-1):
        """
            Return a DynamicIterable over the keys stored in this collection.

            `how_many_times` is for how many iterations it should keep ignoring the new items.
        """
        return self.get_iterator( self.get_key, how_many_times )

    def values(self, how_many_times=-1):
        """
            Return a DynamicIterable over the values stored in this collection.

            `how_many_times` is for how many iterations it should keep ignoring the new items.
        """
        return self.get_iterator( self.get_value, how_many_times )

    def items(self, how_many_times=-1):
        """
            Return a DynamicIterable over the (key, value) stored in this collection.

            `how_many_times` is for how many iterations it should keep ignoring the new items.
        """
        return self.get_iterator( self.get_key_value, how_many_times )

    def get_key(self, index):
        """
            Given a `index` returns its corresponding key.
        """
        return self.keys_list[index]

    def get_value(self, index):
        """
            Given a `index` returns its corresponding value.
        """
        return self.values_list[index]

    def get_key_value(self, index):
        """
            Given a `index` returns its corresponding (key, value) pair.
        """
        return ( self.keys_list[index], self.values_list[index] )

    def get_iterator(self, target_generation, how_many_times=-1):
        """
            Get fully configured iterable given the getter `target_generation(index)` function.

            `how_many_times` is for how many iterations it should keep ignoring the new items.
        """
        self.new_items_skip_count -= 1

        # When the current sequence is exhausted, search for an old one
        if not self.new_items_skip_count > 0:

            # Unwind the stack until a valid item is found
            if self.new_items_skip_stack:
                self.new_items_skip_count = self.new_items_skip_stack.pop()

        self.not_iterate_over_new_items( how_many_times )

        if self.new_items_skip_count > 0:
            return DynamicIterable( self.items_dictionary, target_generation, self.empty_slots, self.maximum_iterable_index, self.filled_slots )

        return DynamicIterable( self.items_dictionary, target_generation, self.empty_slots )

    def not_iterate_over_new_items(self, how_many_times=1):
        """
            If called before start iterating over this dictionary, it will not iterate over the
            new keys added until the current iteration is over.

            `how_many_times` is for how many iterations it should keep ignoring the new items.
        """

        if how_many_times > 0:

            if self.new_items_skip_count > 0:
                self.new_items_skip_stack.append( self.new_items_skip_count )

            self.filled_slots = set()
            self.new_items_skip_count = how_many_times
            self.maximum_iterable_index = [0]
            self.maximum_iterable_index[0] = len( self.keys_list )

    def fromkeys(self, iterable):
        """
            Initialize a dictionary with None default value, acting like a indexed set.
        """

        for key in iterable:
            self[key] = None

    def append(self, element):
        """
            Add a new element to the end of the list.
        """
        self[element] = None

    def remove(self, element):
        """
            Remove new `element` anywhere in the container.
        """
        del self[element]

    def add(self, element):
        """
            Add a new element to the end of the list.
        """
        self[element] = None

    def discard(self, element):
        """
            Remove new `element` anywhere in the container.
        """
        try:
            del self[element]
        except KeyError:
            pass

    def copy(self):
        """
            Return a deep copy of this collection.
        """
        return copy.deepcopy( self )

    def clear(self):
        """
            Remove all items from this dict.
        """
        self.empty_slots.clear()
        self.filled_slots.clear()

        self.keys_list.clear()
        self.values_list.clear()
        self.items_dictionary.clear()

