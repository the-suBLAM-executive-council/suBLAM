# Sublime text plugin to show the schema for the table related to the current
# file as a tooltip.
#
#
# Usage:
#
# Stick something like this in your keybindings:
# { "keys": ["ctrl+alt+s"], "command": "rails_schema" }
#
# Then, edit a rails model file or spec file for a mode and hit the key combo.

import sublime
import sublime_plugin
import os
import re

class RailsSchemaCommand(sublime_plugin.WindowCommand):
    def run(self):
        table_name = TableNameImplier(
            sublime.active_window().active_view().file_name()
        ).perform()

        schema = self._get_schema_for(table_name)

        sublime.active_window().active_view().show_popup(
            self._process_schema_for_popup(schema),
            max_width = 1000,
            max_height = 1000
        )

    def _process_schema_for_popup(self, schema_snippet):
        return SchemaRenderer(schema_snippet).perform()

    def _get_schema_for(self, table_name):
        schema = SchemaFinder(
            sublime.active_window().active_view().file_name()
        ).perform()
        return schema.schema_for(table_name)

class SchemaRenderer(object):
    def __init__(self, schema_snippet):
        self._schema_snippet = schema_snippet

    def perform(self):
        rv = self._schema_snippet
        rv = re.sub(r'( *t\.\w* )"(.*?)"', r'\1"<span style="color: #05b6fc; font-weight: bold">\2</span>"', rv)
        rv = re.sub(r'( *t\.)(\w*)( ")', r'\1<span style="color: #7358fc; font-weight: bold">\2</span>\3', rv)
        rv = rv.replace("\n", "<br>")

        return rv

class SchemaFinder(object):
    def __init__(self, rails_file):
        self._rails_file = rails_file

    def perform(self):
        schema_path = self._find_file(self._rails_file, 'db/schema.rb')
        return SchemaFile(schema_path)

    def _find_file(self, start_file, file_tail):
        current_search_dir = start_file

        while current_search_dir != '/':
            schema = current_search_dir + '/' + file_tail
            if os.path.isfile(schema):
                return schema

            current_search_dir = os.path.dirname(current_search_dir)

class SchemaFile(object):
    def __init__(self, schema_path):
        self._schema_content = open(schema_path).read()

    def schema_for(self, table_name):
        return re.search(
            r'create_table "' + table_name + '".*?end', self._schema_content, re.DOTALL
        ).group(0)


class TableNameImplier(object):
    def __init__(self, fname):
        self._fname = fname

    def perform(self):
        fname_tail = re.match(r'.*/(.*?)(_spec)?.rb$', self._fname)
        if fname_tail == None:
            raise Exception("Could not imply table name")

        name = fname_tail.group(1)
        if self._should_pluralize():
            name = Pluralizer(name).perform()

        return name

    def _should_pluralize(self):
        return re.search('factories', self._fname) == None

class Pluralizer(object):

    def __init__(self, word):
        self._word = word

    def perform(self):
        if re.search(r'(ch|x|ss|sh)$', self._word):
            return self._word + 'es'

        if re.search(r'[^aeiou]y$', self._word):
            return re.sub(r'y$', 'ies', self._word)

        return self._word + 's'
