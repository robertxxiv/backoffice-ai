from __future__ import annotations

import argparse

EMBEDDING_COST_PER_MILLION = 0.02
GENERATION_INPUT_COST_PER_MILLION = 0.25
GENERATION_OUTPUT_COST_PER_MILLION = 2.00


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate RAG indexing and query cost.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="Estimate embedding cost for reindexing.")
    index_parser.add_argument("--document-tokens", type=int, required=True, help="Approximate document token count.")
    index_parser.add_argument("--chunk-size", type=int, default=512, help="Chunk size.")
    index_parser.add_argument("--overlap", type=int, default=64, help="Chunk overlap.")

    query_parser = subparsers.add_parser("query", help="Estimate query-time embedding and generation cost.")
    query_parser.add_argument("--query-tokens", type=int, default=20, help="Approximate query token count.")
    query_parser.add_argument("--input-tokens", type=int, required=True, help="Generation input token count.")
    query_parser.add_argument("--output-tokens", type=int, required=True, help="Generation output token count.")
    query_parser.add_argument("--queries", type=int, default=1, help="Number of repeated queries.")

    args = parser.parse_args()

    if args.command == "index":
        embedded_tokens = estimate_embedded_tokens(args.document_tokens, args.chunk_size, args.overlap)
        cost = embedded_tokens / 1_000_000 * EMBEDDING_COST_PER_MILLION
        print("Index estimate")
        print(f"document_tokens: {args.document_tokens}")
        print(f"estimated_embedded_tokens: {embedded_tokens}")
        print(f"estimated_cost_usd: {cost:.8f}")
        return

    total_cost = estimate_query_cost(args.query_tokens, args.input_tokens, args.output_tokens) * args.queries
    print("Query estimate")
    print(f"query_count: {args.queries}")
    print(f"query_embedding_tokens_each: {args.query_tokens}")
    print(f"generation_input_tokens_each: {args.input_tokens}")
    print(f"generation_output_tokens_each: {args.output_tokens}")
    print(f"estimated_total_cost_usd: {total_cost:.8f}")


def estimate_embedded_tokens(document_tokens: int, chunk_size: int, overlap: int) -> int:
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
    if document_tokens <= 0:
        return 0
    if overlap <= 0:
        return document_tokens
    factor = chunk_size / (chunk_size - overlap)
    return round(document_tokens * factor)


def estimate_query_cost(query_tokens: int, input_tokens: int, output_tokens: int) -> float:
    embedding_cost = query_tokens / 1_000_000 * EMBEDDING_COST_PER_MILLION
    input_cost = input_tokens / 1_000_000 * GENERATION_INPUT_COST_PER_MILLION
    output_cost = output_tokens / 1_000_000 * GENERATION_OUTPUT_COST_PER_MILLION
    return embedding_cost + input_cost + output_cost


if __name__ == "__main__":
    main()
