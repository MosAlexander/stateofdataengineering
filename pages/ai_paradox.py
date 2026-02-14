import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
from data_utils import get_filtered_df, AI_ADOPTION_ORDER, get_options_with_counts, init_multiselect_state, get_multiselect_values
from chart_utils import create_donut_chart, create_gauge_chart, get_compare_colors, get_primary_color, get_secondary_color

st.markdown("# :primary[:material/smart_toy:] The AI Adoption Paradox")
st.markdown("Explore the gap between personal AI use and organizational adoption patterns")

df = get_filtered_df()

daily_ai_pct = df['daily_ai_user'].sum() / len(df) * 100 if len(df) > 0 else 0
ai_embedded_pct = df['ai_embedded'].sum() / len(df) * 100 if len(df) > 0 else 0

with st.container(border=True):
    st.markdown("#### :primary[:material/compare_arrows:] The Personal vs Organizational Gap")
    
    col1, col2, col3 = st.columns([3, 3, 2])
    
    with col1:
        st.markdown("##### Personal AI Usage")
        usage_chart = create_donut_chart(df, 'ai_usage_frequency', height=250)
        st.altair_chart(usage_chart, use_container_width=True)
        st.metric("Daily Users", f"{daily_ai_pct:.0f}%")
    
    with col2:
        st.markdown("##### Organizational AI Adoption")
        adoption_chart = create_donut_chart(df, 'ai_adoption', height=250)
        st.altair_chart(adoption_chart, use_container_width=True)
        st.metric("AI Embedded in Workflows", f"{ai_embedded_pct:.1f}%")
    
    with col3:
        st.markdown("##### :primary[:material/lightbulb:] Key Insights")
        gap = daily_ai_pct - ai_embedded_pct
        st.caption(f"A striking **{gap:.0f} percentage point** gap separates personal AI usage from organizational adoption, with **{daily_ai_pct:.0f}%** using AI daily but only **{ai_embedded_pct:.0f}%** having it embedded in workflows.")
        st.caption(f"This disconnect suggests individual experimentation is far outpacing organizational strategy—practitioners are ready, but their companies aren't.")

gap_cohort = df[(df['daily_ai_user'] == True) & (df['ai_embedded'] == False)]

with st.container(border=True):
    st.markdown("#### :primary[:material/block:] What Blocks Organizational Adoption?")
    st.markdown(f"*Analyzing {len(gap_cohort):,} respondents who use AI daily but report low org adoption*")
    
    if len(gap_cohort) > 0:
        btn_counts = gap_cohort['biggest_bottleneck'].value_counts(normalize=True).head(6) * 100
        ind_counts = gap_cohort['industry'].value_counts(normalize=True).head(6) * 100
        
        col1, col2, col3 = st.columns([3, 3, 2])
        
        with col1:
            st.markdown("##### Their Bottlenecks")
            btn_df = btn_counts.reset_index()
            btn_df.columns = ['bottleneck', 'percentage']
            chart = alt.Chart(btn_df).mark_bar(cornerRadiusEnd=4).encode(
                y=alt.Y('bottleneck:N', sort='-x', title=None),
                x=alt.X('percentage:Q', title='Percentage'),
                color=alt.value(get_compare_colors()[0])
            ).properties(height=250)
            st.altair_chart(chart, use_container_width=True)
        
        with col2:
            st.markdown("##### Their Industries")
            ind_df = ind_counts.reset_index()
            ind_df.columns = ['industry', 'percentage']
            chart = alt.Chart(ind_df).mark_bar(cornerRadiusEnd=4).encode(
                y=alt.Y('industry:N', sort='-x', title=None),
                x=alt.X('percentage:Q', title='Percentage'),
                color=alt.value(get_compare_colors()[1])
            ).properties(height=250)
            st.altair_chart(chart, use_container_width=True)
        
        with col3:
            st.markdown("##### :primary[:material/lightbulb:] Key Insights")
            top_btn = btn_counts.idxmax() if len(btn_counts) > 0 else "N/A"
            top_btn_pct = btn_counts.max() if len(btn_counts) > 0 else 0
            top_ind = ind_counts.idxmax() if len(ind_counts) > 0 else "N/A"
            top_ind_pct = ind_counts.max() if len(ind_counts) > 0 else 0
            st.caption(f":primary[{top_btn[:25]}] emerges as the primary blocker at **{top_btn_pct:.0f}%**, revealing where organizational friction is strongest.")
            st.caption(f"The :primary[{top_ind}] industry leads this gap cohort at **{top_ind_pct:.0f}%**—potentially indicating sector-specific barriers to AI adoption.")

with st.container(border=True):
    st.markdown("#### :primary[:material/sliders:] Adoption Journey Explorer")
    
    available_levels = [a for a in AI_ADOPTION_ORDER if a in df['ai_adoption'].unique()]
    adoption_level = st.select_slider(
        "AI Adoption Level:",
        options=available_levels if available_levels else ["No data"],
        value=available_levels[0] if available_levels else "No data",
        key="ai_journey"
    )
    
    level_df = df[df['ai_adoption'] == adoption_level]
    other_df = df[df['ai_adoption'] != adoption_level]
    
    if len(level_df) > 0:
        col1, col2, col3 = st.columns(3)
        col1.metric("Respondents", f"{len(level_df):,}")
        col2.metric("% of Survey", f"{len(level_df)/len(df)*100:.1f}%")
        
        top_industry = level_df['industry'].value_counts().idxmax() if len(level_df) > 0 else "N/A"
        col3.metric("Top Industry", top_industry)
        
        st.metric("Top Role", level_df['role'].value_counts().idxmax() if len(level_df) > 0 else "N/A")
        
        level_ff = level_df['has_firefighting'].sum() / len(level_df) * 100
        other_ff = other_df['has_firefighting'].sum() / len(other_df) * 100 if len(other_df) > 0 else 0
        level_growth = (level_df['team_growth_2026'] == 'Grow').sum() / len(level_df) * 100
        other_growth = (other_df['team_growth_2026'] == 'Grow').sum() / len(other_df) * 100 if len(other_df) > 0 else 0
        level_lead = level_df['has_leadership_gap'].sum() / len(level_df) * 100
        other_lead = other_df['has_leadership_gap'].sum() / len(other_df) * 100 if len(other_df) > 0 else 0
        
        col4, col5, col6 = st.columns(3)
        col4.metric("Firefighting", f"{level_ff:.0f}%", delta=f"{level_ff - other_ff:+.1f}%", delta_color="inverse")
        col5.metric("Expect Growth", f"{level_growth:.0f}%", delta=f"{level_growth - other_growth:+.1f}%")
        col6.metric("Leadership Gap", f"{level_lead:.0f}%", delta=f"{level_lead - other_lead:+.1f}%", delta_color="inverse")

segment_opts = {
    "industry": "Industry",
    "org_size": "Org Size", 
    "role": "Role",
    "region": "Region"
}

init_multiselect_state("ai_segment", "All segments")

with st.container(border=True):
    st.markdown("#### :primary[:material/explore:] Adoption Gap by Segment")
    st.caption("Select 'All' to include everything; selecting specific options removes 'All'")
    
    segment_dim = st.selectbox(
        "Segment By:",
        options=["industry", "org_size", "role", "region"],
        format_func=lambda x: x.replace('_', ' ').title(),
        key="ai_segment_dim"
    )
    
    segment_value_opts = get_options_with_counts(df, segment_dim)
    all_label = f"All {segment_dim.replace('_', ' ')}"
    
    init_multiselect_state(f"ai_segment_{segment_dim}", all_label)
    
    st.multiselect(
        f"Filter {segment_dim.replace('_', ' ').title()}:",
        options=[all_label] + list(segment_value_opts.keys()),
        key=f"ai_segment_{segment_dim}"
    )
    selected_segments = get_multiselect_values(f"ai_segment_{segment_dim}", all_label, segment_value_opts)
    
    if selected_segments:
        filtered_df = df[df[segment_dim].isin(selected_segments)]
    else:
        filtered_df = df
    
    segment_data = []
    for segment in filtered_df[segment_dim].dropna().unique():
        seg_df = filtered_df[filtered_df[segment_dim] == segment]
        if len(seg_df) >= 10:
            personal_pct = seg_df['daily_ai_user'].sum() / len(seg_df) * 100
            org_pct = seg_df['ai_embedded'].sum() / len(seg_df) * 100
            segment_data.append({
                'segment': segment[:20] + "..." if len(str(segment)) > 20 else segment,
                'Personal (Daily)': personal_pct,
                'Org (Embedded)': org_pct,
                'gap': personal_pct - org_pct
            })
    
    seg_df = pd.DataFrame(segment_data).sort_values('gap', ascending=False)
    
    melted = seg_df.melt(id_vars=['segment', 'gap'], value_vars=['Personal (Daily)', 'Org (Embedded)'],
                         var_name='type', value_name='percentage')
    
    biggest_gap = seg_df.iloc[0] if len(seg_df) > 0 else None
    smallest_gap = seg_df.iloc[-1] if len(seg_df) > 0 else None
    
    chart = alt.Chart(melted).mark_bar().encode(
        x=alt.X('segment:N', title=None, sort=alt.EncodingSortField(field='gap', order='descending')),
        y=alt.Y('percentage:Q', title='Percentage'),
        color=alt.Color('type:N', scale=alt.Scale(domain=['Personal (Daily)', 'Org (Embedded)'],
                                                   range=get_compare_colors()), legend=alt.Legend(orient='bottom', title=None)),
        xOffset='type:N',
        tooltip=['segment:N', 'type:N', alt.Tooltip('percentage:Q', format='.1f')]
    ).properties(height=400)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.altair_chart(chart, use_container_width=True)
        st.caption("Sorted by gap size (Personal - Org)")
    with col2:
        st.markdown("##### :primary[:material/lightbulb:] Key Insights")
        avg_gap = seg_df['gap'].mean() if len(seg_df) > 0 else 0
        if biggest_gap is not None:
            st.caption(f":primary[{biggest_gap['segment']}] shows the widest adoption gap at **{biggest_gap['gap']:.0f}** percentage points, indicating significant untapped organizational potential.")
        if smallest_gap is not None:
            st.caption(f"Conversely, :primary[{smallest_gap['segment']}] has the smallest gap at **{smallest_gap['gap']:.0f}** points—suggesting better alignment between individual and organizational AI adoption.")
        st.caption(f"The average gap across segments is **{avg_gap:.0f}** percentage points.")
