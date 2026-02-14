import streamlit as st
import pandas as pd
from data_utils import get_filtered_df

st.markdown("# :primary[:material/info:] About This App")
st.markdown("Learn about the methodology and technology behind this interactive dashboard")

df = st.session_state.df

col_left, col_right = st.columns(2)

with col_left:
    with st.container(border=True):
        st.markdown("#### :primary[:material/science:] Methodology")
        
        st.markdown(f"""
This dashboard provides an interactive exploration of the **2026 State of Data Engineering Survey** conducted by 
[Joe Reis](https://joereis.github.io/practical_data_data_eng_survey/).

**Data Characteristics**
- **{len(df):,} respondents** from data engineering practitioners worldwide
- Respondents represent **{df['region'].nunique()} regions**, **{df['industry'].nunique()} industries**, and **{df['role'].nunique()} roles**
- The dataset captures insights on technology choices, pain points, AI adoption, and organizational challenges

**Analysis Approach**
- **Segmentation**: Data is segmented to enable comparative analysis:
  - *Role categories*: Aggregated into "Leaders/Managers" (titles containing manager, director, VP, lead, head, chief, founder) vs "Individual Contributors" (data engineer, analytics engineer, software engineer, architect, analyst)
  - *Organization size*: 5 tiers from <50 employees to 10,000+
  - *Region & Industry*: Self-reported geographic and sector classifications
- **Derived Metrics**: Key indicators computed from survey responses:
  - *Firefighting rate*: % citing "Fighting fires" in team focus
  - *Leadership gap*: % citing "Lack of leadership" as biggest bottleneck
  - *AI embedded*: % with "AI embedded in most workflows"
- **Cross-tabulation**: Relationships between variables are explored through grouped comparisons and co-occurrence analysis
- **Dynamic Filtering**: Global filters allow users to drill down into specific cohorts while maintaining context across all pages
""")

with col_right:
    with st.container(border=True):
        st.markdown("#### :primary[:material/code:] Tech Stack")
        
        st.markdown("##### Core Framework")
        core_df = pd.DataFrame([
            {"Library": ["Streamlit"], "Purpose": "Web application framework and UI components"},
            {"Library": ["Pandas"], "Purpose": "Data wrangling and analysis"},
            {"Library": ["NumPy"], "Purpose": "Numerical computations"},
            {"Library": ["textwrap"], "Purpose": "Text formatting and wrapping"},
        ])
        st.dataframe(
            core_df,
            column_config={
                "Library": st.column_config.MultiselectColumn(
                    "Library",
                    options=["Streamlit", "Pandas", "NumPy", "textwrap"],
                    color=["#EF4444", "#3B82F6", "#10B981", "#FACC15"],
                ),
            },
            hide_index=True,
            use_container_width=True,
        )
        
        st.markdown("##### Data Visualization")
        viz_df = pd.DataFrame([
            {"Library": ["Altair"], "Purpose": "Declarative statistical visualizations"},
            {"Library": ["Plotly"], "Purpose": "Interactive charts (heatmaps, radar, sankey)"},
        ])
        st.dataframe(
            viz_df,
            column_config={
                "Library": st.column_config.MultiselectColumn(
                    "Library",
                    options=["Altair", "Plotly"],
                    color=["#F59E0B", "#8B5CF6"],
                ),
            },
            hide_index=True,
            use_container_width=True,
        )
        
        st.markdown("##### Key Features Used")
        st.markdown("""
- **Multi-page Navigation**: `st.navigation()` with grouped sections
- **Session State**: Persistent filters and cached data across pages
- **Caching**: `@st.cache_data` for optimized data loading
- **Responsive Layout**: `st.columns()` for adaptive grid layouts
- **Interactive Widgets**: Sliders, multiselects, and radio buttons
- **Custom Theming**: Consistent color palette via `chart_utils`
""")

with st.container(border=True):
    st.markdown("#### :primary[:material/architecture:] Application Structure")
    
    st.code("""
state-of-engineering/
├── app.py                      # Main entry point with navigation & global filters
├── data_utils.py               # Data loading, filtering, and helper functions
├── chart_utils.py              # Reusable chart components and color schemes
├── survey.csv                  # Source survey data
└── pages/
    ├── home.py                        # Dashboard overview
    ├── persona_matcher.py             # Find similar practitioners
    ├── regional_benchmark.py          # Regional comparisons
    ├── solo_practitioner.py           # Team size analysis
    ├── ai_paradox.py                  # AI adoption patterns
    ├── ai_skeptics.py                 # AI skeptic profiles
    ├── leadership_gap.py              # Leadership impact analysis
    ├── manager_self_awareness.py      # Manager vs IC perspectives
    ├── stack_explorer.py              # Technology combinations
    ├── data_architecture_at_scale.py  # Architecture evolution
    ├── semantic_aspiration.py         # Semantic layer adoption
    ├── pain_point_explorer.py         # Pain point correlations
    ├── firefighting_predictor.py      # Operational burden analysis
    ├── cost_consciousness.py          # Cost optimization focus
    ├── education_alignment.py         # Skills gap analysis
    ├── industry_voices.py             # Practitioner perspectives
    └── about.py                       # This page
    """, language="text")

with st.container(border=True):
    st.markdown("#### :primary[:material/menu:] Page Descriptions")
    
    page_data = pd.DataFrame([
        {"Section": ["—"], "Page": "Home", "Purpose": "Dashboard overview with key metrics and navigation"},
        {"Section": ["Persona"], "Page": "Find Your Tribe", "Purpose": "Match your profile with similar practitioners"},
        {"Section": ["Persona"], "Page": "Regional Benchmark", "Purpose": "Compare metrics across global regions"},
        {"Section": ["Persona"], "Page": "Solo vs Team", "Purpose": "Analyze team structure differences"},
        {"Section": ["Persona"], "Page": "Industry Voices", "Purpose": "Hear practitioner perspectives"},
        {"Section": ["Tech Stack"], "Page": "Stack Explorer", "Purpose": "Discover technology combinations"},
        {"Section": ["Tech Stack"], "Page": "Data Architecture", "Purpose": "See how architecture scales"},
        {"Section": ["AI Adoption"], "Page": "AI Paradox", "Purpose": "Explore personal vs organizational AI adoption"},
        {"Section": ["AI Adoption"], "Page": "AI Skeptics", "Purpose": "Profile practitioners skeptical of AI"},
        {"Section": ["Organization"], "Page": "Leadership Gap", "Purpose": "Analyze leadership direction impact"},
        {"Section": ["Organization"], "Page": "Manager Awareness", "Purpose": "Compare manager vs IC perspectives"},
        {"Section": ["Organization"], "Page": "Cost Consciousness", "Purpose": "Identify cost-focused cohorts"},
        {"Section": ["Pain Points"], "Page": "Pain Points", "Purpose": "Analyze pain point correlations"},
        {"Section": ["Pain Points"], "Page": "Firefighting", "Purpose": "Predict operational burden"},
        {"Section": ["Skills"], "Page": "Education Alignment", "Purpose": "Compare learning vs skill gaps"},
        {"Section": ["Skills"], "Page": "Semantic Gap", "Purpose": "Explore semantic layer adoption"},
        {"Section": ["Info"], "Page": "About", "Purpose": "Methodology and tech stack (this page)"},
    ])
    
    section_options = ["—", "Persona", "Tech Stack", "AI Adoption", "Organization", "Pain Points", "Skills", "Info"]
    section_colors = ["#6B7280", "#8B5CF6", "#3B82F6", "#10B981", "#FACC15", "#F59E0B", "#EF4444", "#EC4899"]
    
    st.dataframe(
        page_data,
        column_config={
            "Section": st.column_config.MultiselectColumn(
                "Section",
                options=section_options,
                color=section_colors,
            ),
        },
        hide_index=True,
        use_container_width=True,
    )

with st.container(border=True):
    st.markdown("#### :primary[:material/favorite:] Acknowledgments")
    st.markdown("""
- **Survey Data**: [Joe Reis' 2026 Practical Data Community State of Data Engineering](https://joereis.github.io/practical_data_data_eng_survey/)
""")
