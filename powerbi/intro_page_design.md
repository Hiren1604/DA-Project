# CreditLens introduction page and visual system

The Introduction page is first in the Power BI report and is the default landing page. It explains the purpose of the report, the three questions it answers, the difference between RBI DBIE Table 16 and the separate Table 15 series, and the safe reading order. It also identifies the data as bundled RBI DBIE historical files for January 2019 through June 2026. The report serves this fixed snapshot locally; it does not connect to a live RBI feed.

`CreditLens-Institutional.json` is the imported Power BI theme, registered in `CreditLens.Report/definition/report.json`. It applies the shared palette, light report canvas, Segoe UI typography, and chart color sequence. The same brand tokens are published at `/static/creditlens-design.json`; the HTML app loads them at startup and applies them to CSS variables and Chart.js defaults.

The visual system uses deep navy and slate for structure, cyan for navigation and key trends, teal for positive or allocation views, and amber for concentration cautions. UI text uses Segoe UI; numeric readouts use tabular numerals.
