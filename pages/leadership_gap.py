import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
from data_utils import get_filtered_df, get_options_with_counts, init_multiselect_state, get_multiselect_values
from chart_utils import get_compare_colors, get_primary_color, get_plotly_scale, get_categorical_colors

st.markdown("# :primary[:material/supervisor_account:] Leadership Gap Dashboard")
st.markdown("Analyze how leadership direction impacts team effectiveness and morale")

df = get_filtered_df()

if 'role_category' not in df.columns:
    df['role_category'] = df['role'].apply(
        lambda x: 'Leaders/Managers' if pd.notna(x) and any(kw in x.lower() for kw in ['manager', 'director', 'vp', 'lead', 'head', 'chief', 'cdo', 'cto', 'cio', 'founder']) else 'Individual Contributors'
    )

leadership_df = df[df['has_leadership_gap'] == True]
non_lead_df = df[df['has_leadership_gap'] == False]
n_leadership_gap = len(leadership_df)
pct_leadership_gap = n_leadership_gap / len(df) * 100 if len(df) > 0 else 0

with st.container(border=True):
    st.markdown("#### :primary[:material/analytics:] Leadership Gap Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Citing Leadership Gap", f"{n_leadership_gap:,}")
    col2.metric("% of Respondents", f"{pct_leadership_gap:.1f}%")
    
    if n_leadership_gap > 0:
        top_industry = leadership_df['industry'].value_counts().idxmax()
        col3.metric("Most Affected Industry", top_industry[:15] + "..." if len(top_industry) > 15 else top_industry)
        
        top_role = leadership_df['role'].value_counts().idxmax()
        col4.metric("Most Affected Role", top_role[:15] + "..." if len(top_role) > 15 else top_role)

init_multiselect_state("lead_breakdown_filter", "All values")

with st.container(border=True):
    st.markdown("#### :primary[:material/tune:] Breakdown Configuration")
    
    col1, col2 = st.columns(2)
    with col1:
        breakdown_dim = st.selectbox(
            "Break Down By:",
            options=["industry", "org_size", "role", "region", "modeling_approach", "ai_adoption"],
            format_func=lambda x: x.replace('_', ' ').title(),
            key="lead_breakdown"
        )
    with col2:
        show_as = st.radio("Show As:", ["Percentage", "Count"], horizontal=True, key="lead_show")

breakdown_opts = get_options_with_counts(df, breakdown_dim)
all_label = f"All {breakdown_dim.replace('_', ' ')}"

init_multiselect_state(f"lead_filter_{breakdown_dim}", all_label)

with st.container(border=True):
    st.markdown(f"#### :primary[:material/bar_chart:] Leadership Gap by {breakdown_dim.replace('_', ' ').title()}")
    st.caption("Select 'All' to include everything; selecting specific options removes 'All'")
    
    st.multiselect(
        f"Filter {breakdown_dim.replace('_', ' ').title()}:",
        options=[all_label] + list(breakdown_opts.keys()),
        key=f"lead_filter_{breakdown_dim}"
    )
    selected_values = get_multiselect_values(f"lead_filter_{breakdown_dim}", all_label, breakdown_opts)
    
    if selected_values:
        filtered_df = df[df[breakdown_dim].isin(selected_values)]
    else:
        filtered_df = df
    
    gap_by_dim = filtered_df.groupby(breakdown_dim).agg(
        total=('has_leadership_gap', 'count'),
        gap_count=('has_leadership_gap', 'sum')
    ).reset_index()
    gap_by_dim['gap_pct'] = (gap_by_dim['gap_count'] / gap_by_dim['total'] * 100).round(1)
    gap_by_dim = gap_by_dim[gap_by_dim['total'] >= 10]
    
    y_col = 'gap_pct' if show_as == "Percentage" else 'gap_count'
    y_title = 'Leadership Gap %' if show_as == "Percentage" else 'Count'
    
    overall_gap_pct = pct_leadership_gap
    
    top_gap = gap_by_dim.loc[gap_by_dim['gap_pct'].idxmax()] if len(gap_by_dim) > 0 else None
    bottom_gap = gap_by_dim.loc[gap_by_dim['gap_pct'].idxmin()] if len(gap_by_dim) > 0 else None
    
    bars = alt.Chart(gap_by_dim).mark_bar(cornerRadiusEnd=4).encode(
        y=alt.Y(f'{breakdown_dim}:N', sort='-x', title=None, axis=alt.Axis(labelLimit=0)),
        x=alt.X(f'{y_col}:Q', title=y_title),
        color=alt.Color(f'{breakdown_dim}:N', scale=alt.Scale(range=get_categorical_colors()), legend=None),
        tooltip=[f'{breakdown_dim}:N', alt.Tooltip('gap_pct:Q', format='.1f', title='Gap %'), 'gap_count:Q', 'total:Q']
    ).properties(height=400)
    
    if show_as == "Percentage":
        rule = alt.Chart(pd.DataFrame({'x': [overall_gap_pct]})).mark_rule(
            color='#F59E0B', strokeDash=[5, 5], strokeWidth=2
        ).encode(x='x:Q')
        chart = bars + rule
    else:
        chart = bars
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.altair_chart(chart, use_container_width=True)
        st.caption("Dashed line = overall average.")
    with col2:
        st.markdown("##### :primary[:material/lightbulb:] Key Insights")
        if top_gap is not None and bottom_gap is not None:
            diff = top_gap['gap_pct'] - bottom_gap['gap_pct']
            st.caption(f"**:primary[{top_gap[breakdown_dim][:25]}]** exhibits the highest leadership gap at **{top_gap['gap_pct']:.0f}%**, significantly {'above' if top_gap['gap_pct'] > overall_gap_pct else 'near'} the overall average of {overall_gap_pct:.0f}%. Meanwhile, **:primary[{bottom_gap[breakdown_dim][:25]}]** reports the lowest gap at **{bottom_gap['gap_pct']:.0f}%**—a **{diff:.0f}** percentage point spread that suggests leadership clarity varies considerably across {breakdown_dim.replace('_', ' ')}s.")

with st.container(border=True):
    st.markdown("#### :primary[:material/grid_on:] Multi-Dimensional View")
    
    col1, col2 = st.columns(2)
    with col1:
        row_dim = st.selectbox("Row Dimension:", 
                               options=["industry", "org_size", "role", "role_category"],
                               format_func=lambda x: "Role (IC vs Leader)" if x == "role_category" else x.replace('_', ' ').title().replace('industry', 'Industry'),
                               key="heat_row")
    with col2:
        col_dim = st.selectbox("Column Dimension:",
                               options=["org_size", "industry", "role", "role_category"],
                               index=0,
                               format_func=lambda x: "Role (IC vs Leader)" if x == "role_category" else x.replace('_', ' ').title().replace('industry', 'Industry'),
                               key="heat_col")
    
    if row_dim != col_dim:
        pivot = df.pivot_table(
            index=row_dim,
            columns=col_dim,
            values='has_leadership_gap',
            aggfunc='mean'
        ) * 100
        
        max_val = pivot.max().max()
        min_val = pivot.min().min()
        max_idx = pivot.stack().idxmax()
        min_idx = pivot.stack().idxmin()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            fig = px.imshow(
                pivot,
                color_continuous_scale=get_plotly_scale(),
                labels=dict(color="Leadership Gap %"),
                text_auto='.0f',
                aspect='auto'
            )
            fig.update_traces(xgap=1, ygap=1)
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.markdown("##### :primary[:material/lightbulb:] Key Insights")
            st.caption(f"The intersection of **:primary[{max_idx[0]}]** and **:primary[{max_idx[1]}]** shows the highest leadership gap at **{max_val:.0f}%**, while **:primary[{min_idx[0]}]** paired with **:primary[{min_idx[1]}]** reports just **{min_val:.0f}%**—a {max_val - min_val:.0f} point range revealing how leadership clarity compounds across organizational dimensions.")
    else:
        st.warning("Please select different dimensions for rows and columns.")

if n_leadership_gap > 0:
    with st.container(border=True):
        st.markdown("#### :primary[:material/compare:] Leadership Gap vs No Gap")
        
        lead_ff = leadership_df['has_firefighting'].sum() / n_leadership_gap * 100
        other_ff = non_lead_df['has_firefighting'].sum() / len(non_lead_df) * 100 if len(non_lead_df) > 0 else 0
        lead_grow = (leadership_df['team_growth_2026'] == 'Grow').sum() / n_leadership_gap * 100
        other_grow = (non_lead_df['team_growth_2026'] == 'Grow').sum() / len(non_lead_df) * 100 if len(non_lead_df) > 0 else 0
        lead_ai = leadership_df['ai_embedded'].sum() / n_leadership_gap * 100
        other_ai = non_lead_df['ai_embedded'].sum() / len(non_lead_df) * 100 if len(non_lead_df) > 0 else 0
        
        ff_diff = lead_ff - other_ff
        grow_diff = lead_grow - other_grow
        ai_diff = lead_ai - other_ai
        
        metric_order = ['Firefighting', 'Expect Growth', 'AI Embedded']
        comparison_df = pd.DataFrame([
            {'metric': 'Firefighting', 'Leadership Gap': lead_ff, 'No Gap': other_ff},
            {'metric': 'Expect Growth', 'Leadership Gap': lead_grow, 'No Gap': other_grow},
            {'metric': 'AI Embedded', 'Leadership Gap': lead_ai, 'No Gap': other_ai}
        ])
        
        col_chart, col_insights = st.columns([2, 1])
        compare_colors = get_compare_colors()
        
        with col_chart:
            m1, m2, m3 = st.columns(3)
            m1.metric("Firefighting Rate", f"{lead_ff:.1f}%", delta=f"{ff_diff:+.1f}% vs no gap", delta_color="inverse")
            m2.metric("Expect Growth", f"{lead_grow:.1f}%", delta=f"{grow_diff:+.1f}% vs no gap")
            m3.metric("AI Embedded", f"{lead_ai:.1f}%", delta=f"{ai_diff:+.1f}% vs no gap")
            
            melted = comparison_df.melt(id_vars=['metric'], value_vars=['Leadership Gap', 'No Gap'], var_name='Group', value_name='Percentage')
            chart = alt.Chart(melted).mark_bar(cornerRadiusEnd=4).encode(
                x=alt.X('metric:N', title=None, axis=alt.Axis(labelAngle=0), sort=metric_order),
                y=alt.Y('Percentage:Q', title='%'),
                color=alt.Color('Group:N', scale=alt.Scale(domain=['Leadership Gap', 'No Gap'], range=compare_colors), legend=alt.Legend(orient='bottom', title=None)),
                xOffset='Group:N',
                tooltip=['metric:N', 'Group:N', alt.Tooltip('Percentage:Q', format='.1f')]
            ).properties(height=400)
            st.altair_chart(chart, use_container_width=True)
        
        with col_insights:
            st.markdown("##### :primary[:material/lightbulb:] Key Insights")
            if ff_diff > 0:
                st.caption(f"**:primary[Firefighting:]** Time spent on reactive crisis work. Those citing leadership gaps report {ff_diff:.1f}% higher rates — lack of direction often manifests as operational chaos.")
            else:
                st.caption(f"**:primary[Firefighting:]** Time spent on reactive crisis work. Those citing leadership gaps report {abs(ff_diff):.1f}% lower rates — an unexpected finding worth investigating.")
            if grow_diff < 0:
                st.caption(f"**:primary[Growth outlook:]** Whether teams expect to grow in 2026. Those with leadership gaps are {abs(grow_diff):.1f}% less likely to anticipate growth — unclear direction dampens expansion confidence.")
            else:
                st.caption(f"**:primary[Growth outlook:]** Whether teams expect to grow in 2026. Those with leadership gaps are {grow_diff:.1f}% more likely to anticipate growth — perhaps hoping new hires will help.")
            if ai_diff < 0:
                st.caption(f"**:primary[AI embedded:]** Whether AI is integrated into workflows. Those with leadership gaps show {abs(ai_diff):.1f}% lower adoption — strategic technology decisions require clear leadership.")
            else:
                st.caption(f"**:primary[AI embedded:]** Whether AI is integrated into workflows. Those with leadership gaps show {ai_diff:.1f}% higher adoption — teams may be self-directing technology choices.")

    with st.container(border=True):
        st.markdown("#### :primary[:material/format_quote:] Voices from the Field")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Citing Leadership Gap")
            lead_wishes = leadership_df[leadership_df['industry_wish'].notna() & (leadership_df['industry_wish'] != '')]
            if len(lead_wishes) > 0:
                all_lead_text = ' '.join(lead_wishes['industry_wish'].str.lower())
                lead_themes = []
                if 'leadership' in all_lead_text or 'leader' in all_lead_text or 'direction' in all_lead_text: lead_themes.append("Leadership clarity")
                if 'strategy' in all_lead_text or 'vision' in all_lead_text: lead_themes.append("Strategic vision")
                if 'communication' in all_lead_text or 'alignment' in all_lead_text: lead_themes.append("Better communication")
                if 'resource' in all_lead_text or 'budget' in all_lead_text or 'hire' in all_lead_text: lead_themes.append("Resources")
                if 'process' in all_lead_text or 'workflow' in all_lead_text: lead_themes.append("Process improvement")
                if lead_themes:
                    st.caption(f":primary[:material/summarize:] **Common themes:** {', '.join(lead_themes)}")
                
                lead_sample = lead_wishes.sample(min(3, len(lead_wishes)))
                for _, row in lead_sample.iterrows():
                    with st.container(border=True):
                        st.markdown(f"*\"{row['industry_wish']}\"*")
                        st.caption(f"— {row['role']}, {row['industry']}")
                
                remaining = lead_wishes[~lead_wishes.index.isin(lead_sample.index)]
                if len(remaining) > 0:
                    with st.expander(f"Show more ({len(remaining)} more quotes)"):
                        for _, row in remaining.iterrows():
                            st.markdown(f"*\"{row['industry_wish']}\"*")
                            st.caption(f"— {row['role']}, {row['industry']}")
                            st.divider()
            else:
                st.info("No quotes available")
        
        with col2:
            st.markdown("##### No Leadership Gap")
            other_wishes = non_lead_df[non_lead_df['industry_wish'].notna() & (non_lead_df['industry_wish'] != '')]
            if len(other_wishes) > 0:
                all_other_text = ' '.join(other_wishes['industry_wish'].str.lower())
                other_themes = []
                if 'tool' in all_other_text or 'technology' in all_other_text: other_themes.append("Better tooling")
                if 'data' in all_other_text or 'quality' in all_other_text: other_themes.append("Data quality")
                if 'ai' in all_other_text or 'automat' in all_other_text: other_themes.append("AI/Automation")
                if 'skill' in all_other_text or 'learn' in all_other_text or 'talent' in all_other_text: other_themes.append("Skills/Talent")
                if 'time' in all_other_text or 'faster' in all_other_text: other_themes.append("Speed/Efficiency")
                if other_themes:
                    st.caption(f":primary[:material/summarize:] **Common themes:** {', '.join(other_themes)}")
                
                other_sample = other_wishes.sample(min(3, len(other_wishes)))
                for _, row in other_sample.iterrows():
                    with st.container(border=True):
                        st.markdown(f"*\"{row['industry_wish']}\"*")
                        st.caption(f"— {row['role']}, {row['industry']}")
                
                remaining = other_wishes[~other_wishes.index.isin(other_sample.index)]
                if len(remaining) > 0:
                    with st.expander(f"Show more ({len(remaining)} more quotes)"):
                        for _, row in remaining.iterrows():
                            st.markdown(f"*\"{row['industry_wish']}\"*")
                            st.caption(f"— {row['role']}, {row['industry']}")
                            st.divider()
            else:
                st.info("No quotes available")
