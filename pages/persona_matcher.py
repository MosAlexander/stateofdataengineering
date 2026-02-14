import streamlit as st
import pandas as pd
import altair as alt
from data_utils import get_filtered_df, compute_similarity, get_value_counts_pct
from chart_utils import create_diverging_bar, create_donut_chart, create_gauge_chart

st.markdown("# :primary[:material/people:] Find Your Tribe")
st.markdown("Input your profile to find practitioners with similar backgrounds and challenges")

df = get_filtered_df()

def get_options_with_counts(df_subset, column, order=None):
    counts = df_subset[column].dropna().value_counts()
    if order:
        ordered_vals = [v for v in order if v in counts.index]
        counts = counts.reindex(ordered_vals)
    return {f"{val} ({count:,})": val for val, count in counts.items() if count > 0}

def filter_df_progressive(df, selections):
    filtered = df.copy()
    for col, val in selections.items():
        if val is not None:
            filtered = filtered[filtered[col] == val]
    return filtered

size_order = ["< 50 employees", "50–199", "200–999", "1,000–10,000", "10,000+"]

with st.container(border=True):
    st.markdown("#### :primary[:material/person_add:] Your Profile")
    st.caption("Options dynamically update to show only combinations with matching data")
    
    selections = {}
    
    with st.container(border=True):
        st.markdown("##### Demographics")
        col1, col2 = st.columns(2)
        
        with col1:
            role_opts = get_options_with_counts(df, 'role')
            my_role_display = st.selectbox("Your Role:", options=list(role_opts.keys()), key="pm_role")
            my_role = role_opts[my_role_display] if my_role_display else None
            selections['role'] = my_role
            
            filtered = filter_df_progressive(df, selections)
            industry_opts = get_options_with_counts(filtered, 'industry')
            if industry_opts:
                my_industry_display = st.selectbox("Your Industry:", options=list(industry_opts.keys()), key="pm_industry")
                my_industry = industry_opts[my_industry_display] if my_industry_display else None
            else:
                st.warning("No industries available for this role")
                my_industry = None
            selections['industry'] = my_industry
        
        with col2:
            filtered = filter_df_progressive(df, selections)
            org_opts = get_options_with_counts(filtered, 'org_size', size_order)
            if org_opts:
                my_org_display = st.selectbox("Organization Size:", options=list(org_opts.keys()), key="pm_org")
                my_org_size = org_opts[my_org_display] if my_org_display else None
            else:
                st.warning("No org sizes available for this combination")
                my_org_size = None
            selections['org_size'] = my_org_size
            
            filtered = filter_df_progressive(df, selections)
            region_opts = get_options_with_counts(filtered, 'region')
            if region_opts:
                my_region_display = st.selectbox("Your Region:", options=list(region_opts.keys()), key="pm_region")
                my_region = region_opts[my_region_display] if my_region_display else None
            else:
                st.warning("No regions available for this combination")
                my_region = None
            selections['region'] = my_region

    final_match_count = len(filter_df_progressive(df, selections))
    if final_match_count > 0:
        st.success(f":primary[:material/check_circle:] **{final_match_count}** exact matches found for your profile")
    else:
        st.warning("No exact matches, but similarity search may find partial matches")

    w_role, w_industry, w_org, w_region = 0.8, 0.5, 0.3, 0.2
    
    similarity_threshold = st.slider("Minimum similarity score:", 0.3, 0.9, 0.5, 0.05, key="sim_thresh")

if True:
    
    user_profile = {
        'role': my_role, 'industry': my_industry, 'org_size': my_org_size, 'region': my_region
    }
    
    weights = {
        'role': w_role,
        'industry': w_industry,
        'org_size': w_org,
        'region': w_region
    }
    
    df['similarity'] = compute_similarity(user_profile, df, weights)
    tribe = df[df['similarity'] >= similarity_threshold]
    
    with st.container(border=True):
        st.markdown("#### :primary[:material/groups:] Your Tribe")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric("Similar Practitioners", f"{len(tribe):,}")
            avg_sim = tribe['similarity'].mean() * 100 if len(tribe) > 0 else 0
            st.metric("Average Match Score", f"{avg_sim:.0f}%")
        
        with col2:
            if len(tribe) > 0:
                st.markdown("**Most Common Traits:**")
                traits = []
                for col in ['role', 'industry', 'org_size', 'region']:
                    top_val = tribe[col].value_counts().idxmax()
                    pct = tribe[col].value_counts().iloc[0] / len(tribe) * 100
                    traits.append(f"- **{col.replace('_', ' ').title()}**: {top_val} ({pct:.0f}%)")
                st.markdown("\n".join(traits))
    
    if len(tribe) > 0:
        with st.container(border=True):
            st.markdown("#### :primary[:material/trending_up:] Your Tribe's Outlook")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            daily_ai_pct = tribe['daily_ai_user'].sum() / len(tribe) * 100
            baseline_daily_ai = df['daily_ai_user'].sum() / len(df) * 100
            col1.metric("Daily AI", f"{daily_ai_pct:.0f}%", delta=f"{daily_ai_pct - baseline_daily_ai:+.1f}%")
            
            ai_embedded_pct = tribe['ai_embedded'].sum() / len(tribe) * 100
            baseline_ai_embedded = df['ai_embedded'].sum() / len(df) * 100
            col2.metric("AI Embedded", f"{ai_embedded_pct:.0f}%", delta=f"{ai_embedded_pct - baseline_ai_embedded:+.1f}%")
            
            ff_pct = tribe['has_firefighting'].sum() / len(tribe) * 100
            baseline_ff = df['has_firefighting'].sum() / len(df) * 100
            col3.metric("Firefighting", f"{ff_pct:.0f}%", delta=f"{ff_pct - baseline_ff:+.1f}%", delta_color="inverse")
            
            lead_gap_pct = tribe['has_leadership_gap'].sum() / len(tribe) * 100
            baseline_lead_gap = df['has_leadership_gap'].sum() / len(df) * 100
            col4.metric("Leadership Gap", f"{lead_gap_pct:.0f}%", delta=f"{lead_gap_pct - baseline_lead_gap:+.1f}%", delta_color="inverse")
            
            growth_pct = (tribe['team_growth_2026'] == 'Grow').sum() / len(tribe) * 100
            baseline_growth = (df['team_growth_2026'] == 'Grow').sum() / len(df) * 100
            col5.metric("Growth Expected", f"{growth_pct:.0f}%", delta=f"{growth_pct - baseline_growth:+.1f}%")
        
        with st.container(border=True):
            st.markdown("#### :primary[:material/warning:] What Your Tribe Struggles With")
            
            col_ctrl1, col_ctrl2 = st.columns(2)
            with col_ctrl1:
                compare_to = st.radio("Compare to:", ["All Respondents", "Same Role", "Same Industry"], horizontal=True, key="pain_cmp")
            with col_ctrl2:
                pain_top_n = st.slider("Show top N:", 5, 12, 8, key="pain_n")
            
            if compare_to == "Same Role":
                baseline = df[df['role'] == my_role]
            elif compare_to == "Same Industry":
                baseline = df[df['industry'] == my_industry]
            else:
                baseline = df
            
            tribe_pains = tribe['biggest_bottleneck'].value_counts(normalize=True) * 100
            baseline_pains = baseline['biggest_bottleneck'].value_counts(normalize=True) * 100
            
            pain_comparison = pd.DataFrame({
                'tribe_pct': tribe_pains,
                'baseline_pct': baseline_pains
            }).fillna(0)
            pain_comparison['difference'] = pain_comparison['tribe_pct'] - pain_comparison['baseline_pct']
            pain_comparison = pain_comparison.reset_index()
            pain_comparison.columns = ['bottleneck', 'tribe_pct', 'baseline_pct', 'difference']
            pain_comparison = pain_comparison.sort_values('difference', ascending=False).head(pain_top_n)
            
            top_struggles = pain_comparison.head(3)
            top_positive = [r for _, r in top_struggles.iterrows() if r['difference'] > 0]
            top_negative = [r for _, r in top_struggles.iterrows() if r['difference'] < 0]
            
            col_chart, col_insights = st.columns([2, 1])
            with col_chart:
                chart = create_diverging_bar(pain_comparison, 'bottleneck', 'difference', height=400, wrap_width=25)
                st.altair_chart(chart, use_container_width=True)
            
            with col_insights:
                st.markdown("##### :primary[:material/lightbulb:] Key Insights")
                if top_positive:
                    top_issue = top_positive[0]
                    st.caption(f"Your tribe reports **{top_issue['bottleneck']}** as a disproportionately common challenge, occurring **{top_issue['difference']:+.1f}%** more frequently than the baseline comparison group. " + 
                              (f"Other elevated concerns include **{top_positive[1]['bottleneck']}** (+{top_positive[1]['difference']:.1f}%) " if len(top_positive) > 1 else "") +
                              (f"and **{top_positive[2]['bottleneck']}** (+{top_positive[2]['difference']:.1f}%)." if len(top_positive) > 2 else "."))
                
                if top_negative:
                    st.caption(f"Conversely, your tribe experiences **{top_negative[0]['bottleneck']}** less often ({top_negative[0]['difference']:.1f}% below baseline)" +
                              (f", along with **{top_negative[1]['bottleneck']}** ({top_negative[1]['difference']:.1f}%)" if len(top_negative) > 1 else "") +
                              ", suggesting these may be areas of relative strength or lower priority for this cohort.")
        
        with st.container(border=True):
            st.markdown("#### :primary[:material/pie_chart:] Team Growth Breakdown")
            
            shrink_pct = (tribe['team_growth_2026'] == 'Shrink').sum() / len(tribe) * 100
            stay_pct = (tribe['team_growth_2026'] == 'Stay the same').sum() / len(tribe) * 100
            baseline_shrink = (df['team_growth_2026'] == 'Shrink').sum() / len(df) * 100
            baseline_stay = (df['team_growth_2026'] == 'Stay the same').sum() / len(df) * 100
            growth_pct = (tribe['team_growth_2026'] == 'Grow').sum() / len(tribe) * 100
            baseline_growth = (df['team_growth_2026'] == 'Grow').sum() / len(df) * 100
            
            col1, col2 = st.columns([2, 1])
            with col1:
                growth_chart = create_donut_chart(tribe, 'team_growth_2026', height=250)
                st.altair_chart(growth_chart, use_container_width=True)
            with col2:
                st.markdown("##### :primary[:material/lightbulb:] Key Insights")
                
                if growth_pct > 50:
                    st.caption(f"**:primary[Bullish outlook:]** {growth_pct:.0f}% of your tribe expects growth, signaling strong confidence in team expansion.")
                elif growth_pct > stay_pct:
                    st.caption(f"**:primary[Cautiously optimistic:]** More expect growth ({growth_pct:.0f}%) than staying flat ({stay_pct:.0f}%), suggesting positive momentum.")
                else:
                    st.caption(f"**:primary[Steady state:]** Most of your tribe ({stay_pct:.0f}%) expects team size to remain stable through 2026.")
                
                if shrink_pct > baseline_shrink + 3:
                    st.caption(f"**:primary[Contraction risk:]** Shrink rate ({shrink_pct:.0f}%) is notably above the survey average ({baseline_shrink:.0f}%).")
                elif shrink_pct < 5:
                    st.caption(f"**:primary[Job security:]** Low shrink expectations ({shrink_pct:.0f}%) suggest stable employment in this cohort.")
                else:
                    st.caption(f"**:primary[Typical churn:]** Shrink rate ({shrink_pct:.0f}%) is in line with overall survey trends ({baseline_shrink:.0f}%).")
                
                growth_vs_baseline = growth_pct - baseline_growth
                if abs(growth_vs_baseline) > 5:
                    direction = "more" if growth_vs_baseline > 0 else "less"
                    st.caption(f"**:primary[vs. Overall:]** Your tribe is {abs(growth_vs_baseline):.0f}% {direction} optimistic about growth than the broader survey population.")
                else:
                    st.caption(f"**:primary[vs. Overall:]** Your tribe's growth outlook closely mirrors the broader survey population.")
    else:
        st.warning("No practitioners match your criteria. Try lowering the similarity threshold.")
