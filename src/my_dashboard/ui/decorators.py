"""Reusable UI decorators for button state and progressbar management."""

from __future__ import annotations

import tkinter as tk
from functools import wraps
from inspect import iscoroutinefunction
from tkinter import DISABLED, NORMAL
from typing import Optional

import ttkbootstrap as ttk


def _resolve_button(instance: tk.Tk, button_name: str) -> Optional[ttk.Button]:
    sidebar = getattr(instance, "sidebar", None)
    if sidebar and hasattr(sidebar, button_name):
        return getattr(sidebar, button_name)
    return getattr(instance, button_name, None)


def with_progressbar(func):
    """Decorator to automatically start/stop the window progressbar."""

    if iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(self, *args, **kwargs):
            progressbar: Optional[ttk.Progressbar] = getattr(self, "progressbar", None)
            if progressbar:
                progressbar.start()
            try:
                return await func(self, *args, **kwargs)
            finally:
                if progressbar:
                    progressbar.stop()

        return async_wrapper

    @wraps(func)
    def sync_wrapper(self, *args, **kwargs):
        progressbar: Optional[ttk.Progressbar] = getattr(self, "progressbar", None)
        if progressbar:
            progressbar.start()
        try:
            return func(self, *args, **kwargs)
        finally:
            if progressbar:
                progressbar.stop()

    return sync_wrapper


def with_button_state(button_name: str):
    """Decorator to disable/enable a button while a handler runs."""

    def decorator(func):
        if iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(self, *args, **kwargs):
                button = _resolve_button(self, button_name)
                if button:
                    button.configure(state=DISABLED)
                try:
                    return await func(self, *args, **kwargs)
                finally:
                    if button:
                        button.configure(state=NORMAL)

            return async_wrapper

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            button = _resolve_button(self, button_name)
            if button:
                button.configure(state=DISABLED)
            try:
                return func(self, *args, **kwargs)
            finally:
                if button:
                    button.configure(state=NORMAL)

        return sync_wrapper

    return decorator
