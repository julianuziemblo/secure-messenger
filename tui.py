from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, Any
import readline


class Tui:
    def __init__(self, control: Any):
        self.ctx = TuiContext(control)
        self.running = False

    def run(self):
        readline.set_auto_history(False)
        readline.clear_history() # TODO: Clear the history and replace it with the self.ctx.cmd_history on mode switch!
        self.running = True
        # TODO: print WELCOME message
        while self.running:
            user_input = input(self.ctx.prompt)
            self.exec_command(user_input)

    def stop(self):
        self.running = False

    def exec_command(self, user_input: str):
        if not user_input.startswith('/'):
            return
        
        tokens = user_input.split(' ')

        self.ctx.add_to_cmd_history(user_input)
        
        if len(tokens) == 0:
            return
        if len(tokens) > 2:
            print('Too many arguments!')
            return
        
        cmd_str = tokens[0]

        if len(tokens) < 2:
            optional_arg = ''
        else:
            optional_arg = tokens[1]

        for tui_command in TuiCommand.available_commands(self.ctx):
            if cmd_str == '/' + tui_command.name:
                if len(tokens) < tui_command.n_args:
                    print(f'Too few arguments ({len(tokens)}) for `{tui_command.name}` command (needed: {tui_command.n_args})')
                    return
                if len(tokens) < tui_command.n_args:
                    print(f'Too many arguments ({len(tokens)}) for `{tui_command.name}` command (needed: {tui_command.n_args})')
                    return
                
                tui_command.execute(self.ctx, optional_arg)
                return
            
        for unavail_cmd in set(TuiCommand.all_commands()).difference(TuiCommand.available_commands(self.ctx)):
            if cmd_str == '/' + unavail_cmd.name:
                print(f'`{unavail_cmd.name}` is not available in this mode!')
                return
        
        print(f'unknown command: `{cmd_str}`')


class TuiMode(Enum):
    Idle = 0
    Conversation = 1


class TuiContext:
    mode: TuiMode = TuiMode.Idle
    prompt: str = '(secure_messenger) ' # TODO: change prompt in conversation mode
    cmd_history: dict[TuiMode, list[str]] = {
        TuiMode.Idle: [],
        TuiMode.Conversation: []
    }
    # last_conversation: Optional[] # TODO: Optional[Conversation!]

    def __init__(self, control: Any):
        self.control = control

    def add_to_cmd_history(self, cmd: str):
        self.cmd_history[self.mode].append(cmd)
        readline.add_history(cmd)

@dataclass
class TuiCommand:
    name: str
    description: str
    modes: set[TuiMode]
    n_args: int
    execute: Callable[[TuiContext, str], None]

    @staticmethod
    def available_commands(ctx: TuiContext):
        return tuple(filter(lambda cmd: ctx.mode in cmd.modes, TuiCommand.all_commands()))

    @staticmethod
    def all_commands():
        return (
            TuiCommand(
                'help', 
                'display this `help` message', 
                {TuiMode.Idle, TuiMode.Conversation},
                1,
                lambda ctx, _: print('\n'.join([f'\t/{cmd.name} - {cmd.description}' for cmd in TuiCommand.available_commands(ctx)]))
            ),
            TuiCommand(
                'join',
                'join a conversation using a known username or IPv4 address',
                {TuiMode.Idle},
                2,
                lambda ctx, user: print('TODO: join a conversation!'),
            ),
            TuiCommand(
                'accept',
                'accept an invitation from another user',
                {TuiMode.Idle},
                2,
                lambda ctx, user: print('TODO: accept a conversation invite!'),
            ),
            TuiCommand(
                'list',
                'idle: display known users with theis IPs; conversation: display users in this conversation',
                {TuiMode.Idle, TuiMode.Conversation},
                1,
                TuiCommand._command_list,
            ),
            TuiCommand(
                'msg',
                'send message in this conversation',
                {TuiMode.Conversation},
                1,
                lambda ctx, _: print('TODO: send message in this conversation!')
            ),
            TuiCommand(
                'whisper',
                'send message directly to a user',
                {TuiMode.Conversation},
                2,
                lambda ctx, user: print('TODO: send message directly to a user!')
            ),
            TuiCommand(
                'exit',
                'idle: exit the app; conversation: exit the conversation',
                {TuiMode.Idle, TuiMode.Conversation},
                1,
                TuiCommand._command_exit
            ),
            TuiCommand(
                'reconnect',
                'reconnect to the last conversation you exited in this app session',
                {TuiMode.Idle},
                1,
                lambda ctx, _: print('TODO: reconnect to the last conversation!')
            ),
            TuiCommand(
                'regenerate-keys',
                're-generate the openssl keys used to encrypt the conversation',
                {TuiMode.Idle},
                1,
                lambda ctx, _: print('TODO: regenerate the openssl keys!')
            )
        )
    
    @staticmethod
    def _command_list(ctx: TuiContext, _: str):
        match ctx.mode:
            case TuiMode.Idle: print('TODO: display known users with theis IPs!')
            case TuiMode.Conversation: print('TODO: display users in this conversation!')

    @staticmethod
    def _command_exit(ctx: TuiContext, _: str):
        match ctx.mode:
            case TuiMode.Idle: 
                if input('Are you sure you want to exit the app? All your session data will be lost! (yes/no/<enter>) ') in {'', 'y', 'Y', 'yes', 'YES', 'Yes'}:
                    ctx.control.stop()
                    exit(0) # TODO: (maybe) cleanup resources
            case TuiMode.Conversation: print('TODO: exit the conversation!')

    def __key(self):
        return (self.name, self.description)

    def __hash__(self):
        return hash(self.__key())


if __name__ == '__main__':
    def main():
        tui = Tui(None)
        tui.run()

    main()

