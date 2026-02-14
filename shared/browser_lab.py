import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union

try:
    from playwright.async_api import async_playwright, Error as PlaywrightError
except ImportError:
    async_playwright = None
    PlaywrightError = None

class BrowserLabManager:
    """
    Manages browser automation tasks using Playwright (Async).
    """
    def __init__(self):
        pass

    def _check_deps(self):
        if async_playwright is None:
            raise ImportError("Playwright is not installed. Please run 'pip install playwright' and 'playwright install'.")

    async def _run_browser(self, url: str, action: str, **kwargs) -> Any:
        self._check_deps()

        try:
            async with async_playwright() as p:
                # Launch arguments optimized for container environments
                launch_args = ["--no-sandbox", "--disable-setuid-sandbox"]
                browser = await p.chromium.launch(headless=True, args=launch_args)

                # Create context with user agent
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )

                page = await context.new_page()
                await page.goto(url)

                # Wait for load
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass

                result = None

                if action == "screenshot":
                    path = kwargs.get("path")
                    full_page = kwargs.get("full_page", True)
                    await page.screenshot(path=path, full_page=full_page)
                    result = str(path)

                elif action == "pdf":
                    path = kwargs.get("path")
                    await page.pdf(path=path)
                    result = str(path)

                elif action == "text":
                    result = await page.inner_text("body")

                elif action == "html":
                    result = await page.content()

                elif action == "evaluate":
                    script = kwargs.get("script")
                    result = await page.evaluate(script)

                elif action == "inspect":
                    result = {
                        "title": await page.title(),
                        "url": page.url,
                        "meta": []
                    }
                    metas = page.locator("meta").all()
                    for meta in metas:
                        name = await meta.get_attribute("name") or await meta.get_attribute("property")
                        content = await meta.get_attribute("content")
                        if name and content:
                            result["meta"].append({name: content})

                await browser.close()
                return result

        except Exception as e:
            raise RuntimeError(f"Browser error: {e}")

    async def screenshot(self, url: str, path: Union[str, Path], full_page: bool = True) -> str:
        return await self._run_browser(url, "screenshot", path=str(path), full_page=full_page)

    async def pdf(self, url: str, path: Union[str, Path]) -> str:
        return await self._run_browser(url, "pdf", path=str(path))

    async def get_text(self, url: str) -> str:
        return await self._run_browser(url, "text")

    async def get_html(self, url: str) -> str:
        return await self._run_browser(url, "html")

    async def evaluate(self, url: str, script: str) -> Any:
        return await self._run_browser(url, "evaluate", script=script)

    async def inspect(self, url: str) -> Dict[str, Any]:
        return await self._run_browser(url, "inspect")


async def run_browser_lab_logic(args):
    """
    CLI logic for Browser Lab.
    """
    manager = BrowserLabManager()

    try:
        if args.action == "screenshot":
            if not args.url or not args.output:
                print("Error: --url and --output are required.", file=sys.stderr)
                sys.exit(1)
            path = await manager.screenshot(args.url, args.output, full_page=not args.viewport)
            print(f"✅ Screenshot saved to {path}")

        elif args.action == "pdf":
            if not args.url or not args.output:
                print("Error: --url and --output are required.", file=sys.stderr)
                sys.exit(1)
            path = await manager.pdf(args.url, args.output)
            print(f"✅ PDF saved to {path}")

        elif args.action == "text":
            if not args.url:
                print("Error: --url is required.", file=sys.stderr)
                sys.exit(1)
            content = await manager.get_text(args.url)
            if args.output:
                Path(args.output).write_text(content, encoding="utf-8")
                print(f"✅ Text saved to {args.output}")
            else:
                print(content)

        elif args.action == "html":
            if not args.url:
                print("Error: --url is required.", file=sys.stderr)
                sys.exit(1)
            content = await manager.get_html(args.url)
            if args.output:
                Path(args.output).write_text(content, encoding="utf-8")
                print(f"✅ HTML saved to {args.output}")
            else:
                print(content)

        elif args.action == "evaluate":
            if not args.url or not args.script:
                print("Error: --url and --script are required.", file=sys.stderr)
                sys.exit(1)
            result = await manager.evaluate(args.url, args.script)
            print(result)

        elif args.action == "inspect":
            if not args.url:
                print("Error: --url is required.", file=sys.stderr)
                sys.exit(1)
            info = await manager.inspect(args.url)
            print(f"Title: {info['title']}")
            print(f"URL:   {info['url']}")
            if info['meta']:
                print("Meta Tags:")
                for m in info['meta']:
                    for k, v in m.items():
                        print(f"  {k}: {v}")

    except ImportError as e:
        print(f"❌ Dependency Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
