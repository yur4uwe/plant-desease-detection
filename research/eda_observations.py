# run with `jupytext --to notebook research/eda_observations.py`
# and then `jupyter nbconvert --to html --execute research/eda_observations.ipynb`

# %% [markdown]
# # Exploratory Data Analysis (EDA)
# **Task:** Perform initial exploratory data analysis for the Plant Disease Detection project.
# **Objective:** Understand data structure, identify quality issues, and analyze feature relationships.

# %% [markdown]
# ## 1. General Description & Technical Review
# In this section, we load the dataset from the SQLite database and perform a high-level inspection of its structure.

# %%
import sqlite3
from typing import cast
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from etl.config.helpers import ETL_ROOT
from IPython.display import display

# Configure plotting
sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = [10, 6]

# Define database path
DB_PATH = Path(ETL_ROOT / "data/processed/observations.db")

# %%
# Connect and load data
conn = sqlite3.connect(DB_PATH)
df: pd.DataFrame = pd.read_sql_query("SELECT * FROM observations", conn)
conn.close()

# Basic shape
print(f"Dataset Shape: {df.shape}")

# %% [markdown]
# ## 2. Data Loading & Initial Overview
# Displaying the first few records and summary statistics.

# %%
# First 5-10 records
display(df.head(10))

# %%
# Summary info
df.info()

# %%
# Summary statistics for relevant numerical features
print("--- Numerical Features Summary ---")
display(df[["latitude", "longitude", "temperature", "precipitation"]].describe())

# %%
# Summary statistics for categorical features
print("--- Categorical Features Summary ---")
display(df.select_dtypes(include=["object", "string"]).describe())

# %% [markdown]
# ## 3. Data Quality & Completeness Analysis
# We check for missing values, duplicates, and potential formatting issues.
# A critical issue is the high rate of missing metadata. We analyze this systematically.

# %%
# Missing values
missing = df.isnull().sum()
missing_pct = (missing / len(df)) * 100
missing_df = pd.DataFrame({"Missing": missing, "Percentage (%)": missing_pct})
print("--- Missing Values Analysis ---")
display(missing_df[missing_df["Missing"] > 0])

# %%
# Duplicates check (based on external_id)
duplicates = df.duplicated(subset=["external_id"]).sum()
print(f"Number of duplicate external_ids: {duplicates}")

# %%
# Missing Data Analysis: Why is ~80% of metadata missing?
df["has_metadata"] = (
    df[["latitude", "longitude", "observation_date"]].notnull().all(axis=1)
)

print("--- Metadata Presence by Source (%) ---")
display(pd.crosstab(df["source"], df["has_metadata"], normalize="index") * 100)

print("\n--- Metadata Presence by Target Class (%) ---")
display(pd.crosstab(df["is_diseased"], df["has_metadata"], normalize="index") * 100)

# %% [markdown]
# ## 4. Univariate Analysis
# Distribution analysis of key features.
# **Note:** For geographical, weather, and seasonal data, we only use the subset of records where metadata is present (~20%).

# %%
# Categorical distributions
fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# All data
sns.countplot(data=df, x="source", ax=axes[0, 0]).set_title("Observations by Source")
sns.countplot(
    data=df, y="label", ax=axes[0, 1], order=df["label"].value_counts().iloc[:10].index
).set_title("Top 10 Labels")

# Subset with metadata
df_meta = cast(pd.DataFrame, df[df["has_metadata"]].copy())

sns.countplot(
    data=df_meta,
    x="season",
    ax=axes[1, 0],
    order=["Spring", "Summer", "Autumn", "Winter"],
).set_title("Observations by Season (Subset)")
sns.countplot(data=df_meta, x="solar_status", ax=axes[1, 1]).set_title(
    "Observations by Solar Status (Subset)"
)

plt.tight_layout()
plt.show()

# %%
# Geographical & Weather Distributions
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

sns.scatterplot(
    data=df_meta, x="longitude", y="latitude", hue="is_diseased", alpha=0.5, ax=axes[0]
)
axes[0].set_title("Geographical Distribution (Subset)")

sns.boxplot(data=df_meta, x="temperature", ax=axes[1]).set_title(
    "Temperature Distribution"
)

sns.histplot(data=df_meta, x="precipitation", bins=50, kde=True, ax=axes[2]).set_title(
    "Precipitation Distribution"
)

plt.tight_layout()
plt.show()

# %% [markdown]
# ## 5. Temporal Analysis
# Analyzing the period of coverage and intensity of observations over time (using the subset with dates).
# We use a log scale to ensure historical depth is visible despite recent data surges.

# %%
df_meta["observation_date_dt"] = pd.to_datetime(
    df_meta["observation_date"], errors="coerce"
)

# Resample to Month End (ME) for a cleaner time-series
temporal_counts = df_meta.set_index("observation_date_dt").resample("ME").size()

plt.figure(figsize=(14, 6))
temporal_counts.plot(kind="line", marker=".", color="coral")
plt.yscale("log")
plt.title("Observation Intensity over Time (Log Scale)")
plt.ylabel("Number of Observations (Log)")
plt.xlabel("Observation Date")
plt.grid(True, which="both", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 6. Bivariate & Multivariate Analysis
# Exploring relationships between features and the target variable.

# %%
# Correlation matrix (including target)
numerical_cols = [
    "temperature",
    "precipitation",
    "latitude",
    "longitude",
    "is_diseased",
]
corr = df_meta[numerical_cols].corr()  # pyright: ignore[reportCallIssue]

plt.figure(figsize=(8, 6))
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f").set_title(
    "Correlation Matrix"
)
plt.show()

# %%
# Weather vs Disease
fig, axes = plt.subplots(1, 2, figsize=(15, 5))

sns.boxplot(data=df_meta, x="is_diseased", y="temperature", ax=axes[0]).set_title(
    "Temperature vs Disease"
)

sns.violinplot(
    data=df_meta, x="is_diseased", y="precipitation", ax=axes[1], inner="quartile"
).set_title("Precipitation vs Disease")
axes[1].set_yscale("symlog")
axes[1].set_ylabel("Precipitation (symlog scale)")

plt.show()

# %% [markdown]
# ## 7. Target Variable Analysis
# Analyzing the balance between healthy and diseased samples.

# %%
# Class distribution
target_counts = df["is_diseased"].value_counts()
target_pct = df["is_diseased"].value_counts(normalize=True) * 100

print("--- Class Distribution ---")
print(f"Healthy (0): {target_counts[0]} ({target_pct[0]:.2f}%)")
print(f"Diseased (1): {target_counts[1]} ({target_pct[1]:.2f}%)")

plt.figure(figsize=(8, 5))
sns.countplot(data=df, x="is_diseased").set_title(
    "Target Class Balance (0=Healthy, 1=Diseased)"
)
plt.show()
