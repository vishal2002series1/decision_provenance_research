import functools
from src.provenance import ProvenanceGraph

# Global Tracker for the demo
audit_log = ProvenanceGraph()

def track_provenance(action_type):
    """
    A Decorator that automatically logs any function call 
    into the immutable Merkle Graph.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Capture Input
            # We keep this as a dict so Pydantic accepts it
            inputs = {"args": args, "kwargs": kwargs}
            
            # 2. Run the actual function (The Agent's "Brain")
            result = func(*args, **kwargs)
            
            # 3. Capture Output & Seal the Node
            # IMPORTANT: We ensure 'result' is wrapped in a dict if it isn't one already
            # This handles cases where a function just returns a string/int
            safe_output = result if isinstance(result, dict) else {"raw_value": result}

            audit_log.add_step(
                action_type=action_type,
                input_data=inputs,         # Pass raw dict, don't str() it
                output_data=safe_output    # Pass raw dict, don't str() it
            )
            return result
        return wrapper
    return decorator