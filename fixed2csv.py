#!/usr/bin/env python
from __future__ import print_function
import csv
import os
import re
import sys
import zipfile
from datetime import date
from commands import getoutput

try:
    import dateutil.parser
    import pytz
except ImportError as e:
    print(e, file=sys.stderr)

VERSION = (0, 2, 4)
__version__ = '.'.join(map(str, VERSION))

class Schema(object):
    """
    Represents a fixed-width column file schema, stored as a CSV.
    """
    
    def __init__(self, fn, name_field=None, length_field=None, help_field=None, type_field=None, auto_convert_dates=False, delimiter='', *args, **kwargs):
        self.schema = list(csv.DictReader(open(fn), *args, **kwargs))
        schema_fields = self.schema[0].keys()
        self.auto_convert_dates = auto_convert_dates
        
        self.delimiter = delimiter
        
        self.name_field = name_field
        if self.name_field is None:
            # Attempt to guess field name.
            name_fields = [_ for _ in schema_fields if 'name' in re.sub('[^a-zA-Z0-9_]+', '_', _.strip().lower())]
            if len(name_fields) != 1:
                raise Exception, 'No name field specified.'
            else:
                self.name_field = name_fields[0]
        
        self.length_field = length_field
        if self.length_field is None:
            # Attempt to guess field name.
            name_fields = [_ for _ in schema_fields if 'length' in re.sub('[^a-zA-Z0-9_]+', '_', _.strip().lower())]
            if len(name_fields) != 1:
                raise Exception, 'No length name specified.'
            else:
                self.length_field = name_fields[0]
        
        self.help_field = help_field
        if self.help_field is None:
            # Attempt to guess field name.
            name_fields = [_ for _ in schema_fields if 'help' in re.sub('[^a-zA-Z0-9_]+', '_', _.strip().lower())]
            if len(name_fields) == 1:
                self.help_field = name_fields[0]
            else:
                name_fields = [_ for _ in schema_fields if 'definition' in re.sub('[^a-zA-Z0-9_]+', '_', _.strip().lower())]
                if len(name_fields) == 1:
                    self.help_field = name_fields[0]
                else:
                    name_fields = [_ for _ in schema_fields if 'description' in re.sub('[^a-zA-Z0-9_]+', '_', _.strip().lower())]
                    if len(name_fields) == 1:
                        self.help_field = name_fields[0]
        
        self.type_field = type_field
        self.datetime_fields = set()
        self.date_fields = set()
        if self.auto_convert_dates and not self.type_field:
            raise Exception, \
                'Can not auto convert date fields without a valid type_field.'
        
        start_index = 0
        self.mapping = [] # [(name, start_index_inclusive, end_index_exclusive)]
        self.help = {}
        self.types = {}
        for schema_line in self.schema:
            field_name = schema_line[self.name_field].strip()
            length = int(schema_line[self.length_field])
            end_index = start_index + length
            self.mapping.append((field_name, start_index, end_index))
            if self.help_field:
                self.help[field_name] = schema_line[self.help_field].strip()
            if self.type_field:
                self.types[field_name] = type_field_value = schema_line[self.type_field].strip()
                if type_field_value.lower() in ('date',):
                    self.date_fields.add(field_name.lower())
                elif type_field_value.lower() in ('datetime',):
                    self.datetime_fields.add(field_name.lower())
            start_index += length
            if self.delimiter:
                start_index += len(self.delimiter)
    
    def fieldnames(self):
        for schema_line in self.schema:
            field_name = schema_line[self.name_field].strip()
            yield field_name
    
    def open(self, fn, skip_to_line=0):
        """
        Reads a fixed-width file using the schema to interpret and convert
        the lines to dictionaries.
        """
        if isinstance(fn, basestring):
            if zipfile.is_zipfile(fn):
                # Read data from inside a ZIP archive without extracting it.
                zf = zipfile.ZipFile(fn, 'r')
                fin = zf.open(zf.namelist()[0])
            else:
                fin = open(fn)
        else:
            fin = fn
            
        i = 0
        for line in fin:
            i += 1
            if skip_to_line and i < skip_to_line:
                continue
            data = {}
            for field_name, start_index, end_index in self.mapping:
                key = field_name.lower()
                data[key] = line[start_index:end_index].strip()
                if self.auto_convert_dates:
                    if key in self.date_fields:
                        if data[key].strip():
                            data[key] = dateutil.parser.parse(data[key])
                            data[key] = date(data[key].year, data[key].month, data[key].day)
                        else:
                            data[key] = None
                    elif key in self.datetime_fields:
                        if data[key].strip():
                            data[key] = dateutil.parser.parse(data[key])
                            if not data[key].tzinfo:
                                data[key] = pytz.utc.localize(data[key])
                        else:
                            data[key] = None
                
                # Convert empty strings to none/null.
                if isinstance(data[key], basestring) and not data[key]:
                    data[key] = None
                            
            yield data

def lookup_django_field(type_name):
    type_name = type_name.strip().lower()
    if type_name in ('integer', 'int', 'smallint', 'tinyint'):
        return 'IntegerField'
    elif type_name in ('numeric', 'float'):
        return 'FloatField'
    elif type_name in ('date',):
        return 'DateField'
    elif type_name in ('timestamp', 'datetime',):
        return 'DateTimeField'
    elif type_name in ('character varying', 'varchar', 'str'):
        return 'CharField'
    else:
        raise NotImplementedError, 'Unknown type: %s' % (type_name,)

def count_lines(filename):
    assert os.path.isfile(filename)
    if zipfile.is_zipfile(filename):
        zf = zipfile.ZipFile(filename, 'r')
        name = zf.namelist()[0]
        return zf.open(name).read().count('\n')
    else:
        return int(getoutput('wc -l "%s"' % filename).split(' ')[0])

if __name__ == '__main__':
    
    import argparse

    parser = argparse.ArgumentParser(description='Convert fixed width file to CSV.')
    parser.add_argument('--schema')
    parser.add_argument('--data')
    parser.add_argument('--name-field')
    parser.add_argument('--help-field')
    parser.add_argument('--type-field')
    parser.add_argument('--delimiter')
    parser.add_argument('--review', action='store_true', default=False)
    parser.add_argument(
        '--output-django-fields',
        action='store_true',
        default=False,
        help='Generates code for Django model fields.')
    args = parser.parse_args()

    s = Schema(
        fn=args.schema,
        name_field=args.name_field,
        help_field=args.help_field,
        type_field=args.type_field,
        delimiter=args.delimiter)
    
    if args.output_django_fields:
        # Convert the schema file into the equivalent Django model code.
        assert s.type_field
        assert s.help_field
        print('class MyModel(models.Model):\n')
        for schema_line in s.schema:
            field_name = schema_line[s.name_field].strip()
            type_name = schema_line[s.type_field].strip()
            help_text = schema_line[s.help_field].strip().replace('"', '\\"')
            max_length = int(schema_line[s.length_field].strip())
            field_type = lookup_django_field(type_name)
            field_args = []
            field_args.append('blank=True')
            field_args.append('null=True')
            field_args.append('editable=False')
            field_args.append('db_index=True')
            if field_type in ('CharField',):
                field_args.append('max_length=%i' % max_length)
            field_args.append('help_text=_("%s")' % help_text)
            field_args = '\n        '+(',\n        '.join(field_args))
            django_field_name = re.sub('[^a-zA-Z0-9_]+', '_', field_name).lower()
            print('    %s = models.%s(%s)' % (django_field_name, field_type, field_args))
            print('\n')
        sys.exit(0)
    
    fout = None
    fieldnames = list(s.fieldnames())
    print('Counting lines...', file=sys.stderr)
    total = count_lines(args.data)
    print('%i total lines.' % total, file=sys.stderr)
    i = 0
    for line in s.open(fn=args.data):
        i += 1
        if args.review:
            max_length = max(len(_) for _ in line.keys())
            for name in sorted(line.keys()):
                print>>sys.stderr, name.ljust(max_length)+' ', line[name]
            raw_input('<enter>')
        else:
            if not i % 1000:
                print>>sys.stderr, '\rProcessing line %i of %i (%.02f%%).' % (i, total, i/float(total)*100),
                sys.stderr.flush()
                sys.stdout.flush()
            if fout is None:
                fout = csv.DictWriter(sys.stdout, fieldnames)
                fout.writerow(dict(zip(fieldnames,fieldnames)))
            fout.writerow(line)
    print>>sys.stderr
    print>>sys.stderr, 'Done!'
    