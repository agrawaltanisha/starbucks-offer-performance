import pandas as pd

offers = pd.read_json("data/portfolio.json", lines=True)
customers = pd.read_json("data/profile.json", lines=True)
events = pd.read_json("data/transcript.json", lines=True)

print("Sizes (rows, columns):")
print(offers.shape, customers.shape, events.shape)

print("\nThe 10 offers:")
print(offers)

print("\nFirst 5 customers:")
print(customers.head())

print("\nFirst 5 events:")
print(events.head())

print("\nHow many of each event:")
print(events["event"].value_counts())
