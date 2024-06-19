import pandas as pd

# Sample data for the Excel file
data = {
    "Interfaces": [
        "Te0/0/0/3", "Te0/0/0/4", "Te0/0/0/5", "Te0/0/0/6",
        "Te0/0/0/7", "Te0/0/0/8", "Te0/0/0/9", "Te0/0/0/10",
        "Te0/0/0/11", "Te0/0/0/12"
    ]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Save to Excel file
df.to_excel("interfaces_sample.xlsx", index=False)
