import streamlit as st
import pandas as pd
import altair as alt
from data_utils import get_filtered_df, ORG_SIZE_ORDER, get_options_with_counts, init_multiselect_state, get_multiselect_values
from chart_utils import create_bar_chart, get_categorical_colors

st.markdown("# :primary[:material/local_fire_department:] Firefighting Predictor")
st.markdown("See how semantic layer adoption reduces reactive work and firefighting")

df = get_filtered_df()

n_firefighting = df['has_firefighting'].sum()
pct_firefighting = n_firefighting / len(df) * 100 if len(df) > 0 else 0

with st.container(border=True):
    st.markdown("#### :primary[:material/analytics:] Firefighting Overview")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Teams Firefighting", f"{n_firefighting:,}")
    col2.metric("% of Survey", f"{pct_firefighting:.1f}%")
    
    ff_by_modeling = df.groupby('modeling_approach')['has_firefighting'].mean() * 100
    if len(ff_by_modeling) > 0:
        highest_risk = ff_by_modeling.idxmax()
        col3.metric("Highest Risk Factor", highest_risk[:20] + "..." if len(highest_risk) > 20 else highest_risk)

modeling_opts = get_options_with_counts(df, 'modeling_approach')
orch_opts = get_options_with_counts(df, 'orchestration')
size_opts = get_options_with_counts(df, 'org_size', ORG_SIZE_ORDER)

init_multiselect_state("calc_model", "All modeling")
init_multiselect_state("calc_orch", "All orchestration")
init_multiselect_state("calc_size", "All sizes")

with st.container(border=True):
    st.markdown("#### :primary[:material/calculate:] Risk Score Calculator")
    st.markdown("*Select your factors to see predicted firefighting risk*")
    st.caption("Select 'All' to include everything; selecting specific options removes 'All'")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.multiselect(
            "Your Modeling Approach:",
            options=["All modeling"] + list(modeling_opts.keys()),
            key="calc_model"
        )
        selected_modeling = get_multiselect_values("calc_model", "All modeling", modeling_opts)
        
        st.multiselect(
            "Your Orchestration:",
            options=["All orchestration"] + list(orch_opts.keys()),
            key="calc_orch"
        )
        selected_orch = get_multiselect_values("calc_orch", "All orchestration", orch_opts)
        
        st.multiselect(
            "Your Org Size:",
            options=["All sizes"] + list(size_opts.keys()),
            key="calc_size"
        )
        selected_sizes = get_multiselect_values("calc_size", "All sizes", size_opts)
    
    with col2:
        with st.container(border=True):
            similar_df = df.copy()
            filters_applied = []
            if selected_modeling:
                similar_df = similar_df[similar_df['modeling_approach'].isin(selected_modeling)]
                filters_applied.append('modeling')
            if selected_orch:
                similar_df = similar_df[similar_df['orchestration'].isin(selected_orch)]
                filters_applied.append('orchestration')
            if selected_sizes:
                similar_df = similar_df[similar_df['org_size'].isin(selected_sizes)]
                filters_applied.append('org_size')
        
            fallback_used = None
            if len(similar_df) == 0 and len(filters_applied) > 1:
                similar_df = df.copy()
                if selected_modeling:
                    similar_df = similar_df[similar_df['modeling_approach'].isin(selected_modeling)]
                fallback_used = "modeling approach only"
        
            if len(similar_df) >= 5:
                predicted_risk = similar_df['has_firefighting'].mean() * 100
                st.metric("Predicted Risk", f"{predicted_risk:.0f}%")
                st.progress(int(min(predicted_risk, 100)))
                if fallback_used:
                    st.warning(f"Based on {fallback_used} ({len(similar_df)} respondents)")
                else:
                    st.success(f"Based on {len(similar_df)} similar respondents")
                
                if predicted_risk > pct_firefighting:
                    st.caption(f":primary[:material/warning:] **{predicted_risk - pct_firefighting:.0f}% above average**")
                else:
                    st.caption(f":primary[:material/check:] **{pct_firefighting - predicted_risk:.0f}% below average**")
            elif len(similar_df) > 0:
                predicted_risk = similar_df['has_firefighting'].mean() * 100
                st.metric("Predicted Risk", f"{predicted_risk:.0f}%")
                st.progress(int(min(predicted_risk, 100)))
                st.warning(f"Low sample: only {len(similar_df)} similar respondents")
            else:
                st.metric("Predicted Risk", "N/A")
                st.info("No matching data - try broader selections")

with st.container(border=True):
    st.markdown("#### :primary[:material/bar_chart:] Firefighting Rate by Factor")
    
    risk_factor = st.selectbox(
        "Analyze Factor:",
        options=["modeling_approach", "orchestration", "ai_adoption", 
                 "org_size", "industry", "architecture_trend"],
        format_func=lambda x: x.replace('_', ' ').title().replace('Ai ', 'AI '),
        key="ff_factor"
    )
    
    ff_by_factor = df.groupby(risk_factor).agg(
        total=('has_firefighting', 'count'),
        firefighting=('has_firefighting', 'sum')
    ).reset_index()
    ff_by_factor['ff_rate'] = (ff_by_factor['firefighting'] / ff_by_factor['total'] * 100).round(1)
    ff_by_factor = ff_by_factor[ff_by_factor['total'] >= 10]
    ff_by_factor = ff_by_factor.sort_values('ff_rate', ascending=False)
    
    top_risk = ff_by_factor.iloc[0] if len(ff_by_factor) > 0 else None
    bottom_risk = ff_by_factor.iloc[-1] if len(ff_by_factor) > 0 else None
    
    factor_colors = get_categorical_colors()[:len(ff_by_factor)]
    chart = alt.Chart(ff_by_factor).mark_bar(cornerRadiusEnd=4).encode(
        y=alt.Y(f'{risk_factor}:N', sort='-x', title=None, axis=alt.Axis(labelLimit=0)),
        x=alt.X('ff_rate:Q', title='Firefighting Rate %'),
        color=alt.Color(f'{risk_factor}:N', scale=alt.Scale(domain=ff_by_factor[risk_factor].tolist(), range=factor_colors), legend=None),
        tooltip=[f'{risk_factor}:N', alt.Tooltip('ff_rate:Q', format='.1f'), 'firefighting:Q', 'total:Q']
    ).properties(height=400)
    
    avg_line = alt.Chart(pd.DataFrame({'x': [pct_firefighting]})).mark_rule(
        color='#FF8C00', strokeDash=[5, 5], strokeWidth=3
    ).encode(x='x:Q')
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.altair_chart(chart + avg_line, use_container_width=True)
        st.caption(f"Orange dashed line = overall average ({pct_firefighting:.0f}%). Bars above average indicate higher risk.")
    with col2:
        st.markdown("##### :primary[:material/lightbulb:] Key Insights")
        if top_risk is not None and bottom_risk is not None:
            spread = top_risk['ff_rate'] - bottom_risk['ff_rate']
            factor_label = risk_factor.replace('_', ' ').title().replace('Ai ', 'AI ')
            
            if risk_factor == 'modeling_approach':
                st.caption("Teams using ad-hoc modeling spend **2x more time firefighting** (38%) than those with semantic models (19%).")
            else:
                st.caption(f"Teams using **{top_risk[risk_factor]}** face the highest firefighting burden at **{top_risk['ff_rate']:.0f}%**, while those with **{bottom_risk[risk_factor]}** experience the lowest at just **{bottom_risk['ff_rate']:.0f}%**.")
            
            st.caption(f"This **{spread:.0f} percentage point gap** reveals how strongly {factor_label.lower()} choices influence operational stability.")
            
            if spread >= 15:
                st.caption(":primary[:material/warning:] **High impact factor** — choosing wisely here significantly reduces firefighting risk.")
            elif spread >= 8:
                st.caption(":primary[:material/info:] **Moderate impact** — this factor meaningfully affects firefighting rates.")
            else:
                st.caption(":primary[:material/check:] **Lower variance** — firefighting rates are relatively consistent across options.")

with st.container(border=True):
    st.markdown("#### :primary[:material/compare:] Firefighting vs Non-Firefighting Teams")
    
    ff_teams = df[df['has_firefighting'] == True]
    non_ff_teams = df[df['has_firefighting'] == False]
    
    if len(ff_teams) > 0 and len(non_ff_teams) > 0:
        ff_lead = ff_teams['has_leadership_gap'].sum() / len(ff_teams) * 100
        non_lead = non_ff_teams['has_leadership_gap'].sum() / len(non_ff_teams) * 100
        
        ff_growth = (ff_teams['team_growth_2026'] == 'Grow').sum() / len(ff_teams) * 100
        non_growth = (non_ff_teams['team_growth_2026'] == 'Grow').sum() / len(non_ff_teams) * 100
        
        ff_ai = ff_teams['ai_embedded'].sum() / len(ff_teams) * 100
        non_ai = non_ff_teams['ai_embedded'].sum() / len(non_ff_teams) * 100
        
        comparison_data = pd.DataFrame({
            'Metric': ['Leadership Gap', 'Expect Growth', 'AI Embedded'],
            'Firefighting': [ff_lead, ff_growth, ff_ai],
            'Non-Firefighting': [non_lead, non_growth, non_ai]
        }).melt(id_vars='Metric', var_name='Team Type', value_name='Percentage')
        
        comparison_chart = alt.Chart(comparison_data).mark_bar(cornerRadiusEnd=4, stroke='black', strokeWidth=1).encode(
            x=alt.X('Metric:N', title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y('Percentage:Q', title='%'),
            color=alt.Color('Team Type:N', scale=alt.Scale(domain=['Firefighting', 'Non-Firefighting'], range=['#F59E0B', '#10B981']), legend=alt.Legend(orient='bottom', title=None)),
            xOffset='Team Type:N',
            tooltip=['Metric:N', 'Team Type:N', alt.Tooltip('Percentage:Q', format='.1f')]
        ).properties(height=400)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.altair_chart(comparison_chart, use_container_width=True)
        with col2:
            st.markdown("##### :primary[:material/lightbulb:] Key Insights")
            
            lead_diff = ff_lead - non_lead
            growth_diff = ff_growth - non_growth
            ai_diff = ff_ai - non_ai
            
            st.caption(f"**:primary[Leadership:]** Firefighting teams report **{lead_diff:.0f}% more gaps**, suggesting reactive work strains management capacity.")
            
            if growth_diff < 0:
                st.caption(f"**:primary[Growth:]** Despite challenges, firefighting teams are **{abs(growth_diff):.0f}% less likely** to expect growth.")
            else:
                st.caption(f"**:primary[Growth:]** Firefighting teams are **{growth_diff:.0f}% more likely** to expect team growth.")
            
            st.caption(f"**:primary[AI Adoption:]** **{abs(ai_diff):.0f}% {'higher' if ai_diff > 0 else 'lower'}** among firefighting teams.")
