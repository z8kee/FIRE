import argparse
import os
import sys
from pathlib import Path

import dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
dotenv.load_dotenv(PROJECT_ROOT / ".env")

from database.connections import SECRepository
from retrieval.query_parser import QueryParsing


def main():
	parser = argparse.ArgumentParser(description="Test financial query parsing")
	parser.add_argument(
		"query",
		nargs="?",
		default="Compare the supply chain risks faced by Microsoft and Apple before 2022.",
	)
	parser.add_argument("--model", default="qwen2.5:3b-instruct")
	args = parser.parse_args()

	db = SECRepository(
		dbname="fire_rag",
		user="fire_user",
		password=os.getenv("POSTGRESPASS"),
	)

	try:
		available_tickers = db.get_tickers()
		result = QueryParsing(model=args.model).parse(args.query, available_tickers)

		print(f"Query: {args.query}")
		print(f"Available tickers: {len(available_tickers)}")
		print(f"Parsed parameters: {result}")
	finally:
		db.close()


if __name__ == "__main__":
	main()
