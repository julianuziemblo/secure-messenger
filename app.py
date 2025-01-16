from app_logic import AppLogic
from tui import Tui
from threading import Thread


class App:
    def __init__(self):
        self.tui = Tui(self)
        self.app_logic = AppLogic(self)

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


def main():
    App().run()


if __name__ == '__main__':
    main()
