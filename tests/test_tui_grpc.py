import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from textual.app import App, ComposeResult
from textual import events
from shared.tui_grpc import GrpcLabTab

class GrpcLabTestApp(App):
    def compose(self) -> ComposeResult:
        yield GrpcLabTab()

class TestGrpcLabTab(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = GrpcLabTestApp()

    @patch('shared.tui_grpc.GrpcLabManager')
    async def test_initial_state(self, MockManager):
        # Setup mock
        mock_manager = MockManager.return_value

        async with self.app.run_test(size=(120, 40)) as pilot:
            tab = pilot.app.query_one(GrpcLabTab)
            self.assertIsNotNone(tab)

            # Check widgets exist
            self.assertIsNotNone(pilot.app.query_one("#grpc-host"))
            self.assertIsNotNone(pilot.app.query_one("#grpc-plaintext"))
            self.assertIsNotNone(pilot.app.query_one("#btn-grpc-list-services"))
            self.assertIsNotNone(pilot.app.query_one("#grpc-service-list"))
            self.assertIsNotNone(pilot.app.query_one("#grpc-method-list"))
            self.assertIsNotNone(pilot.app.query_one("#btn-grpc-call"))

    @patch('shared.tui_grpc.GrpcLabManager')
    async def test_list_services(self, MockManager):
        # Setup mock
        mock_manager = MockManager.return_value
        mock_manager.list_services = MagicMock(return_value=["service1", "service2"])

        async with self.app.run_test(size=(120, 40)) as pilot:
            # Set host
            host_input = pilot.app.query_one("#grpc-host")
            host_input.value = "localhost:50051"

            # Click list services
            await pilot.click("#btn-grpc-list-services")
            await pilot.pause()

            # Verify manager call
            mock_manager.list_services.assert_called_with("localhost:50051", True, "")

            # Verify list population
            list_view = pilot.app.query_one("#grpc-service-list")
            self.assertEqual(len(list_view.children), 2)
            # Textual ListView items are ListItems, containing Label
            # Note: We set name on ListItem
            self.assertEqual(list_view.children[0].name, "service1")
            self.assertEqual(list_view.children[1].name, "service2")

    @patch('shared.tui_grpc.GrpcLabManager')
    async def test_select_service_and_method(self, MockManager):
        # Setup mock
        mock_manager = MockManager.return_value
        mock_manager.list_services = MagicMock(return_value=["myservice"])
        mock_manager.list_methods = MagicMock(return_value=["mymethod"])
        mock_manager.describe = MagicMock(return_value="description of symbol")

        async with self.app.run_test(size=(120, 40)) as pilot:
            # Populate services manually or via interaction
            # Let's do via interaction to be thorough
            host_input = pilot.app.query_one("#grpc-host")
            host_input.value = "localhost:50051"
            await pilot.click("#btn-grpc-list-services")
            await pilot.pause()

            # Select service
            service_list = pilot.app.query_one("#grpc-service-list")
            service_list.focus()
            service_list.index = 0

            await pilot.press("enter")
            # Increase pause to allow async handler to run
            await pilot.pause(0.5)

            # Verify list_methods called
            mock_manager.list_methods.assert_called_with("localhost:50051", "myservice", True, "")
            mock_manager.describe.assert_called_with("localhost:50051", "myservice", True, "")

            # Check method list
            method_list = pilot.app.query_one("#grpc-method-list")
            self.assertEqual(len(method_list.children), 1)
            self.assertEqual(method_list.children[0].name, "mymethod")

            # Select method
            method_list.focus()
            method_list.index = 0
            await pilot.press("enter")
            await pilot.pause()

            # Verify describe called for method
            mock_manager.describe.assert_called_with("localhost:50051", "mymethod", True, "")

            # Verify Call button enabled
            call_btn = pilot.app.query_one("#btn-grpc-call")
            self.assertFalse(call_btn.disabled)

    @patch('shared.tui_grpc.GrpcLabManager')
    async def test_call_method(self, MockManager):
        # Setup mock
        mock_manager = MockManager.return_value
        mock_manager.call = MagicMock(return_value='{"status": "ok"}')

        async with self.app.run_test(size=(120, 40)) as pilot:
            tab = pilot.app.query_one(GrpcLabTab)

            # Pre-set state as if method selected
            tab.selected_method = "mymethod"
            pilot.app.query_one("#grpc-host").value = "localhost:50051"
            pilot.app.query_one("#grpc-request-data").text = '{"foo": "bar"}' # TextArea uses .text

            # Click call
            # We need to enable button first or just click it (Textual might allow clicking disabled buttons programmatically?)
            # But let's be safe
            pilot.app.query_one("#btn-grpc-call").disabled = False

            await pilot.click("#btn-grpc-call")
            await pilot.pause()

            mock_manager.call.assert_called_with(
                "localhost:50051", "mymethod", '{"foo": "bar"}', True, ""
            )

            log = pilot.app.query_one("#grpc-response-log")
            # Textual 0.28+ RichLog content access is tricky, usually we assume write called
            # We can't easily inspect Renderable content in tests without hacking internals
            # But the mock assertion proves logic ran.

if __name__ == "__main__":
    unittest.main()
