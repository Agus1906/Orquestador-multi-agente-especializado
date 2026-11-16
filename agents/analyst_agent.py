"""Especialista de cómputo: recibe sólo evidencia seleccionada."""
from agents.tool_agent import call_role_tool
from tools import calculate_savings

PROMPT = 'Valida evidencia y calcula ahorro de tiempo; conserva IDs. No extrapoles a ahorro monetario.'


def analyst_agent(state, model=None):
    arguments = {'documents': state['research']['documents']}
    result = call_role_tool(model, PROMPT, arguments, calculate_savings, arguments, fixed_arguments=True)
    result['research_version'] = state['research']['version']
    return {'analysis': result,
            'contributions': [{'agent': 'analyst', 'step': state['steps'],
                               'detail': 'calculate_savings: validación y cálculo ponderado'}]}
