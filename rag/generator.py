import json
import re
from ollama import chat
from time import perf_counter

class Generator:
    def __init__(self, model):
        self.model = model
        self.prompt = """
        You are a financial research assistant.

        Answer the user's question using ONLY the evidence provided. Always provide metrics if evidence is sufficient for it.

        Rules:
        - Do not use outside knowledge.
        - Every factual claim must be supported by the supplied evidence.
        - Cite evidence using its ID, for example 'Company X has done this [1] with 14% of risk [2].
        - Never invent citation IDs.
        - If the evidence is insufficient to answer the question, say so.
        - Do not claim information that became available after the user's cutoff date.
        - Be concise and factual.

        Return ONLY valid JSON with this structure:

        {
            "answer": "your answer",
            "citations": [1, 2],
            "insufficient_evidence": false
        }
        """

    def generate(self, query, evidence):
        user_prompt = f"""
        Question:
        {query}

        Evidence:
        {evidence}
        """

        response = chat(model=self.model,
                        messages=[
                            {
                                "role":"system",
                                "content": self.prompt
                            },
                            {
                                "role": "user",
                                "content": user_prompt
                            }
                        ],
                        options={
                            "temperature": 0.18,
                            "num_predict": 350
                        },
                        format="json",
                        keep_alive="15m"
                    )

        print(
            "load:",
            response.load_duration / 1e9
        )

        print(
            "prompt eval:",
            response.prompt_eval_duration / 1e9
        )

        print(
            "generation:",
            response.eval_duration / 1e9
        )

        print(
            "prompt tokens:",
            response.prompt_eval_count
        )

        print(
            "generated tokens:",
            response.eval_count
        )

        if response.eval_count:
            print(
                "tokens/sec:",
                response.eval_count /
                (response.eval_duration / 1e9)
            )

        content = response.message.content.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r"\{.*\}", content, flags=re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass

            return {
                "answer": content,
                "citations": [],
                "insufficient_evidence": True
            }

class RAGPipeline:
    def __init__(self, retrieval_pipeline, generator):
        self.retrival = retrieval_pipeline
        self.generator = generator

    def format_evidence(self, results):
            blocks = []
    
            for i, result in enumerate(results, start=1):
                block = f"""
                [{i}] | {result["ticker"]} | {result["filing_type"]} | {result["filing_date"]} | {result["section"]}
                Text:
                {result["text"]}
                """
    
                blocks.append(block.strip())
    
            return "\n\n".join(blocks)

    def validate(self, response, count):
            citations = response.get("citations", [])
            valid = [citation for citation in citations if isinstance(citation, int)
                     and 1 <= citation <= count]
            response["citations"] = valid
    
            return response

    def ask(self, query):
        total = perf_counter()

        t = perf_counter()
        retrieval = self.retrival.search(query,final_limit=3)
        print("Retrieval:", perf_counter() - t)

        results = (retrieval.get("results", retrieval)
            if isinstance(retrieval, dict)
            else retrieval
        )

        if not results:
            return {
                "answer": "I could not find sufficient evidence.",
                "citations": [],
                "insufficient_evidence": True
            }

        t = perf_counter()
        evidence = self.format_evidence(results)
        print("Evidence formatting:", perf_counter() - t)

        t = perf_counter()
        response = self.generator.generate(query, evidence)
        print("Qwen:", perf_counter() - t)

        response = self.validate(response, len(results))

        response["evidence"] = results

        print("TOTAL:", perf_counter() - total)

        return response

