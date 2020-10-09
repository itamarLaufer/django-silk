from django.test import TestCase
from mock import Mock, NonCallableMock, NonCallableMagicMock, patch

from silk.collector import DataCollector
from silk.models import SQLQuery, Request
from silk.sql import execute_sql
from .util import delete_all_models

from silk.sql import SilkyCursorWrapper


def mock_sql():
    mock_sql_query = Mock(spec_set=['_execute_sql', 'query', 'as_sql'])
    mock_sql_query._execute_sql = Mock()
    mock_sql_query.query = NonCallableMock(spec_set=['model'])
    mock_sql_query.query.model = Mock()
    query_string = 'SELECT * FROM table_name'
    mock_sql_query.as_sql = Mock(return_value=(query_string, ()))
    return mock_sql_query, query_string

def call_execute_sql(cls, request):
    DataCollector().configure(request=request)
    delete_all_models(SQLQuery)
    cls.mock_sql, cls.query_string = mock_sql()
    kwargs = {
        'one': 1,
        'two': 2
    }
    cls.args = [1, 2]
    cls.kwargs = kwargs
    execute_sql(cls.mock_sql, *cls.args, **cls.kwargs)


class TestCallNoRequest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestCallNoRequest, cls).setUpClass()
        call_execute_sql(cls, None)

    def test_called(self):
        self.mock_cursor.execute.assert_called_once_with(self.query_string, self.params)

    def test_count(self):
        self.assertEqual(0, len(DataCollector().queries))


class TestCallRequest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestCallRequest, cls).setUpClass()
        call_execute_sql(cls, Request())

    def test_called(self):
        self.mock_sql._execute_sql.assert_called_once_with(*self.args, **self.kwargs)

    def test_count(self):
        self.assertEqual(1, len(DataCollector().queries))

    def test_query(self):
        query = list(DataCollector().queries.values())[0]
        self.assertEqual(query['query'], self.query_string)


class TestCallSilky(TestCase):
    def test_no_effect(self):
        DataCollector().configure()
        sql, query_string = mock_sql()
        sql.query.model = NonCallableMagicMock(spec_set=['__module__'])
        sql.query.model.__module__ = 'silk.models'
        cursor = mock_cursor()
        wrapper = SilkyCursorWrapper(cursor, Mock(spec_set=[]))
        # No SQLQuery models should be created for silk requests for obvious reasons
        with patch('silk.sql.DataCollector', return_value=Mock()) as mock_DataCollector:
            wrapper.execute(query_string)
            self.assertFalse(mock_DataCollector().register_query.call_count)


class TestCollectorInteraction(TestCase):

    def setUp(self):
        DataCollector().request = Mock()

    def _query(self):
        try:
            query = list(DataCollector().queries.values())[0]
        except IndexError:
            self.fail('No queries created')
        return query

    def test_request(self):
        DataCollector().configure(request=Request.objects.create(path='/path/to/somewhere'))
        sql, qs = mock_sql()
        cursor = mock_cursor()
        wrapper = SilkyCursorWrapper(cursor, Mock(spec_set=[]))
        wrapper.execute(qs)
        query = self._query()
        print query
        self.assertEqual(query['request'], DataCollector().request)

    def test_registration(self):
        DataCollector().configure(request=Request.objects.create(path='/path/to/somewhere'))
        sql, qs = mock_sql()
        cursor = mock_cursor()
        wrapper = SilkyCursorWrapper(cursor, Mock(spec_set=[]))
        wrapper.execute(qs)
        query = self._query()
        self.assertIn(query, DataCollector().queries.values())

