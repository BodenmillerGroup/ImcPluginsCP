import numpy
import pytest
import io
import os
import csv

import cellprofiler_core.image
import cellprofiler_core.measurement

import cellprofiler_core.modules.injectimage
import cellprofiler_core.object
import cellprofiler_core.pipeline
import cellprofiler_core.workspace
from cellprofiler_core.utilities.core import modules as cpmodules

IMAGE_NAME = "image"
OUTPUT_IMAGE_F = "outputimage%d"

COLUMN_NAME = "column_name"
CATEGORY = "category"
IMAGE_NAME = "image_name"
OBJECT_NAME = "object_name"
FEATURE_NAME = "feature_name"
CHANNEL = "channel"
PARAMETERS = "parameters"
DATATYPE = "data_type"
CHANNEL_ID = "channel_id"
PATTERN = "pattern"

import plugins.exportvarcsv as exportvarcsv

DIR_SCRIPT = os.path.dirname(__file__)
PATH_TESTFILE = os.path.join(DIR_SCRIPT, 'testdata/var_test.csv')

class FakePipeline:
    def __init__(self, measurement_columns):
        self.measurement_columns = measurement_columns

    def get_measurement_columns(self):
        return self.measurement_columns

class FakeWorkspace:
    def __init__(self, measurement_columns):
        self.pipeline = FakePipeline(measurement_columns)

@pytest.fixture(scope="function")
def module():
    module = exportvarcsv.ExportVarCsv()
    return module

@pytest.fixture(scope="function")
def testdata():
    with open(PATH_TESTFILE, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        rows = [row for row in csvreader]
    # convert to dict:
    keys = rows.pop(0)
    testdata = []
    for row in rows:
        testcase = {}
        for k, r in zip(keys, row):
            if r == '':
                r = None
            testcase[k] = r
        testdata.append(testcase)
    return testdata



def test_init(module):
    pass

def test_add_imagemeta_group(module):
    module.add_image_meta()

def test_objects_file_name(module):
    fn = module.make_objects_file_name('test', None)
    assert os.path.basename(fn) == 'var_test.csv'

    module.wants_prefix.value = True
    module.prefix.value = 'prefix_'
    fn = module.make_objects_file_name('test', None)
    assert os.path.basename(fn) == 'prefix_test.csv'

def test_parsing(module, testdata):
    """
    Test parsing based on a testset of manually validated parsing
    results.
    """
    test_object = 'test_object'

    measurement_columns = []
    for case in testdata:
        pattern = case.pop(PATTERN)
        column_name = pattern.format(**case)
        assert column_name == case[COLUMN_NAME], f'Pattern {pattern}' \
                                                 f'in testdata not ' \
                                                 'valid.' \
                                                 f'{column_name} != ' \
                                                 f'{case[COLUMN_NAME]}'
        measurement_columns.append(
            (test_object, column_name, case[DATATYPE])
        )

    # remove channel id for this test as no channel id matching was performed.
    for case in testdata:
        case[CHANNEL_ID] = None

    workspace = FakeWorkspace(measurement_columns)
    meta = module.get_var_meta(test_object, workspace)

    assert meta == testdata, 'Parsed metadata doesnt fit test metadata'
    for m, t in zip(meta, testdata):
        assert m.keys() == t.keys(), 'Key order doesnt match'




