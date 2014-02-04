#!/usr/bin/env python
# encoding: utf-8

from fysom import Fysom
from heapq import heappush, heapify
from LEElements import Statement, IfStatement, Block


class LE_Command_Parser:

    _error_occoured = False
    _message_buf = ''
    _delay_buf = ''
    _statement = Statement()
    _block_stack = [Block()]

    def onfound_delay(self, e):
        if self.DEBUG:
            print 'event: %s, src: %s, dst: %s' % (e.event, e.src, e.dst)
        self._statement.delay = e.args[1]

        if e.dst == "error_state":
            self._error_occoured = True

    def onfound_trigger(self, e):
        if self.DEBUG:
            print 'event: %s, src: %s, dst: %s' % (e.event, e.src, e.dst)
        self._statement.trigger = e.args[1]

        if e.dst == "error_state":
            self._error_occoured = True

    def onfound_target(self, e):
        if self.DEBUG:
            print 'event: %s, src: %s, dst: %s' % (e.event, e.src, e.dst)
        self._statement.target = e.args[1]

        if e.dst == "error_state":
            self._error_occoured = True

    def onfound_action(self, e):
        if self.DEBUG:
            print 'event: %s, src: %s, dst: %s' % (e.event, e.src, e.dst)
        self._statement.action = e.args[1]

        if e.dst == "error_state":
            self._error_occoured = True

    def onfound_others(self, e):
        if self.DEBUG:
            print 'event: %s, src: %s, dst: %s' % (e.event, e.src, e.dst)

        if e.dst == "error_state":
            self._error_occoured = True

    def onfound_finish_flag(self, e):
        if self.DEBUG:
            print 'finish ! = event: %s, src: %s, dst: %s' \
                                % (e.event, e.src, e.dst)

        self._statement.finish = e.args[1]

        if e.dst == "error_state":
            self._error_occoured = True
        elif e.src in ['action_state', 'target_state', 'message_state']:
            block = self._block_stack[-1]
            if isinstance(block, Block):
                self._append_statement(block)

            if self.finish_callback:
                self.finish_callback(self._block_stack[0])

            self._reset_element()

    def onfound_stop_flag(self, e):
        if self.DEBUG:
            print 'event: %s, src: %s, dst: %s' % (e.event, e.src, e.dst)

        self._statement.stop = e.args[1]

        if e.dst == "error_state":
            self._error_occoured = True
        elif e.src in ['trigger_state',
                        'action_state',
                        'target_state',
                        'message_state',
                        'delay_state']:
            block = self._block_stack[-1]
            if isinstance(block, Block):
                self._append_statement(block)

            if self.stop_callback:
                self.stop_callback(self._block_stack[0])

            self._reset_element()

    def onfound_nexts_flag(self, e):
        if self.DEBUG:
            print 'event: %s, src: %s, dst: %s' % (e.event, e.src, e.dst)

        self._statement.nexts = e.args[1]
        if e.dst == "trigger_state":
            block = self._block_stack[-1]
            self._append_statement(block)

        if e.dst == "error_state":
            self._error_occoured = True

    def onfound_if(self, e):
        if self.DEBUG:
            print 'event: %s, src: %s, dst: %s' % (e.event, e.src, e.dst)
        self._statement.ifs = e.args[1]

        if e.dst == "error_state":
            self._error_occoured = True

        block = self._block_stack[-1]
        if isinstance(block, Block):
            ifs = IfStatement()
            block.statements.append(ifs)
            self._block_stack.append(ifs)
            self._block_stack.append(ifs.if_block)
        # elif isinstance(block, IfStatement):
        #     print 'event: %s, src: %s, dst: %s' % (e.event, e.src, e.dst)
        #     print "if statement can't be nasted."

    def onfound_then(self, e):
        if self.DEBUG:
            print 'event: %s, src: %s, dst: %s' % (e.event, e.src, e.dst)
        self._statement.thens = e.args[1]

        if e.dst == "error_state":
            self._error_occoured = True

        block = self._block_stack.pop()
        ifs = self._block_stack[-1]
        if isinstance(block, Block) and isinstance(ifs, IfStatement):
            self._append_statement(block)
            self._block_stack.append(ifs.then_block)
        else:
            print "single else error."

    def onfound_else(self, e):
        if self.DEBUG:
            print 'event: %s, src: %s, dst: %s' % (e.event, e.src, e.dst)
        self._statement.elses = e.args[1]

        if e.dst == "error_state":
            self._error_occoured = True

        block = self._block_stack.pop()
        ifs = self._block_stack[-1]
        if isinstance(block, Block) and isinstance(ifs, IfStatement):
            self._append_statement(block)
            self._block_stack.append(ifs.else_block)
        else:
            print "single else error."

    def onreset(self, e):
        if self.DEBUG:
            print 'reset ! = event: %s, src: %s, dst: %s' \
                    % (e.event, e.src, e.dst)

        if e.dst == "error_state":
            self._error_occoured = True

    def onerror_state(self, e):
        if self.DEBUG:
            print 'onerror_state event: %s, src: %s, dst: %s' \
                    % (e.event, e.src, e.dst)

        if self.DEBUG:
            print "error occoured."

    def ontrigger_state(self, e):
        if self.DEBUG:
            print 'ontrigger_state event: %s, src: %s, dst: %s' \
                    % (e.event, e.src, e.dst)

    def oninitial_state(self, e):
        if self.DEBUG:
            print 'oninitial_state event: %s, src: %s, dst: %s' \
                    % (e.event, e.src, e.dst)

    def _append_statement(self, block):
        self._statement.delay_time = self._delay_buf
        self._statement.msg = self._message_buf
        block.statements.append(self._statement)
        self._statement = Statement()

    _FSM = Fysom({
        'initial': 'initial_state',
        #'final': 'initial_state',
        'events': [
                    {'name': 'found_if', 'src': 'initial_state',  'dst': 'initial_state'},
                    {'name': 'found_then', 'src': 'initial_state',  'dst': 'initial_state'},
                    {'name': 'found_else', 'src': 'initial_state',  'dst': 'initial_state'},
                    {'name': 'found_delay', 'src': 'initial_state',  'dst': 'initial_state'},
                    {'name': 'found_trigger', 'src': 'initial_state',  'dst': 'trigger_state'},
                    {'name': 'found_action', 'src': 'initial_state',  'dst': 'initial_state'},
                    {'name': 'found_target', 'src': 'initial_state',  'dst': 'initial_state'},
                    {'name': 'found_others', 'src': 'initial_state',  'dst': 'initial_state'},
                    {'name': 'found_stop_flag', 'src': 'initial_state',  'dst': 'initial_state'},
                    {'name': 'found_finish_flag', 'src': 'initial_state',  'dst': 'initial_state'},
                    {'name': 'found_nexts_flag', 'src': 'initial_state',  'dst': 'initial_state'},

                    {'name': 'found_if', 'src': 'delay_state',  'dst': 'error_state'},
                    {'name': 'found_then', 'src': 'delay_state',  'dst': 'error_state'},
                    {'name': 'found_else', 'src': 'delay_state',  'dst': 'error_state'},
                    {'name': 'found_delay', 'src': 'delay_state',  'dst': 'error_state'},
                    {'name': 'found_trigger', 'src': 'delay_state',  'dst': 'error_state'},
                    {'name': 'found_action', 'src': 'delay_state',  'dst': 'action_state'},
                    {'name': 'found_target', 'src': 'delay_state',  'dst': 'error_state'},
                    {'name': 'found_others', 'src': 'delay_state',  'dst': 'delay_state'},
                    {'name': 'found_finish_flag', 'src': 'delay_state',  'dst': 'error_state'},
                    {'name': 'found_nexts_flag', 'src': 'delay_state',  'dst': 'error_state'},

                    {'name': 'found_if', 'src': 'if_state',  'dst': 'error_state'},
                    {'name': 'found_then', 'src': 'if_state',  'dst': 'error_state'},
                    {'name': 'found_else', 'src': 'if_state',  'dst': 'error_state'},
                    {'name': 'found_delay', 'src': 'if_state',  'dst': 'delay_state'},
                    {'name': 'found_trigger', 'src': 'if_state',  'dst': 'error_state'},
                    {'name': 'found_action', 'src': 'if_state',  'dst': 'action_state'},
                    {'name': 'found_target', 'src': 'if_state',  'dst': 'error_state'},
                    {'name': 'found_others', 'src': 'if_state',  'dst': 'error_state'},
                    {'name': 'found_finish_flag', 'src': 'if_state',  'dst': 'error_state'},
                    {'name': 'found_nexts_flag', 'src': 'if_state',  'dst': 'error_state'},

                    {'name': 'found_if', 'src': 'trigger_state',  'dst': 'if_state'},
                    {'name': 'found_then', 'src': 'trigger_state',  'dst': 'error_state'},
                    {'name': 'found_else', 'src': 'trigger_state',  'dst': 'error_state'},
                    {'name': 'found_delay', 'src': 'trigger_state',  'dst': 'delay_state'},
                    {'name': 'found_trigger', 'src': 'trigger_state',  'dst': 'trigger_state'},
                    {'name': 'found_action', 'src': 'trigger_state',  'dst': 'action_state'},
                    {'name': 'found_target', 'src': 'trigger_state',  'dst': 'error_state'},
                    {'name': 'found_others', 'src': 'trigger_state',  'dst': 'error_state'},
                    {'name': 'found_finish_flag', 'src': 'trigger_state',  'dst': 'initial_state'},
                    {'name': 'found_nexts_flag', 'src': 'trigger_state',  'dst': 'error_state'},

                    {'name': 'found_delay', 'src': 'action_state',  'dst': 'message_state'},
                    {'name': 'found_trigger', 'src': 'action_state',  'dst': 'message_state'},
                    {'name': 'found_action', 'src': 'action_state',  'dst': 'message_state'},
                    {'name': 'found_target', 'src': 'action_state',  'dst': 'target_state'},
                    {'name': 'found_others', 'src': 'action_state',  'dst': 'message_state'},

                    {'name': 'found_delay', 'src': 'target_state',  'dst': 'message_state'},
                    {'name': 'found_trigger', 'src': 'target_state',  'dst': 'message_state'},
                    {'name': 'found_action', 'src': 'target_state',  'dst': 'message_state'},
                    {'name': 'found_target', 'src': 'target_state',  'dst': 'message_state'},
                    {'name': 'found_others', 'src': 'target_state',  'dst': 'message_state'},

                    {'name': 'found_delay', 'src': 'message_state',  'dst': 'message_state'},
                    {'name': 'found_trigger', 'src': 'message_state',  'dst': 'message_state'},
                    {'name': 'found_action', 'src': 'message_state',  'dst': 'message_state'},
                    {'name': 'found_target', 'src': 'message_state',  'dst': 'message_state'},
                    {'name': 'found_others', 'src': 'message_state',  'dst': 'message_state'},

                    {'name': 'reset', 'src': ['error_state', 'initial_state'],  'dst': 'initial_state'},
                    {'name': 'found_stop_flag',
                        'src': ['trigger_state', 'action_state', 'target_state', 'message_state', 'delay_state', 'if_state'], 
                        'dst': 'initial_state'},
                    {'name': 'found_finish_flag', 
                        'src': ['action_state', 'target_state', 'message_state'], 
                        'dst': 'initial_state'},
                    {'name': 'found_nexts_flag', 
                        'src': ['action_state', 'target_state', 'message_state'], 
                        'dst': 'trigger_state'},
                    {'name': 'found_if', 
                        'src': ['action_state', 'target_state', 'message_state'], 
                        'dst': 'message_state'},
                    {'name': 'found_then', 
                        'src': ['action_state', 'target_state', 'message_state'], 
                        'dst': 'trigger_state'},
                    {'name': 'found_else', 
                        'src': ['action_state', 'target_state', 'message_state'], 
                        'dst': 'trigger_state'},
                    ],
        }
        )

    def __init__(self, coms):
        self.FLAG = []

        flags = ['ifs', 'thens', 'elses', 'delay', 'trigger', 'stop', 'finish',
                'action', 'target', 'nexts']
        for flag in flags:
            if flag in coms.keys():
                self.FLAG.append((flag, coms[flag]))

        self.DEBUG = False

        self._FSM.onfound_delay = self.onfound_delay
        self._FSM.onfound_trigger = self.onfound_trigger
        self._FSM.onfound_others = self.onfound_others
        self._FSM.onfound_action = self.onfound_action
        self._FSM.onfound_target = self.onfound_target
        self._FSM.onfound_finish_flag = self.onfound_finish_flag
        self._FSM.onfound_stop_flag = self.onfound_stop_flag
        self._FSM.onfound_nexts_flag = self.onfound_nexts_flag
        self._FSM.onfound_if = self.onfound_if
        self._FSM.onfound_then = self.onfound_then
        self._FSM.onfound_else = self.onfound_else
        self._FSM.onreset = self.onreset

        self._FSM.ontrigger_state = self.ontrigger_state
        self._FSM.oninitial_state = self.oninitial_state
        self._FSM.onerror_state = self.onerror_state

        self._token_buf = []
        self._match_stack = []

        self.finish_callback = None
        self.stop_callback = None

    def _reset(self):
        self._reset_element()
        self._FSM.current = "initial_state"
        del self._token_buf[:]
        del self._match_stack[:]

    def _parse_token(self, word):
        # word = word.encode("utf-8")
        # print word, type(word)
        self._token_buf.append(word)
        _temp_str = "".join(self._token_buf)
        _no_match = True
        _index = 1
        for token_tuple in self.FLAG: 
            _found_match_in_token_flag_array = False # a flag that indicate if all mis-match or not
            _token_type = (_index, token_tuple[0]) #item in heap is tuple (index, item)

            for match_str in token_tuple[1]:
                if match_str.startswith(_temp_str):
                    _found_match_in_token_flag_array = True #found match
                    _no_match = False #for no match in each match token
                    if _token_type not in self._match_stack:
                        heappush(self._match_stack, _token_type) # use heap
                        
                    if len(match_str) == len(_temp_str):
                        # if current match type is on top of heap, that means it has the
                        # highest priority. now it totally match the buf, so we get the 
                        # token type
                        if self._match_stack[0] == _token_type: 
                            del self._match_stack[:]
                            del self._token_buf[:]
                            return _temp_str, _token_type[1] #that we found the final type

                    # we found the current buf's token type, so we clean the scene
                    break

                # in case that token has shorter token length then the buf
                elif _temp_str.startswith(match_str):
                    _found_match_in_token_flag_array = True
                    _no_match = False
                    if _token_type not in self._match_stack:
                        heappush(self._match_stack, _token_type)

                    # in case that lower token has short lengh, and it match
                    if self._match_stack[0] == _token_type:
                        del self._match_stack[:]
                        del self._token_buf[0:len(match_str)] #r
                        return _temp_str, _token_type[1]
                    break

            #buf will never match the current token type, so we pop it
            if not _found_match_in_token_flag_array and _token_type in self._match_stack:
                self._match_stack.remove(_token_type)
                heapify(self._match_stack)

            _index += 1

        if _no_match:
            return self._token_buf.pop(0), "others"

        return None, None
                
    def put_into_parse_stream(self, stream_term):

        # if self.DEBUG :
        #     print "parse: %s" %(stream_term)

        for item in list(stream_term):
            _token, _token_type = self._parse_token(item)
            if _token == None:
                #print "continue"
                continue
            if _token_type == "ifs":
                self._FSM.found_if(self, _token)
                self._message_buf = ''
                self._delay_buf = ''
            elif _token_type == "thens":
                self._FSM.found_then(self, _token)
                self._message_buf = ''
                self._delay_buf = ''
            elif _token_type == "elses":
                self._FSM.found_else(self, _token)
                self._message_buf = ''
                self._delay_buf = ''
            elif _token_type == "delay":
                self._FSM.found_delay(self, _token)
            elif _token_type == "trigger":
                self._FSM.found_trigger(self, _token)
            elif _token_type == "action":
                self._FSM.found_action(self, _token)
            elif _token_type == "target":
                self._FSM.found_target(self, _token)
            elif _token_type == "stop":
                self._FSM.found_stop_flag(self, _token)

                self._message_buf = ''
                self._delay_buf = ''
            elif _token_type == "finish":
                self._FSM.found_finish_flag(self, _token)

                self._message_buf = ''
                self._delay_buf = ''
            elif _token_type == "nexts":
                self._FSM.found_nexts_flag(self, _token)

                self._message_buf = ''
                self._delay_buf = ''
            elif _token_type == "others":
                self._FSM.found_others(self, _token)
                if self._FSM.current == 'delay_state':  # put it into buf here
                    self._delay_buf += _token

            if self._FSM.current == 'message_state':
                self._message_buf += _token

            if self._error_occoured:
                self._FSM.reset()
                self._reset_element()
                self._error_occoured = False
            # print self._FSM.current

    def _reset_element(self):
        self._statement = Statement()
        self._block_stack = [Block()]

    def reset(self):
        self._reset()

if __name__ == '__main__':
    import sys

    def test_callback(block, index=1):
        for statement in block.statements:
            for attr in vars(statement):
                sys.stdout.write("-"*index)
                block = getattr(statement, attr)
                print "obj.%s = %s" % (attr, block)
                if isinstance(block, Block):
                    test_callback(block, index + 1)

    def stop_callback(block, index=1):
        for statement in block.statements:
            for attr in vars(statement):
                sys.stdout.write("-"*index)
                block = getattr(statement, attr)
                print "obj.%s = %s" % (attr, block)
                if isinstance(block, Block):
                    test_callback(block, index + 1)

    fsm = LE_Command_Parser({
            "ifs":["如果"],
            "thens":["那么"],
            "elses":["否则"],
            "delay":["定时"],
            "trigger":["启动"],
            "action":["开", "关"],
            "target":["灯", "门"],
            "stop":["停止"],
            "finish":["结束"],
            "nexts":["然后", "接着"],
            })
    fsm.DEBUG = True
    fsm.finish_callback = test_callback
    fsm.stop_callback = stop_callback
    #TODO - "不要停&停止"
    parser_target = "启动如果开门7那么开灯8否则关门9结束"
    fsm.put_into_parse_stream(parser_target)

