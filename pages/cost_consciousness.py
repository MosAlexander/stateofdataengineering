import streamlit as st
import pandas as pd
import altair as alt
from data_utils import get_filtered_df
from chart_utils import create_donut_chart, create_bar_chart, get_categorical_colors, get_compare_colors

st.markdown("# :primary[:material/payments:] Cost-Consciousness Cohort")
st.markdown("Discover which roles and industries prioritize cost optimization the most")

df = get_filtered_df()

cost_df = df[df['biggest_bottleneck'].str.contains('cost|Cost|Compute', case=False, na=False)]
non_cost_df = df[~df['biggest_bottleneck'].str.contains('cost|Cost|Compute', case=False, na=False)]

n_cost = len(cost_df)
n_non_cost = len(non_cost_df)
pct_cost = n_cost / len(df) * 100 if len(df) > 0 else 0

overview_col1, overview_col2 = st.columns(2)

with overview_col1:
    with st.container(border=True):
        st.markdown("#### :primary[:material/payments:] Cost-Concerned Overview")
        
        if n_cost > 0:
            top_industry = cost_df['industry'].value_counts().idxmax()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Cost-Concerned", f"{n_cost:,}")
            col2.metric("% of Survey", f"{pct_cost:.1f}%")
            col3.metric("Top Industry", top_industry)
            
            top_role = cost_df['role'].value_counts().idxmax()
            st.metric("Top Role", top_role)
            
            cost_ff = cost_df['has_firefighting'].sum() / n_cost * 100
            non_cost_ff = non_cost_df['has_firefighting'].sum() / n_non_cost * 100 if n_non_cost > 0 else 0
            cost_growth = (cost_df['team_growth_2026'] == 'Grow').sum() / n_cost * 100
            non_cost_growth = (non_cost_df['team_growth_2026'] == 'Grow').sum() / n_non_cost * 100 if n_non_cost > 0 else 0
            cost_lead = cost_df['has_leadership_gap'].sum() / n_cost * 100
            non_cost_lead = non_cost_df['has_leadership_gap'].sum() / n_non_cost * 100 if n_non_cost > 0 else 0
            
            col4, col5, col6 = st.columns(3)
            col4.metric("Firefighting", f"{cost_ff:.0f}%", delta=f"{cost_ff - non_cost_ff:+.1f}%", delta_color="inverse")
            col5.metric("Expect Growth", f"{cost_growth:.0f}%", delta=f"{cost_growth - non_cost_growth:+.1f}%")
            col6.metric("Leadership Gap", f"{cost_lead:.0f}%", delta=f"{cost_lead - non_cost_lead:+.1f}%", delta_color="inverse")
            
            st.caption(f"This cohort of **{n_cost:,}** respondents ({pct_cost:.1f}% of the survey) identifies cost as their primary bottleneck. Predominantly **{top_role}s** from the **{top_industry}** sector, they report {'lower' if cost_ff < non_cost_ff else 'higher'} firefighting rates ({cost_ff:.0f}% vs {non_cost_ff:.0f}%) and {'stronger' if cost_growth > non_cost_growth else 'weaker'} growth expectations compared to their peers.")

with overview_col2:
    with st.container(border=True):
        st.markdown("#### :primary[:material/check_circle:] Non-Cost-Concerned Overview")
        
        if n_non_cost > 0:
            non_cost_top_industry = non_cost_df['industry'].value_counts().idxmax()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Non-Cost-Concerned", f"{n_non_cost:,}")
            col2.metric("% of Survey", f"{100 - pct_cost:.1f}%")
            col3.metric("Top Industry", non_cost_top_industry)
            
            non_cost_top_role = non_cost_df['role'].value_counts().idxmax()
            st.metric("Top Role", non_cost_top_role)
            
            non_cost_ff = non_cost_df['has_firefighting'].sum() / n_non_cost * 100
            cost_ff = cost_df['has_firefighting'].sum() / n_cost * 100 if n_cost > 0 else 0
            non_cost_growth = (non_cost_df['team_growth_2026'] == 'Grow').sum() / n_non_cost * 100
            cost_growth = (cost_df['team_growth_2026'] == 'Grow').sum() / n_cost * 100 if n_cost > 0 else 0
            non_cost_lead = non_cost_df['has_leadership_gap'].sum() / n_non_cost * 100
            cost_lead = cost_df['has_leadership_gap'].sum() / n_cost * 100 if n_cost > 0 else 0
            
            col4, col5, col6 = st.columns(3)
            col4.metric("Firefighting", f"{non_cost_ff:.0f}%", delta=f"{non_cost_ff - cost_ff:+.1f}%", delta_color="inverse")
            col5.metric("Expect Growth", f"{non_cost_growth:.0f}%", delta=f"{non_cost_growth - cost_growth:+.1f}%")
            col6.metric("Leadership Gap", f"{non_cost_lead:.0f}%", delta=f"{non_cost_lead - cost_lead:+.1f}%", delta_color="inverse")
            
            st.caption(f"The majority (**{n_non_cost:,}** respondents, {100 - pct_cost:.1f}%) cite bottlenecks other than cost. While also led by **{non_cost_top_role}s** in **{non_cost_top_industry}**, this group shows {'higher' if non_cost_ff > cost_ff else 'lower'} firefighting ({non_cost_ff:.0f}%) and a notable leadership gap of {non_cost_lead:.0f}%—suggesting their challenges lie more in operational and organizational dimensions than budget constraints.")

with st.container(border=True):
    st.markdown("#### :primary[:material/bar_chart:] Cost Concerns by Segment")
    
    segment_dim = st.selectbox(
        "Segment by:",
        options=["storage_environment", "architecture_trend", "org_size", "industry"],
        format_func=lambda x: x.replace('_', ' ').title(),
        key="cost_segment"
    )
    
    cost_by_segment = df.groupby(segment_dim).agg(
        total=('biggest_bottleneck', 'count'),
        cost_count=('biggest_bottleneck', lambda x: x.str.contains('cost|Cost|Compute', case=False, na=False).sum())
    ).reset_index()
    cost_by_segment['cost_pct'] = (cost_by_segment['cost_count'] / cost_by_segment['total'] * 100).round(1)
    cost_by_segment = cost_by_segment[cost_by_segment['total'] >= 10]
    cost_by_segment = cost_by_segment.sort_values('cost_pct', ascending=False)
    
    top_segment = cost_by_segment.iloc[0][segment_dim] if len(cost_by_segment) > 0 else "N/A"
    top_pct = cost_by_segment.iloc[0]['cost_pct'] if len(cost_by_segment) > 0 else 0
    bottom_segment = cost_by_segment.iloc[-1][segment_dim] if len(cost_by_segment) > 0 else "N/A"
    bottom_pct = cost_by_segment.iloc[-1]['cost_pct'] if len(cost_by_segment) > 0 else 0
    
    segment_colors = get_categorical_colors()[:len(cost_by_segment)]
    chart = alt.Chart(cost_by_segment).mark_bar(cornerRadiusEnd=4).encode(
        y=alt.Y(f'{segment_dim}:N', sort='-x', title=None, axis=alt.Axis(labelLimit=0)),
        x=alt.X('cost_pct:Q', title='% Citing Cost Issues'),
        color=alt.Color(f'{segment_dim}:N', scale=alt.Scale(domain=cost_by_segment[segment_dim].tolist(), range=segment_colors), legend=None),
        tooltip=[f'{segment_dim}:N', alt.Tooltip('cost_pct:Q', format='.1f'), 'cost_count:Q', 'total:Q']
    ).properties(height=400)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.altair_chart(chart, use_container_width=True)
    with col2:
        st.markdown("##### :primary[:material/lightbulb:] Key Insights")
        st.caption(f":primary[{top_segment[:20]}] leads in cost concerns at **{top_pct:.0f}%**, suggesting this segment faces the most significant cloud billing pressure.")
        st.caption(f"In contrast, :primary[{bottom_segment[:20]}] shows the lowest cost concern at **{bottom_pct:.0f}%**—a **{top_pct - bottom_pct:.0f}** percentage point gap that may reflect different scale or architecture choices.")

if n_cost > 0:
    with st.container(border=True):
        st.markdown("#### :primary[:material/compare:] Cost-Concerned vs Others Comparison")
        
        cost_btn = cost_df['biggest_bottleneck'].value_counts(normalize=True).head(5) * 100
        non_cost_btn = non_cost_df['biggest_bottleneck'].value_counts(normalize=True).head(5) * 100
        
        cost_btn_df = cost_btn.reset_index()
        cost_btn_df.columns = ['bottleneck', 'percentage']
        cost_btn_df['group'] = 'Cost-Concerned'
        
        non_cost_btn_df = non_cost_btn.reset_index()
        non_cost_btn_df.columns = ['bottleneck', 'percentage']
        non_cost_btn_df['group'] = 'Others'
        
        combined = pd.concat([cost_btn_df, non_cost_btn_df])
        
        chart = alt.Chart(combined).mark_bar(cornerRadiusEnd=4).encode(
            y=alt.Y('bottleneck:N', sort='-x', title=None, axis=alt.Axis(labelLimit=0)),
            x=alt.X('percentage:Q', title='Percentage'),
            color=alt.Color('group:N', scale=alt.Scale(domain=['Cost-Concerned', 'Others'], range=get_compare_colors()), legend=alt.Legend(orient='bottom', title=None)),
            xOffset='group:N',
            tooltip=['bottleneck:N', 'group:N', alt.Tooltip('percentage:Q', format='.1f')]
        ).properties(height=400)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.altair_chart(chart, use_container_width=True)
        with col2:
            st.markdown("##### :primary[:material/lightbulb:] Key Insights")
            cost_top = cost_btn.idxmax() if len(cost_btn) > 0 else "N/A"
            cost_top_pct = cost_btn.max() if len(cost_btn) > 0 else 0
            non_cost_top = non_cost_btn.idxmax() if len(non_cost_btn) > 0 else "N/A"
            non_cost_top_pct = non_cost_btn.max() if len(non_cost_btn) > 0 else 0
            st.caption(f"For the Cost-Concerned group, :primary[{cost_top}] is the dominant bottleneck at **{cost_top_pct:.0f}%**.")
            st.caption(f"Others prioritize :primary[{non_cost_top}] at **{non_cost_top_pct:.0f}%**, revealing fundamentally different pain point profiles between the two cohorts.")
    
    with st.container(border=True):
        st.markdown("#### :primary[:material/pie_chart:] Cost-Concerned Profile")
        
        cost_storage = cost_df['storage_environment'].value_counts(normalize=True).head(5) * 100
        cost_size = cost_df['org_size'].value_counts(normalize=True).head(5) * 100
        
        col1, col2, col3 = st.columns([3, 3, 2])
        
        with col1:
            st.markdown("##### Storage Environment")
            storage_chart = create_donut_chart(cost_df, 'storage_environment', height=310, legend_offset=-10)
            st.altair_chart(storage_chart, use_container_width=True)
        
        with col2:
            st.markdown("##### Organization Size")
            size_chart = create_donut_chart(cost_df, 'org_size', height=310, legend_offset=-10)
            st.altair_chart(size_chart, use_container_width=True)
        
        with col3:
            st.markdown("##### :primary[:material/lightbulb:] Key Insights")
            top_storage = cost_storage.idxmax() if len(cost_storage) > 0 else "N/A"
            top_storage_pct = cost_storage.max() if len(cost_storage) > 0 else 0
            top_size = cost_size.idxmax() if len(cost_size) > 0 else "N/A"
            top_size_pct = cost_size.max() if len(cost_size) > 0 else 0
            st.caption(f":primary[{top_storage}] dominates storage choices among the cost-concerned at **{top_storage_pct:.0f}%**, potentially indicating cost-optimization patterns in storage selection.")
            st.caption(f"Organizations of :primary[{top_size}] size make up **{top_size_pct:.0f}%** of this cohort—revealing which organizational scales feel cost pressure most acutely.")
    
    with st.container(border=True):
        st.markdown("#### :primary[:material/format_quote:] Voices from the Field")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Cost-Concerned")
            cost_wishes = cost_df[cost_df['industry_wish'].notna() & (cost_df['industry_wish'] != '')]
            if len(cost_wishes) > 0:
                cost_sample = cost_wishes.sample(min(3, len(cost_wishes)))
                for _, row in cost_sample.iterrows():
                    with st.container(border=True):
                        st.markdown(f"*\"{row['industry_wish']}\"*")
                        st.caption(f"— {row['role']}, {row['industry']}")
                
                remaining = cost_wishes[~cost_wishes.index.isin(cost_sample.index)]
                if len(remaining) > 0:
                    with st.expander(f"Show more ({len(remaining)} more quotes)"):
                        for _, row in remaining.iterrows():
                            st.markdown(f"*\"{row['industry_wish']}\"*")
                            st.caption(f"— {row['role']}, {row['industry']}")
                            st.divider()
            else:
                st.info("No quotes available")
        
        with col2:
            st.markdown("##### Others")
            other_wishes = non_cost_df[non_cost_df['industry_wish'].notna() & (non_cost_df['industry_wish'] != '')]
            if len(other_wishes) > 0:
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
