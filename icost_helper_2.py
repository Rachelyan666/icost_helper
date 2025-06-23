import pandas as pd

month = "mar_apr_may2025"

# Mapping rules for category conversion
category_mapping = {
    "Groceries": ("餐饮", "蔬菜"),
    "Food & Drink": ("餐饮", "三餐"),
    "Travel": ("旅行", None),
    "Shopping": ("购物", None),
}

# Special rules for description-based mapping
description_mapping = [
    ("7-ELEVEN", ("餐饮", "零食")),
    ("Cornell Universi DIR DEP", ("工资", None)),
    ("Industrial and C", ("转账", None)),
    ("zelle", ("社交", None)),
    ("uber", ("交通", None)),
    ("doordash", ("餐饮", "三餐")),
    ("spotify", ("应用软件", None)),
    ("paypal", ("购物", None)),
]

# Keywords to exclude (credit card payments)
exclude_keywords = ["Payment to Chase card", "Payment Thank You"]

# Load Chase Checking CSV
df_checking = pd.read_csv(month+"/chase_checking.CSV")

# Load Chase Freedom CSV
df_freedom = pd.read_csv(month+"/chase_freedom.CSV")

# Save original 'Type' column to check for refund
df_checking["类型原始"] = df_checking["Type"] if "Type" in df_checking.columns else ""
df_freedom["类型原始"] = df_freedom["Type"] if "Type" in df_freedom.columns else ""

# Normalize column names
df_checking.rename(columns={"Posting Date": "日期", "Description": "备注", "Amount": "金额"}, inplace=True)
df_freedom.rename(columns={"Transaction Date": "日期", "Description": "备注", "Amount": "金额", "Category": "Category"}, inplace=True)

# Convert '类型' column (支出 for negative amounts, 收入 for positive amounts)
df_checking["类型"] = df_checking["金额"].apply(lambda x: "收入" if x > 0 else "支出")
df_freedom["类型"] = df_freedom["金额"].apply(lambda x: "收入" if x > 0 else "支出")

# Make all money values positive
df_checking["金额"] = df_checking["金额"].abs()
df_freedom["金额"] = df_freedom["金额"].abs()

# Exclude transactions related to credit card payments
df_checking = df_checking[~df_checking["备注"].str.contains('|'.join(exclude_keywords), case=False, na=False)]
df_freedom = df_freedom[~df_freedom["备注"].str.contains('|'.join(exclude_keywords), case=False, na=False)]

# Map categories based on Chase data
def map_category(row):
    # Refund rule
    if "类型原始" in row and str(row["类型原始"]).lower() == "return":
        return ("退款", None)

    # Category-based rule
    if "Category" in row and row["Category"] in category_mapping:
        return category_mapping[row["Category"]]

    # Description-based rule
    for keyword, (main_cat, sub_cat) in description_mapping:
        if keyword.lower() in str(row["备注"]).lower():
            return (main_cat, sub_cat)

    # Expensive rent rule
    if abs(row["金额"]) >= 1000:
        return ("住房", "房租")

    return (None, None)

# Apply category mapping
df_freedom[["一级分类", "二级分类"]] = df_freedom.apply(map_category, axis=1, result_type="expand")
df_checking[["一级分类", "二级分类"]] = df_checking.apply(map_category, axis=1, result_type="expand")

# Fill blank 一级分类 with "其他"
df_freedom["一级分类"].fillna("其他", inplace=True)
df_checking["一级分类"].fillna("其他", inplace=True)

# Assign account information
df_freedom["账户1"] = "chase freedom unlimited"
df_checking["账户1"] = "chase student checking"

# Add fixed columns
df_freedom["货币"] = "USD"
df_checking["货币"] = "USD"
df_freedom["标签"] = ""
df_checking["标签"] = ""

# Select relevant columns
columns_order = ["日期", "类型", "金额", "一级分类", "二级分类", "账户1", "备注", "货币", "标签"]
df_freedom = df_freedom[columns_order]
df_checking = df_checking[columns_order]

# Merge both datasets
df_final = pd.concat([df_freedom, df_checking], ignore_index=True)

# Ensure date format is consistent
df_final["日期"] = pd.to_datetime(df_final["日期"]).dt.strftime("%Y-%m-%d")

# Save as Excel file for iCost import
output_file = month+"_icost.xlsx"
df_final.to_excel(output_file, index=False)
