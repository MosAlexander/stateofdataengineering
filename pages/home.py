import streamlit as st
import pandas as pd
import altair as alt
from data_utils import get_filtered_df, get_value_counts_pct
from chart_utils import create_donut_chart, create_bar_chart, create_lollipop_chart, get_categorical_colors

st.markdown("# :primary[:material/dashboard:] State of Data Engineering 2026")
st.caption("Based on data from [Joe Reis' 2026 Practical Data Community State of Data Engineering](https://joereis.github.io/practical_data_data_eng_survey/)")
st.markdown("Interactive exploration of data engineering practitioners' insights")

df = get_filtered_df()

with st.container(border=True):
    st.markdown("#### :primary[:material/analytics:] Survey Overview")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1.metric("Total Respondents", f"{len(df):,}")
    col2.metric("Regions", f"{df['region'].nunique()}")
    col3.metric("Industries", f"{df['industry'].nunique()}")
    
    daily_ai_pct = (df['daily_ai_user'].sum() / len(df) * 100)
    col4.metric("Daily AI Users", f"{daily_ai_pct:.0f}%")
    
    top_bottleneck = df['biggest_bottleneck'].value_counts().idxmax() if len(df) > 0 else "N/A"
    top_bottleneck_short = top_bottleneck[:20] + "..." if len(top_bottleneck) > 20 else top_bottleneck
    col5.metric("Top Bottleneck", top_bottleneck_short)

with st.container(border=True):
    st.markdown("#### :primary[:material/lightbulb:] Key Findings")
    
    storage_unique = df['storage_environment'].nunique()
    bottleneck_unique = df['biggest_bottleneck'].nunique()
    
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
    with col_ctrl1:
        storage_top_n = st.slider("Storage categories", 3, storage_unique, min(5, storage_unique), key="home_storage_n")
    with col_ctrl2:
        orch_min_pct = st.slider("Min orch. % to show", 0, 15, 3, key="home_orch_min")
    with col_ctrl3:
        bottleneck_top_n = st.slider("Bottleneck categories", 3, bottleneck_unique, min(6, bottleneck_unique), key="home_btn_n")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("##### :primary[:material/storage:] Storage Trends")
        storage_counts = get_value_counts_pct(df, 'storage_environment', top_n=storage_top_n)
        storage_counts['storage_label'] = storage_counts['storage_environment'].str.replace(r'\s*\(.*\)', '', regex=True)
        storage_chart = alt.Chart(storage_counts).mark_bar(cornerRadiusEnd=4).encode(
            y=alt.Y('storage_label:N', sort='-x', title=None, axis=alt.Axis(labelLimit=0)),
            x=alt.X('count:Q', title='Respondents'),
            color=alt.Color('storage_label:N', scale=alt.Scale(range=get_categorical_colors()), legend=None),
            tooltip=['storage_label:N', 'count:Q', alt.Tooltip('percentage:Q', format='.1f', title='%')]
        ).properties(height=320)
        st.altair_chart(storage_chart, use_container_width=True)
        top_storage = storage_counts.iloc[0]['storage_environment'] if len(storage_counts) > 0 else "N/A"
        top_storage_pct = storage_counts.iloc[0]['percentage'] if len(storage_counts) > 0 else 0
        second_storage = storage_counts.iloc[1]['storage_environment'] if len(storage_counts) > 1 else "N/A"
        second_storage_pct = storage_counts.iloc[1]['percentage'] if len(storage_counts) > 1 else 0
        st.caption(f"**{top_storage}** leads at {top_storage_pct:.0f}%, followed by **{second_storage}** at {second_storage_pct:.0f}%. Cloud-first architectures dominate modern data engineering. Lakehouse adoption signals a shift toward unified analytics.")
    
    with col2:
        st.markdown("##### :primary[:material/account_tree:] Orchestration")
        orch_counts = get_value_counts_pct(df, 'orchestration')
        orch_counts = orch_counts[orch_counts['percentage'] >= orch_min_pct]
        chart = alt.Chart(orch_counts).mark_bar(cornerRadiusEnd=4).encode(
            y=alt.Y('orchestration:N', sort='-x', title=None),
            x=alt.X('count:Q', title='Respondents'),
            color=alt.Color('orchestration:N', scale=alt.Scale(range=get_categorical_colors()), legend=None),
            tooltip=['orchestration:N', 'count:Q', alt.Tooltip('percentage:Q', format='.1f', title='%')]
        ).properties(height=320)
        st.altair_chart(chart, use_container_width=True)
        top_orch = orch_counts.iloc[0]['orchestration'] if len(orch_counts) > 0 else "N/A"
        top_orch_pct = orch_counts.iloc[0]['percentage'] if len(orch_counts) > 0 else 0
        no_orch_pct = orch_counts[orch_counts['orchestration'].str.contains('No orch', case=False, na=False)]['percentage'].values
        no_orch_msg = f" Surprisingly, {no_orch_pct[0]:.0f}% use no orchestration at all." if len(no_orch_pct) > 0 else ""
        st.caption(f"**{top_orch}** dominates at {top_orch_pct:.0f}%.{no_orch_msg} The orchestration landscape remains fragmented despite clear leaders.")
    
    with col3:
        st.markdown("##### :primary[:material/warning:] Biggest Bottlenecks")
        btn_counts = get_value_counts_pct(df, 'biggest_bottleneck', top_n=bottleneck_top_n)
        chart = create_lollipop_chart(btn_counts, 'biggest_bottleneck', 'percentage', height=320, varied_colors=True)
        st.altair_chart(chart, use_container_width=True)
        top_btn = btn_counts.iloc[0]['biggest_bottleneck'] if len(btn_counts) > 0 else "N/A"
        top_btn_pct = btn_counts.iloc[0]['percentage'] if len(btn_counts) > 0 else 0
        second_btn = btn_counts.iloc[1]['biggest_bottleneck'] if len(btn_counts) > 1 else "N/A"
        second_btn_pct = btn_counts.iloc[1]['percentage'] if len(btn_counts) > 1 else 0
        st.caption(f"**{top_btn}** tops at {top_btn_pct:.0f}%, with **{second_btn}** close behind at {second_btn_pct:.0f}%. Technical and organizational issues outweigh pure data challenges. Addressing these requires cultural change, not just better tools.")

with st.container(border=True):
    st.markdown("#### :primary[:material/explore:] Explore the Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.markdown("##### :primary[:material/people:] Find Your Tribe")
            st.markdown("Input your profile and find practitioners with similar backgrounds and challenges")
            if st.button("Explore →", key="nav_persona"):
                st.switch_page("pages/persona_matcher.py")
    
    with col2:
        with st.container(border=True):
            st.markdown("##### :primary[:material/person:] Solo vs Team")
            st.markdown("Compare challenges and tools across team structures and sizes")
            if st.button("Explore →", key="nav_solo"):
                st.switch_page("pages/solo_practitioner.py")
    
    with col3:
        with st.container(border=True):
            st.markdown("##### :primary[:material/public:] Regional Benchmark")
            st.markdown("Compare metrics and trends across different global regions and markets")
            if st.button("Explore →", key="nav_regional"):
                st.switch_page("pages/regional_benchmark.py")
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        with st.container(border=True):
            st.markdown("##### :primary[:material/smart_toy:] AI Paradox")
            st.markdown("Explore the gap between personal AI use and organizational adoption patterns")
            if st.button("Explore →", key="nav_ai"):
                st.switch_page("pages/ai_paradox.py")
    
    with col5:
        with st.container(border=True):
            st.markdown("##### :primary[:material/do_not_disturb:] AI Skeptics")
            st.markdown("Profile practitioners who remain skeptical about AI adoption and tools")
            if st.button("Explore →", key="nav_skeptics"):
                st.switch_page("pages/ai_skeptics.py")
    
    with col6:
        with st.container(border=True):
            st.markdown("##### :primary[:material/supervisor_account:] Leadership Gap")
            st.markdown("Analyze how leadership direction impacts team effectiveness and morale")
            if st.button("Explore →", key="nav_leader"):
                st.switch_page("pages/leadership_gap.py")
    
    col7, col8, col9 = st.columns(3)
    
    with col7:
        with st.container(border=True):
            st.markdown("##### :primary[:material/psychology:] Manager Awareness")
            st.markdown("Compare manager vs IC perspectives on leadership challenges and gaps")
            if st.button("Explore →", key="nav_manager"):
                st.switch_page("pages/manager_self_awareness.py")
    
    with col8:
        with st.container(border=True):
            st.markdown("##### :primary[:material/account_tree:] Stack Explorer")
            st.markdown("Discover popular technology stack combinations and tool pairings")
            if st.button("Explore →", key="nav_stack"):
                st.switch_page("pages/stack_explorer.py")
    
    with col9:
        with st.container(border=True):
            st.markdown("##### :primary[:material/trending_up:] Data Architecture")
            st.markdown("Explore how data architecture patterns evolve with organizational scale")
            if st.button("Explore →", key="nav_arch"):
                st.switch_page("pages/data_architecture_at_scale.py")
    
    col10, col11, col12 = st.columns(3)
    
    with col10:
        with st.container(border=True):
            st.markdown("##### :primary[:material/hub:] Semantic Gap")
            st.markdown("Explore the gap between semantic layer goals and actual adoption rates")
            if st.button("Explore →", key="nav_semantic"):
                st.switch_page("pages/semantic_aspiration.py")
    
    with col11:
        with st.container(border=True):
            st.markdown("##### :primary[:material/report_problem:] Pain Points")
            st.markdown("Explore pain point co-occurrence patterns and common challenge clusters")
            if st.button("Explore →", key="nav_pain"):
                st.switch_page("pages/pain_point_explorer.py")
    
    with col12:
        with st.container(border=True):
            st.markdown("##### :primary[:material/local_fire_department:] Firefighting")
            st.markdown("See how semantic layer adoption reduces reactive work and firefighting")
            if st.button("Explore →", key="nav_fire"):
                st.switch_page("pages/firefighting_predictor.py")
    
    col13, col14, col15 = st.columns(3)
    
    with col13:
        with st.container(border=True):
            st.markdown("##### :primary[:material/payments:] Cost Consciousness")
            st.markdown("Discover which roles and industries prioritize cost optimization the most")
            if st.button("Explore →", key="nav_cost"):
                st.switch_page("pages/cost_consciousness.py")
    
    with col14:
        with st.container(border=True):
            st.markdown("##### :primary[:material/school:] Education Alignment")
            st.markdown("Compare what practitioners want to learn vs actual skill gaps")
            if st.button("Explore →", key="nav_edu"):
                st.switch_page("pages/education_alignment.py")
    
    with col15:
        with st.container(border=True):
            st.markdown("##### :primary[:material/forum:] Industry Voices")
            st.markdown("Discover what data practitioners wish the industry understood better")
            if st.button("Explore →", key="nav_voices"):
                st.switch_page("pages/industry_voices.py")
