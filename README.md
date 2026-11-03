# Jodo Fee-Collection Lab

Built for **Jodo's Founder's Office (Analytics) internship**. All data is **simulated** and shaped like a school-fee EMI business; the numbers show method, not Jodo facts.

| Module | Result (simulated) |
| --- | --- |
| Bank reconciliation engine (DuckDB SQL) | 87,965 instalments vs bank feed: caught all **300 injected breaks** (amount mismatch, duplicate, missing credit), **0 false alarms**, auto-matched 100 reference typos |
| Collection risk by EMI plan | Students with at least one missed instalment: **4%** (1 instalment) → **61%** (12 instalments) |
| Unit economics per student-year | Contribution **₹3,696** on 3-month plans vs **₹1,325** on 12-month and **₹249** on full payment; credit loss and cost of funds drive the gap |
| AOP tracker | Monthly plan vs actual; flags months more than 5% below plan (4 of 12) |

Run: `pip install pandas numpy duckdb pytest && python run.py && pytest -q`
