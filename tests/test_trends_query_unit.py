"""Dependency-free checks of the actual function; SQL semantics run in PGlite CI."""
import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest


def query_function():
    tree = ast.parse((Path(__file__).resolve().parents[1] / 'trends/main.py').read_text())
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'all_articles')
    scope = {'timedelta': timedelta, 'active_urls': lambda: ['https://fixture.example/rss']}
    exec(compile(ast.Module(body=[function], type_ignores=[]), 'trends/main.py', 'exec'), scope)
    return scope['all_articles']


class Rows:
    def __init__(self, rows): self.rows = rows
    def fetchall(self): return self.rows


class TrendsQueryTest(unittest.TestCase):
    def test_pages_advance_without_loss_or_duplicates(self):
        calls = []
        class DB:
            def execute(self, sql, args):
                calls.append(args)
                return Rows([{'id': i} for i in [2, 5, 9, 12] if i > args[0]][:args[-1]])
        cutoff = datetime(2026, 10, 24, tzinfo=timezone.utc)
        result = query_function()(DB(), cutoff, page_size=2)
        self.assertEqual([r['id'] for r in result], [2, 5, 9, 12])
        self.assertEqual([c[0] for c in calls], [0, 5, 12])
        self.assertEqual(calls[0][1:4], (cutoff, cutoff-timedelta(hours=24), cutoff))

    def test_later_page_failure_does_not_return_partial_results(self):
        class QueryCancelled(Exception): pass
        class DB:
            def execute(self, sql, args):
                if args[0]: raise QueryCancelled('fixture')
                return Rows([{'id': 1}])
        with self.assertRaises(QueryCancelled):
            query_function()(DB(), datetime.now(timezone.utc), [], page_size=1)

    def test_invalid_page_sizes_fail_before_database_access(self):
        for size in [0, -1, True, 1.5, '1000']:
            with self.subTest(size=size), self.assertRaises(ValueError):
                query_function()(None, datetime.now(timezone.utc), page_size=size)


if __name__ == '__main__': unittest.main()
