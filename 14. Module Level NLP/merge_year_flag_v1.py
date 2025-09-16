import pandas as pd
import glob
import os

def merge_years_with_flag(
    input_dir=r"module_theme_similarity_matrix2",
    output_csv=r"all_years_similarity_comparison2.csv"
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

    id_cols = ["Module_Code", "Module_Title", "Module_Faculty", "Module_School", "Year"]
    theme_cols = [c for c in merged.columns if c not in id_cols + ["Academic_year"]]

    grouped = merged.groupby("Module_Code")[theme_cols]
    changed_modules = grouped.apply(lambda g: (g.nunique() > 1).any()).reset_index()
    changed_modules.columns = ["Module_Code", "Changed"]
    changed_modules_map = dict(zip(changed_modules["Module_Code"], changed_modules["Changed"]))

    merged["Change_Flag"] = merged["Module_Code"].map(lambda m: "CHANGED" if changed_modules_map.get(m, False) else "")

    merged = merged[["Year", "Module_Code", "Module_Title", "Module_Faculty", "Module_School"] + theme_cols + ["Change_Flag"]]
    merged.to_csv(output_csv, index=False)
    print(f"Year-column merged file saved as {output_csv}")

if __name__ == "__main__":
    merge_years_with_flag()
