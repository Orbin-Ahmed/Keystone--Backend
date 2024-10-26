import resource
import logging
import psutil
import os
import sys

class RailwayMemoryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('railway_memory')
        
        # Setup logging to stdout for Railway
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('MEMORY_MONITOR - %(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def __call__(self, request):
        # Get memory usage before request
        process = psutil.Process(os.getpid())
        before_memory = process.memory_info().rss / 1024 / 1024  # Convert to MB
        
        # Process the request
        response = self.get_response(request)
        
        # Get memory usage after request
        after_memory = process.memory_info().rss / 1024 / 1024
        memory_difference = after_memory - before_memory
        
        # Log with a distinct prefix for easy filtering
        self.logger.info(
            f"[MEMORY_STATS] "
            f"Path: {request.path[:100]} | "  # Truncate long paths
            f"Method: {request.method} | "
            f"Memory Before: {before_memory:.1f}MB | "
            f"Memory After: {after_memory:.1f}MB | "
            f"Difference: {memory_difference:+.1f}MB"
        )
        
        # Warning for high memory usage
        if after_memory > 500:  # Adjust threshold as needed
            self.logger.warning(
                f"[HIGH_MEMORY_ALERT] "
                f"Path: {request.path[:100]} | "
                f"Memory Usage: {after_memory:.1f}MB"
            )
        
        return response

    def process_exception(self, request, exception):
        process = psutil.Process(os.getpid())
        current_memory = process.memory_info().rss / 1024 / 1024
        
        self.logger.error(
            f"[MEMORY_ERROR] "
            f"Exception in {request.path[:100]} | "
            f"Memory: {current_memory:.1f}MB | "
            f"Error: {str(exception)[:200]}"  # Truncate long error messages
        )