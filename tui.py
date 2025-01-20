from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, Any
import readline
from alp import Packet, PayloadType
import os
import socket


class Tui:
    def __init__(self, control: Any, username: str, port=None):
        self.ctx = TuiContext(control, username, port)
        self.running = False

    def run(self):
        readline.set_auto_history(False)
        readline.clear_history()
        self.running = True
        print(f'Welcome, {self.ctx.username}!\nType /help to see available commands')
        print(f'Interfaces:')
        local_hostname = socket.gethostname()
        ip_addresses = socket.gethostbyname_ex(local_hostname)[2]
        print(ip_addresses)
        while self.running:
            user_input = input(self.ctx.prompt)
            self.exec_command(user_input)

    def stop(self):
        self.running = False

    def change_mode(self, mode):
        self.ctx.change_mode(mode)

    def exec_command(self, user_input: str):
        if not user_input.startswith('/'):
            return
        
        tokens = user_input.split(' ')

        self.ctx.add_to_cmd_history(user_input)
        
        if len(tokens) == 0:
            return
        
        cmd_str = tokens[0].lstrip('/')
        tui_command = TuiCommand.from_name(cmd_str)
        if not tui_command:
            print(f'Unknown command `{cmd_str}`')
            return

        if tui_command.name not in set([cmd.name for cmd in TuiCommand.available_commands(self.ctx)]):
            print(f'Command `{cmd_str}` is not available in this mode!')
            print(f'Available commands:')
            TuiCommand.all_commands()['help'].execute(self.ctx)
            return
        
        match tui_command.n_args:
            case 1: tui_command.execute(self.ctx)
            case 2: 
                if tui_command.name == 'msg':
                    tui_command.execute(self.ctx, ' '.join(tokens[1::]))
                else:
                    if not self._guard(tui_command, tokens):
                        return
                    tui_command.execute(self.ctx, tokens[1])
            case 3:
                try:
                    tui_command.execute(self.ctx, tokens[1], ' '.join(tokens[2::]))
                except Exception as e:
                    print(f'Couldn\'t whisper to {tokens[1]}: {e}')
            case n: print(f'Internal error: unreachable statement reached with n_args={n} (???)')

    def _guard(self, cmd, tokens):
        if len(tokens) != cmd.n_args:
            print(f'Too {"few" if len(tokens) < cmd.n_args else "many"} arguments ({len(tokens)}) for `{cmd.name}` command (needed: {cmd.n_args})')
            return False
        return True


class TuiMode(Enum):
    Idle = 0
    Conversation = 1


class TuiContext:
    mode: TuiMode = TuiMode.Idle
    prompt: str = '(secure_messenger) '
    cmd_history: dict[TuiMode, list[str]] = {
        TuiMode.Idle: [],
        TuiMode.Conversation: []
    }

    def __init__(self, control: Any, username: str, port=None):
        self.control = control
        self.username = username
        self.port = port

    def add_to_cmd_history(self, cmd: str):
        self.cmd_history[self.mode].append(cmd)
        readline.add_history(cmd)

    def change_mode(self, mode: TuiMode):
        readline.clear_history()
        for elem in self.cmd_history[mode]:
            readline.add_history(elem)
        self.mode = mode
        match mode:
            case TuiMode.Idle: self.prompt = '(secure_messenger) '
            case TuiMode.Conversation: self.prompt = '> '
    

@dataclass
class TuiCommand:
    name: str
    description: str
    modes: set[TuiMode]
    n_args: int
    execute: Callable

    @staticmethod
    def available_commands(ctx: TuiContext):
        return set(filter(lambda cmd: ctx.mode in cmd.modes, TuiCommand.all_commands().values()))

    @staticmethod
    def all_commands():
        return {
            'join': TuiCommand(
                'join',
                'join a conversation using a known username or IPv4 address',
                {TuiMode.Idle},
                2,
                TuiCommand._join,
            ),
            'accept': TuiCommand(
                'accept',
                'accept an invitation from another user',
                {TuiMode.Idle, TuiMode.Conversation},
                2,
                TuiCommand._command_accept
            ),
            'list': TuiCommand(
                'list',
                'idle: display known users with theis IPs; conversation: display users in this conversation',
                {TuiMode.Idle, TuiMode.Conversation},
                1,
                TuiCommand._command_list,
            ),
            'msg': TuiCommand(
                'msg',
                'send message in this conversation',
                {TuiMode.Conversation},
                2,
                lambda ctx, msg: ctx.control.sendall(
                    Packet.new(
                        ctx.username,
                        PayloadType.MSG,
                        msg,
                    )
                )
            ),
            'whisper': TuiCommand(
                'whisper',
                'send message directly to a user',
                {TuiMode.Conversation},
                3,
                lambda ctx, user, msg: ctx.control.send(
                    Packet.new(
                        ctx.username,
                        PayloadType.WHISPER,
                        msg,
                    ),
                    ctx.control.find_by_username(user)
                )
            ),
            'exit': TuiCommand(
                'exit',
                'idle: exit the app; conversation: exit the conversation',
                {TuiMode.Idle, TuiMode.Conversation},
                1,
                TuiCommand._command_exit
            ),
            # 'reconnect': TuiCommand(
            #     'reconnect',
            #     'reconnect to the last conversation you exited in this app session',
            #     {TuiMode.Idle},
            #     1,
            #     lambda ctx: print('TODO: reconnect to the last conversation!')
            # ),
            # 'regenerate-keys': TuiCommand(
            #     'regenerate-keys',
            #     're-generate the openssl keys used to encrypt the conversation',
            #     {TuiMode.Idle},
            #     1,
            #     lambda ctx: print('TODO: regenerate the openssl keys!')
            # ),
            'help': TuiCommand(
                'help', 
                'display this `help` message', 
                {TuiMode.Idle, TuiMode.Conversation},
                1,
                lambda ctx: print('\n'.join([f'\t/{cmd.name} - {cmd.description}' for cmd in TuiCommand.available_commands(ctx)]))
            )
        }
    
    @staticmethod
    def _command_accept(ctx: TuiContext, user):
        users = ctx.control.users_list()
        mapping = {}
        for u in users:
            if u.name == user:
                continue
            elif u.name == ctx.username:
                continue
            name = u.name
            ip = u.addr[0]
            if u.addr[1] != 2137:
                port = f':{u.addr[1]}'
            else:
                port = ''
            mapping[name] = f'{ip}{port}'
        ctx.control.send(
            Packet.new(
                ctx.username,
                PayloadType.ACCEPT,
                mapping,
                port=ctx.port
            ), 
            ctx.control.find_by_username(user)
        )
        ctx.change_mode(TuiMode.Conversation)
    
    @staticmethod
    def _command_list(ctx: TuiContext):
        print('Users:')
        for u in ctx.control.users_list():
            print(f'{u}')

    @staticmethod
    def _join(ctx: TuiContext, addr: str):
        if ':' in addr:
            spl = addr.split(':')
            ip, port = spl[0], int(spl[1])
        else:
            ip, port = addr, 2137
        print(f'Joining {ip}:{port}...')
        ctx.control.join(ip, port)

    @staticmethod
    def _command_exit(ctx: TuiContext):
        match ctx.mode:
            case TuiMode.Idle: 
                if input('Are you sure you want to exit the app? All your session data will be lost! (yes/no/<enter>) ') in {'', 'y', 'Y', 'yes', 'YES', 'Yes'}:
                    ctx.control.stop()
                    exit(0)
            case TuiMode.Conversation: 
                ctx.change_mode(TuiMode.Idle)
                ctx.control.exit_conversation()

    def __key(self):
        return (self.name, self.description)

    def __hash__(self):
        return hash(self.__key())
    
    @staticmethod
    def from_name(name: str):
        return TuiCommand.all_commands().get(name, None)


if __name__ == '__main__':
    def main():
        tui = Tui(None)
        tui.run()

    main()

