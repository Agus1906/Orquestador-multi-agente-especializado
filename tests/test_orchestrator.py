import copy

import pytest
from langchain_core.messages import AIMessage

from agents.analyst_agent import analyst_agent
from agents.research_agent import research_agent
from agents.supervisor import Decision, rubric
from graph import build_graph, run
from main import DEMO_QUERY
from state import initial_state
from tools import calculate_savings, search_corpus


def test_complete_flow_and_totals():
    result = run(DEMO_QUERY)
    assert result['task_completed']
    assert [e['agent'] for e in result['contributions']] == [
        'supervisor', 'research', 'supervisor', 'analyst', 'supervisor', 'synthesis']
    assert result['analysis']['saved_hours'] == pytest.approx(190)
    assert result['analysis']['before_hours'] == pytest.approx(256.6666666667)
    assert result['analysis']['after_hours'] == pytest.approx(66.6666666667)
    assert result['analysis']['reduction_pct'] == pytest.approx(74.02597402597)
    assert len(result['messages']) == 2
    assert 'SIMULADOS' in result['final_answer']
    assert all(d['source'] in result['final_answer'] for d in result['research']['documents'])


def test_refinement_replaces_invalid_analysis_preserving_history():
    attempts = []

    def inaccurate_then_correct(state):
        attempts.append(1)
        update = analyst_agent(state)
        if len(attempts) == 1:
            update['analysis']['saved_hours'] = 999
        return update

    result = run(DEMO_QUERY, analyst_node=inaccurate_then_correct)
    assert result['task_completed']
    assert len(attempts) == 2
    assert result['analysis']['saved_hours'] == 190
    assert any('no concilia' in e['detail'] for e in result['contributions'])


def test_no_evidence_stops_with_bounded_steps():
    result = run('astrofísica cuántica galaxias', max_steps=3)
    assert not result['task_completed']
    assert result['steps'] == 4
    assert 'No se completó' in result['final_answer']


def test_permanent_wrong_analysis_does_not_loop_forever():
    result = run(DEMO_QUERY, max_steps=3, analyst_node=lambda state: {'analysis': {}})
    assert not result['task_completed']
    assert result['steps'] == 4


def test_tool_failure_stops_without_exposing_secret():
    def broken(state):
        raise RuntimeError('secret-do-not-log')
    result = run(DEMO_QUERY, research_node=broken)
    assert not result['task_completed']
    assert 'RuntimeError' in result['error']
    assert 'secret-do-not-log' not in str(result)


def test_old_analysis_invalidated():
    state = initial_state(DEMO_QUERY)
    state.update(research_agent(state))
    state.update(analyst_agent(state))
    state['research']['version'] += 1
    assert rubric(state)[0] == 'analyst'


@pytest.mark.parametrize('query', ['', ' ', 'x' * 4001, None])
def test_query_validation(query):
    with pytest.raises(ValueError):
        initial_state(query)


@pytest.mark.parametrize('field,value', [('before_minutes', 0), ('after_minutes', -1),
                                       ('volume_month', 0.5), ('before_minutes', float('nan')),
                                       ('before_minutes', True), ('after_minutes', 999)])
def test_invalid_numbers(field, value):
    documents = copy.deepcopy(search_corpus.invoke({'query': 'RPA'}))
    documents[0][field] = value
    with pytest.raises(ValueError):
        calculate_savings.invoke({'documents': documents})


def test_duplicate_source_rejected():
    documents = search_corpus.invoke({'query': 'RPA'})
    with pytest.raises(ValueError):
        calculate_savings.invoke({'documents': documents + documents})


def test_branches_present_in_graph():
    mermaid = build_graph().get_graph().draw_mermaid()
    for node in ('supervisor', 'research', 'analyst', 'synthesis', 'stop'):
        assert node in mermaid


class FakeModel:
    """Transport simulado: ejercita prompts, esquema y herramientas sin API."""
    def __init__(self, early_finish=False):
        self.early_finish = early_finish
        self.contexts = []

    def with_structured_output(self, schema):
        parent = self

        class Router:
            def invoke(self, messages):
                import json
                data = json.loads(messages[1][1])
                parent.contexts.append(data)
                return Decision(next_agent='synthesis' if parent.early_finish else data['required'],
                                reason='Decisión de prueba')
        return Router()

    def bind_tools(self, tools, tool_choice):
        class Specialist:
            def invoke(self, messages):
                import json
                context = json.loads(messages[1][1])
                args = {'query': context['query']} if tool_choice == 'search_corpus' else context
                return AIMessage(content='', tool_calls=[{'name': tool_choice, 'args': args, 'id': 'call-1'}])
        return Specialist()


@pytest.mark.parametrize('early_finish', [False, True])
def test_model_tool_flow_and_rubric_guard(early_finish):
    model = FakeModel(early_finish)
    result = run(DEMO_QUERY, model=model)
    assert result['task_completed']
    assert result['analysis']['saved_hours'] == 190
    assert all('messages' not in context and 'documents' not in context for context in model.contexts)


def test_analysis_cannot_modify_tool_inputs():
    from agents.tool_agent import call_role_tool
    model = FakeModel()
    with pytest.raises(ValueError, match='alterar'):
        call_role_tool(model, 'Analiza', {'documents': []}, calculate_savings,
                       {'documents': [{'id': 'different'}]}, fixed_arguments=True)
