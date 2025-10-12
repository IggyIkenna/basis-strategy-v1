# Process Management Platform

## Overview
- Centralized process control for all trading platforms
- Event-driven architecture for platform coordination
- Manages platform dependencies and startup sequences
- Handles process lifecycle and health monitoring
- Provides unified API for process control
- Supports both manual and automated control
- Lives in common/ repository for cross-platform access

## Service Components

### 1. Event Management
- **Event Listening**:
  - Platform state change events
  - Health check events
  - Error and warning events
  - Resource utilization events
- **Event Processing**:
  - Event prioritization
  - Dependency validation
  - Action determination
  - Response orchestration

### 2. Process Control
- **Platform Management**:
  - Start/stop/restart commands
  - Graceful shutdown handling
  - Process health monitoring
  - Resource allocation
- **Dependency Management**:
  - Platform dependency graph
  - Startup sequence control
  - Shutdown order management
  - Cross-platform coordination

### 3. API Interface
- **Control Endpoints**:
  ```python
  @app.post("/api/v1/platform/{platform_id}/control")
  async def control_platform(
      platform_id: str,
      action: Literal["start", "stop", "restart"],
      config: Optional[Dict] = None
  ):
      """Control platform processes."""
      return await process_controller.execute_action(
          platform_id, action, config
      )
  ```
- **Status Endpoints**:
  ```python
  @app.get("/api/v1/platform/{platform_id}/status")
  async def get_platform_status(platform_id: str):
      """Get platform status and health metrics."""
      return await process_controller.get_status(platform_id)
  ```

### 4. Configuration Management
- **Platform Configs**:
  - Environment-specific settings
  - Resource limits
  - Dependency definitions
  - Health check parameters
- **User Configs**:
  - User-defined process controls
  - Custom startup sequences
  - Platform-specific settings
  - Alert preferences

## Platform Dependencies

### Dependency Graph
```python
PLATFORM_DEPENDENCIES = {
    'market_data_service': [],  # No dependencies
    'feature_engineering': ['market_data_service'],
    'ml_inference': ['feature_engineering'],
    'strategy_generation': ['ml_inference'],
    'order_management': ['strategy_generation'],
    'position_management': ['order_management']
}

class DependencyManager:
    def __init__(self):
        self.graph = PLATFORM_DEPENDENCIES
        self.platform_states = {}
        
    def can_start_platform(self, platform_id: str) -> bool:
        """Check if all dependencies are running."""
        dependencies = self.graph.get(platform_id, [])
        return all(
            self.platform_states.get(dep, {}).get('status') == 'running'
            for dep in dependencies
        )
    
    def get_startup_sequence(self) -> List[str]:
        """Generate ordered startup sequence."""
        visited = set()
        sequence = []
        
        def visit(platform):
            if platform in visited:
                return
            visited.add(platform)
            for dep in self.graph.get(platform, []):
                visit(dep)
            sequence.append(platform)
            
        for platform in self.graph:
            visit(platform)
        return sequence
```

### Process Control Implementation
```python
class ProcessController:
    def __init__(self, config: Dict):
        self.config = config
        self.dependency_manager = DependencyManager()
        self.platform_processes = {}
        
    async def start_platform(self, platform_id: str, config: Dict = None):
        """Start a platform and its dependencies."""
        if not self.dependency_manager.can_start_platform(platform_id):
            raise DependencyError(f"Dependencies not met for {platform_id}")
        
        platform_config = {
            **self.config.get(platform_id, {}),
            **(config or {})
        }
        
        # Send start command to platform's control API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://{platform_id}/api/v1/control/start",
                json=platform_config
            )
            
        if response.status_code == 200:
            self.platform_processes[platform_id] = {
                'status': 'running',
                'started_at': datetime.now(),
                'config': platform_config
            }
            
    async def stop_platform(self, platform_id: str):
        """Stop a platform and dependent platforms."""
        dependent_platforms = [
            p for p, deps in self.dependency_manager.graph.items()
            if platform_id in deps
        ]
        
        # Stop dependent platforms first
        for dep_platform in dependent_platforms:
            await self.stop_platform(dep_platform)
            
        # Stop the requested platform
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://{platform_id}/api/v1/control/stop"
            )
            
        if response.status_code == 200:
            self.platform_processes[platform_id] = {
                'status': 'stopped',
                'stopped_at': datetime.now()
            }
```

### Event Handling
```python
class EventHandler:
    def __init__(self, process_controller: ProcessController):
        self.controller = process_controller
        self.event_queue = asyncio.Queue()
        
    async def handle_platform_event(self, event: Dict):
        """Handle platform events and take appropriate action."""
        platform_id = event['platform_id']
        event_type = event['type']
        
        if event_type == 'health_check_failed':
            await self.controller.restart_platform(platform_id)
        elif event_type == 'resource_exceeded':
            await self.controller.stop_platform(platform_id)
        elif event_type == 'dependency_failed':
            dependent_platforms = [
                p for p, deps in self.controller.dependency_manager.graph.items()
                if platform_id in deps
            ]
            for dep_platform in dependent_platforms:
                await self.controller.stop_platform(dep_platform)
```

## Configuration Example
```python
config = {
    'platforms': {
        'market_data_service': {
            'health_check_interval': 30,
            'max_restart_attempts': 3,
            'startup_timeout': 60,
            'required_resources': {
                'cpu_cores': 4,
                'memory_mb': 8192
            }
        },
        'feature_engineering': {
            'health_check_interval': 60,
            'max_restart_attempts': 3,
            'startup_timeout': 120,
            'required_resources': {
                'cpu_cores': 8,
                'memory_mb': 16384
            }
        }
    },
    'dependencies': {
        'startup_timeout': 300,
        'shutdown_timeout': 180,
        'health_check_enabled': True
    },
    'monitoring': {
        'event_retention_days': 7,
        'log_level': 'INFO',
        'alert_channels': ['slack', 'email']
    }
}
```

## Best Practices
- Implement comprehensive dependency validation
- Handle graceful shutdowns
- Monitor platform health metrics
- Maintain detailed process logs
- Implement circuit breakers for cascading failures
- Monitor resource usage across platforms
- Regular health checks
- Automated recovery procedures
- Maintain audit trail of process control actions 