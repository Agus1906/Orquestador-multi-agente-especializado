"""CLI: demo offline o supervisor LLM configurable sin secretos en código."""
import argparse
import json
import logging
import os
from pathlib import Path

from graph import run

DEMO_QUERY = 'Investiga los pilotos de automatización RPA administrativos y calcula el ahorro mensual de tiempo.'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query', nargs='?', default=DEMO_QUERY)
    parser.add_argument('--mode', choices=['offline', 'llm'], default='offline')
    parser.add_argument('--max-steps', type=int, default=8)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s %(message)s')
    model = None
    if args.mode == 'llm':
        from langchain_openai import ChatOpenAI
        if not os.environ.get('OPENAI_API_KEY') or not os.environ.get('OPENAI_MODEL'):
            parser.error('Configura OPENAI_API_KEY y OPENAI_MODEL en el entorno')
        model = ChatOpenAI(model=os.environ['OPENAI_MODEL'], timeout=30, max_retries=1)
    result = run(args.query, max_steps=args.max_steps, model=model)
    for event in result['contributions']:
        print(f"{event['step']:02} | {event['agent']}: {event['detail']}")
    print('\n' + result['final_answer'])
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Sólo una selección serializable; salida explícitamente solicitada por CLI.
        args.output.write_text(json.dumps({k: v for k, v in result.items() if k != 'messages'},
                                         ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if result['task_completed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
