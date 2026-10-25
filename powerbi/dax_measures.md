# CreditLens Power BI DAX Measures

These measures are design material for a future Power BI model. The repository does not include a verified PBIX. The fact table contains every hierarchy level, so measures must select either the grand-total row or the 19 mutually exclusive Level-1 industries explicitly.

## Base measures

```dax
Credit Amount Raw (Cr) =
SUM(FactCredit[CreditOutstandingCr])

Total Industry Credit (Cr) =
CALCULATE(
    [Credit Amount Raw (Cr)],
    REMOVEFILTERS(DimSector),
    DimSector[SectorCode] = "2"
)

Level 1 Sector Credit (Cr) =
CALCULATE(
    [Credit Amount Raw (Cr)],
    DimSector[IsMutuallyExclusive] = TRUE()
)

Total Level 1 Credit (Cr) =
CALCULATE(
    [Credit Amount Raw (Cr)],
    REMOVEFILTERS(DimSector),
    DimSector[IsMutuallyExclusive] = TRUE()
)

Sector Share % =
DIVIDE([Level 1 Sector Credit (Cr)], [Total Level 1 Credit (Cr)])

Total Industry Credit (Lakh Cr) =
DIVIDE([Total Industry Credit (Cr)], 100000)
```

## Growth measures

Use a complete, continuous date dimension marked as the model date table. The reporting observations occur once per month; the date dimension supplies calendar alignment.

```dax
Credit Previous Month (Cr) =
CALCULATE(
    [Total Industry Credit (Cr)],
    DATEADD(DimDate[CalendarDate], -1, MONTH)
)

MoM Change (Cr) =
[Total Industry Credit (Cr)] - [Credit Previous Month (Cr)]

MoM Growth % =
DIVIDE([MoM Change (Cr)], [Credit Previous Month (Cr)])

Credit Previous Year (Cr) =
CALCULATE(
    [Total Industry Credit (Cr)],
    DATEADD(DimDate[CalendarDate], -1, YEAR)
)

YoY Change (Cr) =
[Total Industry Credit (Cr)] - [Credit Previous Year (Cr)]

YoY Growth % =
DIVIDE([YoY Change (Cr)], [Credit Previous Year (Cr)])
```

## Concentration measures

```dax
Top 3 Concentration Share % =
VAR SectorTable =
    FILTER(ALL(DimSector), DimSector[IsMutuallyExclusive] = TRUE())
VAR RankedSectors =
    TOPN(3, SectorTable, CALCULATE([Level 1 Sector Credit (Cr)]), DESC)
VAR Top3Credit =
    SUMX(RankedSectors, CALCULATE([Level 1 Sector Credit (Cr)]))
RETURN
    DIVIDE(Top3Credit, [Total Level 1 Credit (Cr)])

HHI Index =
VAR SectorTable =
    FILTER(ALL(DimSector), DimSector[IsMutuallyExclusive] = TRUE())
RETURN
    SUMX(
        SectorTable,
        VAR SharePct = CALCULATE([Sector Share %]) * 100
        RETURN SharePct * SharePct
    )
```

## Visual guardrails

- Use `Total Industry Credit (Cr)` for the grand-total headline and overall trend.
- Use `Level 1 Sector Credit (Cr)` and `Sector Share %` for sector comparisons.
- Use `Total Level 1 Credit (Cr)` as the denominator for industry portfolio distribution.
- Do not sum all rows in `FactCredit`: grand totals and nested sub-sectors overlap.
- Validate every report measure against the pandas outputs and SQLite views before publishing.
