"""AI-powered documentation generator using OpenAI API."""
import os
from openai import OpenAI
from typing import Optional


class AIDocGenerator:
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate_module_docs(self, module_name: str, classes: list, functions: list, existing_doc: Optional[str] = None) -> str:
        """Generate Markdown documentation for a module."""
        class_names = [cls.name for cls in classes]
        func_names = [fn.name for fn in functions]
        prompt = self._build_module_prompt(module_name, class_names, func_names, existing_doc)
        return self._call_ai(prompt, "module")

    def generate_class_docs(self, class_name: str, bases: list, methods: list, existing_doc: Optional[str] = None) -> str:
        """Generate Markdown documentation for a class."""
        method_sigs = [f"{m.name}({', '.join(m.args)})" for m in methods]
        prompt = self._build_class_prompt(class_name, bases, method_sigs, existing_doc)
        return self._call_ai(prompt, "class")

    def generate_function_docs(self, func_name: str, args: list, returns: Optional[str], existing_doc: Optional[str] = None) -> str:
        """Generate Markdown documentation for a function."""
        sig = f"{func_name}({', '.join(args)})"
        prompt = self._build_function_prompt(sig, returns, existing_doc)
        return self._call_ai(prompt, "function")

    def _build_module_prompt(self, name: str, classes: list, functions: list, existing_doc: Optional[str]) -> str:
        items = []
        if classes:
            items.append("Classes: " + ", ".join(classes))
        if functions:
            items.append("Functions: " + ", ".join(functions))
        items_str = "; ".join(items) if items else "No classes or functions."
        doc = existing_doc or "(no docstring)"
        return (
            f"Generate comprehensive Markdown documentation for a Python module.\n\n"
            f"Module name: {name}\n"
            f"Contents: {items_str}\n"
            f"Existing docstring: {doc}\n\n"
            "Write a module-level overview, describe the purpose, list and briefly explain each class and function. "
            "Use appropriate Markdown headings (# for module title, ## for classes, ## for functions). "
            "Focus on helping users understand how to use this module."
        )

    def _build_class_prompt(self, name: str, bases: list, methods: list, existing_doc: Optional[str]) -> str:
        bases_str = ", ".join(bases) if bases else "object"
        methods_list = "\n  - ".join(methods) if methods else "None"
        doc = existing_doc or "(no docstring)"
        return (
            f"Generate detailed Markdown documentation for a Python class.\n\n"
            f"Class: {name}({bases_str})\n"
            f"Methods:\n  - {methods_list}\n"
            f"Existing docstring: {doc}\n\n"
            "Write a clear description of the class, its responsibilities, and usage. "
            "Include a subsection 'Methods' with a brief description for each method. "
            "Use ## heading for class title and ### for sections."
        )

    def _build_function_prompt(self, sig: str, returns: Optional[str], existing_doc: Optional[str]) -> str:
        ret_type = f" -> {returns}" if returns else ""
        doc = existing_doc or "(no docstring)"
        return (
            f"Generate clear, detailed Markdown documentation for a Python function.\n\n"
            f"Signature: {sig}{ret_type}\n"
            f"Existing docstring: {doc}\n\n"
            "Write a comprehensive docstring that includes:\n"
            "- A description of what the function does\n"
            "- Parameter descriptions (list each parameter with type and meaning)\n"
            "- Return value description\n"
            "- Any exceptions that may be raised\n"
            "Use separate paragraphs and bullet points. Do not include code fences."
        )

    def _call_ai(self, prompt: str, kind: str) -> str:
        """Call OpenAI API with retry logic (simplified)."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a technical writer generating API documentation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500,
            )
            content = response.choices[0].message.content.strip()
            return content
        except Exception as e:
            # In a real robust system, implement retries with backoff
            return f"**Error generating documentation:** {e}\n\nPlease check your API key and network connection."