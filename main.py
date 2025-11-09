from async_tkinter_loop import async_mainloop

import bootstrap  # noqa: F401

from my_dashboard import App


if __name__ == "__main__":
    app = App()
    async_mainloop(app)
