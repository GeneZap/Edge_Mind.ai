import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from edgemind.retrieval import LocalIndex
from edgemind.service import run_task


class TestPrivateIndex(unittest.TestCase):
    def test_persistence_and_workspace_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            db = str(Path(directory) / 'index.db')
            with patch('edgemind.retrieval.embeddings', return_value=None):
                index = LocalIndex(db_path=db)
                self.assertGreater(index.put('workspace-A', 'foo.py', 'def calculate_invoice(): return 4'), 0)
                self.assertEqual(index.put('workspace-A', 'image.png', 'not text'), 0)
                self.assertEqual(index.count('workspace-A'), 1)
                self.assertEqual(index.count('workspace-B'), 0)
                fresh = LocalIndex(db_path=db)
                self.assertEqual(fresh.search('workspace-A', 'calculate_invoice')[0]['source_id'], 'foo.py#chunk-0')
                self.assertEqual(fresh.search('workspace-B', 'calculate_invoice'), [])

    def test_replace_document(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('edgemind.retrieval.embeddings', return_value=None):
                index = LocalIndex(db_path=str(Path(directory) / 'index.db'))
                index.put('space', 'test.py', 'first_token')
                index.put('space', 'test.py', 'second_token')
                self.assertEqual(index.count('space'), 1)
                self.assertEqual(index.search('space', 'first_token'), [])
                self.assertEqual(len(index.search('space', 'second_token')), 1)


class TestRealPipeline(unittest.TestCase):
    registry = [
        {'model_id': 'local-test', 'provider': 'local', 'device': 'LOCAL',
         'complexities': ['simple', 'complex'], 'available': True},
        {'model_id': 'cloud-test', 'provider': 'cloud', 'device': 'CLOUD',
         'complexities': ['simple', 'complex'], 'available': True},
    ]

    @patch('edgemind.providers.generate')
    def test_cloud_failure_falls_back_to_local(self, generate):
        from edgemind.providers import ProviderError
        def answer(model, provider, query, evidence):
            if provider == 'cloud':
                raise ProviderError('network disconnected')
            return 'Local answer'
        generate.side_effect = answer
        result = run_task('Explain the function', privacy_mode='cloud_allowed',
                          available_models=self.registry, use_real_models=True, prefer_cloud=True)
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertEqual(result['decision']['provider'], 'local')
        self.assertEqual(result['tool_result']['content'], 'Local answer')
        self.assertEqual(generate.call_count, 2)

    @patch('edgemind.providers.generate')
    def test_private_request_never_calls_cloud(self, generate):
        generate.return_value = 'Private local answer'
        result = run_task('Analyze private source', privacy_mode='local_only',
                          available_models=self.registry, use_real_models=True)
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertEqual(result['decision']['provider'], 'local')
        self.assertEqual(generate.call_args.args[1], 'local')

    @patch('edgemind.providers.generate')
    def test_no_models_is_deferred(self, generate):
        result = run_task('Something', available_models=[], use_real_models=True)
        self.assertEqual(result['status'], 'DEFERRED')
        generate.assert_not_called()

    @patch('edgemind.providers.generate')
    def test_fallback_failure_is_bounded(self, generate):
        from edgemind.providers import ProviderError
        generate.side_effect = ProviderError('service unavailable')
        result = run_task('Something', privacy_mode='cloud_allowed',
                          available_models=self.registry, use_real_models=True, prefer_cloud=True)
        self.assertEqual(result['status'], 'DEFERRED')
        self.assertEqual(generate.call_count, 2)


if __name__ == '__main__':
    unittest.main()
