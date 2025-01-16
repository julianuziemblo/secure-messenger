from tui import Tui
from threading import Thread


def main():
    tui = Tui.new()
    logic = ... # TODO: app logic thread

    tui_thread = Thread(target=tui.run, name='tui_thread', args=(logic))
    tui_thread.run()

    tui_thread.join()


if __name__ == '__main__':
    main()
