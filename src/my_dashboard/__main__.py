"""Run the dashboard application via ``python -m my_dashboard``."""

from async_tkinter_loop import async_mainloop

from . import App



def main() -> None:
        app = App()
        async_mainloop(app)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
