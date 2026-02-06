"""
Location Extraction Pipeline - Full Feature Extraction with Ensemble Strategy

This script extracts locations from text data using the EnsembleExtractionStrategy,
combines it with the LocationExtractor for geocoding and feature calculation,
and outputs comprehensive location features with original text columns.

Usage:
    python main.py                              # Run with default settings
    python main.py --input data.xlsx            # Specify input file
    python main.py --output results.xlsx        # Specify output file
    python main.py --demo                       # Run demo with sample data
    python main.py --benchmark                  # Run benchmark comparison
    python main.py --no-cache                   # Disable location caching
"""

import argparse
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# Local imports
from location_extraction import (
    AUSTRALIAN_LOCATIONS,
    LocationExtractor,
    LocationCache,
    LocationValidator,
    GazetteerRegexStrategy,
    AhoCorasickStrategy,
    NominatimGeocodingStrategy,
    GoogleSearchGeocodingStrategy,
)
from location_extraction.strategies.extraction.ensemble_strategy import EnsembleExtractionStrategy

# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_CONFIG = {
    "input_file": "data/data_raw_2024-25.xlsx",
    "output_file": "data/location_features_with_text_columns.xlsx",
    "cache_dir": "data",
    "text_columns": [
        "LINE_DESCR",
        "PURPOSE",
        "INVOICE_DESCR",
        "VENDOR_NAME",
        "CHARGE_DESCRIPTION",
    ],
    # Reference location (Sydney CBD by default)
    "reference_location": {
        "lat": -33.8688,
        "lon": 151.2093,
        "name": "Sydney CBD",
    },
    # Ensemble strategy settings
    "enable_aho_corasick": True,
    "enable_regex": True,
    "enable_spacy": True,
    "enable_phonetic": True,
    "enable_tfidf": False,  # Expensive, disabled by default
    "enable_bow": False,
    # Geocoding settings
    "enable_online_geocoding": True,
    "enable_cache": True,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def combine_text_columns(df: pd.DataFrame, columns: List[str], sep: str = " | ") -> pd.Series:
    """Combine multiple text columns into a single string per row."""
    available_cols = [c for c in columns if c in df.columns]
    if not available_cols:
        raise ValueError(f"None of the columns {columns} found in dataframe")

    def join_row(row):
        parts = [str(v).strip() for v in row if pd.notna(v) and str(v).strip()]
        return sep.join(parts)

    return df[available_cols].apply(join_row, axis=1)


def create_ensemble_extractor(
    config: Dict,
    location_cache: Optional[LocationCache] = None,
) -> LocationExtractor:
    """
    Create a LocationExtractor with EnsembleExtractionStrategy.

    This combines:
    - EnsembleExtractionStrategy for intelligent multi-tier extraction
    - LocationExtractor for geocoding and feature calculation
    - LocationCache for persistent caching
    """
    # Create ensemble extraction strategy
    ensemble_strategy = EnsembleExtractionStrategy(
        locations_db=AUSTRALIAN_LOCATIONS,
        enable_aho_corasick=config.get("enable_aho_corasick", True),
        enable_regex=config.get("enable_regex", True),
        enable_spacy=config.get("enable_spacy", True),
        enable_phonetic=config.get("enable_phonetic", True),
        enable_tfidf=config.get("enable_tfidf", False),
        enable_bow=config.get("enable_bow", False),
    )

    # Create geocoding strategy (chained: Google Search refinement -> Nominatim)
    geocoding_strategy = None
    if config.get("enable_online_geocoding", True):
        geocoding_strategy = GoogleSearchGeocodingStrategy(
            inner=NominatimGeocodingStrategy(country_hint="Australia"),
            locations_db=AUSTRALIAN_LOCATIONS,
        )

    # Create the extractor
    extractor = LocationExtractor(
        reference_location=config.get("reference_location", DEFAULT_CONFIG["reference_location"]),
        strategy=ensemble_strategy,
        geocoding_strategy=geocoding_strategy,
        location_cache=location_cache,
    )

    return extractor


def extract_location_features_dataframe(
    df: pd.DataFrame,
    extractor: LocationExtractor,
    ensemble_strategy: EnsembleExtractionStrategy,
    text_columns: List[str],
    verbose: bool = True,
    allow_online_fallback: bool = False,
) -> pd.DataFrame:
    """
    Extract location features from a dataframe and return comprehensive results.

    Returns a dataframe with:
    - All original text columns
    - Combined text column
    - Extracted locations with confidence scores
    - Geocoded coordinates
    - Distance/travel features
    - Validation results
    """
    combined_text = combine_text_columns(df, text_columns)
    results = []
    total = len(combined_text)

    if verbose:
        print(f"Processing {total} rows...")
        print(f"Ensemble strategy status: {ensemble_strategy.get_strategy_status()}")

    start_time = time.time()
    found_count = 0

    for i, text in enumerate(combined_text):
        # Get ensemble extraction with confidence
        ensemble_results = ensemble_strategy.extract_with_confidence(text)

        # Get full location features from extractor (includes geocoding)
        features = extractor.extract_location_features(
            text,
            allow_online_fallback=allow_online_fallback
        )

        # Build result row
        result = {
            "row_index": i,
            "combined_text": text,
        }

        # Add original text columns
        for col in text_columns:
            if col in df.columns:
                result[col] = df.iloc[i][col]

        # Add ensemble-specific fields
        if ensemble_results:
            best = ensemble_results[0]
            result["ensemble_location"] = best["location"]
            result["ensemble_confidence"] = best["confidence"]
            result["ensemble_sources"] = ", ".join(best["sources"])
            result["ensemble_in_database"] = best["in_database"]
            result["ensemble_all_locations"] = ", ".join([e["location"] for e in ensemble_results])
            result["ensemble_num_locations"] = len(ensemble_results)
        else:
            result["ensemble_location"] = None
            result["ensemble_confidence"] = 0.0
            result["ensemble_sources"] = ""
            result["ensemble_in_database"] = False
            result["ensemble_all_locations"] = ""
            result["ensemble_num_locations"] = 0

        # Add all features from LocationExtractor
        result.update(features)

        results.append(result)

        if features.get("locations_found", 0) > 0:
            found_count += 1

        # Progress reporting
        if verbose and (i + 1) % 100 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            remaining = (total - i - 1) / rate if rate > 0 else 0
            pct_found = 100 * found_count / (i + 1)
            print(f"  Processed {i + 1}/{total} ({100 * (i + 1) / total:.1f}%) "
                  f"- Found: {pct_found:.1f}% - ETA: {remaining:.0f}s")

    elapsed = time.time() - start_time
    if verbose:
        print(f"\nCompleted in {elapsed:.1f}s ({total / elapsed:.1f} rows/sec)")
        print(f"Locations found: {found_count}/{total} ({100 * found_count / total:.1f}%)")

    return pd.DataFrame(results)


def run_demo():
    """Run a demo with sample data."""
    print("=" * 70)
    print("LOCATION EXTRACTION DEMO - ENSEMBLE + FULL FEATURES")
    print("=" * 70)

    sample_texts = [
        "Client dinner at Crown Sydney with partners",
        "Flight to Melbourne for conference",
        "Team meeting in Brisbane CBD",
        "Taxi from Sydney airport to hotel",
        "Business lunch at Thai restaurant",
        "Conference in Cairns next week",
        "Travel to Perth for client meeting",
        "Meeting in Sydny office",  # Typo - should catch with phonetic
        "Flight to Singapore via Brisbane",
        "Client visit to Alice Springs",
        "Accommodation at Park Hyatt Sydney",
        "Meal at Quay restaurant",
        "Trip to Broken Hill for site inspection",
        "International conference in Tokyo",
    ]

    print("\nInitializing EnsembleExtractionStrategy...")
    ensemble_strategy = EnsembleExtractionStrategy(
        locations_db=AUSTRALIAN_LOCATIONS,
        enable_aho_corasick=True,
        enable_regex=True,
        enable_spacy=True,
        enable_phonetic=True,
        enable_tfidf=False,
    )

    print(f"Strategy status: {ensemble_strategy.get_strategy_status()}")
    print(f"Locations database: {len(AUSTRALIAN_LOCATIONS)} entries")

    # Create full extractor (without cache for demo)
    extractor = LocationExtractor(
        reference_location=DEFAULT_CONFIG["reference_location"],
        strategy=ensemble_strategy,
        geocoding_strategy=None,  # Use DB only for demo
        location_cache=None,
    )

    print("\n" + "-" * 70)
    print("EXTRACTION RESULTS WITH FULL FEATURES")
    print("-" * 70)

    for text in sample_texts:
        # Ensemble results
        ensemble_results = ensemble_strategy.extract_with_confidence(text)

        # Full features
        features = extractor.extract_location_features(text)

        print(f"\nText: {text}")

        if ensemble_results:
            best = ensemble_results[0]
            print(f"  Ensemble → {best['location']} (conf: {best['confidence']:.2f}, "
                  f"sources: {', '.join(best['sources'])})")
        else:
            print(f"  Ensemble → No location found")

        if features.get("locations_found", 0) > 0:
            print(f"  Features → Primary: {features.get('primary_location', 'N/A')}")
            print(f"             State: {features.get('primary_state', 'N/A')}, "
                  f"Type: {features.get('travel_category', 'N/A')}")
            if not np.isnan(features.get("distance_from_ref_km", np.nan)):
                print(f"             Distance: {features.get('distance_from_ref_km', 0):.1f} km, "
                      f"Travel: {features.get('estimated_travel_hours', 0):.1f} hrs")
            print(f"             Validation: {features.get('validation_confidence', 0):.2f} "
                  f"({'Valid' if features.get('is_valid_location') else 'Invalid'})")

    # Summary stats
    found = sum(1 for t in sample_texts if ensemble_strategy.extract(t))
    print("\n" + "-" * 70)
    print(f"SUMMARY: Found locations in {found}/{len(sample_texts)} texts "
          f"({100 * found / len(sample_texts):.1f}%)")


def run_benchmark():
    """Run benchmark comparing strategies."""
    print("=" * 70)
    print("STRATEGY BENCHMARK")
    print("=" * 70)

    test_texts = [
        "Meeting in Sydney CBD tomorrow",
        "Flight to Melbourne for conference",
        "Client dinner at Crown Brisbane",
        "Travel to Perth next week",
        "Sydny office meeting",  # Typo
        "Accommodation in Cairns",
        "Site visit to Alice Springs",
        "Conference at Park Hyatt",
        "Business lunch Quay restaurant",
        "International travel to Singapore",
    ] * 10  # 100 texts total

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
        ("Ensemble (Spacy+Phonetic)", EnsembleExtractionStrategy(
            locations_db=AUSTRALIAN_LOCATIONS,
            enable_aho_corasick=False, enable_regex=False,
            enable_spacy=True, enable_phonetic=True,
        )),
        ("Aho-Corasick Only", AhoCorasickStrategy(locations_db=AUSTRALIAN_LOCATIONS)),
        ("Regex Only", GazetteerRegexStrategy(locations_db=AUSTRALIAN_LOCATIONS)),
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

    print("\n" + "=" * 70)
    print("BENCHMARK RESULTS")
    print("=" * 70)
    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    return df


def process_file(
    input_file: str,
    output_file: str,
    text_columns: List[str],
    config: Dict,
    verbose: bool = True,
):
    """Process an Excel file and output location features."""

    # Load input data
    if verbose:
        print(f"Loading data from {input_file}...")

    df = pd.read_excel(input_file)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    # Show available columns
    available_text_cols = [c for c in text_columns if c in df.columns]
    if verbose:
        print(f"Text columns found: {available_text_cols}")
        missing = [c for c in text_columns if c not in df.columns]
        if missing:
            print(f"Text columns missing: {missing}")

    if not available_text_cols:
        raise ValueError(f"No text columns found in {input_file}")

    # Initialize cache
    location_cache = None
    if config.get("enable_cache", True):
        cache_dir = config.get("cache_dir", "data")
        location_cache = LocationCache(cache_dir=cache_dir)
        if verbose:
            stats = location_cache.get_stats()
            print(f"Location cache: {stats['total_entries']} entries, "
                  f"{stats['resolved']} resolved, {stats['overrides']} overrides")

    # Create ensemble strategy
    ensemble_strategy = EnsembleExtractionStrategy(
        locations_db=AUSTRALIAN_LOCATIONS,
        enable_aho_corasick=config.get("enable_aho_corasick", True),
        enable_regex=config.get("enable_regex", True),
        enable_spacy=config.get("enable_spacy", True),
        enable_phonetic=config.get("enable_phonetic", True),
        enable_tfidf=config.get("enable_tfidf", False),
        enable_bow=config.get("enable_bow", False),
    )

    if verbose:
        print(f"Ensemble strategy: {ensemble_strategy.get_strategy_status()}")

    # Create extractor
    extractor = create_ensemble_extractor(config, location_cache)

    # Extract features
    results_df = extract_location_features_dataframe(
        df=df,
        extractor=extractor,
        ensemble_strategy=ensemble_strategy,
        text_columns=available_text_cols,
        verbose=verbose,
        allow_online_fallback=config.get("enable_online_geocoding", False),
    )

    # Save cache
    if location_cache is not None:
        location_cache.save()
        if verbose:
            stats = location_cache.get_stats()
            print(f"Cache updated: {stats['total_entries']} entries, "
                  f"{stats['total_lookups']} total lookups")

    # Ensure output directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    # Save results
    results_df.to_excel(output_file, index=False)

    # Print summary
    found = results_df["locations_found"].gt(0).sum()
    validated = results_df["is_valid_location"].sum() if "is_valid_location" in results_df.columns else 0

    print("\n" + "=" * 70)
    print("EXTRACTION SUMMARY")
    print("=" * 70)
    print(f"Total rows:          {len(results_df)}")
    print(f"Locations found:     {found} ({100 * found / len(results_df):.1f}%)")
    print(f"Validated locations: {validated} ({100 * validated / len(results_df):.1f}%)")
    print(f"Output saved to:     {output_file}")

    # Show travel category breakdown
    if "travel_category" in results_df.columns:
        print("\nTravel Category Breakdown:")
        category_counts = results_df["travel_category"].value_counts()
        for cat, count in category_counts.items():
            print(f"  {cat}: {count} ({100 * count / len(results_df):.1f}%)")

    return results_df


def main():
    parser = argparse.ArgumentParser(
        description="Location Extraction Pipeline with Ensemble Strategy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --demo                    Run demo with sample data
  python main.py --benchmark               Run strategy benchmark
  python main.py -i data.xlsx -o out.xlsx  Process file
  python main.py --no-spacy                Disable spaCy (faster)
  python main.py --enable-tfidf            Enable TF-IDF (expensive)
        """
    )

    # Mode selection
    parser.add_argument("--demo", action="store_true", help="Run demo with sample data")
    parser.add_argument("--benchmark", action="store_true", help="Run strategy benchmark")

    # File options
    parser.add_argument("-i", "--input", type=str, help="Input Excel file")
    parser.add_argument("-o", "--output", type=str, help="Output Excel file")
    parser.add_argument("--columns", type=str, help="Comma-separated text columns")

    # Strategy options
    parser.add_argument("--no-spacy", action="store_true", help="Disable spaCy NER")
    parser.add_argument("--no-phonetic", action="store_true", help="Disable phonetic matching")
    parser.add_argument("--enable-tfidf", action="store_true", help="Enable TF-IDF (expensive)")
    parser.add_argument("--enable-bow", action="store_true", help="Enable Bag-of-Words")

    # Cache options
    parser.add_argument("--no-cache", action="store_true", help="Disable location caching")
    parser.add_argument("--cache-dir", type=str, default="data", help="Cache directory")

    # Output options
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")

    args = parser.parse_args()

    # Demo mode
    if args.demo:
        run_demo()
        return

    # Benchmark mode
    if args.benchmark:
        run_benchmark()
        return

    # File processing mode
    config = dict(DEFAULT_CONFIG)

    # Override config from args
    if args.columns:
        config["text_columns"] = [c.strip() for c in args.columns.split(",")]
    if args.no_spacy:
        config["enable_spacy"] = False
    if args.no_phonetic:
        config["enable_phonetic"] = False
    if args.enable_tfidf:
        config["enable_tfidf"] = True
    if args.enable_bow:
        config["enable_bow"] = True
    if args.no_cache:
        config["enable_cache"] = False
    if args.cache_dir:
        config["cache_dir"] = args.cache_dir

    input_file = args.input or config["input_file"]
    output_file = args.output or config["output_file"]

    # Check input file exists
    if not Path(input_file).exists():
        print(f"Error: Input file not found: {input_file}")
        print("\nTry one of:")
        print("  python main.py --demo       # Run demo")
        print("  python main.py --benchmark  # Run benchmark")
        print(f"  python main.py -i <your_file.xlsx>")
        return

    # Process file
    process_file(
        input_file=input_file,
        output_file=output_file,
        text_columns=config["text_columns"],
        config=config,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()