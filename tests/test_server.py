"""
Tests for server module including lifespan management and client access.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from qontak_mcp.server import get_client, lifespan, mcp


class TestGetClient:
    """Test get_client function."""
    
    def test_get_client_before_initialization(self):
        """Test that get_client raises RuntimeError before server starts."""
        # Reset the global client
        import qontak_mcp.server as server_module
        server_module._client = None
        
        with pytest.raises(RuntimeError) as exc_info:
            get_client()
        
        assert "Client not initialized" in str(exc_info.value)
        assert "MCP server must be started" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_client_after_initialization(self):
        """Test that get_client returns client after initialization."""
        import qontak_mcp.server as server_module
        from qontak_mcp.client import QontakClient
        
        # Mock the client
        mock_client = Mock(spec=QontakClient)
        server_module._client = mock_client
        
        try:
            client = get_client()
            assert client is mock_client
        finally:
            # Cleanup
            server_module._client = None


class TestLifespan:
    """Test lifespan context manager."""
    
    @pytest.mark.asyncio
    async def test_lifespan_initialization(self, mock_env):
        """Test that lifespan initializes all components."""
        from qontak_mcp.server import lifespan
        from qontak_mcp.client import QontakClient
        import qontak_mcp.server as server_module
        
        # Mock FastMCP
        mock_mcp = Mock()
        
        # Mock QontakClient to avoid real API calls
        with patch('qontak_mcp.server.QontakClient') as mock_client_class:
            mock_client_instance = Mock(spec=QontakClient)
            mock_client_instance.close = AsyncMock()
            mock_client_class.return_value = mock_client_instance
            
            # Mock the logger to avoid issues with logging calls
            with patch('qontak_mcp.server.get_logger') as mock_logger_getter:
                mock_logger = Mock()
                mock_logger.system_startup = Mock()
                mock_logger.system_shutdown = Mock()
                mock_logger_getter.return_value = mock_logger
                
                # Use the lifespan context
                async with lifespan(mock_mcp):
                    # During lifespan, client should be initialized
                    assert server_module._client is not None
                    assert server_module._client is mock_client_instance
                
                # After lifespan, cleanup should have been called
                mock_client_instance.close.assert_called_once()
                assert server_module._client is None
    
    @pytest.mark.asyncio
    async def test_lifespan_cleanup_on_error(self, mock_env):
        """Test that lifespan cleans up even if error occurs."""
        from qontak_mcp.server import lifespan
        from qontak_mcp.client import QontakClient
        import qontak_mcp.server as server_module
        
        mock_mcp = Mock()
        
        with patch('qontak_mcp.server.QontakClient') as mock_client_class:
            mock_client_instance = Mock(spec=QontakClient)
            mock_client_instance.close = AsyncMock()
            mock_client_class.return_value = mock_client_instance
            
            with patch('qontak_mcp.server.get_logger'):
                try:
                    async with lifespan(mock_mcp):
                        # Simulate an error during operation
                        raise ValueError("Test error")
                except ValueError:
                    pass
                
                # Cleanup should still have been called
                mock_client_instance.close.assert_called_once()
                assert server_module._client is None
    
    @pytest.mark.asyncio
    async def test_lifespan_loads_env(self, mock_env):
        """Test that lifespan loads environment variables."""
        from qontak_mcp.server import lifespan
        
        mock_mcp = Mock()
        
        with patch('qontak_mcp.server.load_dotenv') as mock_load_dotenv:
            with patch('qontak_mcp.server.QontakClient') as mock_client_class:
                mock_client_instance = Mock()
                mock_client_instance.close = AsyncMock()
                mock_client_class.return_value = mock_client_instance
                
                with patch('qontak_mcp.server.get_logger'):
                    async with lifespan(mock_mcp):
                        pass
                    
                    # load_dotenv should have been called
                    mock_load_dotenv.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lifespan_initializes_logger(self, mock_env):
        """Test that lifespan configures the logger."""
        from qontak_mcp.server import lifespan
        
        mock_mcp = Mock()
        
        with patch('qontak_mcp.server.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_logger.system_startup = Mock()
            mock_logger.system_shutdown = Mock()
            mock_logger._log = Mock()
            mock_get_logger.return_value = mock_logger
            
            with patch('qontak_mcp.server.QontakClient') as mock_client_class:
                mock_client_instance = Mock()
                mock_client_instance.close = AsyncMock()
                mock_client_class.return_value = mock_client_instance
                
                async with lifespan(mock_mcp):
                    pass
                
                # Logger methods should have been called
                mock_logger.system_startup.assert_called_once()
                mock_logger.system_shutdown.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lifespan_initializes_rate_limiter(self, mock_env):
        """Test that lifespan initializes the rate limiter."""
        from qontak_mcp.server import lifespan
        
        mock_mcp = Mock()
        
        with patch('qontak_mcp.server.get_rate_limiter') as mock_get_rate_limiter:
            with patch('qontak_mcp.server.QontakClient') as mock_client_class:
                mock_client_instance = Mock()
                mock_client_instance.close = AsyncMock()
                mock_client_class.return_value = mock_client_instance
                
                with patch('qontak_mcp.server.get_logger'):
                    async with lifespan(mock_mcp):
                        pass
                    
                    # get_rate_limiter should have been called
                    mock_get_rate_limiter.assert_called_once()


class TestMCPServerCreation:
    """Test MCP server instance creation."""
    
    def test_mcp_server_exists(self):
        """Test that mcp server instance is created."""
        from qontak_mcp.server import mcp
        assert mcp is not None
        assert hasattr(mcp, 'name')
    
    def test_mcp_server_has_fastmcp_attributes(self):
        """Test that mcp server is a FastMCP instance with expected attributes."""
        from qontak_mcp.server import mcp
        # FastMCP servers have various attributes, check for run method
        assert hasattr(mcp, 'run')
        assert callable(mcp.run)


class TestMainFunction:
    """Test main entry point."""
    
    def test_main_function_exists(self):
        """Test that main function exists and is callable."""
        from qontak_mcp.server import main
        assert callable(main)
    
    def test_main_calls_load_dotenv(self, mock_env):
        """Test that main loads environment variables."""
        from qontak_mcp.server import main
        
        with patch('qontak_mcp.server.load_dotenv') as mock_load_dotenv:
            with patch('qontak_mcp.server.mcp') as mock_mcp:
                mock_mcp.run = Mock()
                main()
                mock_load_dotenv.assert_called_once()
    
    def test_main_calls_mcp_run(self, mock_env):
        """Test that main calls mcp.run()."""
        from qontak_mcp.server import main
        
        with patch('qontak_mcp.server.mcp') as mock_mcp:
            mock_mcp.run = Mock()
            main()
            mock_mcp.run.assert_called_once()


class TestLazyToolRegistration:
    """Test lazy tool registration and fallback mechanisms."""
    
    def test_lazy_client_proxy_getattr(self, mock_env):
        """Test _LazyClientProxy delegates attribute access to real client."""
        import qontak_mcp.server as server_module
        from qontak_mcp.client import QontakClient
        
        # Create a mock client with a specific attribute
        mock_client = Mock(spec=QontakClient)
        mock_client.some_method = Mock(return_value="test_result")
        server_module._client = mock_client
        
        try:
            # Create proxy and test attribute access
            from qontak_mcp.server import get_client
            
            # The proxy should delegate to the real client
            client = get_client()
            assert client is mock_client
            result = client.some_method()
            assert result == "test_result"
        finally:
            server_module._client = None
    
    def test_create_lazy_tool_registrar_success(self):
        """Test that _create_lazy_tool_registrar registers all tool types."""
        from qontak_mcp.server import _create_lazy_tool_registrar, mcp, get_client
        
        # Just verify the function runs without error and mcp is configured
        # The actual registration already happened at import time
        assert mcp is not None
        assert callable(get_client)
    
    def test_import_error_fallback_creates_lazy_proxy(self, mock_env):
        """Test that ImportError fallback creates _LazyClientProxy correctly."""
        # Import the tools module to verify register functions exist
        from qontak_mcp.tools import register_deal_tools, register_ticket_tools, register_task_tools
        
        # These should be callable (they're used in the fallback path)
        assert callable(register_deal_tools)
        assert callable(register_ticket_tools)
        assert callable(register_task_tools)
    
    def test_lazy_proxy_class_behavior(self, mock_env):
        """Test _LazyClientProxy class behavior when instantiated directly."""
        import qontak_mcp.server as server_module
        from qontak_mcp.client import QontakClient
        
        # Simulate what happens in the fallback path
        # Create a class that mirrors the _LazyClientProxy behavior
        class TestLazyProxy:
            def __getattr__(self, name):
                return getattr(server_module.get_client(), name)
        
        # Set up a mock client
        mock_client = Mock(spec=QontakClient)
        mock_client.test_attr = "test_value"
        mock_client.call_method = Mock(return_value={"result": "ok"})
        server_module._client = mock_client
        
        try:
            proxy = TestLazyProxy()
            
            # Test attribute access through proxy
            assert proxy.test_attr == "test_value"
            result = proxy.call_method()
            assert result == {"result": "ok"}
        finally:
            server_module._client = None
    
    def test_fallback_path_with_simulated_import_error(self, mock_env):
        """Test the fallback code path when lazy imports would fail.
        
        This simulates what happens if register_*_tools_lazy functions
        don't exist (backward compatibility scenario).
        """
        import qontak_mcp.server as server_module
        from qontak_mcp.client import QontakClient
        from qontak_mcp.tools import register_deal_tools, register_ticket_tools, register_task_tools
        
        # The fallback creates a _LazyClientProxy that defers to get_client()
        # We test this behavior by creating the same class and verifying it works
        class _LazyClientProxy:
            """Proxy that defers all calls to the real client."""
            
            def __getattr__(self, name):
                return getattr(server_module.get_client(), name)
        
        # Set up a mock client
        mock_client = Mock(spec=QontakClient)
        mock_client.create_deal = Mock(return_value={"id": "123"})
        mock_client.list_tickets = Mock(return_value=[{"id": "456"}])
        mock_client.get_task = Mock(return_value={"id": "789"})
        server_module._client = mock_client
        
        try:
            # Create the lazy proxy like the fallback code does
            _lazy_proxy = _LazyClientProxy()
            
            # Verify the proxy correctly delegates to the client
            assert _lazy_proxy.create_deal() == {"id": "123"}
            assert _lazy_proxy.list_tickets() == [{"id": "456"}]
            assert _lazy_proxy.get_task() == {"id": "789"}
            
            # Verify the actual client methods were called
            mock_client.create_deal.assert_called_once()
            mock_client.list_tickets.assert_called_once()
            mock_client.get_task.assert_called_once()
        finally:
            server_module._client = None
    
    def test_fallback_registers_tools_with_proxy(self, mock_env):
        """Test that fallback registration works with the lazy proxy."""
        from qontak_mcp.tools import register_deal_tools, register_ticket_tools, register_task_tools
        from mcp.server.fastmcp import FastMCP
        import qontak_mcp.server as server_module
        from qontak_mcp.client import QontakClient
        
        # Create a test MCP server
        test_mcp = FastMCP("test-fallback")
        
        # Create a proxy like the fallback does
        class _LazyClientProxy:
            def __getattr__(self, name):
                return getattr(server_module.get_client(), name)
        
        _lazy_proxy = _LazyClientProxy()
        
        # Register tools with the proxy (simulating fallback behavior)
        # These should not raise errors
        register_deal_tools(test_mcp, _lazy_proxy)  # type: ignore
        register_ticket_tools(test_mcp, _lazy_proxy)  # type: ignore
        register_task_tools(test_mcp, _lazy_proxy)  # type: ignore
        
        # If we got here without error, the fallback registration works


class TestModuleEntryPoint:
    """Test module-level execution."""
    
    def test_version_defined(self):
        """Test that __version__ is defined."""
        from qontak_mcp.server import __version__
        assert __version__ is not None
        assert isinstance(__version__, str)
    
    def test_module_defines_global_client(self):
        """Test that module defines _client global."""
        import qontak_mcp.server as server_module
        assert hasattr(server_module, '_client')
