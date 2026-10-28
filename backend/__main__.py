import argparse
import os

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Run AutoQuote AI locally")
    parser.add_argument("--demo", action="store_true", help="Use clearly labelled sample results")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.demo:
        os.environ["AUTOQUOTE_DEMO"] = "1"
    uvicorn.run("backend.main:app", host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
