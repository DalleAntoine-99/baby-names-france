# Week 2 - Initial Implementation

Our dashboard explores French baby-name data from 1900 to 2020 through
three interactive visualizations.

## 1. Evolution over time

![Temporal evolution heatmap](<Capture d’écran 2026-06-12 120448.png>)

The first visualization is a heatmap showing the normalized popularity of
names for each year. Darker red cells represent greater popularity.

This representation makes it possible to compare many names simultaneously
and identify names that remained popular, disappeared, or became popular
during a specific period.

### Strengths

- It provides a compact overview of long-term trends.
- Sudden increases, decreases, and periods of stable popularity are visible.
- Normalization makes years with different total birth counts comparable.

### Weaknesses

- Displaying many names makes some labels difficult to read.
- The logarithmic scale is less intuitive than raw birth counts.
- A name-selection filter could make detailed comparisons easier.

## 2. Regional effects

![Regional effects map](<Capture d’écran 2026-06-12 120348.png>)

The second visualization uses a choropleth map to display the location
quotient (LQ) of a selected name. A value above 1 means that the name is more
represented in a department than in France as a whole.

The dropdown allows the user to select a name. Clicking a department displays
the names that are most overrepresented there. This answers both regional
questions: where a selected name is particularly popular and which names
characterize a selected department.

### Strengths

- The map makes geographic patterns easy to identify.
- The dropdown allows different names to be compared.
- The linked bar chart provides more detail for a selected department.
- The location quotient reduces the influence of differences in department
  population.

### Weaknesses

- The location quotient requires a short explanation.
- Results based on very small numbers of births can be unstable.
- Minimum frequency thresholds may hide rare but locally significant names.

## 3. Effects related to sex

![Gender effects visualization](<Capture d’écran 2026-06-12 120501.png>)

The third visualization places each name according to its total popularity
and its proportion of female births. Point size represents the total number
of births, while color indicates how balanced the name is between both
recorded sexes.

Clicking a name displays its historical evolution for girls and boys. This
helps identify strongly gendered and mixed-gender names and determine whether
their use changed over time. For example, the detail view for Camille shows
a strong increase among girls after 1980.

### Strengths

- It combines a general overview with a detailed historical view.
- The 50% reference line helps identify mixed-gender names.
- The linked line chart shows how gender distribution changes over time.

### Weaknesses

- Many points overlap near 0% and 100%.
- Logarithmic popularity and the color scale require explanation.
- The dataset represents sex as binary, which is a limitation of the source
  data.


