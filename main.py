"""
Location Extraction Pipeline - Simplified Runner

This script extracts locations from text data using the EnsembleExtractionStrategy,
which combines multiple extraction methods with intelligent fallbacks.

Usage:
    python main.py                          # Run with default settings
    python main.py --input data.xlsx        # Specify input file
    python main.py --demo                   # Run demo with sample data
    python main.py --benchmark              # Run benchmark comparison
"""

import argparse
import time
from pathlib import Path
from typing import List

import pandas as pd

# Local imports
from location_extraction import (AhoCorasickStrategy, AUSTRALIAN_LOCATIONS, GazetteerRegexStrategy)
from location_extraction.strategies.extraction.ensemble_strategy import EnsembleExtractionStrategy

# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_CONFIG = {
    "input_file": "data/data_raw_2024-25.xlsx",
    "output_file": "data/location_results.xlsx",
    "text_columns": [
        "LINE_DESCR",
        "PURPOSE",
        "INVOICE_DESCR",
        "VENDOR_NAME",
        "CHARGE_DESCRIPTION",
    ],
    # Ensemble strategy settings
    "enable_aho_corasick": True,
    "enable_regex": True,
    "enable_spacy": True,
    "enable_phonetic": True,
    "enable_tfidf": False,  # Expensive, disabled by default
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def combine_text_columns(df: pd.DataFrame, columns: List[str], sep: str = " ") -> pd.Series:
    """Combine multiple text columns into a single string per row."""
    available_cols = [c for c in columns if c in df.columns]
    if not available_cols:
        raise ValueError(f"None of the columns {columns} found in dataframe")

    def join_row(row):
        parts = [str(v).strip() for v in row if pd.notna(v) and str(v).strip()]
        return sep.join(parts)

    return df[available_cols].apply(join_row, axis=1)


def extract_locations_from_dataframe(
        df: pd.DataFrame,
        strategy: EnsembleExtractionStrategy,
        text_columns: List[str],
        verbose: bool = True,
) -> pd.DataFrame:
    """
    Extract locations from a dataframe and return results.
    """
    combined_text = combine_text_columns(df, text_columns)
    results = []
    total = len(combined_text)

    if verbose:
        print(f"Processing {total} rows...")

    start_time = time.time()

    for i, text in enumerate(combined_text):
        extraction = strategy.extract_with_confidence(text)

        if extraction:
            best = extraction[0]
            result = {
                "row_index": i,
                "combined_text": text[:200] + "..." if len(text) > 200 else text,
                "location_found": best["location"],
                "confidence": best["confidence"],
                "sources": ", ".join(best["sources"]),
                "in_database": best["in_database"],
                "all_locations": ", ".join([e["location"] for e in extraction]),
                "num_locations": len(extraction),
            }
        else:
            result = {
                "row_index": i,
                "combined_text": text[:200] + "..." if len(text) > 200 else text,
                "location_found": None,
                "confidence": 0.0,
                "sources": "",
                "in_database": False,
                "all_locations": "",
                "num_locations": 0,
            }

        results.append(result)

        if verbose and (i + 1) % 100 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            remaining = (total - i - 1) / rate if rate > 0 else 0
            print(f"  Processed {i + 1}/{total} ({100 * (i + 1) / total:.1f}%) - ETA: {remaining:.0f}s")

    elapsed = time.time() - start_time
    if verbose:
        print(f"Completed in {elapsed:.1f}s ({total / elapsed:.1f} rows/sec)")

    results_df = pd.DataFrame(results)

    for col in text_columns:
        if col in df.columns:
            results_df[col] = df[col].values

    return results_df


def run_demo():
    """Run a demo with sample data."""
    print("=" * 60)
    print("LOCATION EXTRACTION DEMO")
    print("=" * 60)

    sample_texts = [
        "Client dinner at Crown Sydney with partners",
        "Flight to Melbourne for conference",
        "Team meeting in Brisbane CBD",
        "Taxi from Sydney airport to hotel",
        "Business lunch at Thai restaurant",
        "Conference in Cairns next week",
        "Travel to Perth for client meeting",
        "Meeting in Sydny office",  # Typo
        "Flight to Singapore via Brisbane",
        "Client visit to Alice Springs",
    ]

    print("\nInitializing EnsembleExtractionStrategy...")
    strategy = EnsembleExtractionStrategy(
        locations_db=AUSTRALIAN_LOCATIONS,
        enable_aho_corasick=True,
        enable_regex=True,
        enable_spacy=True,
        enable_phonetic=True,
    )

    print(f"Strategy status: {strategy.get_strategy_status()}")
    print(f"Locations database: {len(AUSTRALIAN_LOCATIONS)} entries")

    print("\n" + "-" * 60)
    print("EXTRACTION RESULTS")
    print("-" * 60)

    for text in sample_texts:
        results = strategy.extract_with_confidence(text)

        if results:
            best = results[0]
            print(f"\nText: {text}")
            print(f"  → Location: {best['location']} (conf: {best['confidence']:.2f})")
            print(f"  → Sources: {', '.join(best['sources'])}")
        else:
            print(f"\nText: {text}")
            print(f"  → No location found")

    found = sum(1 for t in sample_texts if strategy.extract(t))
    print("\n" + "-" * 60)
    print(f"SUMMARY: Found locations in {found}/{len(sample_texts)} texts ({100 * found / len(sample_texts):.1f}%)")


def run_benchmark():
    """Run benchmark comparing strategies."""
    print("=" * 60)
    print("STRATEGY BENCHMARK")
    print("=" * 60)

    test_texts = [
                     "Meeting in Sydney CBD tomorrow",
                     "Flight to Melbourne for conference",
                     "Client dinner at Crown Brisbane",
                     "Travel to Perth next week",
                     "Sydny office meeting",  # Typo
                 ] * 20

    strategies = [
        ("Ensemble (Full)", EnsembleExtractionStrategy(
            locations_db=AUSTRALIAN_LOCATIONS,
            enable_aho_corasick=True, enable_regex=True,
            enable_spacy=True, enable_phonetic=True,
        )),
        ("Ensemble (Fast)", EnsembleExtractionStrategy(
            locations_db=AUSTRALIAN_LOCATIONS,
            enable_aho_corasick=True, enable_regex=True,
            enable_spacy=False, enable_phonetic=False,
        )),
        ("Aho-Corasick", AhoCorasickStrategy(locations_db=AUSTRALIAN_LOCATIONS)),
        ("Regex", GazetteerRegexStrategy(locations_db=AUSTRALIAN_LOCATIONS)),
    ]

    results = []
    for name, strategy in strategies:
        print(f"\nBenchmarking: {name}...")

        start = time.time()
        found = sum(1 for t in test_texts if strategy.extract(t))
        elapsed = time.time() - start

        results.append({
            "Strategy": name,
            "Time (s)": round(elapsed, 3),
            "Texts/sec": round(len(test_texts) / elapsed, 1),
            "Found": found,
            "Rate": f"{100 * found / len(test_texts):.1f}%",
        })

    print("\n" + "=" * 60)
    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    return df


def main():
    parser = argparse.ArgumentParser(description="Location Extraction Pipeline")
    parser.add_argument("--demo", action="store_true", help="Run demo")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark")
    parser.add_argument("-i", "--input", type=str, help="Input Excel file")
    parser.add_argument("-o", "--output", type=str, help="Output Excel file")
    parser.add_argument("--columns", type=str, help="Comma-separated text columns")
    parser.add_argument("--no-spacy", action="store_true", help="Disable spaCy")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")

    args = parser.parse_args()

    if args.demo:
        run_demo()
        return

    if args.benchmark:
        run_benchmark()
        return

    # File processing mode
    input_file = args.input or DEFAULT_CONFIG["input_file"]
    output_file = args.output or DEFAULT_CONFIG["output_file"]
    text_columns = args.columns.split(",") if args.columns else DEFAULT_CONFIG["text_columns"]

    if not Path(input_file).exists():
        print(f"Error: Input file not found: {input_file}")
        print("Try: python main.py --demo")
        return

    df = pd.read_excel(input_file)
    print(f"Loaded {len(df)} rows from {input_file}")

    strategy = EnsembleExtractionStrategy(
        locations_db=AUSTRALIAN_LOCATIONS,
        enable_spacy=not args.no_spacy,
    )

    results_df = extract_locations_from_dataframe(df, strategy, text_columns, not args.quiet)

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    results_df.to_excel(output_file, index=False)

    found = results_df["location_found"].notna().sum()
    print(f"\nResults: {found}/{len(results_df)} locations found ({100 * found / len(results_df):.1f}%)")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    from location_extraction import AUSTRALIAN_LOCATIONS, EnsembleExtractionStrategy

    # Create the ensemble strategy (recommended)
    strategy = EnsembleExtractionStrategy(
        locations_db=AUSTRALIAN_LOCATIONS,
        enable_aho_corasick=True,  # Fast exact matching
        enable_regex=True,  # Pattern matching
        enable_spacy=True,  # NER extraction
        enable_phonetic=True,  # Typo tolerance
        enable_tfidf=True,  # Expensive, disable unless needed
    )

    # Simple extraction
    locations = strategy.extract("Meeting in Sydney tomorrow")
    # Returns: ['sydney']

    # Extraction with confidence scores
    results = strategy.extract_with_confidence("Flight from Sydny to Melborne")
    # Returns: [{'location': 'sydney', 'confidence': 0.85, 'sources': ['phonetic', 'aho_corasick'], ...}]

    # Get single best match
    best = strategy.extract_best("Conference in Brisbane", min_confidence=0.3)
    # Returns: 'brisbane'
