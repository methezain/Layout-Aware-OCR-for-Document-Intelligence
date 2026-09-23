import json

from openai import OpenAI

from app.schemas import ContractExtraction


def strict_json_schema(model: type[ContractExtraction]) -> dict:
    """Groq strict json_schema requires additionalProperties false on every object."""
    schema = model.model_json_schema()

    def mark(node):
        if isinstance(node, dict):
            if node.get("type") == "object" or "properties" in node:
                node["additionalProperties"] = False
            for value in node.values():
                mark(value)
        elif isinstance(node, list):
            for item in node:
                mark(item)

    mark(schema)
    return schema


def extract_contract(ocr_text: str, client: OpenAI, model: str) -> ContractExtraction:
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Extract target contract details strictly from the provided OCR text.",
            },
            {"role": "user", "content": ocr_text},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "ContractExtraction",
                "strict": True,
                "schema": strict_json_schema(ContractExtraction),
            },
        },
    )
    raw_content = completion.choices[0].message.content or "{}"
    return ContractExtraction.model_validate(json.loads(raw_content))
