from typing import List, Dict, Literal
from llama_cpp import Llama, LlamaGrammar
from .messages_formatter import MessagesFormatterType, get_predefined_messages_formatter

class LlamaCppAgent:
    name: str
    system_prompt: str
    model: Llama
    messages: List[Dict[str, str]] = []

    def __init__(self, model, name="model", system_prompt="You are helpful assistant.",
                 predefined_messages_formatter_type: MessagesFormatterType = None, debug_output=False):
        self.model = model
        self.name = name
        self.system_prompt = system_prompt
        self.debug_output = debug_output
        if predefined_messages_formatter_type:
            self.messages_formatter = get_predefined_messages_formatter(predefined_messages_formatter_type)
        else:
            self.messages_formatter = get_predefined_messages_formatter(MessagesFormatterType.CHATML)

    def get_chat_response(
            self,
            message: str,
            role: Literal["system"] | Literal["user"] | Literal["assistant"] = "user",
            grammar: LlamaGrammar = None,
            max_tokens: int = 0,
            temperature: float = 0.4,
            top_k: int = 0,
            top_p: float = 1.0,
            min_p: float = 0.05,
            typical_p: float = 1.0,
            repeat_penalty: float = 1.0,
            mirostat_mode: int = 0,
            mirostat_tau: float = 5.0,
            mirostat_eta: float = 0.1,
            tfs_z: float = 1.0,
            stop_sequences: List[str] = None,
            stream: bool = True,
            add_response_to_chat_history: bool = True,
            print_output: bool = True
    ):
        messages = [
            {
                "role": "system",
                "content": self.system_prompt,
            },
        ]

        self.messages.append(
            {
                "role": role,
                "content": message,
            },
        )
        messages.extend(self.messages)

        prompt, response_role = self.messages_formatter.format_messages(messages)
        if self.debug_output:
            print(prompt, end="")

        if stop_sequences is None:
            stop_sequences = self.messages_formatter.DEFAULT_STOP_SEQUENCES

        if self.model:
            completion = self.model.create_completion(
                prompt=prompt,
                max_tokens=max_tokens,
                stream=stream,
                stop=stop_sequences,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                min_p=min_p,
                typical_p=typical_p,
                mirostat_mode=mirostat_mode,
                mirostat_tau=mirostat_tau,
                mirostat_eta=mirostat_eta,
                tfs_z=tfs_z,
                repeat_penalty=repeat_penalty,
                grammar=grammar
            )
            if stream and print_output:
                full_response = ""
                for out in completion:
                    text = out['choices'][0]['text']
                    full_response += text
                    print(text, end="")
                print("")
                if add_response_to_chat_history:
                    self.messages.append(
                        {
                            "role": response_role,
                            "content": full_response,
                        },
                    )
                return full_response
            if stream:
                full_response = ""
                for out in completion:
                    text = out['choices'][0]['text']
                    full_response += text
                if add_response_to_chat_history:
                    self.messages.append(
                        {
                            "role": response_role,
                            "content": full_response,
                        },
                    )
                return full_response
            if print_output:
                text = completion['choices'][0]['text']
                print(text)

                if add_response_to_chat_history:
                    self.messages.append(
                        {
                            "role": response_role,
                            "content": text,
                        },
                    )
                return text
            text = completion['choices'][0]['text']
            if add_response_to_chat_history:
                self.messages.append(
                    {
                        "role": response_role,
                        "content": text,
                    },
                )
            return text
        return "Error: No model loaded!"

    def remove_last_k_chat_messages(self, k):
        # Ensure k is not greater than the length of the messages list
        k = min(k, len(self.messages))

        # Remove the last k elements
        self.messages = self.messages[:-k] if k > 0 else self.messages
