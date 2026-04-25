import multiprocessing as mp
import sys
import traceback


class FunctionExecutionError(Exception):
    """Exception raised when the executed function raises an exception."""

    def __init__(self, original_exception, traceback_str):
        self.original_exception = original_exception
        self.traceback_str = traceback_str
        super().__init__(f"Function execution failed: {original_exception}\n{traceback_str}")


def _worker(func, args, queue):
    """Worker function that runs in a separate process."""
    try:
        result = func(*args)
        queue.put(("ok", result))
    except Exception as e:
        # Capture the full exception information
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        queue.put(("err", (str(e), tb_str)))


def run_with_timeout(func, args=(), timeout=5):
    """Run a function with a timeout using multiprocessing.

    Args:
        func: The function to execute.
        args: Arguments to pass to the function.
        timeout: Maximum execution time in seconds.

    Returns:
        The result of the function call.

    Raises:
        TimeoutError: If the function execution exceeds the timeout.
        FunctionExecutionError: If the function raises an exception.
        RuntimeError: If there are issues with the multiprocessing setup.
    """
    queue = mp.Queue()

    try:
        process = mp.Process(
            target=_worker,
            args=(func, args, queue)
        )
        process.start()
        process.join(timeout)

        if process.is_alive():  # Timeout reached: killing process
            process.terminate()
            process.join()  # Wait for termination
            raise TimeoutError(f"Function execution timed out after {timeout} seconds")

        if queue.empty():
            raise RuntimeError("No result received from worker process")

        status, result = queue.get(timeout=1)  # Small timeout for queue.get

        if status == "err":
            exc_str, tb_str = result
            raise FunctionExecutionError(exc_str, tb_str)

        return result

    except RuntimeError as e:
        raise RuntimeError("Failed to retrieve result from worker process queue") from e
    except Exception as e:
        # Handle any other multiprocessing-related errors
        raise RuntimeError(f"Multiprocessing error during function execution: {e}") from e
