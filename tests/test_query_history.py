"""
Test query_history.py.

All tests isolate storage to a pytest `tmp_path` via the `history_dir` fixture below -
none of them touch the real project's `.query_history/` directory.
"""
import json
import os
from unittest import mock
import pytest
import source.library.query_history as qh


@pytest.fixture
def history_dir(tmp_path, monkeypatch):  # noqa
    monkeypatch.setattr(qh, 'HISTORY_DIR', str(tmp_path / '.query_history'))
    return tmp_path


def test_load_history__missing_file_returns_empty(history_dir):  # noqa
    assert qh.load_history('snowflake') == []


def test_record_query__adds_new_entry(history_dir):  # noqa
    history = qh.record_query('snowflake', 'SELECT 1')
    assert len(history) == 1
    assert history[0]['sql'] == 'SELECT 1'
    assert history[0]['title'] is None
    assert history[0]['last_used']


def test_record_query__strips_whitespace(history_dir):  # noqa
    history = qh.record_query('snowflake', '  SELECT 1  \n')
    assert history[0]['sql'] == 'SELECT 1'


def test_record_query__blank_query_is_a_noop(history_dir):  # noqa
    assert qh.record_query('snowflake', '') == []
    assert qh.record_query('snowflake', '   ') == []
    assert qh.load_history('snowflake') == []


def test_record_query__dedup_bumps_to_front_without_duplicating(history_dir):  # noqa
    qh.record_query('snowflake', 'SELECT 1')
    qh.record_query('snowflake', 'SELECT 2')
    history = qh.record_query('snowflake', 'SELECT 1')
    assert [e['sql'] for e in history] == ['SELECT 1', 'SELECT 2']
    assert len(history) == 2


def test_record_query__bumping_preserves_existing_title(history_dir):  # noqa
    qh.record_query('snowflake', 'SELECT 1')
    qh.update_title('snowflake', 'SELECT 1', 'My Favorite')
    qh.record_query('snowflake', 'SELECT 2')
    history = qh.record_query('snowflake', 'SELECT 1')
    assert history[0]['sql'] == 'SELECT 1'
    assert history[0]['title'] == 'My Favorite'


def test_record_query__caps_at_max_entries(history_dir):  # noqa
    for i in range(qh.MAX_ENTRIES + 5):
        qh.record_query('snowflake', f'SELECT {i}')
    history = qh.load_history('snowflake')
    assert len(history) == qh.MAX_ENTRIES
    # most recent should be first
    assert history[0]['sql'] == f'SELECT {qh.MAX_ENTRIES + 4}'


def test_record_query__sources_are_independent(history_dir):  # noqa
    qh.record_query('snowflake', 'SELECT 1')
    qh.record_query('bigquery', 'SELECT 2')
    assert [e['sql'] for e in qh.load_history('snowflake')] == ['SELECT 1']
    assert [e['sql'] for e in qh.load_history('bigquery')] == ['SELECT 2']


def test_update_title__sets_title(history_dir):  # noqa
    qh.record_query('snowflake', 'SELECT 1')
    history = qh.update_title('snowflake', 'SELECT 1', 'My Title')
    assert history[0]['title'] == 'My Title'


def test_update_title__blank_clears_title(history_dir):  # noqa
    qh.record_query('snowflake', 'SELECT 1')
    qh.update_title('snowflake', 'SELECT 1', 'My Title')
    history = qh.update_title('snowflake', 'SELECT 1', '')
    assert history[0]['title'] is None


def test_update_title__unknown_query_is_a_noop(history_dir):  # noqa
    qh.record_query('snowflake', 'SELECT 1')
    history = qh.update_title('snowflake', 'SELECT does not exist', 'Title')
    assert len(history) == 1
    assert history[0]['title'] is None


def test_delete_query__removes_matching_entry(history_dir):  # noqa
    qh.record_query('snowflake', 'SELECT 1')
    qh.record_query('snowflake', 'SELECT 2')
    history = qh.delete_query('snowflake', 'SELECT 1')
    assert [e['sql'] for e in history] == ['SELECT 2']
    assert [e['sql'] for e in qh.load_history('snowflake')] == ['SELECT 2']


def test_delete_query__unknown_query_is_a_noop(history_dir):  # noqa
    qh.record_query('snowflake', 'SELECT 1')
    history = qh.delete_query('snowflake', 'SELECT does not exist')
    assert len(history) == 1


def test_delete_query__last_entry_leaves_empty_list(history_dir):  # noqa
    qh.record_query('snowflake', 'SELECT 1')
    history = qh.delete_query('snowflake', 'SELECT 1')
    assert history == []
    assert qh.load_history('snowflake') == []


# -- malformed / hand-edited history file -------------------------------------------

def test_load_history__top_level_not_a_list_returns_empty(history_dir):  # noqa
    os.makedirs(qh.HISTORY_DIR)
    with open(os.path.join(qh.HISTORY_DIR, 'snowflake.json'), 'w') as f:
        json.dump({'not': 'a list'}, f)
    assert qh.load_history('snowflake') == []


def test_load_history__invalid_json_returns_empty(history_dir):  # noqa
    os.makedirs(qh.HISTORY_DIR)
    with open(os.path.join(qh.HISTORY_DIR, 'snowflake.json'), 'w') as f:
        f.write('{not valid json')
    assert qh.load_history('snowflake') == []


def test_load_history__filters_and_normalizes_malformed_entries(history_dir):  # noqa
    os.makedirs(qh.HISTORY_DIR)
    with open(os.path.join(qh.HISTORY_DIR, 'snowflake.json'), 'w') as f:
        json.dump([
            'just a string',
            {'no_sql_key': True},
            {'sql': 123},
            {'sql': '   '},
            {'sql': 'SELECT good', 'title': 5, 'last_used': None},
            {'sql': 'SELECT also_good', 'title': 'Nice', 'last_used': '2026-01-01T00:00:00+00:00'},
        ], f)
    history = qh.load_history('snowflake')
    assert [e['sql'] for e in history] == ['SELECT also_good', 'SELECT good']
    # bad title type coerced to None, bad last_used type coerced to '' - never raises downstream
    assert history[1]['title'] is None
    assert history[1]['last_used'] == ''


def test_record_query__still_works_after_malformed_entries_are_present(history_dir):  # noqa
    os.makedirs(qh.HISTORY_DIR)
    with open(os.path.join(qh.HISTORY_DIR, 'snowflake.json'), 'w') as f:
        json.dump([{'sql': 'SELECT good'}, {'garbage': True}], f)
    history = qh.record_query('snowflake', 'SELECT new')
    assert [e['sql'] for e in history] == ['SELECT new', 'SELECT good']


# -- atomic write ----------------------------------------------------------------------

def test_save_history__failed_write_does_not_corrupt_existing_file(history_dir):  # noqa
    qh.record_query('snowflake', 'SELECT 1')
    qh.record_query('snowflake', 'SELECT 2')

    with mock.patch.object(qh.json, 'dump', side_effect=OSError('simulated disk failure')), \
            pytest.raises(OSError, match='simulated disk failure'):
        qh.record_query('snowflake', 'SELECT 3')

    # file must still hold the last good state, not be empty/truncated/corrupted
    history = qh.load_history('snowflake')
    assert [e['sql'] for e in history] == ['SELECT 2', 'SELECT 1']

    # no leftover temp files
    leftovers = [f for f in os.listdir(qh.HISTORY_DIR) if f.endswith('.tmp')]
    assert leftovers == []


# -- truncate_sql_preview --------------------------------------------------------------

def test_truncate_sql_preview__short_query_unchanged():
    assert qh.truncate_sql_preview('SELECT 1') == 'SELECT 1'


def test_truncate_sql_preview__collapses_newlines_and_whitespace():
    sql = 'SELECT  1\n  FROM\ttable\n  WHERE x = 1'
    assert qh.truncate_sql_preview(sql) == 'SELECT 1 FROM table WHERE x = 1'


def test_truncate_sql_preview__truncates_long_query_with_ellipsis():
    sql = 'SELECT ' + ('x' * 600)
    preview = qh.truncate_sql_preview(sql, max_length=50)
    assert len(preview) == 51  # 50 chars + ellipsis
    assert preview.endswith('…')
