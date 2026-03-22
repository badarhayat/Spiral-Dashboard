# Spiral Concentrator Analysis Dashboard

A comprehensive Streamlit dashboard for analyzing spiral concentrator performance in mineral processing plants. This application provides detailed solids-based analysis of spiral performance metrics, KPIs, and operational recommendations.

## Features

- **🏭 Plant Performance Overview**: Feed distribution, mass balance, and circulating load analysis
- **🔍 Individual Spiral Analysis**: Detailed performance metrics for selected spirals
- **📊 Spiral Comparison**: Ranking and comparison of all spirals based on solids yield
- **🔬 Sensitivity Analysis**: Performance analysis across different operating conditions
- **💡 Recommendations**: Actionable insights and optimization suggestions
- **📄 PDF Report Generation**: Export key findings and recommendations to PDF

## Key Metrics

- **Solids Yield %**: Concentrate solids ÷ Total solids (target > 55%)
- **Middling %**: Middling solids ÷ Total solids (target < 25%)
- **Tailing %**: Tailing solids ÷ Total solids (target < 15%)
- **Performance Score**: Composite metric for spiral ranking

## Methodology

All calculations use **solids-only analysis** to eliminate water-related distortions:
- Solids flow = flowrate × (dry_weight / slurry_weight)
- Provides true separation efficiency metrics

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   streamlit run spiral_dashboard.py
   ```

## Data Requirements

- Excel file: `Spiral Plant Sheet.xlsx` with sheets:
  - 'Spiral Data on Actual Run'
  - 'Feed Flow Distribution Spiral'
  - 'Sensitivity Analysis Spiral 1'

## Deployment

This app is deployed on Streamlit Cloud. Access it at: [Your Streamlit Cloud URL]

## Technologies Used

- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis
- **Matplotlib**: Data visualization
- **OpenPyXL**: Excel file processing

## License

[Add your license information here]