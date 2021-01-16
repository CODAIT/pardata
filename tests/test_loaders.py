#
# Copyright 2020 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from collections import namedtuple
import re

import pytest
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_float_dtype, is_integer_dtype, is_string_dtype

from pydax.dataset import Dataset
from pydax.loaders import Loader
from pydax.loaders import FormatLoaderMap
from pydax.loaders._format_loader_map import load_data_files
from pydax.loaders.text import PlainTextLoader
from pydax.loaders.table import CSVPandasLoader


class TestBaseLoader:
    "Test loaders._base.*"

    def test_abstract(self):
        "Loader is an abstract class."

        with pytest.raises(TypeError) as e:
            Loader()
        assert 'abstract class' in str(e.value)

    def test_load(self, tmp_path):
        "Loader.load() must be overridden upon Loader being inherited."

        class MyLoader(Loader):
            pass

        # Error out when instantiating MyLoader because load method is not overridden
        with pytest.raises(TypeError) as e:
            MyLoader()
        assert "Can't instantiate abstract class MyLoader with abstract method" in str(e.value)

        class MyLoader(Loader):
            def load(self, path, options):
                # Calling the parent's load() method shouldn't lead to error
                super().load(path, options)
        # This line shouldn't error out even though it calls an abstract method in its parent
        MyLoader().load(tmp_path, None)

    def test_check_path(self):
        "Test Loader.check_path method."

        class MyLoader(Loader):
            def load(self):
                pass

        loader = MyLoader()
        integer = 1
        with pytest.raises(TypeError) as e:
            loader.check_path(integer)
        assert str(e.value) == f'Unsupported path type "{type(integer)}".'


class TestFormatLoaderMap:
    "Test loaders._format_loader.*"

    def test_register_non_loader(self):
        "Test when it registers a non-Loader instance."

        flm = FormatLoaderMap()

        with pytest.raises(TypeError) as e:
            flm.register_loader('some-format', 'some-string')
        assert str(e.value) == 'loader "some-string" must be a Loader instance.'

    def test_load_non_existing_format(self, tmp_path):
        "Test loading a non-existing format."

        with pytest.raises(RuntimeError) as e:
            load_data_files('nonsense', tmp_path)

        assert str(e.value) == 'The format loader map does not specify a loader for format "nonsense".'

    def test_load_wrong_format_type(self, tmp_path):
        "Test loading a non-existing format."

        with pytest.raises(TypeError) as e:
            load_data_files(0x348f, tmp_path)

        assert str(e.value) == 'Parameter "fmt" must be a string or a dict, but it is of type "<class \'int\'>".'


class TestTextLoaders:

    def test_plain_text_loader_no_path(self):
        "Test PlainTextLoader when fed in with non-path."

        integer = 1
        with pytest.raises(TypeError) as e:
            PlainTextLoader().load(integer, {})

        assert str(e.value) == f'Unsupported path type "{type(integer)}".'

    def test_plain_text_loader_bad_encoding(self, tmp_path):
        "Test PlainTextLoader when the encoding is nonsense."

        text_file = tmp_path / 'some-text.txt'
        text_file.write_text("I'm a text file :)", encoding='utf-8')
        with pytest.raises(LookupError) as e:
            PlainTextLoader().load(text_file, {'encoding': "non-encoding"})

        assert str(e.value) == 'unknown encoding: non-encoding'

    def test_plain_text_loader_incorrect_encoding(self, tmp_path):
        "Test PlainTextLoader when the encoding does not match."

        text_file = tmp_path / 'some-text.txt'
        text_file.write_text("I'm a text file :)", encoding='utf-8')
        with pytest.raises(UnicodeError) as e:
            PlainTextLoader().load(text_file, {'encoding': "utf-16"})

        assert str(e.value) == 'UTF-16 stream does not start with BOM'


class TestTableLoaders:

    def test_csv_pandas_loader(self, tmp_path, noaa_jfk_schema):
        "Test the basic functioning of CSVPandasLoader."

        dataset = Dataset(noaa_jfk_schema, tmp_path, mode=Dataset.InitializationMode.DOWNLOAD_AND_LOAD)
        data = dataset.data['jfk_weather_cleaned']
        assert isinstance(data, pd.DataFrame)
        assert data.shape == (75119, 16)
        dataset.delete()

    Column = namedtuple('Column', ('name', 'dtype', 'check'))

    @pytest.mark.parametrize('columns',  # a list of Column (column name, specified data type, check function)
                             [
                                 # Only one column specified
                                 [Column('DATE', 'datetime', is_datetime64_any_dtype)],
                                 [Column('DATE', 'str', is_string_dtype)],
                                 [Column('DATE', 'string', is_string_dtype)],
                                 [Column('HOURLYPressureTendencyCons', 'float', is_float_dtype)],
                                 # Two columns specified
                                 [Column('DATE', 'datetime', is_datetime64_any_dtype),
                                  Column('HOURLYPressureTendencyCons', 'float', is_float_dtype)],
                                 # No column specified (let Pandas autodetect dtype)
                                 [Column('DATE', None, is_string_dtype),
                                  Column('HOURLYPressureTendencyCons', None, is_integer_dtype),
                                  Column('HOURLYVISIBILITY', None, is_float_dtype)],
                             ])
    def test_csv_pandas_column_data_types(self, tmp_path, noaa_jfk_schema, columns):
        "Test the column data types."

        assert len(columns) > 0  # Sanity check, make sure columns are there

        # Clear columns
        column_dict = noaa_jfk_schema['subdatasets']['jfk_weather_cleaned']['format']['options']['columns'] = {}

        # Update column dictionary as specified
        for col in columns:
            if col.dtype is not None:
                column_dict[col.name] = col.dtype

        dataset = Dataset(noaa_jfk_schema, tmp_path, mode=Dataset.InitializationMode.DOWNLOAD_AND_LOAD)
        data = dataset.data['jfk_weather_cleaned']
        for col in columns:
            assert col.check(data.dtypes[col.name])

    @pytest.mark.parametrize(('err_column',  # (column name, specified data type, default dtype checked for conversion)
                              'other_columns'),  # (column name, specified data type, None)
                             [
                                 # Only one unsupported specified
                                 (Column('DATE', 'float', 'str'), []),
                                 (Column('HOURLYVISIBILITY', 'int', 'float'), []),
                                 # Some supported specified
                                 (Column('DATE', 'float', 'str'), [Column('HOURLYPressureTendencyCons', 'int', None)]),
                                 (Column('HOURLYVISIBILITY', 'int', 'float'), [Column('DATE', 'datetime', None)]),
                                 # More than one unsupported specified. The error that raises the exception should be
                                 # put as err_column.
                                 (Column('DATE', 'float', 'str'), [Column('HOURLYVISIBILITY', 'int', 'float')]),
                             ])
    def test_csv_pandas_column_unsupported_data_types(self, tmp_path, noaa_jfk_schema,
                                                      err_column, other_columns):
        "Test column data types when they are unsupported."

        # Clear columns
        column_dict = noaa_jfk_schema['subdatasets']['jfk_weather_cleaned']['format']['options']['columns'] = {}

        # Update column dictionary as specified
        for col in other_columns:
            if col.dtype is not None:
                column_dict[col.name] = col.dtype
        column_dict[err_column.name] = err_column.dtype

        with pytest.raises(ValueError) as e:
            Dataset(noaa_jfk_schema, tmp_path, mode=Dataset.InitializationMode.DOWNLOAD_AND_LOAD)
        # Pandas is a 3rd-party library. We don't check for the exact wording but only some keywords
        # Examples:
        #   ValueError: cannot safely convert passed user dtype of int64 for float64 dtyped data in column 1
        #   ValueError: could not convert string to float: '2010-01-01 01:00:00'
        assert 'convert' in str(e.value)
        for t in (err_column.dtype, err_column.check):
            assert re.search(rf"{t}(\d*|ing)\b", str(e.value))  # "ing" is for "str'ing'"

    def test_csv_pandas_no_delimiter(self, tmp_path, noaa_jfk_schema):
        "Test when no delimiter is given."
        # Remove the delimiter option
        del noaa_jfk_schema['subdatasets']['jfk_weather_cleaned']['format']['options']['delimiter']
        data = Dataset(noaa_jfk_schema, tmp_path,
                       mode=Dataset.InitializationMode.DOWNLOAD_AND_LOAD).data['jfk_weather_cleaned']
        assert len(data.columns) == 16  # number of columns remain the same

    @pytest.mark.parametrize('delimiter', ('\t', ' ', '|', ';'))
    def test_csv_pandas_delimiter(self, tmp_path, noaa_jfk_schema, delimiter):
        "Test common delimiter settings. Note that the case of comma has been tested in ``test_csv_pandas_loader``."

        del noaa_jfk_schema['subdatasets']['jfk_weather_cleaned']['format']['options']['columns']
        # Change delimiter to tab, |, ;, space
        noaa_jfk_schema['subdatasets']['jfk_weather_cleaned']['format']['options']['delimiter'] = delimiter
        data = Dataset(noaa_jfk_schema, tmp_path,
                       mode=Dataset.InitializationMode.DOWNLOAD_AND_LOAD).data['jfk_weather_cleaned']
        # None of these delimiters exist in the file, number of columns should be 1.
        assert len(data.columns) == 1

    def test_csv_pandas_loader_no_path(self):
        "Test CSVPandasLoader when fed in with non-path."

        integer = 1
        with pytest.raises(TypeError) as e:
            CSVPandasLoader().load(integer, {})

        assert str(e.value) == f'Unsupported path type "{type(integer)}".'

    def test_csv_pandas_loader_non_option(self, tmp_path, noaa_jfk_schema):
        "Test CSVPandasLoader when None option is passed."

        del noaa_jfk_schema['subdatasets']['jfk_weather_cleaned']['format']['options']
        dataset = Dataset(noaa_jfk_schema, tmp_path, mode=Dataset.InitializationMode.DOWNLOAD_AND_LOAD)
        data = dataset.data['jfk_weather_cleaned']
        assert isinstance(data, pd.DataFrame)
        assert len(data) == 75119

    def test_csv_pandas_loader_no_encoding(self, tmp_path, noaa_jfk_schema):
        "Test CSVPandasLoader when no encoding is specified."

        del noaa_jfk_schema['subdatasets']['jfk_weather_cleaned']['format']['options']['encoding']
        self.test_csv_pandas_loader(tmp_path, noaa_jfk_schema)

    def test_csv_pandas_header(self, tmp_path, noaa_jfk_schema):
        "Test CSVPandasLoader header options"

        noaa_jfk_schema['subdatasets']['jfk_weather_cleaned']['format']['options']['no_header'] = True
        noaa_dataset = Dataset(noaa_jfk_schema, tmp_path, mode=Dataset.InitializationMode.DOWNLOAD_ONLY)
        with pytest.raises(ValueError) as exinfo:  # Pandas should error from trying to read string as another dtype
            noaa_dataset.load()
        assert('could not convert string to float' in str(exinfo.value))
        noaa_dataset.delete()

        false_test_cases = [False, '', None]  # These should all be treated as False
        for case in false_test_cases:
            noaa_jfk_schema['subdatasets']['jfk_weather_cleaned']['format']['options']['no_header'] = case
            self.test_csv_pandas_loader(tmp_path, noaa_jfk_schema)

        del noaa_jfk_schema['subdatasets']['jfk_weather_cleaned']['format']['options']['no_header']
        self.test_csv_pandas_loader(tmp_path, noaa_jfk_schema)
