from app_logic import AppLogic
from tui import Tui
from threading import Thread
import sys


class App:
    def __init__(self, username: str, port=2137):
        self.tui = Tui(self, username)
        self.app_logic = AppLogic(self, username, port=port)

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


def main():
    if len(sys.argv) not in {2, 3}:
        print('Usage: python3 app.py <username> [<port>]')
        sys.exit(0)
    username = sys.argv[1]
    if len(sys.argv) == 3:
        App(username, port=int(sys.argv[2])).run()
    else:
        App(username).run()


if __name__ == '__main__':
    main()
