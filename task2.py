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
import pandas as pd
from pathlib import Path
import re

# ===== CONFIG =====
input_file = "input2.xlsx"            # input workbook
sheet_name = "Sheet1"                 # data sheet
output_dir = "interest_rate_output"   # folder for output files

# ===== READ INPUT =====
df = pd.read_excel(input_file, sheet_name=sheet_name)

# Clean column names
df.columns = df.columns.astype(str).str.strip()

# Handle duplicated Excel column names like INTEREST_ID.1, TERM_ID.1, etc.
# We only need these columns:
required_cols = ["EOD_DATE", "CURRENCY_ID", "TERM_ID", "INTEREST_PCT"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

df = df[required_cols].copy()

# ===== HELPERS =====
def term_to_days(term: str) -> int:
    """
    Convert term labels like 1M, 2M, 1Y, 7Y, 50Y into days.
    Uses:
      1M = 30 days
      1Y = 365 days
    """
    term = str(term).strip().upper()
    m = re.fullmatch(r"(\d+)([MY])", term)
    if not m:
        raise ValueError(f"Unsupported TERM_ID format: {term}")

    value = int(m.group(1))
    unit = m.group(2)

    if unit == "M":
        return value * 30
    if unit == "Y":
        return value * 365

    raise ValueError(f"Unsupported TERM_ID unit: {term}")

# ===== PREPARE DATA =====
df["EOD_DATE"] = pd.to_datetime(df["EOD_DATE"], errors="coerce")
df = df.dropna(subset=["EOD_DATE", "CURRENCY_ID", "TERM_ID", "INTEREST_PCT"])

df["tenor_days"] = df["TERM_ID"].apply(term_to_days)
df["tenor_col"] = "tenor_" + df["tenor_days"].astype(int).astype(str) + "d"

# ===== SAVE ONE FILE PER CURRENCY =====
Path(output_dir).mkdir(parents=True, exist_ok=True)

for currency, group in df.groupby("CURRENCY_ID"):
    # Pivot to wide format: one row per date, one column per tenor
    out = group.pivot_table(
        index="EOD_DATE",
        columns="tenor_col",
        values="INTEREST_PCT",
        aggfunc="first"
    )

    # Sort rows by date
    out = out.sort_index()

    # Sort tenor columns numerically: tenor_30d, tenor_60d, ...
    tenor_cols = sorted(
        out.columns,
        key=lambda x: int(x.replace("tenor_", "").replace("d", ""))
    )
    out = out[tenor_cols]

    # Reset index and rename date column
    out = out.reset_index().rename(columns={"EOD_DATE": "Date"})

    # Format date like the sample output
    out["Date"] = out["Date"].dt.strftime("%-m/%-d/%Y")   # Linux / Mac
    # For Windows, use:
    # out["Date"] = out["Date"].dt.strftime("%#m/%#d/%Y")

    # Save file
    output_file = Path(output_dir) / f"{currency}_InterestRate.csv"
    out.to_csv(output_file, index=False)

    print(f"Saved: {output_file}")
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