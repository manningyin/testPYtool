import pandas as pd
from pathlib import Path

# ===== CONFIG =====
input_file = "input.csv"      # change to your file path
output_dir = "fxrate_output"  # folder for output files

# ===== READ INPUT =====
# For CSV:
df = pd.read_csv(input_file)

# If your source is Excel, use this instead:
# df = pd.read_excel("input.xlsx")

# Clean column names
df.columns = df.columns.str.strip()

# Keep only needed columns
df = df[["EOD_DATE", "CURRENCY_ID", "PRICE"]].copy()

# Convert date column
df["EOD_DATE"] = pd.to_datetime(df["EOD_DATE"], errors="coerce")

# Remove bad rows
df = df.dropna(subset=["EOD_DATE", "CURRENCY_ID", "PRICE"])

# Create output folder
Path(output_dir).mkdir(parents=True, exist_ok=True)

# ===== SPLIT AND SAVE =====
for currency, group in df.groupby("CURRENCY_ID"):
    # Sort by date ascending
    group = group.sort_values("EOD_DATE").copy()

    # Format output exactly as requested
    out = pd.DataFrame({
        "Date": group["EOD_DATE"].dt.strftime("%-m/%-d/%Y"),  # Linux / Mac
        "Spot": group["PRICE"]
    })

    # For Windows, use this instead of the line above:
    # "Date": group["EOD_DATE"].dt.strftime("%#m/%#d/%Y")

    output_file = Path(output_dir) / f"{currency}_FxRate.csv"
    out.to_csv(output_file, index=False)

    print(f"Saved: {output_file}")