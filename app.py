from app_logic import AppLogic
from tui import Tui
from threading import Thread
import argparse
import os
import sys


class App:
    def __init__(self, username: str, port: int = 2137, passwd=None, public: str = None, private: str = None, delete_keys: bool = True):
        self.tui = Tui(self, username)
        self.app_logic = AppLogic(self, username, port=port, passwd=passwd, public=public, private=private, delete_keys=delete_keys)

    def run(self):
        self.tui_thread = Thread(target=self.tui.run, name='tui_thread')
        self.app_logic_thread = Thread(target=self.app_logic.run, name='app_logic_thread')
        
        self.tui_thread.start()
        self.app_logic_thread.start()

        self.tui_thread.join()
        self.app_logic_thread.join()

    def stop(self):
        self.tui.stop()
        self.app_logic.stop()
    
    def send(self, *args):
        self.app_logic.send(*args)

    def sendall(self, *args):
        self.app_logic.sendall(*args)

    def find_by_username(self, *args):
        return self.app_logic.find_by_username(*args)

    def users_list(self):
        return self.app_logic.server.users
    
    def join(self, *args, **kwargs):
        self.app_logic.join(*args, **kwargs)

    def change_mode(self, *args):
        self.tui.change_mode(*args)
    
    def exit_conversation(self):
        self.app_logic.exit_conversation()


def main():
    parser = argparse.ArgumentParser(
        prog='secure_messenger',
        description='A secure P2P chat with end-to-end encryption.'
    )

    def find_keys(path):
        spl = path.split(',')
        if not len(spl) == 2:
            raise argparse.ArgumentTypeError(f'\'{path}\' should be formatted like: <public_key_path>,<private_key_path>')
        public = spl[0]
        private = spl[1]
        
        if not os.path.isfile(public):
            raise argparse.ArgumentTypeError(f'\'{path}\' is not a cert file!')
        if not os.path.isfile(private):
            raise argparse.ArgumentTypeError(f'\'{path}\' is not a key file!')
        
        return (public, private)

    parser.add_argument('-k', '--keys', type=find_keys, help='Optional path to the public and private keys, separated by comma, e.g.: \'--keys /path/to/public.pem,/path/to/private.key\'')
    parser.add_argument('-u', '--username', required=True, type=str, help='Your username that will be used in communication.')
    parser.add_argument('-P', '--password', required='--keys' not in sys.argv and '-k' not in sys.argv, help='Passphrase for generating public-private key pair.')
    parser.add_argument('-p', '--port', type=int, default=2137, help='Optional TCP port for the main socket. The default is 2137.')
    parser.add_argument('--delete-keys', type=bool, default='--keys' not in sys.argv and '-k' not in sys.argv, help='If the keys used for communication encryption should be deleted, True on default.')
    args = parser.parse_args()

    username = args.username
    port = args.port

    if not args.keys:
        public = None
        private = None
    else:
        public = args.keys[0]
        private = args.keys[1]
    App(username, port=port, passwd=args.password, public=public, private=private, delete_keys=args.delete_keys).run()


if __name__ == '__main__':
    main()
