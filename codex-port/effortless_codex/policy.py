"""Deterministic boundaries around the model's routing recommendation."""
from copy import deepcopy
from dataclasses import dataclass
import math
import re

PROFILES = {
    'luna_low': ('gpt-6-luna','low'),
    'luna_medium': ('gpt-6-luna','medium'),
    'luna_xhigh': ('gpt-6-luna','xhigh'),
    'sol_low': ('gpt-6.1-sol','low'),
    'sol_medium': ('gpt-6.1-sol','medium'),
    'sol_xhigh': ('gpt-6.1-sol','xhigh'),
    'astra_medium': ('gpt-6-astra','medium'),
    'astra_high': ('gpt-6-astra','high'),
}

@dataclass
class State:
    model: str = 'gpt-6.1-sol'
    effort: str = 'high'
    auto: bool = True
    last_routed: tuple | None = None
    recent_user: str = ''
    recent_reply: str = ''
    tokens: int = 0
    cached_tokens: int = 0
    provider: str = 'openai'
    main_thread: bool = True

def text_input(params):
    return '\n'.join(x.get('text','') for x in params.get('input',[]) if x.get('type')=='text')

def is_followup(text):
    value=re.sub(r'[.!?,\s]+$','',text.strip().lower())
    return value in {'yes','yep','yeah','ok','okay','go','go ahead','continue','proceed','thanks','thank you'}

def current_pair(params,state):
    mode=params.get('collaborationMode') or {}
    settings=mode.get('settings') or {}
    return (settings.get('model') or params.get('model') or state.model,
            settings.get('reasoning_effort') or params.get('effort') or state.effort)

def observe_manual(message,state):
    if message.get('method') in {'thread/settings/update','turn/settings/update'}:
        p=message.get('params') or {}
        if any(p.get(k) is not None for k in ['model','effort','collaborationMode']):
            state.auto=False

def eligible(message,state,config):
    if message.get('method')!='turn/start':return False,'passthrough'
    if not config.get('auto',True) or not state.auto:return False,'auto_off'
    p=message.get('params') or {}
    if not state.main_thread or p.get('parentTurnId') or p.get('rootTurnId'):return False,'delegated_turn'
    pair=current_pair(p,state)
    if is_followup(text_input(p)) and pair[0]==state.model:return False,'continuation'
    if state.last_routed and pair!=state.last_routed:
        state.auto=False
        return False,'manual_override'
    if state.provider!='openai' or pair[0]!='gpt-6.1-sol':return False,'manual_model'
    if pair[1] in {'max','ultra'}:return False,'manual_effort'
    if any(x.get('type')!='text' for x in p.get('input',[])):return False,'attached_input'
    if not text_input(p).strip():return False,'no_text'
    if is_followup(text_input(p)):return False,'continuation'
    return True,'eligible'

def choose(message,state,decision,config,catalog):
    result=deepcopy(message)
    allowed,reason=eligible(message,state,config)
    if reason=='continuation' and state.last_routed:
        set_pair(result['params'],*state.last_routed)
    if not allowed:return result,reason
    if not isinstance(decision,dict):return result,'judge_unavailable'
    confidence=decision.get('confidence')
    if isinstance(confidence,bool) or not isinstance(confidence,(int,float)) or not math.isfinite(confidence) or not config.get('minimum_confidence',0.85)<=confidence<=1:
        return result,'low_confidence'
    if decision.get('action')!='route':return result,'judge_keep'
    profile=decision.get('profile')
    if profile not in PROFILES:return result,'invalid_profile'
    recommended_model,effort=PROFILES[profile]
    model='gpt-6.1-sol'
    # The worker floor is independent of a judge's confidence or category.
    if recommended_model=='gpt-6-luna':effort='low'
    elif recommended_model=='gpt-6-astra':effort='xhigh'
    if effort not in catalog.get(model,[]):return result,'unavailable_profile'
    set_pair(result['params'],model,effort)
    state.last_routed=(model,effort)
    return result,'routed'


def set_pair(params,model,effort):
    params['model']=model;params['effort']=effort
    mode=params.get('collaborationMode')
    if isinstance(mode,dict) and isinstance(mode.get('settings'),dict):
        mode['settings']['model']=model
        mode['settings']['reasoning_effort']=effort
