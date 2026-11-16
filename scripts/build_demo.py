"""Regenera y ejecuta la demo portable; usa el intérprete actual como kernel."""
import os
import sys
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from graph import build_graph  # noqa: E402


def main():
    (ROOT / 'notebooks').mkdir(exist_ok=True)
    (ROOT / 'docs').mkdir(exist_ok=True)
    (ROOT / 'docs' / 'graph.mmd').write_text(build_graph().get_graph().draw_mermaid(), encoding='utf-8')
    notebook = nbf.v4.new_notebook(cells=[
        nbf.v4.new_markdown_cell('# Demo: orquestador multi-agente\n\n'
                                '**Pre-entrega 6 — Agustina Irisarri.** Demo del flujo de delegación.\n\n'
                                'Modo offline: agentes basados en reglas, búsqueda y datos simulados. '
                                'Sin claves ni llamadas a un proveedor de IA. '
                                'Resultado: 190 horas/mes de ahorro simulado. '
                                'Se comprueban también refinamiento y parada.'),
        nbf.v4.new_markdown_cell('## 1. Preparar\nEjecutar desde la raíz o desde `notebooks/`, '
                                'con dependencias instaladas y el kernel del entorno `.venv`.'),
        nbf.v4.new_code_cell("import sys\nfrom pathlib import Path\n\n"
                            "root = Path.cwd() if Path('graph.py').exists() else Path.cwd().parent\n"
                            "assert (root / 'graph.py').exists(), 'Abrir desde el repositorio'\n"
                            "sys.path.insert(0, str(root))\n"
                            "from agents.analyst_agent import analyst_agent  # noqa: E402\n"
                            "from graph import build_graph, run  # noqa: E402\n"
                            "from main import DEMO_QUERY  # noqa: E402\n"
                            "from state import initial_state  # noqa: E402\n\n"
                            "print(DEMO_QUERY)"),
        nbf.v4.new_markdown_cell('## 2. Observar la delegación real\n'
                                'Cada línea se obtiene de un evento del grafo; no es una traza escrita a mano.'),
        nbf.v4.new_code_cell("graph = build_graph()\n"
                            "for event in graph.stream(initial_state(DEMO_QUERY), {'recursion_limit': 100}):\n"
                            "    for node, update in event.items():\n"
                            "        print(node, '→', update.get('next_agent', 'aporte registrado'))\n"
                            "        if update.get('final_answer'):\n"
                            "            print('\\n' + update['final_answer'])"),
        nbf.v4.new_markdown_cell('## 3. Verificar el estado y la trazabilidad'),
        nbf.v4.new_code_cell("result = run(DEMO_QUERY)\n"
                            "assert result['task_completed']\n"
                            "assert result['analysis']['saved_hours'] == 190\n"
                            "assert len(result['analysis']['source_ids']) == 3\n"
                            "for item in result['contributions']:\n"
                            "    print(f\"{item['step']:02} | {item['agent']}: {item['detail']}\")"),
        nbf.v4.new_markdown_cell('## 4. Demostrar refinamiento\n'
                                'Inyección de fallo controlada: el primer análisis informa 999 horas. '
                                'El supervisor detecta la inconsistencia y exige recalcular.'),
        nbf.v4.new_code_cell("attempts = []\n"
                            "def incorrect_then_correct(state):\n"
                            "    attempts.append(1)\n    update = analyst_agent(state)\n"
                            "    if len(attempts) == 1:\n        update['analysis']['saved_hours'] = 999\n"
                            "    return update\n"
                            "refined = run(DEMO_QUERY, analyst_node=incorrect_then_correct)\n"
                            "assert refined['task_completed'] and len(attempts) == 2\n"
                            "assert refined['analysis']['saved_hours'] == 190\n"
                            "for item in refined['contributions']:\n"
                            "    print(item['agent'], '→', item['detail'])"),
        nbf.v4.new_markdown_cell('## 5. Demostrar parada segura\n'
                                'Una consulta ajena al corpus no debe producir cifras inventadas ni un ciclo infinito.'),
        nbf.v4.new_code_cell("incomplete = run('astrofísica cuántica galaxias', max_steps=3)\n"
                            "assert not incomplete['task_completed']\n"
                            "assert incomplete['steps'] == 4\n"
                            "print(incomplete['final_answer'])\n"
                            "print('Visitas al supervisor:', incomplete['steps'])"),
        nbf.v4.new_markdown_cell('## Comprobaciones\n'
                                'La ejecución verifica delegación, conservación de aportes, refinamiento y parada. '
                                'Los resultados son simulados; no prueban beneficios reales. '
                                'El modo LLM se configura en el README y requiere una API externa; '
                                'este notebook no consume créditos ni afirma validar una llamada real.')
    ])
    notebook.metadata.kernelspec = {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}
    # Kernel temporal autocontenido: no modifica kernels globales del usuario.
    kernel_dir = ROOT / 'output' / 'jupyter' / 'kernels' / 'demo'
    kernel_dir.mkdir(parents=True, exist_ok=True)
    import json
    (kernel_dir / 'kernel.json').write_text(json.dumps({
        'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
        'display_name': 'Demo local', 'language': 'python'}), encoding='utf-8')
    os.environ['JUPYTER_PATH'] = str(ROOT / 'output' / 'jupyter')
    NotebookClient(notebook, timeout=90, kernel_name='demo', resources={'metadata': {'path': str(ROOT)}}).execute()
    nbf.validate(notebook)
    path = ROOT / 'notebooks' / 'demo_delegacion.ipynb'
    nbf.write(notebook, path)
    print(f'Notebook ejecutado: {path}')


if __name__ == '__main__':
    main()
