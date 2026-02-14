import streamlit as st

st.set_page_config(
    page_title="State of Data Engineering 2026",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="expanded"
)

from data_utils import load_survey_data, apply_global_filters, reset_filters, get_options_with_counts, init_multiselect_state, get_multiselect_values

if 'df' not in st.session_state:
    st.session_state.df = load_survey_data()

df = st.session_state.df

page_home = st.Page("pages/home.py", title="Home", icon=":material/dashboard:", default=True)
page_persona_matcher = st.Page("pages/persona_matcher.py", title="Find Your Tribe", icon=":material/people:")
page_regional_benchmark = st.Page("pages/regional_benchmark.py", title="Regional Benchmark", icon=":material/public:")
page_solo_practitioner = st.Page("pages/solo_practitioner.py", title="Solo vs Team", icon=":material/person:")
page_stack_explorer = st.Page("pages/stack_explorer.py", title="Stack Explorer", icon=":material/account_tree:")
page_data_architecture = st.Page("pages/data_architecture_at_scale.py", title="Data Architecture at Scale", icon=":material/trending_up:")
page_ai_paradox = st.Page("pages/ai_paradox.py", title="AI Paradox", icon=":material/smart_toy:")
page_ai_skeptics = st.Page("pages/ai_skeptics.py", title="AI Skeptics", icon=":material/do_not_disturb:")
page_leadership_gap = st.Page("pages/leadership_gap.py", title="Leadership Gap", icon=":material/supervisor_account:")
page_manager_self_awareness = st.Page("pages/manager_self_awareness.py", title="Manager Awareness", icon=":material/psychology:")
page_cost_consciousness = st.Page("pages/cost_consciousness.py", title="Cost Consciousness", icon=":material/payments:")
page_pain_point_explorer = st.Page("pages/pain_point_explorer.py", title="Pain Points", icon=":material/report_problem:")
page_firefighting_predictor = st.Page("pages/firefighting_predictor.py", title="Firefighting", icon=":material/local_fire_department:")
page_education_alignment = st.Page("pages/education_alignment.py", title="Education Alignment", icon=":material/school:")
page_semantic_aspiration = st.Page("pages/semantic_aspiration.py", title="Semantic Gap", icon=":material/hub:")
page_industry_voices = st.Page("pages/industry_voices.py", title="Industry Voices", icon=":material/forum:")
page_about = st.Page("pages/about.py", title="About", icon=":material/info:")

pg = st.navigation(
    {
        "": [page_home],
        "Persona": [
            page_persona_matcher,
            page_regional_benchmark,
            page_solo_practitioner,
            page_industry_voices,
        ],
        "Tech Stack": [
            page_stack_explorer,
            page_data_architecture,
        ],
        "AI Adoption": [
            page_ai_paradox,
            page_ai_skeptics,
        ],
        "Organization": [
            page_leadership_gap,
            page_manager_self_awareness,
            page_cost_consciousness,
        ],
        "Pain Points": [
            page_pain_point_explorer,
            page_firefighting_predictor,
        ],
        "Skills": [
            page_education_alignment,
            page_semantic_aspiration,
        ],
        "Info": [
            page_about,
        ],
    },
    position="top"
)

with st.sidebar:
    st.header(":primary[:material/filter_list:] Global Filters")
    
    role_exclude = ['All of above', 'All of the above']
    
    init_multiselect_state("filter_role", "All Roles")
    init_multiselect_state("filter_industry", "All Industries")
    init_multiselect_state("filter_org_size", "All Org Sizes")
    init_multiselect_state("filter_region", "All Regions")
    
    with st.container(border=True):
        st.subheader(":primary[:material/person:] Role")
        role_opts = get_options_with_counts(df[~df['role'].isin(role_exclude)], 'role')
        st.multiselect(
            "Select Role(s):",
            options=["All Roles"] + list(role_opts.keys()),
            key="filter_role",
            label_visibility="collapsed"
        )
        selected_roles = get_multiselect_values("filter_role", "All Roles", role_opts)
    
    with st.container(border=True):
        st.subheader(":primary[:material/business:] Industry")
        industry_opts = get_options_with_counts(df, 'industry')
        st.multiselect(
            "Select Industry(ies):",
            options=["All Industries"] + list(industry_opts.keys()),
            key="filter_industry",
            label_visibility="collapsed"
        )
        selected_industries = get_multiselect_values("filter_industry", "All Industries", industry_opts)
    
    with st.container(border=True):
        st.subheader(":primary[:material/groups:] Org Size")
        size_order = ["< 50 employees", "50–199", "200–999", "1,000–10,000", "10,000+"]
        org_opts = get_options_with_counts(df, 'org_size', size_order)
        st.multiselect(
            "Select Org Size(s):",
            options=["All Org Sizes"] + list(org_opts.keys()),
            key="filter_org_size",
            label_visibility="collapsed"
        )
        selected_org_sizes = get_multiselect_values("filter_org_size", "All Org Sizes", org_opts)
    
    with st.container(border=True):
        st.subheader(":primary[:material/public:] Region")
        region_opts = get_options_with_counts(df, 'region')
        st.multiselect(
            "Select Region(s):",
            options=["All Regions"] + list(region_opts.keys()),
            key="filter_region",
            label_visibility="collapsed"
        )
        selected_regions = get_multiselect_values("filter_region", "All Regions", region_opts)
    
    df_filtered = df.copy()
    if selected_roles:
        df_filtered = df_filtered[df_filtered['role'].isin(selected_roles)]
    if selected_industries:
        df_filtered = df_filtered[df_filtered['industry'].isin(selected_industries)]
    if selected_org_sizes:
        df_filtered = df_filtered[df_filtered['org_size'].isin(selected_org_sizes)]
    if selected_regions:
        df_filtered = df_filtered[df_filtered['region'].isin(selected_regions)]
    
    n_filtered = len(df_filtered)
    st.session_state.df_filtered = df_filtered
    
    st.metric("Matching Respondents", f"{n_filtered:,}", 
              delta=f"{n_filtered/len(df)*100:.1f}% of total")
    
    if st.button(":primary[:material/refresh:] Reset Filters", use_container_width=True):
        reset_filters()
        st.rerun()

pg.run()
