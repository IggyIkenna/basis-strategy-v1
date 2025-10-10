# Results Store Specification

## Overview

The Results Store is responsible for persisting backtest and live trading results to storage. It operates as an async I/O exception to the standard synchronous component architecture, using async/await for performance reasons to keep I/O operations outside the critical trading loop.

## 📚 **Canonical Sources**

- **Architectural Principles**: [REFERENCE_ARCHITECTURE_CANONICAL.md](../REFERENCE_ARCHITECTURE_CANONICAL.md) - Canonical architectural principles
- **Strategy Specifications**: [MODES.md](../MODES.md) - Canonical strategy mode definitions
- **Component Specifications**: [specs/](specs/) - Detailed component implementation guides

## Component Identity

- **Component Name**: `ResultsStore`
- **Component Type**: Storage/Persistence
- **Execution Mode**: Async I/O (exception to synchronous architecture)
- **Dependencies**: Event Logger, P&L Calculator, Strategy Manager

## Core Responsibilities

### 1. Results Persistence
- **Backtest Results**: Store complete backtest results including performance metrics, trades, and events
- **Live Trading Results**: Store real-time performance data and trade history
- **Incremental Updates**: Support both full dumps and incremental updates
- **Format Support**: CSV (MVP), JSON, and future database formats

### 2. Performance Optimization
- **Async I/O**: Use async/await to prevent blocking the critical trading loop
- **Queue-Based Processing**: FIFO queue ensures ordering guarantees
- **Background Workers**: Process storage operations in background threads
- **Batch Operations**: Group related writes for efficiency

### 3. Data Integrity
- **Atomic Writes**: Ensure complete writes or rollback on failure
- **Ordering Guarantees**: Maintain chronological order of results
- **Error Handling**: Graceful degradation on storage failures
- **Recovery**: Resume from last successful write on restart

## Architecture Integration

### Full Loop Position
```
time trigger → position_monitor → exposure_monitor → risk_monitor → strategy_manager → [tight loop if execution needed] → pnl_calculator → results_store
```

### Async I/O Exception Pattern
- **Standard Components**: Synchronous direct method calls
- **Results Store**: Async/await for I/O operations only
- **Rationale**: File/DB writes shouldn't block trading operations
- **Implementation**: Queue-based async with background worker

## Interface Specification

### Core Methods

```python
class ResultsStore:
    def __init__(self, config: Dict, data_provider: DataProvider, 
                 execution_mode: str, event_logger: EventLogger = None):
        """Initialize Results Store with async I/O capabilities"""
        
    async def store_timestep_results(self, timestamp: pd.Timestamp, 
                                   results: Dict) -> None:
        """Store results for a single timestep (async I/O)"""
        
    async def store_backtest_results(self, request_id: str, 
                                   results: Dict) -> None:
        """Store complete backtest results (async I/O)"""
        
    async def store_live_results(self, request_id: str, 
                               results: Dict) -> None:
        """Store live trading results (async I/O)"""
        
    def get_storage_status(self) -> Dict:
        """Get current storage status (synchronous)"""
        
    async def cleanup_old_results(self, retention_days: int) -> None:
        """Clean up old results (async I/O)"""
```

### Event Integration

```python
# Components call Results Store via await
await self.results_store.store_timestep_results(timestamp, results)

# Results Store logs its own operations
await self.event_logger.log_event(
    event_type="RESULTS_STORED",
    timestamp=timestamp,
    data={"request_id": request_id, "size_bytes": size}
)
```

## Storage Strategy

### Phase 1: CSV Files (MVP)
- **Format**: CSV files in `results/{request_id}/` directory
- **Files**: `performance.csv`, `trades.csv`, `events.csv`
- **Benefits**: Simple, human-readable, easy debugging
- **Limitations**: No concurrent access, limited querying

### Phase 2: Database (Future)
- **Format**: PostgreSQL or similar relational database
- **Benefits**: Concurrent access, complex queries, ACID compliance
- **Migration**: Gradual migration from CSV to database
- **Backward Compatibility**: Maintain CSV export capability

## Performance Characteristics

### Async I/O Benefits
- **Non-Blocking**: Trading operations continue while results are stored
- **Throughput**: Higher throughput for large result sets
- **Responsiveness**: Better system responsiveness under load
- **Scalability**: Can handle multiple concurrent storage operations

### Queue-Based Processing
- **FIFO Ordering**: Results stored in chronological order
- **Backpressure**: Queue size limits prevent memory issues
- **Error Isolation**: Storage failures don't affect trading
- **Recovery**: Can replay queue on restart

## Error Handling

### Storage Failures
- **Graceful Degradation**: Continue trading even if storage fails
- **Error Logging**: Log all storage errors for debugging
- **Retry Logic**: Automatic retry for transient failures
- **Fallback**: Use in-memory storage if persistent storage fails

### Data Corruption
- **Validation**: Validate data before storage
- **Checksums**: Use checksums to detect corruption
- **Backup**: Maintain backup copies of critical results
- **Recovery**: Restore from backup on corruption detection

## Configuration

### Storage Settings
```yaml
results_store:
  storage_type: "csv"  # csv, database
  storage_path: "results/"
  max_queue_size: 1000
  batch_size: 100
  retention_days: 30
  compression: true
  async_workers: 2
```

### Performance Tuning
- **Queue Size**: Balance memory usage vs. throughput
- **Batch Size**: Optimize for storage medium (SSD vs. HDD)
- **Worker Count**: Match to storage I/O capacity
- **Compression**: Trade CPU for storage space

## Testing Strategy

### Unit Tests
- **Storage Operations**: Test individual storage methods
- **Error Handling**: Test failure scenarios and recovery
- **Data Integrity**: Verify data consistency after storage
- **Performance**: Test async I/O performance characteristics

### Integration Tests
- **Full Loop Integration**: Test Results Store in full loop
- **Event Logging**: Verify event logging integration
- **Error Propagation**: Test error handling in full system
- **Recovery**: Test system recovery from storage failures

### Performance Tests
- **Throughput**: Measure storage throughput under load
- **Latency**: Measure storage latency impact on trading
- **Memory Usage**: Monitor memory usage with large queues
- **Concurrent Access**: Test multiple concurrent storage operations

## Future Enhancements

### Database Integration
- **Schema Design**: Design database schema for results
- **Migration Tools**: Tools to migrate from CSV to database
- **Query Interface**: API for querying stored results
- **Analytics**: Built-in analytics on stored results

### Advanced Features
- **Compression**: Automatic compression of stored data
- **Encryption**: Encrypt sensitive result data
- **Replication**: Replicate results to multiple storage locations
- **Archival**: Automatic archival of old results

### Monitoring
- **Storage Metrics**: Monitor storage performance and health
- **Queue Monitoring**: Monitor queue size and processing rate
- **Error Tracking**: Track and alert on storage errors
- **Capacity Planning**: Monitor storage capacity usage

## Dependencies

### Required Components
- **Event Logger**: For logging storage operations
- **P&L Calculator**: For performance data
- **Strategy Manager**: For strategy execution data

### External Dependencies
- **File System**: For CSV storage (Phase 1)
- **Database**: For database storage (Phase 2)
- **AsyncIO**: For async I/O operations
- **Queue**: For async queue processing

## Security Considerations

### Data Protection
- **Access Control**: Restrict access to result files
- **Encryption**: Encrypt sensitive result data
- **Audit Trail**: Log all access to result data
- **Backup Security**: Secure backup storage locations

### Privacy
- **Data Minimization**: Store only necessary data
- **Retention**: Automatic deletion of old data
- **Anonymization**: Anonymize sensitive data if needed
- **Compliance**: Ensure compliance with data protection regulations

## Implementation Notes

### Async I/O Pattern
```python
# Standard synchronous component call
result = self.some_component.process_data(data)

# Results Store async call (exception)
await self.results_store.store_results(result)
```

### Queue Processing
```python
# Background worker processes queue
async def process_storage_queue():
    while True:
        item = await self.storage_queue.get()
        try:
            await self._store_item(item)
        except Exception as e:
            await self.event_logger.log_error(e)
        finally:
            self.storage_queue.task_done()
```

### Error Recovery
```python
# Resume from last successful write
async def recover_from_failure():
    last_successful = await self._get_last_successful_write()
    await self._replay_queue_from(last_successful)
```

This specification ensures the Results Store operates efficiently as an async I/O exception while maintaining data integrity and system performance.
