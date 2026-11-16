"""Herramientas acotadas: recuperación local y cálculo sin eval ni ejecución de código."""
import json
import math
import re
import unicodedata
from pathlib import Path

from langchain_core.tools import tool

CORPUS = Path(__file__).parent / 'data' / 'corpus.json'


def tokens(text: str) -> set[str]:
    normalized = ''.join(c for c in unicodedata.normalize('NFD', text.lower())
                         if unicodedata.category(c) != 'Mn')
    stopwords = {'los', 'las', 'del', 'una', 'por', 'para', 'con', 'que', 'sus', 'como'}
    return set(re.findall(r'[a-z0-9]{3,}', normalized)) - stopwords


@tool
def search_corpus(query: str, limit: int = 3) -> list[dict]:
    """Busca documentos relevantes en un corpus local de pilotos RPA simulados."""
    if not 1 <= limit <= 10:
        raise ValueError('limit debe estar entre 1 y 10')
    documents = json.loads(CORPUS.read_text(encoding='utf-8'))
    if not isinstance(documents, list):
        raise ValueError('El corpus debe ser una lista')
    ranked = [(len(tokens(query) & tokens(d['text'])), d) for d in documents]
    return [dict(d) for score, d in sorted(ranked, key=lambda x: -x[0]) if score > 0][:limit]


@tool
def calculate_savings(documents: list[dict]) -> dict:
    """Valida registros y calcula ahorro mensual en horas y porcentaje ponderado."""
    if not documents:
        raise ValueError('No hay documentos para analizar')
    ids = set()
    rows = []
    for d in documents:
        if not d.get('id') or d['id'] in ids or not d.get('source'):
            raise ValueError('Documento sin identidad/fuente o duplicado')
        ids.add(d['id'])
        values = [d[k] for k in ('before_minutes', 'after_minutes', 'volume_month')]
        if any(isinstance(v, bool) or not isinstance(v, (int, float))
               or not math.isfinite(v) for v in values):
            raise ValueError('Datos numéricos inválidos')
        before, after, volume = values
        if before <= 0 or after < 0 or after > before or volume <= 0 or int(volume) != volume:
            raise ValueError('Tiempos o volumen fuera de dominio')
        rows.append({'id': d['id'], 'source': d['source'],
                     'before_hours': before * volume / 60,
                     'after_hours': after * volume / 60,
                     'saved_hours': (before - after) * volume / 60})
    before = sum(r['before_hours'] for r in rows)
    after = sum(r['after_hours'] for r in rows)
    return {'rows': rows, 'before_hours': before, 'after_hours': after,
            'saved_hours': before - after, 'reduction_pct': (before - after) / before * 100,
            'source_ids': [d['id'] for d in documents]}
