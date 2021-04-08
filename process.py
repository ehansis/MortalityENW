from pathlib import Path
import json

import numpy as np
import pandas as pd
import re


#
# Directory and file names
#

raw_data_dir = (Path(__file__).parent / ".." / "rawdata").absolute()
output_dir = (Path(__file__).parent / ".." / "outdata").absolute()
output_dir.mkdir(exist_ok=True)

file_names_20th_century = [
    "1911-1920-icd2.xls",
    "1921-1930-icd3.xls",
    "1931-1939-icd4.xls",
    "1940-1949-icd5.xls",
    "1950-1957-icd6.xls",
    "1958-1967-icd7.xlsx",
    "1968-1978-icd8.xls",
    "1979-1984-icd9a.xlsx",
    "1985-1993-icd9b.xls",
    "1994-2000-icd9c.xls",
]


#
# Configuration
#

# years to keep
years = list(range(1915, 2000 + 1, 5))

# how many top-N codes to keep
top_n_codes = 100


#
# Mapping from ICD codes to categories
#

ICD_CATEGORIES = {
    "Infectious disease": {
        "ICD-9": "1-136, 460-519",
        "ICD-8": "1-136, 460-519",
        "ICD-7": "1-138, 571, 240-241, 470-527",
        "ICD-6": "1-138, 571, 240-241, 470-527",
        "ICD-5": "1-32, 34-44, 119-120, 177, 33, 104-114, 115",
        "ICD-4": "1-10, 12-44, 79-80, 83, 119-120, 177, 11, 104-114, 115",
        "ICD-3": "1-10, 12-42, 71, 72, 76, 113-116, 121, 175, 11, 109, 97-107",
        "ICD-2": "1-9, 11-25, 28-35, 37-38, 60-62, 67, 104-107, 112, 164, 10, 86-98, 100",
    },
    "Complications of pregnancy and childbirth": {
        "ICD-9": "630-679",
        "ICD-8": "630-679",
        "ICD-7": "640-689",
        "ICD-6": "640-689",
        "ICD-5": "401-503",
        "ICD-4": "400-503",
        "ICD-3": "431-500",
        "ICD-2": "134-141",
    },
    "Injury and poisoning": {
        "ICD-9": "800-999",
        "ICD-8": "800-999",
        "ICD-7": "800-999",
        "ICD-6": "800-999",
        "ICD-5": "163-176, 178-198",
        "ICD-4": "163-175, 178-198",
        "ICD-3": "165-174, 176-203",
        "ICD-2": "57-58, 153, 155-163, 165-173, 174-186",
    },
    "Circulatory system": {
        "ICD-9": "390-459",
        "ICD-8": "390-459, 782-789",
        "ICD-7": "330-334, 400-468, 782",
        "ICD-6": "330-334, 400-468, 782",
        "ICD-5": "58, 83, 87a, 90-97, 99-103",
        "ICD-4": "56, 82, 87a, 90-97, 99-103",
        "ICD-3": "51, 74, 81, 83, 87-96",
        "ICD-2": "47, 64-65, 72, 77-85",
    },
    "Nervous system": {
        "ICD-9": "320-389",
        "ICD-8": "320-389, 739-781",
        "ICD-7": "335-398, 740-744",
        "ICD-6": "335-398, 740-744",
        "ICD-5": "80-82, 85, 87b, 87c, 87d, 88, 89",
        "ICD-4": "81, 85, 87b, 87c, 87d, 87e, 88, 89",
        "ICD-3": "70, 73, 75, 78, 79-80, 82, 84(3), 84(4), 84(5), 85, 86",
        "ICD-2": "63, 66, 69, 73, 74a, 74b, 74d, 75, 76",
    },
    "Digestive system": {
        "ICD-9": "520-577",
        "ICD-8": "520-577",
        "ICD-7": "530-570, 572-587",
        "ICD-6": "530-570, 572-587",
        "ICD-5": "116-118, 121-129",
        "ICD-4": "115a, 115b, 116-118, 121-129",
        "ICD-3": "108, 110-112, 117-120, 122-127",
        "ICD-2": "99, 101-103, 108-111, 113-115, 117-118",
    },
    # "Musculoskeletal system": {
    #     "ICD-9": "710-739",
    #     "ICD-8": "710-738",
    #     "ICD-7": "710-732, 734-738",
    #     "ICD-6": "720-739, 745-749",
    #     "ICD-5": "59, 154-156",
    #     "ICD-4": "57, 154-156",
    #     "ICD-3": "52, 155-158",
    #     "ICD-2": "48, 146-149",
    # },
    "Cancer": {
        "ICD-9": "140-239",
        "ICD-8": "140-239",
        "ICD-7": "140-239, 294",
        "ICD-6": "140-239, 294",
        "ICD-5": "45-57, 74",
        "ICD-4": "45-55, 72",
        "ICD-3": "43-49, 50, 65, 84b, 139",
        "ICD-2": "39-45, 46, 74c, 53, 129",
    },
}

# order and left/right sorting of categories
CATEGORY_ORDER = {
    "Infectious disease": -1,
    "Complications of pregnancy and childbirth": -2,
    "Injury and poisoning": -3,
    "Other": 1,
    "Circulatory system": 2,
    "Cancer": 3,
    "Nervous system": 4,
    "Digestive system": 5,
    # "Musculoskeletal system": 5,
}


def left_pad_code(code):
    """Left-pad the leading numerical part of a code with zeros to 3 digits"""
    code = code.lstrip("0")
    i_str = re.search("^[0-9]+", code).group()
    i = int(i_str)
    assert 0 < i <= 999
    return f"{int(i_str):03d}{code[len(i_str):]}"


def map_icd_codes_to_categories(df, icd_version):
    """Append a column 'category' to df containing disease categories"""
    # default label
    df["category"] = "Other"

    # From ICD6 on we have numerical-only four-digit codes, categorization works
    # on 3-digit codes only. Drop the last digit before left-padding.
    if icd_version >= 6:
        lp_code_map = {c: c[:-1] for c in df["code"].unique()}
    else:
        # Generate left-padded codes for lexsorted selection in table.
        lp_code_map = {c: left_pad_code(c) for c in df["code"].unique()}
    df["lp_code"] = df["code"].map(lp_code_map)

    for category, mappings in ICD_CATEGORIES.items():
        codes = mappings[f"ICD-{icd_version}"]
        for code in [c.strip().strip(",") for c in codes.split()]:
            if "-" in code:
                start_code, end_code = code.split("-")
            else:
                start_code = end_code = code

            # make sure there are no category overlaps
            row_sel = (df["lp_code"] >= left_pad_code(start_code)) & (
                df["lp_code"] <= left_pad_code(end_code) + "z"
            )
            assert (df.loc[row_sel, "category"].isin(["Other", category])).all()

            # set category
            df.loc[
                row_sel,
                "category",
            ] = category


def load_20th_century():
    """Load/process data from 20th century"""

    # container for processed data files, for output
    out = []

    for file_name in file_names_20th_century:
        print(file_name)

        xl = pd.ExcelFile(raw_data_dir / file_name)

        descriptions = xl.parse(
            sheet_name="description",
            skiprows=1,
            usecols="A:C",
            names=["code", "desc1", "desc2"],
            dtype=str,
        ).fillna("")

        # Descriptions are split across two columns. Either the value in both columns is identical
        # or the second column specifies the first more precisely. Join or drop second value.
        descriptions["desc1"] = descriptions["desc1"].str.strip()
        descriptions["desc2"] = descriptions["desc2"].str.strip()
        descriptions["desc"] = descriptions.apply(
            lambda s: s["desc1"]
            if s["desc1"] == s["desc2"] or len(s["desc2"]) == 0
            else s["desc1"] + ", " + s["desc2"],
            axis=1,
        )
        descriptions["code"] = descriptions["code"].str.strip()
        descriptions = descriptions.set_index("code")["desc"]

        # file name ends in ICD version number, plus 'a', 'b' or 'c' for ICD9
        icd_version = file_name.split(".")[0][-1]
        if not icd_version.isdigit():
            icd_version = file_name.split(".")[0][-2]
        assert icd_version.isdigit()
        icd_version = int(icd_version)
        assert 2 <= icd_version <= 9

        # data sheets are called icdN_1, icdN_2, ... concatenate them all
        sheet_data = []
        for sheet_name in [
            s for s in xl.sheet_names if s.startswith(f"icd{icd_version}")
        ]:
            sheet_data.append(
                xl.parse(
                    sheet_name=sheet_name,
                    skiprows=1,
                    names=["code", "year", "sex", "age", "n"],
                    dtype={"code": str},
                )
            )

        assert len(sheet_data) >= 2

        df_all_years = pd.concat(sheet_data)

        # keep only desired years
        for year in df_all_years["year"].unique():
            if year not in years:
                continue

            # select data, map in metadata
            df = df_all_years[df_all_years["year"] == year].copy()
            df["code"] = df["code"].str.strip()
            df["desc"] = df["code"].map(descriptions).fillna("Other")
            assert (df["desc"] == "Other").sum() / len(df) < 0.05
            map_icd_codes_to_categories(df, icd_version)
            assert (df["category"] == "Other").sum() / len(df) < 0.3

            # keep only top N codes by number of deaths (across all age groups)
            kept_codes = (
                df.groupby("code")["n"]
                .sum()
                .sort_values(ascending=False)
                .iloc[:top_n_codes]
                .index.values
            )

            # map descriptions of other codes to category + ", other"
            has_kept_code = df["code"].isin(kept_codes)
            df.loc[~has_kept_code, "desc"] = (
                df.loc[~has_kept_code, "category"] + ", other"
            )

            # aggregate to 80+ age group (early data has only 80+, later data has 80-84 and 85+),
            # aggregation is done in next line
            df.loc[df["age"].str.startswith("8"), "age"] = "80+"

            # aggregate by description age group and sex to reduce data size
            df_agg = (
                df.groupby(["year", "age", "category", "desc"])["n"].sum().reset_index()
            )

            # done with this chunk
            out.append(df_agg)

    # concatenate all output data
    return pd.concat(out, ignore_index=True)


def data_to_tree(df):
    """Process data table to derive structure useful for tree plotting

    Generates three files:
    (1) categories data (communicable disease, injury, ...) - this is used to plot the
        Sankey-style links that make up the trunk and branches of the tree;
    (2) diagnosis data (single ICD codes) - this is used to plot the tips of the
        branches.
    (3) metadata: JSON file containing all sorts of useful information, like sorted
        age groups, total counts, centering information, ...

    In each file there is one line per category or per diagnosis. Each line contains fields:
    * ageIdx: linear integer index of age group, starting at 0 for age group 0-1
    * catIdx: integer index of category; 0 for trunk, negative for left half, positive for
        right half, with absolute value increasing away from the trunk
    * frac: fraction of deaths that fall into this age group and category or disease
    * cumFrac: fraction at right edge for sorted placement of categories/diseases
        (a category or disease covers the scaled horizontal range cumFrac - frac ... cumFrac)
    """
    # container for metadata JSON
    meta = dict(years=sorted([int(i) for i in df["year"].unique()]))

    # sort age groups, then rename to strip leading zeros
    df.loc[df["age"] == "<1", "age"] = "00-01"
    ages_sorted = sorted(df["age"].unique())
    age_map = {
        s: s if s == "80+" else f"{int(s.split('-')[0])}-{int(s.split('-')[1])}"
        for s in ages_sorted
    }
    meta["ages"] = [age_map[s] for s in ages_sorted]

    # map in category order
    df["catIdx"] = df["category"].map(CATEGORY_ORDER)
    assert not df["catIdx"].isnull().any()

    # compute fraction of deaths per year occurring in each age group and code
    df["frac"] = df.groupby("year", group_keys=False).apply(
        lambda g: g["n"] / g["n"].sum()
    )
    assert abs(df["frac"].sum() - len(years)) < 1.0e-9
    df = df.drop(["n"], axis=1)

    # for each age group add an entry for deaths occurring at older ages
    df = df.set_index(["year", "age"]).sort_index()
    older_ages_rows = []
    for year in years:
        prev_frac_sum = 1
        for age in ages_sorted:
            age_frac_sum = df.loc[(year, age)]["frac"].sum()
            older_frac = prev_frac_sum - age_frac_sum
            desc = (
                f"Older than {int(age.split('-')[1])} years"
                if "-" in age
                else "Impossible!"  # for 85+
            )
            older_ages_rows.append(
                dict(
                    year=year,
                    age=age,
                    category=desc,
                    desc=desc,
                    catIdx=0,
                    frac=older_frac,
                )
            )
            prev_frac_sum = older_frac

    # append the additional rows, sort everything
    assert df.isnull().sum().sum() == 0
    df = pd.concat([df.reset_index(), pd.DataFrame(older_ages_rows)]).sort_values(
        by=["year", "age", "catIdx"]
    )  # type: pd.DataFrame
    assert df.isnull().sum().sum() == 0

    # within each year, age and category sort such that large fractions are close to the trunk
    df["sort_order"] = df["frac"] * np.sign(df["catIdx"])
    df = df.sort_values(
        by=["year", "age", "catIdx", "sort_order"],
        ascending=[True, True, True, False],
    ).drop(["sort_order"], axis=1)

    # compute cumulative fraction per year and age group for horizontal positioning
    df["cumFrac"] = df.groupby(["year", "age"], group_keys=False)["frac"].apply(
        lambda g: g.cumsum()
    )
    assert df["cumFrac"].min() > 1.0e-9
    assert df["cumFrac"].max() < 1 + 1.0e-9

    def center_trunk(g):
        trunk_row = g[g["catIdx"] == 0].iloc[0]
        frac_shift = 0.5 - (trunk_row["cumFrac"] - 0.5 * trunk_row["frac"])
        return g["cumFrac"] + frac_shift

    # shift cumFrac such that trunk (catIdx = 0) is always centered at 0.5
    df["cumFrac"] = df.groupby(["year", "age"], group_keys=False).apply(center_trunk)

    # this is the disease-level file, map ages to nicer strings before returning
    # (can only do that now because we needed the leading zeros for sorting)
    dis = df.copy()
    dis["age"] = dis["age"].map(age_map)
    assert not dis["age"].isnull().any()

    # aggregate on the category level
    cat = (
        df.groupby(["year", "age", "category"])
        .agg({"frac": "sum", "catIdx": "first", "cumFrac": "max"})
        .reset_index()
    )
    cat = cat.sort_values(by=["year", "age", "catIdx"])
    cat["age"] = cat["age"].map(age_map)
    assert not cat["age"].isnull().any()

    return dis, cat, meta


if __name__ == "__main__":
    # convert data to CSV table, if it doesn't exist yet
    all_data_csv = output_dir / "Deaths_ENW_1915-2015.csv"
    if not all_data_csv.exists():
        df20 = load_20th_century()
        df20.to_csv(all_data_csv, index=False)

    # process into tree definitions
    df20 = pd.read_csv(all_data_csv)
    diseases, categories, metadata = data_to_tree(df20)
    diseases.to_csv(output_dir / "Deaths_ENW_1915-2015_disease_tree.csv", index=False)
    categories.to_csv(
        output_dir / "Deaths_ENW_1915-2015_category_tree.csv", index=False
    )
    json.dump(metadata, (output_dir / "Deaths_ENW_1915-2015_tree_meta.json").open("w"))
