# Standard library imports
import time
from typing import List, Dict, Tuple, Optional, Sequence

# Third-party imports
import pandas as pd

# Local imports
from location_extraction import (
    AUSTRALIAN_LOCATIONS,
    LocationExtractor,
    LocationCache,
    LocationExtractionStrategy,
    GazetteerRegexStrategy,
    SklearnBoWStrategy,
    SklearnTfidfStrategy,
    AhoCorasickStrategy,
    PhoneticGazetteerStrategy,
    SpacyNerStrategy,
)

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG = {
    # File paths
    "raw_data_path": "data/data_raw_2024-25.xlsx",
    "wp_files": [
        "data/WP_1_Apr_to_Dec_24_FBT_ent_acc.xlsx",
        "data/WP_2_Apr_to_Dec_24_FBT_ent_acc.xlsx",
        "data/WP_3_Jan_to_Mar_25_FBT_ent_acc.xlsx",
        "data/WP_4_Jan_to_Mar_25_FBT_ent_acc.xlsx",
    ],
    # Classification mode: 'supervised' or 'unsupervised'
    "mode": "supervised",
    # Enable/disable features
    "enable_clustering": True,
    # Clustering settings
    "n_clusters": 8,
    # Model training
    "test_size": 0.2,
    "random_state": 42,
    "cv_folds": 5,
    # Text vectorization
    "max_features": 5000,
    "ngram_range": (1, 3),
    "min_df": 2,
    "max_df": 0.95,
    # Output paths
    "model_output": "fbt_classifier_pipeline.joblib",
    "encoder_output": "fbt_label_encoder.joblib",
    "predictions_output": "fbt_predictions.csv",
}

print("All imports successful")
print(f"Loaded {len(AUSTRALIAN_LOCATIONS)} locations in database")

available: List[tuple[str, LocationExtractionStrategy]] = []
skipped: List[tuple[str, str]] = []
allow_online_fallback = True


def try_add(name, ctor):
    try:
        s = ctor()
        available.append((name, s))
    except Exception as e:
        skipped.append((name, str(e)))


def _build_texts(
    *,
    texts: Optional[Sequence] = None,
    dataframe: Optional[pd.DataFrame] = None,
    text_columns: Optional[List[str]] = None,
    sep: str = " ",
) -> List[str]:
    if texts is not None:
        return ["" if pd.isna(t) else str(t) for t in texts]
    if dataframe is None or not text_columns:
        raise ValueError("Provide either `texts` or (`dataframe` and `text_columns`).")
    missing = [c for c in text_columns if c not in dataframe.columns]
    if missing:
        raise ValueError(f"Missing columns in dataframe: {missing}")

    def _join_row(row: pd.Series) -> str:
        parts = [str(v).strip() for v in row.values if pd.notna(v) and str(v).strip()]
        return sep.join(parts)

    return dataframe[text_columns].apply(_join_row, axis=1).tolist()


def _build_texts_column(df: pd.DataFrame, column: str) -> List[str]:
    vals = df[column].tolist()
    return ["" if pd.isna(v) else str(v) for v in vals]


def run_benchmark(
    available: List[Tuple[str, LocationExtractionStrategy]],
    texts: Optional[Sequence[str]] = None,
    repeats: int = 5,
    dataframe: Optional[pd.DataFrame] = None,
    text_columns: Optional[List[str]] = None,
    sep: str = " ",
    columnwise: bool = False,
    location_cache: Optional[LocationCache] = None,
) -> pd.DataFrame:
    """
    Benchmark extraction strategies. If `columnwise=True` and `dataframe`+`text_columns` provided,
    computes found/not-found per column and percent of columns found.

    Default behavior (columnwise=False) reports overall totals and percent across all input texts.
    """
    if columnwise:
        if dataframe is None or not text_columns:
            raise ValueError(
                "For columnwise mode, provide `dataframe` and `text_columns`."
            )
        # Validate columns
        miss = [c for c in text_columns if c not in dataframe.columns]
        if miss:
            raise ValueError(f"Missing columns in dataframe: {miss}")

        rows: List[Dict] = []
        for strat_name, strat in available:
            loc_extractor = LocationExtractor(strategy=strat, location_cache=location_cache)

            # Aggregate overall across all columns (row-column pairs)
            overall_pairs = 0
            overall_found_extracted = 0.0
            overall_found_geocoded = 0.0
            overall_confidence = 0.0
            overall_time = 0.0

            for col in text_columns:
                built_texts = _build_texts_column(dataframe, col)
                n_texts = len(built_texts)

                t0 = time.perf_counter()
                found_extracted_total = 0
                found_geocoded_total = 0
                found_confidence_total = 0.0
                texts_with_any_total = 0

                for _ in range(repeats):
                    texts_with_any_run = 0
                    for txt in built_texts:
                        matches = strat.extract(txt)
                        try:
                            extracted = len(matches)
                        except TypeError:
                            extracted = int(bool(matches))
                        found_extracted_total += extracted
                        feats = loc_extractor.extract_location_features(txt, allow_online_fallback=allow_online_fallback)
                        geocoded = int(feats.get("locations_found", 0))
                        found_geocoded_total += geocoded
                        found_confidence_total += feats.get("validation_confidence", 0.0)
                        if geocoded > 0:
                            texts_with_any_run += 1
                    texts_with_any_total += texts_with_any_run
                avg_time = (time.perf_counter() - t0) / repeats

                # Percent of rows in this column with any match per run (average)
                avg_texts_with_any = texts_with_any_total / repeats
                percent_found = (
                    ((avg_texts_with_any / n_texts) * 100) if n_texts else 0.0
                )

                rows.append(
                    {
                        "strategy": strat_name,
                        "column": col,
                        "texts": n_texts,
                        "avg_time_s": round(avg_time, 6),
                        "extracted_matches": round(found_extracted_total / repeats, 2),
                        "geocoded_matches": round(found_geocoded_total / repeats, 2),
                        "avg_confidence": round(found_confidence_total / repeats / n_texts, 4),
                        "texts_with_any": round(avg_texts_with_any, 2),
                        "percent_found": round(percent_found, 4),
                    }
                )

                # Update overall aggregates
                overall_pairs += n_texts
                overall_found_extracted += found_extracted_total / repeats
                overall_found_geocoded += found_geocoded_total / repeats
                overall_confidence += found_confidence_total / repeats
                overall_time += avg_time

            # Add an overall summary row per strategy
            overall_percent = (
                ((overall_found_geocoded / overall_pairs) * 100)
                if overall_pairs
                else 0.0
            )
            rows.append(
                {
                    "strategy": strat_name,
                    "column": "ALL",
                    "texts": int(overall_pairs),
                    "avg_time_s": round(overall_time / max(len(text_columns), 1), 6),
                    "extracted_matches": round(overall_found_extracted, 2),
                    "geocoded_matches": round(overall_found_geocoded, 2),
                    "avg_confidence": round(overall_confidence / overall_pairs, 4) if overall_pairs else 0.0,
                    "texts_with_any": round(overall_found_geocoded, 2),  # approx
                    "percent_found": round(overall_percent, 4),
                }
            )

        return pd.DataFrame(rows)

    # Fallback: existing behavior combining columns/texts
    built_texts = _build_texts(
        texts=texts, dataframe=dataframe, text_columns=text_columns, sep=sep
    )

    n_texts = len(built_texts)

    out_rows: List[Dict] = []
    for name, strat in available:
        loc_extractor = LocationExtractor(strategy=strat, location_cache=location_cache)
        t0 = time.perf_counter()
        found_extracted = 0
        found_geocoded = 0
        found_confidence = 0.0
        texts_with_any_total = 0
        for _ in range(repeats):
            texts_with_any_run = 0
            for txt in built_texts:
                matches = strat.extract(txt)
                try:
                    extracted = len(matches)
                except TypeError:
                    extracted = int(bool(matches))
                found_extracted += extracted
                feats = loc_extractor.extract_location_features(txt, allow_online_fallback=allow_online_fallback)
                geocoded = int(feats.get("locations_found", 0))
                found_geocoded += geocoded
                found_confidence += feats.get("validation_confidence", 0.0)
                if geocoded > 0:
                    texts_with_any_run += 1
            texts_with_any_total += texts_with_any_run
        avg_time = (time.perf_counter() - t0) / repeats
        avg_texts_with_any = texts_with_any_total / repeats
        match_rate = (avg_texts_with_any / n_texts) if n_texts else 0.0
        percent_found_overall = match_rate * 100
        out_rows.append(
            {
                "strategy": name,
                "mode": "extract+geocode",
                "texts": n_texts,
                "avg_time_s": round(avg_time, 6),
                "extracted_matches": round(found_extracted / repeats, 2),
                "geocoded_matches": round(found_geocoded / repeats, 2),
                "avg_confidence": round(found_confidence / repeats / n_texts, 4),
                "total_matches": round((found_extracted + found_geocoded) / repeats, 2),
                "match_rate": round(match_rate, 4),
                "percent_found_overall": round(percent_found_overall, 4),
            }
        )

    return pd.DataFrame(out_rows)


def test_location_extraction(
    available: List[Tuple[str, LocationExtractionStrategy]],
    texts: Optional[Sequence[str]] = None,
    dataframe: Optional[pd.DataFrame] = None,
    text_columns: Optional[List[str]] = None,
    sep: str = " ",
    per_row_single: bool = False,
    location_cache: Optional[LocationCache] = None,
) -> pd.DataFrame:
    built_texts = _build_texts(
        texts=texts, dataframe=dataframe, text_columns=text_columns, sep=sep
    )
    used_cols = text_columns or []

    if not per_row_single:
        out_rows: List[Dict] = []
        for name, strategy in available:
            loc_extractor = LocationExtractor(strategy=strategy, location_cache=location_cache)
            for i, txt in enumerate(built_texts):
                feats = loc_extractor.extract_location_features(txt, allow_online_fallback=allow_online_fallback)
                row = dict(feats)
                row.update(
                    {
                        "row_index": i,
                        "strategy": name,
                    }
                )
                # Attach original column values per row when dataframe is provided
                if dataframe is not None and used_cols:
                    try:
                        src = dataframe.iloc[i]
                        for c in used_cols:
                            row[c] = src.get(c, None)
                    except Exception:
                        for c in used_cols:
                            row[c] = None
                out_rows.append(row)
        return pd.DataFrame(out_rows)

    # Pre-build extractors to reuse across rows (preserves in-memory cache)
    extractors = {
        name: LocationExtractor(strategy=strategy, location_cache=location_cache)
        for name, strategy in available
    }

    out_rows: List[Dict] = []
    for i, txt in enumerate(built_texts):
        chosen_feats: Optional[Dict] = None
        chosen_strategy: Optional[str] = None
        for name, strategy in available:
            feats = extractors[name].extract_location_features(txt, allow_online_fallback=allow_online_fallback)
            if int(feats.get("locations_found", 0)) > 0:
                chosen_feats = dict(feats)
                chosen_strategy = name
                break
        if chosen_feats is None:
            if available:
                name0, strategy0 = available[0]
                chosen_feats = dict(extractors[name0].extract_location_features(txt, allow_online_fallback=allow_online_fallback))
                chosen_strategy = name0
            else:
                chosen_feats = {}
                chosen_strategy = None
        row = dict(chosen_feats)
        row.update(
            {
                "row_index": i,
                "selected_strategy": chosen_strategy,
            }
        )
        if dataframe is not None and used_cols:
            try:
                src = dataframe.iloc[i]
                for c in used_cols:
                    row[c] = src.get(c, None)
            except Exception:
                for c in used_cols:
                    row[c] = None
        out_rows.append(row)

    return pd.DataFrame(out_rows)

try_add(
    "Gazetteer Regex",
    lambda: GazetteerRegexStrategy(locations_db=AUSTRALIAN_LOCATIONS),
)

try_add(
    "Sklearn BoW",
    lambda: SklearnBoWStrategy(
        locations_db=AUSTRALIAN_LOCATIONS,
        ngram_range=(1, 3),
        min_df=1,
        max_df=0.9,
        max_features=5000,
    ),
)

try_add(
    "Sklearn TF-IDF",
    lambda: SklearnTfidfStrategy(
        locations_db=AUSTRALIAN_LOCATIONS,
        ngram_range=(1, 3),
        min_df=1,
        max_df=0.9,
        max_features=5000,
    ),
)

try_add(
    "Aho-Corasick",
    lambda: AhoCorasickStrategy(locations_db=AUSTRALIAN_LOCATIONS),
)

try_add(
    "Phonetic Gazetteer",
    lambda: PhoneticGazetteerStrategy(
        locations_db=AUSTRALIAN_LOCATIONS,
        distance_threshold=3,  # Increased from 2 for more matches
    ),
)

try_add(
    "SpacyNER (Small Model)",
    lambda: SpacyNerStrategy(
        locations_db=AUSTRALIAN_LOCATIONS,  # Reverted to filter to known Australian locations
        model_name="en_core_web_sm",
        models_preference=[
            "en_core_web_sm",
        ],
    ),
)

try_add(
    "SpacyNER (Transformer Pipeline Model)",
    lambda: SpacyNerStrategy(
        locations_db=AUSTRALIAN_LOCATIONS,  # Reverted to filter to known Australian locations
        model_name="en_core_web_trf",
        models_preference=[
            "en_core_web_trf",
        ],
    ),
)

def main():
    # Read data from excel files
    df = pd.read_excel(CONFIG["raw_data_path"])
    text_columns = [
        "LINE_DESCR",
        "PURPOSE",
        "INVOICE_DESCR",
        "VENDOR_NAME",
        "CHARGE_DESCRIPTION",
    ]

    # Initialize persistent location cache
    loc_cache = LocationCache(cache_dir="data")
    print(f"Location cache loaded: {loc_cache.get_stats()['total_entries']} cached entries, "
          f"{loc_cache.get_stats()['overrides']} overrides")

    df_bm_all = run_benchmark(
        available=available,
        texts=None,
        repeats=5,
        dataframe=df,
        text_columns=text_columns,
        location_cache=loc_cache,
    )
    print("Strategy Benchmark (lower time is better):")
    print(df_bm_all)
    df_bm_all.to_excel("data/location_extraction_benchmark.xlsx", index=False)

    print("Included strategies:", [n for n, _ in available])
    if skipped:
        print("Skipped strategies (reason):")
        for n, r in skipped:
            print(" -", n, "->", r)

    df_location_features = test_location_extraction(
        available=available,
        texts=None,
        dataframe=df,
        text_columns=text_columns,
        location_cache=loc_cache,
    )
    print("Location Extraction Results:")
    print(df_location_features)

    # Store in excel file with text columns and strategy info
    df_location_features.to_excel(
        "data/location_features_with_text_columns.xlsx", index=False
    )

    # Persist cache and print summary
    loc_cache.save()

    stats = loc_cache.get_stats()
    print("\n=== Location Cache Summary ===")
    print(f"Total cached entries: {stats['total_entries']}")
    print(f"  Resolved:   {stats['resolved']}")
    print(f"  Unresolved: {stats['unresolved']}")
    print(f"  Overrides:  {stats['overrides']}")
    print(f"Total lookups: {stats['total_lookups']}")
    if stats['sources']:
        print("  Sources:", stats['sources'])

    top = loc_cache.get_top_locations(10)
    if top:
        print("\n=== Top 10 Locations (by frequency) ===")
        for entry in top:
            name = entry.get("display_name") or entry["key"]
            print(f"  {name:<45s}  {entry['hit_count']:>4d} hits")

    unresolved = loc_cache.get_unresolved()
    if unresolved:
        print(f"\n=== Unresolved Review Queue ({len(unresolved)} entries) ===")
        print("  Fix the top ones in data/location_overrides.json for maximum impact.")
        for entry in unresolved[:20]:
            print(f"  {entry['key']:<45s}  {entry['hit_count']:>4d} hits")


if __name__ == "__main__":
    main()