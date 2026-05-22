# Deployment Risk Analysis Report

Based on the 20 sample deployments currently seeded in the local database, here is an exploratory data analysis breaking down the AI risk predictions.

## 1. Overall Risk Distribution
Of the deployments analyzed by the AI engine, the distribution of risk severity is as follows:

- **🟢 Low Risk:** 50% (6 deployments)
- **🟠 Medium Risk:** 25% (3 deployments)
- **🔴 High Risk:** 25% (3 deployments)

> [!TIP]
> A healthy CI/CD pipeline typically sees a 70-80% Low Risk rate. The elevated High Risk rate here is due to our synthetic testing data.

---

## 2. Risk Score by Author
The AI engine tracks historical stability per developer. Here is the average risk score (0-100, lower is better) assigned to deployments based on the author:

| Author | Avg Risk Score | Profile |
| :--- | :--- | :--- |
| `alpha_tester` | **15.69** | Highly reliable, mostly small non-breaking changes. |
| `mpscharan123-cyber` | **17.11** | Very reliable, consistent low-risk commits. |
| `release_lead` | **43.29** | Moderate risk, often merges large feature branches. |
| `dev_master` | **49.46** | Moderate-High risk, likely tackling complex architectural refactors. |

---

## 3. Code Metrics vs. Risk Level
As expected, the AI strongly correlates the size and spread of a code change with its potential to cause an outage.

| Risk Classification | Avg Files Changed | Insight |
| :--- | :--- | :--- |
| **Low Risk** | 7.33 files | Small, isolated bug fixes or UI tweaks. |
| **Medium Risk** | 9.33 files | Standard feature additions spanning a few modules. |
| **High Risk** | **20.33 files** | Massive refactors touching multiple microservices or core logic. |

> [!WARNING]
> Deployments touching more than 15 files are consistently flagged as **High Risk** by the model. These deployments should be broken down into smaller, iterative pull requests to reduce the blast radius of a potential failure.
