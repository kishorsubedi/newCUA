# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# ...

import logging
import termcolor
import time
import os
import sys
from ..computer import Computer, EnvState
from playwright.async_api import async_playwright
from typing import Literal

# Mapping of user-friendly keys to Playwright key names
PLAYWRIGHT_KEY_MAP = {
    "backspace": "Backspace",
    "tab": "Tab",
    "return": "Enter",
    "enter": "Enter",
    "shift": "Shift",
    "control": "ControlOrMeta",
    "alt": "Alt",
    "escape": "Escape",
    "space": "Space",
    "pageup": "PageUp",
    "pagedown": "PageDown",
    "end": "End",
    "home": "Home",
    "left": "ArrowLeft",
    "up": "ArrowUp",
    "right": "ArrowRight",
    "down": "ArrowDown",
    "insert": "Insert",
    "delete": "Delete",
    "semicolon": ";",
    "equals": "=",
    "multiply": "Multiply",
    "add": "Add",
    "separator": "Separator",
    "subtract": "Subtract",
    "decimal": "Decimal",
    "divide": "Divide",
    "f1": "F1",
    "f2": "F2",
    "f3": "F3",
    "f4": "F4",
    "f5": "F5",
    "f6": "F6",
    "f7": "F7",
    "f8": "F8",
    "f9": "F9",
    "f10": "F10",
    "f11": "F11",
    "f12": "F12",
    "command": "Meta",
}


class PlaywrightComputer(Computer):
    """Async Playwright Computer for Browser Automation"""

    def __init__(
        self,
        screen_size: tuple[int, int],
        initial_url: str = "https://www.google.com",
        search_engine_url: str = "https://www.google.com",
        highlight_mouse: bool = False,
    ):
        self._initial_url = initial_url
        self._screen_size = screen_size
        self._search_engine_url = search_engine_url
        self._highlight_mouse = highlight_mouse
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    async def _handle_new_page(self, new_page):
        new_url = new_page.url
        await new_page.close()
        await self._page.goto(new_url)

    async def __aenter__(self):
        print("Creating async Playwright session...")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            args=[
                "--disable-extensions",
                "--disable-file-system",
                "--disable-plugins",
                "--disable-dev-shm-usage",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-sync",
            ],
            headless=True,
        )
        self._context = await self._browser.new_context(
            viewport={"width": self._screen_size[0], "height": self._screen_size[1]}
        )
        self._page = await self._context.new_page()
        await self._page.goto(self._initial_url)
        self._context.on("page", lambda page: self._handle_new_page(page))
        termcolor.cprint("Started async Playwright.", color="green", attrs=["bold"])
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def open_web_browser(self) -> EnvState:
        return await self.current_state()

    async def click_at(self, x: int, y: int):
        await self.highlight_mouse(x, y)
        await self._page.mouse.click(x, y)
        await self._page.wait_for_load_state()
        return await self.current_state()

    async def hover_at(self, x: int, y: int):
        await self.highlight_mouse(x, y)
        await self._page.mouse.move(x, y)
        await self._page.wait_for_load_state()
        return await self.current_state()

    async def type_text_at(
        self,
        x: int,
        y: int,
        text: str,
        press_enter: bool = False,
        clear_before_typing: bool = True,
    ) -> EnvState:
        await self.highlight_mouse(x, y)
        await self._page.mouse.click(x, y)
        await self._page.wait_for_load_state()

        if clear_before_typing:
            if sys.platform == "darwin":
                await self.key_combination(["Command", "A"])
            else:
                await self.key_combination(["Control", "A"])
            await self.key_combination(["Delete"])

        await self._page.keyboard.type(text)

        if press_enter:
            await self.key_combination(["Enter"])

        await self._page.wait_for_load_state()
        return await self.current_state()

    async def _horizontal_document_scroll(self, direction: Literal["left", "right"]) -> EnvState:
        horizontal_scroll_amount = self.screen_size()[0] // 2
        sign = "-" if direction == "left" else ""
        scroll_argument = f"{sign}{horizontal_scroll_amount}"
        await self._page.evaluate(f"window.scrollBy({scroll_argument}, 0);")
        await self._page.wait_for_load_state()
        return await self.current_state()

    async def scroll_document(self, direction: Literal["up", "down", "left", "right"]) -> EnvState:
        if direction == "down":
            return await self.key_combination(["PageDown"])
        elif direction == "up":
            return await self.key_combination(["PageUp"])
        elif direction in ("left", "right"):
            return await self._horizontal_document_scroll(direction)
        else:
            raise ValueError("Unsupported direction: ", direction)

    async def scroll_at(self, x: int, y: int, direction: Literal["up", "down", "left", "right"], magnitude: int = 800) -> EnvState:
        await self.highlight_mouse(x, y)
        await self._page.mouse.move(x, y)
        await self._page.wait_for_load_state()

        dx, dy = 0, 0
        if direction == "up":
            dy = -magnitude
        elif direction == "down":
            dy = magnitude
        elif direction == "left":
            dx = -magnitude
        elif direction == "right":
            dx = magnitude
        else:
            raise ValueError("Unsupported direction: ", direction)

        await self._page.mouse.wheel(dx, dy)
        await self._page.wait_for_load_state()
        return await self.current_state()

    async def wait_5_seconds(self) -> EnvState:
        await self._page.wait_for_timeout(5000)
        return await self.current_state()

    async def go_back(self) -> EnvState:
        await self._page.go_back()
        await self._page.wait_for_load_state()
        return await self.current_state()

    async def go_forward(self) -> EnvState:
        await self._page.go_forward()
        await self._page.wait_for_load_state()
        return await self.current_state()

    async def search(self) -> EnvState:
        return await self.navigate(self._search_engine_url)

    async def navigate(self, url: str) -> EnvState:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        await self._page.goto(url)
        await self._page.wait_for_load_state()
        return await self.current_state()

    async def key_combination(self, keys: list[str]) -> EnvState:
        keys = [PLAYWRIGHT_KEY_MAP.get(k.lower(), k) for k in keys]

        for key in keys[:-1]:
            await self._page.keyboard.down(key)
        await self._page.keyboard.press(keys[-1])
        for key in reversed(keys[:-1]):
            await self._page.keyboard.up(key)

        return await self.current_state()

    async def drag_and_drop(self, x: int, y: int, destination_x: int, destination_y: int) -> EnvState:
        await self.highlight_mouse(x, y)
        await self._page.mouse.move(x, y)
        await self._page.wait_for_load_state()
        await self._page.mouse.down()
        await self._page.wait_for_load_state()
        await self.highlight_mouse(destination_x, destination_y)
        await self._page.mouse.move(destination_x, destination_y)
        await self._page.wait_for_load_state()
        await self._page.mouse.up()
        return await self.current_state()

    async def current_state(self) -> EnvState:
        await self._page.wait_for_load_state()
        await self._page.wait_for_timeout(500)  # ensure page finished rendering
        screenshot_bytes = await self._page.screenshot(type="png", full_page=False)
        return EnvState(screenshot=screenshot_bytes, url=self._page.url)

    def screen_size(self) -> tuple[int, int]:
        viewport_size = self._page.viewport_size
        if viewport_size:
            return viewport_size["width"], viewport_size["height"]
        return self._screen_size

    async def highlight_mouse(self, x: int, y: int):
        if not self._highlight_mouse:
            return
        await self._page.evaluate(
            f"""
            () => {{
                const element_id = "playwright-feedback-circle";
                const div = document.createElement('div');
                div.id = element_id;
                div.style.pointerEvents = 'none';
                div.style.border = '4px solid red';
                div.style.borderRadius = '50%';
                div.style.width = '20px';
                div.style.height = '20px';
                div.style.position = 'fixed';
                div.style.zIndex = '9999';
                document.body.appendChild(div);
                div.hidden = false;
                div.style.left = {x}-10+'px';
                div.style.top = {y}-10+'px';
                setTimeout(() => {{ div.hidden = true; }}, 2000);
            }}
        """
        )
        await self._page.wait_for_timeout(1000)
