import streamlit as st
import pandas as pd
import altair as alt
from data_utils import get_filtered_df
from chart_utils import create_donut_chart, create_bar_chart, get_compare_colors, get_categorical_colors

st.markdown("# :primary[:material/do_not_disturb:] AI Skeptics Profile")
st.markdown("Profile practitioners who remain skeptical about AI adoption and tools")

df = get_filtered_df()

skeptics_df = df[df['ai_helps_with'].str.contains("don't find AI helpful", case=False, na=False)]
enthusiasts_df = df[~df['ai_helps_with'].str.contains("don't find AI helpful", case=False, na=False)]

n_skeptics = len(skeptics_df)
n_enthusiasts = len(enthusiasts_df)
pct_skeptics = n_skeptics / len(df) * 100 if len(df) > 0 else 0
pct_enthusiasts = n_enthusiasts / len(df) * 100 if len(df) > 0 else 0

overview_col1, overview_col2 = st.columns(2)

with overview_col1:
    with st.container(border=True):
        st.markdown("#### :primary[:material/do_not_disturb:] AI Skeptic Overview")
        
        if n_skeptics > 0:
            top_industry = skeptics_df['industry'].value_counts().idxmax()
            top_role = skeptics_df['role'].value_counts().idxmax()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("AI Skeptics", f"{n_skeptics:,}")
            col2.metric("% of Survey", f"{pct_skeptics:.1f}%")
            col3.metric("Top Industry", top_industry)
            
            st.metric("Top Role", top_role)
            
            skeptic_ff = skeptics_df['has_firefighting'].sum() / n_skeptics * 100
            enth_ff = enthusiasts_df['has_firefighting'].sum() / len(enthusiasts_df) * 100 if len(enthusiasts_df) > 0 else 0
            skeptic_growth = (skeptics_df['team_growth_2026'] == 'Grow').sum() / n_skeptics * 100
            enth_growth = (enthusiasts_df['team_growth_2026'] == 'Grow').sum() / len(enthusiasts_df) * 100 if len(enthusiasts_df) > 0 else 0
            skeptic_lead = skeptics_df['has_leadership_gap'].sum() / n_skeptics * 100
            enth_lead = enthusiasts_df['has_leadership_gap'].sum() / len(enthusiasts_df) * 100 if len(enthusiasts_df) > 0 else 0
            
            col5, col6, col7 = st.columns(3)
            col5.metric("Firefighting", f"{skeptic_ff:.0f}%", delta=f"{skeptic_ff - enth_ff:+.1f}%", delta_color="inverse")
            col6.metric("Expect Growth", f"{skeptic_growth:.0f}%", delta=f"{skeptic_growth - enth_growth:+.1f}%")
            col7.metric("Leadership Gap", f"{skeptic_lead:.0f}%", delta=f"{skeptic_lead - enth_lead:+.1f}%", delta_color="inverse")

with overview_col2:
    with st.container(border=True):
        st.markdown("#### :primary[:material/thumb_up:] AI Enthusiast Overview")
        
        if n_enthusiasts > 0:
            enth_top_industry = enthusiasts_df['industry'].value_counts().idxmax()
            enth_top_role = enthusiasts_df['role'].value_counts().idxmax()
            
            col1, col2, col3 = st.columns(3)
            col1.metric("AI Enthusiasts", f"{n_enthusiasts:,}")
            col2.metric("% of Survey", f"{pct_enthusiasts:.1f}%")
            col3.metric("Top Industry", enth_top_industry)
            
            st.metric("Top Role", enth_top_role)
            
            enth_ff = enthusiasts_df['has_firefighting'].sum() / n_enthusiasts * 100
            skeptic_ff = skeptics_df['has_firefighting'].sum() / len(skeptics_df) * 100 if len(skeptics_df) > 0 else 0
            enth_growth = (enthusiasts_df['team_growth_2026'] == 'Grow').sum() / n_enthusiasts * 100
            skeptic_growth = (skeptics_df['team_growth_2026'] == 'Grow').sum() / len(skeptics_df) * 100 if len(skeptics_df) > 0 else 0
            enth_lead = enthusiasts_df['has_leadership_gap'].sum() / n_enthusiasts * 100
            skeptic_lead = skeptics_df['has_leadership_gap'].sum() / len(skeptics_df) * 100 if len(skeptics_df) > 0 else 0
            
            col5, col6, col7 = st.columns(3)
            col5.metric("Firefighting", f"{enth_ff:.0f}%", delta=f"{enth_ff - skeptic_ff:+.1f}%", delta_color="inverse")
            col6.metric("Expect Growth", f"{enth_growth:.0f}%", delta=f"{enth_growth - skeptic_growth:+.1f}%")
            col7.metric("Leadership Gap", f"{enth_lead:.0f}%", delta=f"{enth_lead - skeptic_lead:+.1f}%", delta_color="inverse")

if n_skeptics > 0:
    with st.container(border=True):
        st.markdown("#### :primary[:material/bar_chart:] Demographics Comparison")
        
        breakdown_dim = st.selectbox(
            "Break down by:",
            options=["role", "industry", "org_size", "region"],
            format_func=lambda x: x.replace('_', ' ').title(),
            key="skeptic_breakdown"
        )
        
        st.markdown("##### AI Skeptic Demographics")
        skeptic_counts = skeptics_df[breakdown_dim].value_counts().head(8).reset_index()
        skeptic_counts.columns = [breakdown_dim, 'count']
        skeptic_counts['percentage'] = (skeptic_counts['count'] / n_skeptics * 100).round(1)
        
        skeptic_chart = alt.Chart(skeptic_counts).mark_bar(cornerRadiusEnd=4).encode(
            y=alt.Y(f'{breakdown_dim}:N', sort='-x', title=None),
            x=alt.X('percentage:Q', title='% of AI Skeptics'),
            color=alt.Color(f'{breakdown_dim}:N', scale=alt.Scale(range=get_categorical_colors()), legend=None),
            tooltip=[f'{breakdown_dim}:N', 'count:Q', alt.Tooltip('percentage:Q', format='.1f')]
        ).properties(height=300)
        
        chart_col, insight_col = st.columns([3, 1])
        with chart_col:
            st.altair_chart(skeptic_chart, use_container_width=True)
        with insight_col:
            st.markdown("###### :primary[:material/lightbulb:] Key Insights")
            top_item = skeptic_counts.iloc[0][breakdown_dim] if len(skeptic_counts) > 0 else "N/A"
            top_pct = skeptic_counts.iloc[0]['percentage'] if len(skeptic_counts) > 0 else 0
            dim_label = breakdown_dim.replace('_', ' ')
            st.caption(f":primary[{top_item}] leads among AI Skeptics at **{top_pct:.0f}%**, suggesting this {dim_label} may face unique AI adoption challenges.")
            if len(skeptic_counts) > 1:
                second = skeptic_counts.iloc[1][breakdown_dim]
                second_pct = skeptic_counts.iloc[1]['percentage']
                gap = top_pct - second_pct
                st.caption(f":primary[{second}] follows at **{second_pct:.0f}%**, trailing by {gap:.0f} percentage points.")
        
        st.markdown("##### AI Enthusiast Demographics")
        enth_counts = enthusiasts_df[breakdown_dim].value_counts().head(8).reset_index()
        enth_counts.columns = [breakdown_dim, 'count']
        enth_counts['percentage'] = (enth_counts['count'] / n_enthusiasts * 100).round(1) if n_enthusiasts > 0 else 0
        
        enth_chart = alt.Chart(enth_counts).mark_bar(cornerRadiusEnd=4).encode(
            y=alt.Y(f'{breakdown_dim}:N', sort='-x', title=None),
            x=alt.X('percentage:Q', title='% of AI Enthusiasts'),
            color=alt.Color(f'{breakdown_dim}:N', scale=alt.Scale(range=get_categorical_colors()), legend=None),
            tooltip=[f'{breakdown_dim}:N', 'count:Q', alt.Tooltip('percentage:Q', format='.1f')]
        ).properties(height=300)
        
        chart_col, insight_col = st.columns([3, 1])
        with chart_col:
            st.altair_chart(enth_chart, use_container_width=True)
        with insight_col:
            st.markdown("###### :primary[:material/lightbulb:] Key Insights")
            enth_top_item = enth_counts.iloc[0][breakdown_dim] if len(enth_counts) > 0 else "N/A"
            enth_top_pct = enth_counts.iloc[0]['percentage'] if len(enth_counts) > 0 else 0
            dim_label = breakdown_dim.replace('_', ' ')
            st.caption(f":primary[{enth_top_item}] dominates the AI Enthusiast group at **{enth_top_pct:.0f}%**, reflecting strong AI adoption in this {dim_label}.")
            if len(enth_counts) > 1:
                enth_second = enth_counts.iloc[1][breakdown_dim]
                enth_second_pct = enth_counts.iloc[1]['percentage']
                enth_gap = enth_top_pct - enth_second_pct
                st.caption(f":primary[{enth_second}] comes next at **{enth_second_pct:.0f}%**, {enth_gap:.0f} points behind the leader.")
    
    with st.container(border=True):
        st.markdown("#### :primary[:material/compare:] AI Skeptics vs AI Enthusiasts")
        
        skeptic_btn = skeptics_df['biggest_bottleneck'].value_counts(normalize=True).head(5) * 100
        enth_btn = enthusiasts_df['biggest_bottleneck'].value_counts(normalize=True).head(5) * 100
        
        skeptic_btn_df = skeptic_btn.reset_index()
        skeptic_btn_df.columns = ['bottleneck', 'percentage']
        skeptic_btn_df['group'] = 'AI Skeptics'
        
        enth_btn_df = enth_btn.reset_index()
        enth_btn_df.columns = ['bottleneck', 'percentage']
        enth_btn_df['group'] = 'AI Enthusiasts'
        
        combined = pd.concat([skeptic_btn_df, enth_btn_df])
        
        merged = skeptic_btn_df[['bottleneck', 'percentage']].merge(
            enth_btn_df[['bottleneck', 'percentage']], 
            on='bottleneck', 
            suffixes=('_skeptic', '_enth'),
            how='outer'
        ).fillna(0)
        merged['diff'] = merged['percentage_skeptic'] - merged['percentage_enth']
        biggest_gap_row = merged.loc[merged['diff'].abs().idxmax()] if len(merged) > 0 else None
        most_similar_row = merged.loc[merged['diff'].abs().idxmin()] if len(merged) > 0 else None
        
        chart = alt.Chart(combined).mark_bar(cornerRadiusEnd=4).encode(
            y=alt.Y('bottleneck:N', sort='-x', title=None),
            x=alt.X('percentage:Q', title='Percentage'),
            color=alt.Color('group:N', scale=alt.Scale(domain=['AI Skeptics', 'AI Enthusiasts'], range=get_compare_colors()), legend=alt.Legend(orient='bottom', title=None)),
            xOffset='group:N',
            tooltip=['bottleneck:N', 'group:N', alt.Tooltip('percentage:Q', format='.1f')]
        ).properties(height=300)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.altair_chart(chart, use_container_width=True)
        with col2:
            st.markdown("##### :primary[:material/lightbulb:] Key Insights")
            skeptic_top = skeptic_btn.idxmax() if len(skeptic_btn) > 0 else "N/A"
            skeptic_top_pct = skeptic_btn.max() if len(skeptic_btn) > 0 else 0
            enth_top = enth_btn.idxmax() if len(enth_btn) > 0 else "N/A"
            enth_top_pct = enth_btn.max() if len(enth_btn) > 0 else 0
            st.caption(f"For AI Skeptics, :primary[{skeptic_top}] emerges as the top bottleneck at **{skeptic_top_pct:.0f}%**.")
            st.caption(f"AI Enthusiasts cite :primary[{enth_top}] most frequently at **{enth_top_pct:.0f}%**.")
            if biggest_gap_row is not None:
                gap_cat = biggest_gap_row['bottleneck']
                gap_val = biggest_gap_row['diff']
                if gap_val > 0:
                    st.caption(f"The widest divergence appears on :primary[{gap_cat}], where AI Skeptics score **{abs(gap_val):.0f}%** higher—potentially revealing where AI skepticism stems from.")
                else:
                    st.caption(f"The widest divergence appears on :primary[{gap_cat}], where AI Enthusiasts score **{abs(gap_val):.0f}%** higher—suggesting AI adoption alleviates this pain point.")
    
    with st.container(border=True):
        st.markdown("#### :primary[:material/format_quote:] Skeptic Voices")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### AI Skeptics")
            skeptic_wishes = skeptics_df[skeptics_df['industry_wish'].notna() & (skeptics_df['industry_wish'] != '')]
            if len(skeptic_wishes) > 0:
                skeptic_sample = skeptic_wishes.sample(min(3, len(skeptic_wishes)))
                for _, row in skeptic_sample.iterrows():
                    with st.container(border=True):
                        st.markdown(f"*\"{row['industry_wish']}\"*")
                        st.caption(f"— {row['role']}, {row['industry']}")
                
                remaining = skeptic_wishes[~skeptic_wishes.index.isin(skeptic_sample.index)]
                if len(remaining) > 0:
                    with st.expander(f"Show more ({len(remaining)} more quotes)"):
                        for _, row in remaining.iterrows():
                            st.markdown(f"*\"{row['industry_wish']}\"*")
                            st.caption(f"— {row['role']}, {row['industry']}")
                            st.divider()
            else:
                st.info("No quotes available")
        
        with col2:
            st.markdown("##### AI Enthusiasts")
            enth_wishes = enthusiasts_df[enthusiasts_df['industry_wish'].notna() & (enthusiasts_df['industry_wish'] != '')]
            if len(enth_wishes) > 0:
                enth_sample = enth_wishes.sample(min(3, len(enth_wishes)))
                for _, row in enth_sample.iterrows():
                    with st.container(border=True):
                        st.markdown(f"*\"{row['industry_wish']}\"*")
                        st.caption(f"— {row['role']}, {row['industry']}")
                
                remaining = enth_wishes[~enth_wishes.index.isin(enth_sample.index)]
                if len(remaining) > 0:
                    with st.expander(f"Show more ({len(remaining)} more quotes)"):
                        for _, row in remaining.iterrows():
                            st.markdown(f"*\"{row['industry_wish']}\"*")
                            st.caption(f"— {row['role']}, {row['industry']}")
                            st.divider()
            else:
                st.info("No quotes available")

else:
    st.info("No AI skeptics found in the current filtered data.")
