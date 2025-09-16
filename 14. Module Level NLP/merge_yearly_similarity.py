import pandas as pd
import glob
import os

def merge_yearly_similarity(
    input_dir=r"\module_theme_similarity_matrix2",
    output_csv=r"\all_years_similarity_comparison.csv"
):
    csv_files = glob.glob(os.path.join(input_dir, "module_theme_similarity_*.csv"))
    if not csv_files:
        print("No yearly CSVs found in", input_dir)
        return
    dfs = []
    for file in csv_files:
        year = os.path.basename(file).replace("module_theme_similarity_", "").replace(".csv", "")
        df = pd.read_csv(file)
        df["Year"] = year
        dfs.append(df)
    merged = pd.concat(dfs, ignore_index=True)
    id_cols = ["Module_Code", "Module_Title", "Module_Faculty", "Module_School"]
    theme_cols = [c for c in merged.columns if c not in id_cols + ["Academic_year", "Year"]]
    pivoted = merged.pivot_table(index=id_cols, columns="Year", values=theme_cols)
    pivoted.columns = [f"{theme}_{year}" for theme, year in pivoted.columns]
    pivoted.reset_index(inplace=True)
    change_flags = []
    for _, row in pivoted.iterrows():
        changed = False
        for theme in theme_cols:
            theme_years = [c for c in pivoted.columns if c.startswith(theme + "_")]
            values = row[theme_years].dropna().values
            if len(set(values)) > 1:
                changed = True
                break
        change_flags.append("CHANGED" if changed else "")
    pivoted["Change_Flag"] = change_flags
    pivoted.to_csv(output_csv, index=False)
    print(f"Merged yearly similarity saved as {output_csv}")

if __name__ == "__main__":
    merge_yearly_similarity()
