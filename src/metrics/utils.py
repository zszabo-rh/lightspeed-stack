"""Utility functions for metrics handling."""

from typing import cast, Any

# Try to import llama-stack dependencies, fallback to stubs if not available
try:
    from llama_stack.models.llama.datatypes import RawMessage
    from llama_stack.models.llama.llama3.chat_format import ChatFormat
    from llama_stack.models.llama.llama3.tokenizer import Tokenizer
    from llama_stack_client.types.agents.turn import Turn
    LLAMA_STACK_AVAILABLE = True
except ImportError:
    # Create stub classes when llama-stack dependencies are not available
    class RawMessage:
        pass
    class ChatFormat:
        pass
    class Tokenizer:
        pass
    class Turn:
        pass
    LLAMA_STACK_AVAILABLE = False

try:
    import metrics
    from client import AsyncLlamaStackClientHolder
    from configuration import configuration
    from log import get_logger
    from utils.common import run_once_async
    METRICS_AVAILABLE = True
except ImportError:
    # Create minimal stubs
    def run_once_async(func):
        return func
    METRICS_AVAILABLE = False

    class MockLogger:
        def info(self, msg, *args): pass
        def error(self, msg, *args): pass

    logger = MockLogger()

if METRICS_AVAILABLE:
    logger = get_logger(__name__)
    
    async def setup_model_metrics():
        """Set up model metrics - called when needed, not at import time."""
        if not LLAMA_STACK_AVAILABLE or not METRICS_AVAILABLE:
            logger.info("Metrics setup skipped - dependencies not available")
            return
            
        try:
            logger.info("Setting up model metrics")
            model_list = await AsyncLlamaStackClientHolder().get_client().models.list()

            models = [
                model
                for model in model_list
                if model.model_type == "llm"  # pyright: ignore[reportAttributeAccessIssue]
            ]

            default_model_label = (
                configuration.inference.default_provider,  # type: ignore[reportAttributeAccessIssue]
                configuration.inference.default_model,  # type: ignore[reportAttributeAccessIssue]
            )

            for model in models:
                provider = model.provider_id
                model_name = model.identifier
                if provider and model_name:
                    # If the model/provider combination is the default, set the metric value to 1
                    # Otherwise, set it to 0
                    default_model_value = 0
                    label_key = (provider, model_name)
                    if label_key == default_model_label:
                        default_model_value = 1

                    # Set the metric for the provider/model configuration
                    metrics.provider_model_configuration.labels(*label_key).set(
                        default_model_value
                    )
            logger.info("Model metrics setup complete")
        except Exception as e:
            logger.error("Failed to setup model metrics: %s", e)
else:
    # Create stub function when metrics not available
    async def setup_model_metrics():
        pass


def update_llm_token_count_from_turn(
    turn: Any, model: str, provider: str, system_prompt: str = ""
) -> None:
    """Update the LLM calls metrics from a turn."""
    if not LLAMA_STACK_AVAILABLE or not METRICS_AVAILABLE:
        # Silently skip when dependencies not available
        return
        
    tokenizer = Tokenizer.get_instance()
    formatter = ChatFormat(tokenizer)

    raw_message = cast(RawMessage, turn.output_message)
    encoded_output = formatter.encode_dialog_prompt([raw_message])
    token_count = len(encoded_output.tokens) if encoded_output.tokens else 0
    metrics.llm_token_received_total.labels(provider, model).inc(token_count)

    input_messages = [RawMessage(role="user", content=system_prompt)] + cast(
        list[RawMessage], turn.input_messages
    )
    encoded_input = formatter.encode_dialog_prompt(input_messages)
    token_count = len(encoded_input.tokens) if encoded_input.tokens else 0
    metrics.llm_token_sent_total.labels(provider, model).inc(token_count) 