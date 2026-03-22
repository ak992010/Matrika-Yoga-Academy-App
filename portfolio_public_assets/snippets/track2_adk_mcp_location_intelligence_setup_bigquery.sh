#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCS_ROOT="$(cd "$PROJECT_ROOT/../.." && pwd)"

resolve_bin() {
    local name="$1"
    local candidate="$2"
    if command -v "$name" >/dev/null 2>&1; then
        command -v "$name"
        return 0
    fi
    if [ -x "$candidate" ]; then
        printf '%s\n' "$candidate"
        return 0
    fi
    printf 'Error: could not find %s. Install Google Cloud SDK or add it to PATH.\n' "$name" >&2
    exit 1
}

GCLOUD_BIN="$(resolve_bin gcloud "$DOCS_ROOT/tools/google-cloud-sdk/bin/gcloud")"
BQ_BIN="$(resolve_bin bq "$DOCS_ROOT/tools/google-cloud-sdk/bin/bq")"

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-$("$GCLOUD_BIN" config get-value project 2>/dev/null)}"
DATASET_NAME="${LOCATION_INTELLIGENCE_DATASET:-location_intelligence_demo}"
LOCATION="${BIGQUERY_LOCATION:-US}"
BUCKET_NAME="${1:-gs://${PROJECT_ID}-location-intelligence-data}"

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
    echo "Error: Could not determine Google Cloud project."
    echo "Run: $GCLOUD_BIN config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "----------------------------------------------------------------"
echo "Location Intelligence BigQuery Setup"
echo "Project: $PROJECT_ID"
echo "Dataset: $DATASET_NAME"
echo "Bucket:  $BUCKET_NAME"
echo "----------------------------------------------------------------"

if "$GCLOUD_BIN" storage buckets describe "$BUCKET_NAME" >/dev/null 2>&1; then
    echo "[1/7] Bucket already exists."
else
    echo "[1/7] Creating bucket $BUCKET_NAME..."
    "$GCLOUD_BIN" storage buckets create "$BUCKET_NAME" --location="$LOCATION"
fi

echo "[2/7] Uploading CSV files..."
"$GCLOUD_BIN" storage cp "$PROJECT_ROOT"/data/*.csv "$BUCKET_NAME"

if "$BQ_BIN" show "$PROJECT_ID:$DATASET_NAME" >/dev/null 2>&1; then
    echo "[3/7] Dataset already exists."
else
    echo "[3/7] Creating dataset $PROJECT_ID:$DATASET_NAME..."
    "$BQ_BIN" mk --location="$LOCATION" --dataset "$PROJECT_ID:$DATASET_NAME"
fi

echo "[4/7] Creating demographics table..."
"$BQ_BIN" query --use_legacy_sql=false "
CREATE OR REPLACE TABLE \`$PROJECT_ID.$DATASET_NAME.demographics\` (
    zip_code STRING OPTIONS(description='5-digit US zip code'),
    city STRING OPTIONS(description='City name'),
    neighborhood STRING OPTIONS(description='Neighborhood name'),
    median_household_income INT64 OPTIONS(description='Median household income in USD'),
    total_population INT64 OPTIONS(description='Total population'),
    median_age FLOAT64 OPTIONS(description='Median age'),
    bachelors_degree_pct FLOAT64 OPTIONS(description='Percentage with a bachelors degree or higher'),
    foot_traffic_index FLOAT64 OPTIONS(description='Composite foot traffic index')
)
OPTIONS(description='Neighborhood demographic signals for site selection.');"

"$BQ_BIN" load --source_format=CSV --skip_leading_rows=1 --replace \
    "$PROJECT_ID:$DATASET_NAME.demographics" \
    "$BUCKET_NAME/demographics.csv"

echo "[5/7] Creating bakery_prices table..."
"$BQ_BIN" query --use_legacy_sql=false "
CREATE OR REPLACE TABLE \`$PROJECT_ID.$DATASET_NAME.bakery_prices\` (
    store_name STRING OPTIONS(description='Competitor bakery or retailer'),
    product_type STRING OPTIONS(description='Type of baked good'),
    price FLOAT64 OPTIONS(description='Unit price in USD'),
    region STRING OPTIONS(description='Geographic region'),
    is_organic BOOL OPTIONS(description='Whether the product is organic')
)
OPTIONS(description='Competitive pricing signals for bakery products.');"

"$BQ_BIN" load --source_format=CSV --skip_leading_rows=1 --replace \
    "$PROJECT_ID:$DATASET_NAME.bakery_prices" \
    "$BUCKET_NAME/bakery_prices.csv"

echo "[6/7] Creating sales_history_weekly table..."
"$BQ_BIN" query --use_legacy_sql=false "
CREATE OR REPLACE TABLE \`$PROJECT_ID.$DATASET_NAME.sales_history_weekly\` (
    week_start_date DATE OPTIONS(description='Week start date'),
    store_location STRING OPTIONS(description='Store location'),
    product_type STRING OPTIONS(description='Product category'),
    quantity_sold INT64 OPTIONS(description='Units sold'),
    total_revenue FLOAT64 OPTIONS(description='Total revenue in USD')
)
OPTIONS(description='Historical weekly sales data for revenue projection.');"

"$BQ_BIN" load --source_format=CSV --skip_leading_rows=1 --replace \
    "$PROJECT_ID:$DATASET_NAME.sales_history_weekly" \
    "$BUCKET_NAME/sales_history_weekly.csv"

echo "[7/7] Creating foot_traffic table..."
"$BQ_BIN" query --use_legacy_sql=false "
CREATE OR REPLACE TABLE \`$PROJECT_ID.$DATASET_NAME.foot_traffic\` (
    zip_code STRING OPTIONS(description='5-digit US zip code'),
    time_of_day STRING OPTIONS(description='morning, afternoon, or evening'),
    foot_traffic_score FLOAT64 OPTIONS(description='Synthetic foot traffic score')
)
OPTIONS(description='Foot traffic by zip code and time of day.');"

"$BQ_BIN" load --source_format=CSV --skip_leading_rows=1 --replace \
    "$PROJECT_ID:$DATASET_NAME.foot_traffic" \
    "$BUCKET_NAME/foot_traffic.csv"

echo "----------------------------------------------------------------"
echo "Setup complete."
echo "----------------------------------------------------------------"

