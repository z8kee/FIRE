import json
from ollama import chat

class QueryParsing:
    def __init__(self,model="qwen2.5:3b-instruct"):
        self.model = model
    
    def parse(self, query, available_tickers):
        prompt = f"""
        You extract retrieval parameters from financial research queries.

        Available tickers:
        {", ".join(available_tickers)}

        Return ONLY valid JSON in this exact format:

        {{
            "tickers": [],
            "cutoff_datetime": null
        }}

        Rules:
        - Identify only companies explicitly referred to by the user.
        - Convert company names to their ticker.
        - Do NOT add related companies that were not requested.
        - Every ticker must come from the available ticker list.
        - If multiple companies are explicitly mentioned, return all of them.
        - If no company is identifiable, return [].
        - If the query specifies an "as of", "before", "by", or equivalent historical cutoff,
        convert it to ISO-8601 UTC.
        - A date without a specified time should use 23:59:59 UTC.
        - If there is no historical cutoff, return null.
        - Do not answer the user's question.
        - Do not provide explanations.

        Query:
        {query}
        """

        response = chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0}
        )

        before = json.loads(response.message.content)

        tickers = before.get("tickers", [])
        tickers = [ticker for ticker in tickers if ticker in available_tickers]
        cutoff = before.get("cutoff_datetime")

        return {"tickers": tickers,
                "cutoff_datetime": cutoff
        }