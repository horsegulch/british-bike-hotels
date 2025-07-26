
This document outlines the strategic decision regarding the output scale of the cycling route difficulty model, addressing different use cases and target audiences.

  

**1. Core Model Output: Raw Difficulty Score**

  
The fundamental calculation performed by the `calculate_total_difficulty` function results in a "raw" difficulty score. This score is derived from:

* A base difficulty calculated from distance (including a flat addition and a quadratic component).

* An Elevation Factor (EF) that modifies the distance difficulty, composed of an Uphill Factor (UF) and a Downhill Reduction Factor (DRF).

  

**2. Initial Web Application: Uncapped Score**

  

* **Target Audience:** The initial web application is primarily aimed at cyclists, potentially including those interested in more challenging or "extreme" routes.

* **Rationale for Uncapped Score:**

    * **Enhanced Granularity:** An uncapped score allows for finer differentiation between very difficult rides. A ride scoring a raw 150 can be distinguished from one scoring 200, which would be lost if both were capped at 100.

    * **Direct Reflection of Model:** The score directly represents the model's calculated output without an artificial ceiling, providing a more transparent measure.

    * **Highlights Outliers:** Exceptionally demanding routes will achieve very high scores, clearly marking them as such.

* **Implementation:** The `calculate_total_difficulty` function will return this raw score, ensuring only that it does not fall below a minimum (currently 0.0).

  

**3. Future Product for Tour Operators: Capped Score**

  

* **Target Audience:** Tour operators and their broader customer base, who may benefit from a more standardized and bounded difficulty scale.

* **Rationale for Capped Score:**

    * **Comparability:** A capped scale (e.g., 0-100, or categories like 1-5 stars) can make it easier for customers to compare different tours or products, both within a single operator's offerings and potentially across different operators if a standard is adopted.

    * **Simplified Categorization:** Easier for operators to classify rides into understandable difficulty bands (e.g., "Easy," "Moderate," "Challenging," "Expert").

    * **Broader Appeal:** A familiar, bounded scale can be less intimidating and more accessible to a wider range of cyclists.

* **Implementation:** This would be a separate presentation layer or a modified version of the scoring output. It would take the `Raw_Total_Difficulty` (as calculated by the current core algorithm) and apply an upper cap (e.g., 100). The underlying calculation logic would remain consistent.

  

**4. Summary**

  

The strategy is to:

* **Develop and refine the core algorithm to produce a meaningful raw, uncapped difficulty score.** This is the current focus for the web application.

* **Adapt the presentation of this score for different products/audiences in the future.** The ability to offer a capped version for tour operators is a planned extension, leveraging the same fundamental difficulty calculation.

  

This dual approach allows the model to serve the detailed needs of keen cyclists while also being adaptable for business applications requiring a more standardized scale.