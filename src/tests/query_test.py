import argparse, os, sys, time
from pathlib import Path

import dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
dotenv.load_dotenv(PROJECT_ROOT / ".env")

from database.connections import SECRepository
from retrieval.query_parser import QueryParser


def main():
	parser = argparse.ArgumentParser(description="Test financial query parsing")
	parser.add_argument(
		"query",
		nargs="?",
		default="What was microsoft's revenue in 2023?",
	)
	parser.add_argument("--model", default="qwen2.5:3b")
	args = parser.parse_args()

	db = SECRepository(
		dbname="fire_rag",
		user="fire_user",
		password=os.getenv("POSTGRESPASS"),
	)

	try:
		companies = db.get_companies()
		parsing = QueryParser(companies)
		parsed = parsing.parse(args.query)
		return parsed
	finally:
		db.close()


if __name__ == "__main__":
	s = time.time()
	r = main()
	print(
		f"raw query : {r['raw_query']} \n"
		f"tickers: {r['tickers']} \n"
		f"cutoff: {r['cutoff_datetime']}")
	e = time.time()
	print("latency is ", e-s, "seconds")
