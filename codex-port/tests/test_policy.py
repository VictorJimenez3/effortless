import copy
import unittest
from effortless_codex.policy import State, choose, observe_manual, is_followup

CATALOG={'gpt-6.1-sol':['low','medium','high','xhigh','max','ultra']}

def request(effort='high',model='gpt-6.1-sol',mode=True,text='Implement this function.'):
    p={'threadId':'t','model':model,'effort':effort,'input':[{'type':'text','text':text}],
       'approvalPolicy':'on-request','sandboxPolicy':{'type':'readOnly'},
       'cwd':'/example','futureField':{'value':[1,2]}}
    if mode:p['collaborationMode']={'mode':'default','settings':{
        'model':model,'reasoning_effort':effort,'developer_instructions':'Keep me.'}}
    return {'id':4,'method':'turn/start','params':p}

def decision(profile='sol_low',**kw):
    return {'id':'turn','profile':profile,'action':'route','confidence':0.96,'reason':'Bounded work.',**kw}

class PolicyTests(unittest.TestCase):
    def test_changes_actual_settings_and_preserves_all_other_fields(self):
        r=request();original=copy.deepcopy(r);state=State()
        got,why=choose(r,state,decision(),{'auto':True},CATALOG)
        self.assertEqual(r,original)
        self.assertEqual(got['params']['effort'],'low')
        self.assertEqual(got['params']['collaborationMode']['settings']['reasoning_effort'],'low')
        self.assertEqual(got['params']['collaborationMode']['settings']['developer_instructions'],'Keep me.')
        for key in ['input','cwd','approvalPolicy','sandboxPolicy','futureField']:
            self.assertEqual(got['params'][key],r['params'][key])
        self.assertEqual(why,'routed')

    def test_luna_and_astra_suggestions_stay_on_sol(self):
        for profile,effort in [('luna_low','low'),('luna_medium','low'),('luna_xhigh','low'),('astra_high','xhigh'),('astra_medium','xhigh')]:
            got,_=choose(request(),State(),decision(profile),{'auto':True},CATALOG)
            self.assertEqual(got['params']['model'],'gpt-6.1-sol')
            self.assertEqual(got['params']['effort'],effort)

    def test_manual_other_model_and_maximum_effort_win(self):
        for r in [request(model='gpt-6-astra'),request(model='gpt-6-luna'),request(effort='max'),request(effort='ultra')]:
            self.assertEqual(choose(r,State(),decision(),{'auto':True},CATALOG)[0],r)

    def test_native_picker_change_disables_auto_but_permissions_change_does_not(self):
        state=State()
        observe_manual({'method':'thread/settings/update','params':{'threadId':'t','sandboxPolicy':{'type':'readOnly'}}},state)
        self.assertTrue(state.auto)
        msg={'method':'thread/settings/update','params':{'threadId':'t','effort':'high'}}
        observe_manual(msg,state)
        self.assertFalse(state.auto)
        self.assertEqual(choose(request(),state,decision(),{'auto':True},CATALOG)[0],request())

    def test_changed_per_turn_selection_wins(self):
        state=State();state.last_routed=('gpt-6.1-sol','low')
        r=request(effort='medium')
        self.assertEqual(choose(r,state,decision(),{'auto':True},CATALOG)[0],r)
        self.assertFalse(state.auto)

    def test_ui_following_automatic_settings_is_not_a_manual_override(self):
        state=State();state.last_routed=('gpt-6.1-sol','low')
        r=request(effort='low')
        got,_=choose(r,state,decision('sol_medium'),{'auto':True},CATALOG)
        self.assertEqual(got['params']['effort'],'medium')
        self.assertTrue(state.auto)

    def test_failures_and_unavailable_choices_forward_original(self):
        for d in [None,{},decision('missing'),decision(confidence=0.4),decision(confidence=True),decision(confidence=float('nan')),decision(action='keep')]:
            r=request()
            self.assertEqual(choose(r,State(),d,{'auto':True},CATALOG)[0],r)
        r=request();self.assertEqual(choose(r,State(),decision(),{'auto':True},{})[0],r)

    def test_auto_off_non_turn_and_followup_forward_original(self):
        for msg in [request(text='yes'),request(text='go ahead'),{'method':'turn/steer','params':{'threadId':'t'}}]:
            self.assertEqual(choose(msg,State(),decision(),{'auto':True},CATALOG)[0],msg)
        r=request();self.assertEqual(choose(r,State(),decision(),{'auto':False},CATALOG)[0],r)
        self.assertTrue(is_followup('Thanks!'))
        self.assertFalse(is_followup('Yes, but change the algorithm.'))

if __name__=='__main__':unittest.main()
