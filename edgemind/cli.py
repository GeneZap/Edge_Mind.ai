"""Terminal-only Layer 1 adapter. Does not leak CLI concerns into Layer 2."""
import argparse
import json
from .service import run_task

SAMPLE_DOCUMENTS = [
    {'source_id': 'sample/privacy', 'text': 'Private documents must remain on the local device.'},
    {'source_id': 'sample/compute', 'text': 'GPU accelerates supported language models; NPU can run small neural networks.'},
    {'source_id': 'sample/offline', 'text': 'Offline requests cannot call a cloud model.'},
]


def main():
    parser = argparse.ArgumentParser(description='EdgeMind Layer 2 terminal demonstration')
    parser.add_argument('--query', help='Task text; prompted if omitted')
    parser.add_argument('--privacy', choices=['local_only', 'cloud_allowed'], default='local_only')
    parser.add_argument('--network', choices=['online', 'offline'], default='online')
    parser.add_argument('--complexity', choices=['simple', 'complex'], default='simple')
    parser.add_argument('--demo-docs', action='store_true', help='Use three fake sample documents')
    parser.add_argument('--simulate-failure', action='store_true', help='Trigger one recoverable mock timeout')
    parser.add_argument('--json', action='store_true', help='Print complete state in JSON')
    args = parser.parse_args()
    query = args.query if args.query is not None else input('EdgeMind > ').strip()
    result = run_task(
        query=query,
        privacy_mode=args.privacy,
        network=args.network,
        complexity=args.complexity,
        documents=SAMPLE_DOCUMENTS if args.demo_docs else [],
        simulate_failure=args.simulate_failure,
    )
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print('\n===== EDGEMIND LAYER 2 / MOCK DEMO =====')
    for entry in result['trace']:
        print('  ' + entry)
    print('\nStatus:', result['status'])
    print('Decision:', result['decision'])
    print('Result:', result['tool_result']['content'] or '(none)')
    print('\nWARNING: All model responses and model capabilities are simulated.')
    print('No GPU/NPU inference and no cloud API call occurred in this demo.')


if __name__ == '__main__':
    main()
