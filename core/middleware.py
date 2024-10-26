import logging
import psutil
import os

class RailwayMemoryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('railway_memory')

    def __call__(self, request):
        try:
            # Get memory usage before request
            process = psutil.Process(os.getpid())
            before_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Process the request
            response = self.get_response(request)
            
            # Get memory usage after request
            after_memory = process.memory_info().rss / 1024 / 1024
            memory_diff = after_memory - before_memory
            
            # Log memory usage
            self.logger.info(
                f"Memory Stats - Path: {request.path[:50]} | "
                f"Before: {before_memory:.1f}MB | "
                f"After: {after_memory:.1f}MB | "
                f"Diff: {memory_diff:+.1f}MB"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Memory monitoring error: {str(e)}")
            return self.get_response(request)