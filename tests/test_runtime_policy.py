"""Run the real entrypoint guards offline, without importing model SDKs."""
import ast
import os
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

from collector.runtime_policy import AIDisabled, require_ai

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {'trends/main.py': ['vectors', 'prepare', 'main'],
           'daily/main.py': ['embeddings', 'run', 'main'],
           'reference_compare/main.py': ['run'], 'trends/calibrate.py': ['main']}


class RuntimePolicyTest(unittest.TestCase):
    def test_keys_and_legacy_flags_cannot_enable_ai(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'fixture-only', 'AI_ENABLED': '1'}):
            with self.assertRaisesRegex(AIDisabled, 'FARZA_AI_DISABLED'):
                require_ai()


def entrypoint_test(path, name):
    def test(self):
        tree = ast.parse((ROOT/path).read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
        scope = {'require_ai': require_ai}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), path, 'exec'), scope)
        # No database/model globals are provided: any work before the guard fails.
        with patch.object(socket, 'socket', side_effect=AssertionError('network forbidden')) as net:
            with self.assertRaisesRegex(AIDisabled, 'FARZA_AI_DISABLED'):
                scope[name](*([None]*len(fn.args.args)))
            net.assert_not_called()
    return test


for path, names in TARGETS.items():
    for name in names:
        setattr(RuntimePolicyTest, 'test_disabled_'+path.replace('/', '_').replace('.', '_')+'_'+name,
                entrypoint_test(path, name))


if __name__ == '__main__': unittest.main()
