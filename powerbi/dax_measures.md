# CreditLens — Power BI DAX Measures & Semantic Model

This document specifies the complete DAX calculation layer for the CreditLens 3-page Power BI dashboard.
All measures assume a star schema with `FactCredit`, `DimDate`, `DimSector`, and an isolated mutually exclusive fact filter to avoid parent-child double-counting.

---

## 1. Core Base Measures

### 1.1 Total Credit Outstanding
Returns the sum of bank credit outstanding in ₹ crore for the active filter context.
```dax
Total Credit (₹ Cr) = 
SUM(FactCredit[CreditOutstandingCr])
```

### 1.2 Formatted Credit Outstanding (₹ Lakh Crore)
Formats large aggregate values into readable Indian lakh crore notation.
```dax
Total Credit (₹ Lakh Cr) = 
DIVIDE([Total Credit (₹ Cr)], 100000, 0)
```

---

## 2. Time-Intelligence & Growth Measures

### 2.1 Credit Previous Month (MoM Base)
Uses continuous calendar dates to ensure month-over-month comparisons are strictly aligned.
```dax
Credit Previous Month = 
CALCULATE(
    [Total Credit (₹ Cr)],
    DATEADD(DimDate[CalendarDate], -1, MONTH)
)
```

### 2.2 MoM Credit Change (₹ Cr)
Absolute movement in credit outstanding compared to prior month.
```dax
MoM Credit Change (₹ Cr) = 
VAR PrevMonth = [Credit Previous Month]
RETURN
    IF(
        NOT ISBLANK(PrevMonth),
        [Total Credit (₹ Cr)] - PrevMonth,
        BLANK()
    )
```

### 2.3 MoM Credit Growth %
Relative percentage change month-over-month.
```dax
MoM Credit Growth % = 
DIVIDE(
    [MoM Credit Change (₹ Cr)],
    [Credit Previous Month]
)
```

### 2.4 Credit Previous Year (YoY Base)
Strictly shifts the active calendar date window back by exactly one calendar year.
```dax
Credit Previous Year = 
CALCULATE(
    [Total Credit (₹ Cr)],
    DATEADD(DimDate[CalendarDate], -1, YEAR)
)
```

### 2.5 YoY Credit Change (₹ Cr)
Absolute expansion in credit over 12 months.
```dax
YoY Credit Change (₹ Cr) = 
VAR PrevYear = [Credit Previous Year]
RETURN
    IF(
        NOT ISBLANK(PrevYear),
        [Total Credit (₹ Cr)] - PrevYear,
        BLANK()
    )
```

### 2.6 YoY Credit Growth %
Standard annual lending expansion rate.
```dax
YoY Credit Growth % = 
DIVIDE(
    [YoY Credit Change (₹ Cr)],
    [Credit Previous Year]
)
```

---

## 3. Portfolio Allocation & Concentration Measures

### 3.1 Total Mutually Exclusive Industry Credit
Calculates total industrial credit across the 19 mutually exclusive sectors, removing individual sector filters while strictly preserving date filters.
```dax
Total Mutually Exclusive Industry Credit = 
CALCULATE(
    [Total Credit (₹ Cr)],
    DimSector[IsMutuallyExclusive] = TRUE,
    REMOVEFILTERS(DimSector[SectorName], DimSector[SectorCode])
)
```

### 3.2 Sector Portfolio Share %
Sector's proportion of the total industrial credit portfolio.
```dax
Sector Share % = 
DIVIDE(
    [Total Credit (₹ Cr)],
    [Total Mutually Exclusive Industry Credit]
)
```

### 3.3 Top 3 Sectors Concentration Share %
Measures exposure concentration in the top three largest sectors in the selected period.
```dax
Top 3 Concentration Share % = 
VAR Top3Sectors = 
    TOPN(
        3, 
        CALCULATETABLE(
            DimSector, 
            DimSector[IsMutuallyExclusive] = TRUE
        ), 
        [Total Credit (₹ Cr)], 
        DESC
    )
VAR Top3Credit = 
    CALCULATE(
        [Total Credit (₹ Cr)], 
        KEEPFILTERS(Top3Sectors)
    )
RETURN
    DIVIDE(Top3Credit, [Total Mutually Exclusive Industry Credit])
```

### 3.4 Herfindahl-Hirschman Index (HHI - Points)
Calculates market concentration as the sum of squared sector shares (scale 0 to 10,000 points).
- Below 1,000: Unconcentrated
- 1,000 to 1,500: Moderate Concentration
- Above 1,800: Highly Concentrated
```dax
HHI Index = 
VAR SectorShares = 
    ADDCOLUMNS(
        CALCULATETABLE(
            DimSector, 
            DimSector[IsMutuallyExclusive] = TRUE
        ),
        "SharePct", [Sector Share %] * 100
    )
RETURN
    SUMX(SectorShares, [SharePct] ^ 2)
```

---

## 4. Hierarchy & Integrity Guards

### 4.1 Is Non-Additive Row Warning
Flag to warn if a visual is mixing parent sector totals with sub-sectors.
```dax
Double Count Risk Flag = 
IF(
    CALCULATE(COUNTROWS(FactCredit), DimSector[HierarchyLevel] = "grand_total") > 0 &&
    CALCULATE(COUNTROWS(FactCredit), DimSector[HierarchyLevel] = "sub_sector") > 0,
    "WARNING: Mixed Hierarchy Detected",
    "NORMAL"
)
```
