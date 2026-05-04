import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import os

def load_before():
    conn = sqlite3.connect("etl/data/processed/observations.db")
    df_db = pd.read_sql("SELECT * FROM observations", conn)
    conn.close()
    df_syn = pd.read_csv("data/syn_data_gen_tsar.csv")
    return pd.concat([df_db, df_syn], ignore_index=True)

def load_after():
    return pd.read_csv("data/df_cleaned_tsar.csv")

def main():
    os.makedirs("docs/images", exist_ok=True)
    df_before = load_before()
    df_after = load_after()
    
    num_cols = ['latitude', 'longitude', 'temperature', 'precipitation']
    
    # 1. Boxplots Before vs After
    fig, axes = plt.subplots(len(num_cols), 2, figsize=(12, 16))
    fig.suptitle('Numerical Distributions: Before vs After Cleaning (Isolation Forest + Limits)', fontsize=16)
    
    for i, col in enumerate(num_cols):
        # Before
        sns.boxplot(y=df_before[col], ax=axes[i, 0], color='lightcoral')
        axes[i, 0].set_title(f'{col} (Before)')
        
        # After
        sns.boxplot(y=df_after[col], ax=axes[i, 1], color='lightgreen')
        axes[i, 1].set_title(f'{col} (After)')
        
    plt.tight_layout()
    plt.subplots_adjust(top=0.95)
    plt.savefig('docs/images/eda_v2_boxplots.png')
    print("Saved docs/images/eda_v2_boxplots.png")
    
    # 2. Scatterplot Latitude vs Longitude
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Geospatial Distribution: Before vs After', fontsize=16)
    
    sns.scatterplot(x='longitude', y='latitude', data=df_before, ax=axes[0], alpha=0.5, color='red')
    axes[0].set_title('Before Cleaning (Contains Outliers)')
    axes[0].set_xlim(-200, 350)
    axes[0].set_ylim(-100, 160)
    
    sns.scatterplot(x='longitude', y='latitude', data=df_after, ax=axes[1], alpha=0.5, color='green')
    axes[1].set_title('After Cleaning (Standardized)')
    # Note: After data is standardized, so limits are different.
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.9)
    plt.savefig('docs/images/eda_v2_scatter_geo.png')
    print("Saved docs/images/eda_v2_scatter_geo.png")

if __name__ == "__main__":
    main()
