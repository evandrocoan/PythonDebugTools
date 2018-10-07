#! /usr/bin/env python
# -*- coding: utf-8 -*-

####################### Licensing #######################################################
#
#   Copyright 2018 @ Evandro Coan
#   Project Unit Tests
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
#########################################################################################
#

import os
import sys

import unittest

try:
    import sublime_plugin

    import debug_tools.logger
    from debug_tools import utilities
    from debug_tools import testing_utilities

    # Import and reload the debugger
    sublime_plugin.reload_plugin( "debug_tools.logger" )
    sublime_plugin.reload_plugin( "debug_tools.utilities" )
    sublime_plugin.reload_plugin( "debug_tools.testing_utilities" )

except ImportError:

    def assert_path(module):

        if module not in sys.path:
            sys.path.append( module )

    # Import the debug tools
    assert_path( os.path.join( os.path.dirname( os.path.dirname( os.path.dirname( os.path.realpath( __file__ ) ) ) ), 'all' ) )

    import debug_tools.logger
    from debug_tools import utilities
    from debug_tools import testing_utilities


class UtilitiesUnitTests(testing_utilities.TestingUtilities):

    def test_characthersDiffModeExample1(self):
        self.diffMode = 0
        expected = "1. Duplicated target language name defined in your grammar on: [@-1,63:87='Abstract Machine Language'<__ANON_3>,3:19]\n" \
                "2. Duplicated master scope name defined in your grammar on: [@-1,138:147='source.sma'<__ANON_3>,5:20]"

        actual = "1. Duplicated target language name defined in your grammar on: free_input_string\n" \
                "  text_chunk_end  Abstract Machine Language\n" \
                "\n" \
                "2. Duplicated master scope name defined in your grammar on: free_input_string\n" \
                "  text_chunk_end  source.sma" \

        with self.assertRaises( AssertionError ) as error:
            self.assertEqual( expected, actual )

        self.assertTextEqual(
        r"""
              1. Duplicated target language name defined in your grammar on:
            - [@-1,63:87='
            + free_input_string
            +   text_chunk_end    Abstract Machine Language
            - '<__ANON_3>,3:19]
            +
              2. Duplicated master scope name defined in your grammar on:
            - [@-1,138:147='
            + free_input_string
            +   text_chunk_end    source.sma
            - '<__ANON_3>,5:20]
        """, error.exception, trim_plus=False)

    @unittest.skip("Not sure how to fix this")
    def test_wordsDiffModeExample1(self):
        self.diffMode = 1
        expected = "1. Duplicated target language name defined in your grammar on: [@-1,63:87='Abstract Machine Language'<__ANON_3>,3:19]\n" \
                "2. Duplicated master scope name defined in your grammar on: [@-1,138:147='source.sma'<__ANON_3>,5:20]"

        actual = "1. Duplicated target language name defined in your grammar on: free_input_string\n" \
                "  text_chunk_end  Abstract Machine Language\n" \
                "\n" \
                "2. Duplicated master scope name defined in your grammar on: free_input_string\n" \
                "  text_chunk_end  source.sma" \

        with self.assertRaises( AssertionError ) as error:
            self.assertEqual( expected, actual )

        self.assertTextEqual(
        r"""
              1. Duplicated target language name defined in your grammar on:
            - [@-1,63:87='Abstract Machine Language'<__ANON_3>,3:19]
            + free_input_string
            +   text_chunk_end  Abstract Machine Language
            +
              2. Duplicated master scope name defined in your grammar on:
            - [@-1,138:147='source.sma'<__ANON_3>,5:20]
            + free_input_string
            +   text_chunk_end  source.sma
        """, error.exception, trim_plus=False)

    def test_linesDiffModeExample1(self):
        self.diffMode = 2
        expected = "1. Duplicated target language name defined in your grammar on: [@-1,63:87='Abstract Machine Language'<__ANON_3>,3:19]\n" \
                "2. Duplicated master scope name defined in your grammar on: [@-1,138:147='source.sma'<__ANON_3>,5:20]"

        actual = "1. Duplicated target language name defined in your grammar on: free_input_string\n" \
                "  text_chunk_end  Abstract Machine Language\n" \
                "\n" \
                "2. Duplicated master scope name defined in your grammar on: free_input_string\n" \
                "  text_chunk_end  source.sma" \

        with self.assertRaises( AssertionError ) as error:
            self.assertEqual( expected, actual )

        self.assertTextEqual(
        r"""
            - 1. Duplicated target language name defined in your grammar on: [@-1,63:87='Abstract Machine Language'<__ANON_3>,3:19]
            - 2. Duplicated master scope name defined in your grammar on: [@-1,138:147='source.sma'<__ANON_3>,5:20]
            + 1. Duplicated target language name defined in your grammar on: free_input_string
            +   text_chunk_end  Abstract Machine Language
            +
            + 2. Duplicated master scope name defined in your grammar on: free_input_string
            +   text_chunk_end  source.sma
        """, error.exception, trim_plus=False)
