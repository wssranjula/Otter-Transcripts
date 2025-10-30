"""
Production-ready resilience utilities for external service calls.
Includes retry logic, circuit breakers, and timeout handling.
"""

import time
import logging
import functools
from typing import Callable, Any, Optional, Type, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback function called on each retry
        
    Example:
        @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        def call_external_api():
            # API call that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}",
                            exc_info=True
                        )
                        raise
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    
                    if on_retry:
                        on_retry(e, attempt)
                    
                    time.sleep(delay)
                    delay *= backoff_factor
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern for external service calls.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, requests fail fast
    - HALF_OPEN: Testing if service has recovered
    
    Example:
        neo4j_breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        
        @neo4j_breaker.call
        def query_neo4j():
            # Database query
            pass
    """
    
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting recovery (HALF_OPEN)
            expected_exception: Exception type that triggers the circuit breaker
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = self.CLOSED
        
        logger.info(
            f"CircuitBreaker initialized: threshold={failure_threshold}, "
            f"timeout={timeout}s"
        )
    
    def call(self, func: Callable) -> Callable:
        """Decorator to protect a function with circuit breaker."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if self.state == self.OPEN:
                if self._should_attempt_reset():
                    logger.info(f"Circuit breaker entering HALF_OPEN state for {func.__name__}")
                    self.state = self.HALF_OPEN
                else:
                    elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                    wait_time = self.timeout - elapsed
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is OPEN for {func.__name__}. "
                        f"Try again in {wait_time:.0f}s"
                    )
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try recovery."""
        if self.last_failure_time is None:
            return True
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout
    
    def _on_success(self):
        """Handle successful call."""
        if self.state == self.HALF_OPEN:
            logger.info("Circuit breaker recovered, returning to CLOSED state")
            self.state = self.CLOSED
        
        self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            if self.state != self.OPEN:
                logger.error(
                    f"Circuit breaker OPEN after {self.failure_count} failures. "
                    f"Will attempt recovery in {self.timeout}s"
                )
                self.state = self.OPEN
    
    def reset(self):
        """Manually reset the circuit breaker."""
        logger.info("Circuit breaker manually reset")
        self.failure_count = 0
        self.last_failure_time = None
        self.state = self.CLOSED
    
    def get_status(self) -> dict:
        """Get current circuit breaker status."""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "threshold": self.failure_threshold
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and blocking calls."""
    pass


def timeout(seconds: float):
    """
    Timeout decorator for functions (note: uses threading for I/O operations).
    
    For CPU-bound operations, consider using multiprocessing or asyncio.
    
    Args:
        seconds: Maximum execution time in seconds
        
    Example:
        @timeout(30.0)
        def slow_operation():
            # Long-running operation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"{func.__name__} exceeded timeout of {seconds}s")
            
            # Set alarm signal (Unix-like systems only)
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(seconds))
                
                try:
                    result = func(*args, **kwargs)
                finally:
                    signal.alarm(0)  # Cancel alarm
                
                return result
            except AttributeError:
                # Windows doesn't support SIGALRM, fall back to simple execution
                logger.warning(
                    f"Timeout decorator not supported on this platform for {func.__name__}"
                )
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Pre-configured circuit breakers for common services
neo4j_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=60.0,
    expected_exception=Exception
)

mistral_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    timeout=30.0,
    expected_exception=Exception
)

gdrive_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=120.0,
    expected_exception=Exception
)

postgres_circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=60.0,
    expected_exception=Exception
)


def log_execution_time(func: Callable) -> Callable:
    """
    Decorator to log function execution time.
    
    Useful for monitoring performance of critical operations.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"{func.__name__} completed in {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.2f}s: {e}")
            raise
    
    return wrapper


if __name__ == "__main__":
    # Test examples
    logging.basicConfig(level=logging.INFO)
    
    # Test retry decorator
    @retry_with_backoff(max_attempts=3, initial_delay=0.5)
    def flaky_function(fail_count=2):
        """Simulates a function that fails N times before succeeding."""
        if not hasattr(flaky_function, 'attempts'):
            flaky_function.attempts = 0
        
        flaky_function.attempts += 1
        
        if flaky_function.attempts <= fail_count:
            raise ConnectionError(f"Simulated failure {flaky_function.attempts}")
        
        return "Success!"
    
    print("Testing retry decorator...")
    result = flaky_function()
    print(f"Result: {result}")
    
    # Test circuit breaker
    print("\nTesting circuit breaker...")
    breaker = CircuitBreaker(failure_threshold=3, timeout=2)
    
    @breaker.call
    def failing_service():
        raise ConnectionError("Service unavailable")
    
    # Trigger failures
    for i in range(3):
        try:
            failing_service()
        except ConnectionError:
            print(f"Call {i+1} failed")
    
    # Now circuit should be open
    try:
        failing_service()
    except CircuitBreakerOpenError as e:
        print(f"Circuit breaker blocked call: {e}")
    
    print(f"Circuit breaker status: {breaker.get_status()}")

