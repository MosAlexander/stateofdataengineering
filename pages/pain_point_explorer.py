import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
from data_utils import get_filtered_df, init_multiselect_state, get_multiselect_values
from chart_utils import get_compare_colors, get_categorical_colors, get_categorical_colors, get_plotly_scale, get_primary_color

st.markdown("# :primary[:material/report_problem:] Pain Point Impact Explorer")
st.markdown("Explore pain point co-occurrence patterns and common challenge clusters")

df = get_filtered_df()

pain_points = []
for pains in df['modeling_pain_points'].dropna():
    for p in str(pains).split(', '):
        if p.strip() and p.strip() != 'None / modeling is going well':
            pain_points.append(p.strip())

unique_pains = sorted(list(set(pain_points)))
pain_opts = {p: p for p in unique_pains}

if "pain_select" not in st.session_state:
    st.session_state.pain_select = []

with st.container(border=True):
    st.markdown("#### :primary[:material/checklist:] Select Pain Points")
    select_col, mode_col = st.columns([2, 1])
    with select_col:
        st.multiselect(
            "Modeling Pain Points:",
            options=unique_pains,
            key="pain_select",
            label_visibility="collapsed"
        )
    with mode_col:
        comparison_mode = st.radio(
            "Comparison Mode:",
            options=["Has ANY selected", "Has ALL selected"],
            help="ANY = at least one selected pain point",
            key="pain_mode",
            horizontal=True,
            label_visibility="collapsed"
        )

selected_pains = st.session_state.pain_select

if selected_pains:
    if comparison_mode == "Has ANY selected":
        mask = df['modeling_pain_points'].apply(
            lambda x: any(p in str(x) for p in selected_pains) if pd.notna(x) else False
        )
    else:
        mask = df['modeling_pain_points'].apply(
            lambda x: all(p in str(x) for p in selected_pains) if pd.notna(x) else False
        )
    
    selected_df = df[mask]
    baseline_df = df[~mask]
    n_selected = len(selected_df)
    
    pain_label = selected_pains[0][:25] + "..." if len(selected_pains) == 1 else f"{len(selected_pains)} pain points"
    
    if len(selected_pains) == 1:
        pain_desc = f"'{selected_pains[0]}'"
    elif len(selected_pains) == 2:
        pain_desc = f"'{selected_pains[0]}' and '{selected_pains[1]}'"
    else:
        pain_desc = f"'{selected_pains[0]}', '{selected_pains[1]}', and {len(selected_pains) - 2} other pain point{'s' if len(selected_pains) > 3 else ''}"
    
    with st.container(border=True):
        st.markdown("#### :primary[:material/compare:] Impact Comparison")
        st.caption(f"Analyzing {n_selected:,} respondents with {pain_label} vs {len(baseline_df):,} others")
        
        col1, col2, col3, col4 = st.columns(4)
        
        if n_selected > 0:
            ff_selected = selected_df['has_firefighting'].sum() / n_selected * 100
            ff_baseline = baseline_df['has_firefighting'].sum() / len(baseline_df) * 100 if len(baseline_df) > 0 else 0
            ff_diff = ff_selected - ff_baseline
            col1.metric("Firefighting", f"{ff_selected:.0f}%", 
                       delta=f"{ff_diff:+.0f}%", delta_color="inverse")
            if ff_diff > 5:
                col1.caption(f"Teams spend {ff_diff:.0f}pp more time firefighting, diverting resources from strategic work.")
            elif ff_diff < -5:
                col1.caption(f"Teams report {abs(ff_diff):.0f}pp less firefighting, freeing capacity for innovation.")
            else:
                col1.caption("Reactive workload mirrors the baseline—neither a clear burden nor an advantage.")
            
            growth_selected = (selected_df['team_growth_2026'] == 'Grow').sum() / n_selected * 100
            growth_baseline = (baseline_df['team_growth_2026'] == 'Grow').sum() / len(baseline_df) * 100 if len(baseline_df) > 0 else 0
            growth_diff = growth_selected - growth_baseline
            col2.metric("Growth", f"{growth_selected:.0f}%",
                       delta=f"{growth_diff:+.0f}%")
            if growth_diff > 5:
                col2.caption(f"Growth expectations are {growth_diff:.0f}pp higher, signaling strong confidence in team expansion.")
            elif growth_diff < -5:
                col2.caption(f"Growth outlook trails by {abs(growth_diff):.0f}pp—these teams may face budget or headcount constraints.")
            else:
                col2.caption("Hiring sentiment aligns with the broader population—no outsized optimism or caution.")
            
            ai_selected = selected_df['ai_embedded'].sum() / n_selected * 100
            ai_baseline = baseline_df['ai_embedded'].sum() / len(baseline_df) * 100 if len(baseline_df) > 0 else 0
            ai_diff = ai_selected - ai_baseline
            col3.metric("AI Adoption", f"{ai_selected:.0f}%",
                       delta=f"{ai_diff:+.0f}%")
            if ai_diff > 3:
                col3.caption(f"AI adoption leads by {ai_diff:.0f}pp, suggesting these teams prioritize automation to offset pain points.")
            elif ai_diff < -3:
                col3.caption(f"AI usage lags by {abs(ai_diff):.0f}pp—pain points may be blocking modernization efforts.")
            else:
                col3.caption("AI integration tracks the baseline—pain points don't appear to accelerate or hinder adoption.")
            
            lead_selected = selected_df['has_leadership_gap'].sum() / n_selected * 100
            lead_baseline = baseline_df['has_leadership_gap'].sum() / len(baseline_df) * 100 if len(baseline_df) > 0 else 0
            lead_diff = lead_selected - lead_baseline
            col4.metric("Lead Gap", f"{lead_selected:.0f}%",
                       delta=f"{lead_diff:+.0f}%", delta_color="inverse")
            if lead_diff > 5:
                col4.caption(f"Leadership gaps are {lead_diff:.0f}pp more common, hinting at organizational misalignment.")
            elif lead_diff < -5:
                col4.caption(f"Fewer leadership gaps ({abs(lead_diff):.0f}pp below baseline)—teams may benefit from clearer direction.")
            else:
                col4.caption("Leadership alignment is on par with typical teams—neither a strength nor a weakness.")

if selected_pains and n_selected > 0:
    with st.container(border=True):
        header_left, header_right = st.columns([2, 1])
        with header_left:
            st.markdown("#### :primary[:material/bar_chart:] Bottlenecks")
        with header_right:
            st.markdown("##### :primary[:material/lightbulb:] Key Insights")
        chart_col, insight_col = st.columns([2, 1])
        
        with chart_col:
            btn_sel = selected_df['biggest_bottleneck'].value_counts().head(6)
            btn_base = baseline_df['biggest_bottleneck'].value_counts().head(6)
            all_bottlenecks = list(set(btn_sel.index) | set(btn_base.index))
            
            btn_data = []
            for b in all_bottlenecks:
                sel_pct = (btn_sel.get(b, 0) / n_selected * 100) if n_selected > 0 else 0
                base_pct = (btn_base.get(b, 0) / len(baseline_df) * 100) if len(baseline_df) > 0 else 0
                btn_data.append({'bottleneck': b[:30] + '...' if len(b) > 30 else b, 'Selected': sel_pct, 'Baseline': base_pct})
            
            btn_comp = pd.DataFrame(btn_data)
            melted_btn = btn_comp.melt(id_vars=['bottleneck'], value_vars=['Selected', 'Baseline'],
                                       var_name='group', value_name='percentage')
            
            chart = alt.Chart(melted_btn).mark_bar(cornerRadiusEnd=4).encode(
                y=alt.Y('bottleneck:N', title=None, sort='-x'),
                x=alt.X('percentage:Q', title='Percentage'),
                color=alt.Color('group:N', scale=alt.Scale(domain=['Selected', 'Baseline'], range=get_compare_colors()),
                               legend=alt.Legend(orient='bottom', direction='horizontal', titleOrient='left')),
                yOffset='group:N',
                tooltip=['bottleneck:N', 'group:N', alt.Tooltip('percentage:Q', format='.1f')]
            ).properties(height=280)
            st.altair_chart(chart, use_container_width=True)
        
        with insight_col:
            top_sel = btn_sel.idxmax() if len(btn_sel) > 0 else "N/A"
            top_sel_pct = btn_sel.max() / n_selected * 100 if len(btn_sel) > 0 else 0
            biggest_diff = max(btn_data, key=lambda x: abs(x['Selected'] - x['Baseline']), default=None)
            if biggest_diff:
                diff = biggest_diff['Selected'] - biggest_diff['Baseline']
                direction = "more" if diff > 0 else "less"
                st.caption(f"When examining respondents experiencing {pain_desc}, **{top_sel}** stands out as the most commonly cited bottleneck at **{top_sel_pct:.0f}%**.")
                st.caption(f"The most striking divergence from baseline appears in **{biggest_diff['bottleneck']}**—affected teams report this challenge **{abs(diff):.1f}%** {direction} frequently than their peers.")
                if diff > 5:
                    st.caption(f"This pattern suggests that {pain_desc} may compound existing organizational friction, making certain bottlenecks feel more acute.")
                elif diff < -5:
                    st.caption(f"Interestingly, teams with {pain_desc} report this bottleneck less often, possibly indicating different operational priorities.")
    
    with st.container(border=True):
        header_left, header_right = st.columns([2, 1])
        with header_left:
            st.markdown("#### :primary[:material/trending_up:] Growth Outlook")
        with header_right:
            st.markdown("##### :primary[:material/lightbulb:] Key Insights")
        chart_col, insight_col = st.columns([2, 1])
        
        with chart_col:
            growth_data = []
            for outlook in ['Grow', 'Stay the same', 'Shrink']:
                sel_pct = (selected_df['team_growth_2026'] == outlook).sum() / n_selected * 100
                base_pct = (baseline_df['team_growth_2026'] == outlook).sum() / len(baseline_df) * 100 if len(baseline_df) > 0 else 0
                label = 'Stay' if outlook == 'Stay the same' else outlook
                growth_data.append({'outlook': label, 'Selected': sel_pct, 'Baseline': base_pct})
            
            growth_comp = pd.DataFrame(growth_data)
            melted_growth = growth_comp.melt(id_vars=['outlook'], value_vars=['Selected', 'Baseline'],
                                              var_name='group', value_name='percentage')
            
            chart = alt.Chart(melted_growth).mark_bar(cornerRadiusEnd=4).encode(
                y=alt.Y('outlook:N', title=None, sort=['Grow', 'Stay', 'Shrink']),
                x=alt.X('percentage:Q', title='Percentage'),
                color=alt.Color('group:N', scale=alt.Scale(domain=['Selected', 'Baseline'], range=get_compare_colors()),
                               legend=alt.Legend(orient='bottom', direction='horizontal', titleOrient='left')),
                yOffset='group:N',
                tooltip=['outlook:N', 'group:N', alt.Tooltip('percentage:Q', format='.1f')]
            ).properties(height=360)
            st.altair_chart(chart, use_container_width=True)
        
        with insight_col:
            grow_diff = growth_data[0]['Selected'] - growth_data[0]['Baseline']
            shrink_diff = growth_data[2]['Selected'] - growth_data[2]['Baseline']
            stay_diff = growth_data[1]['Selected'] - growth_data[1]['Baseline']
            st.caption(f"Looking at hiring outlook, **{growth_data[0]['Selected']:.0f}%** of respondents with {pain_desc} anticipate :primary[team expansion] in 2026, compared to **{growth_data[0]['Baseline']:.0f}%** of others.")
            if grow_diff < -5:
                st.caption(f"This **{abs(grow_diff):.0f}%** gap suggests that {pain_desc} correlates with :primary[dampened optimism] about headcount growth—teams facing these challenges may be more cautious about expansion plans.")
            elif grow_diff > 5:
                st.caption(f"Despite facing {pain_desc}, these teams remain **{abs(grow_diff):.0f}%** more :primary[bullish on growth] than baseline. This resilience may indicate that pain points are seen as growing pains rather than existential threats.")
            else:
                st.caption(f"Growth expectations remain :primary[remarkably consistent] regardless of {pain_desc}, suggesting these challenges don't significantly influence hiring confidence.")
            if shrink_diff > 3:
                st.caption(f"Notably, **{growth_data[2]['Selected']:.0f}%** expect :primary[shrinkage] vs **{growth_data[2]['Baseline']:.0f}%** baseline—a signal worth monitoring.")
    
    with st.container(border=True):
        header_left, header_right = st.columns([2, 1])
        with header_left:
            st.markdown("#### :primary[:material/smart_toy:] AI Adoption")
        with header_right:
            st.markdown("##### :primary[:material/lightbulb:] Key Insights")
        chart_col, insight_col = st.columns([2, 1])
        
        with chart_col:
            ai_comp_data = []
            for level in df['ai_adoption'].dropna().unique():
                sel_pct = (selected_df['ai_adoption'] == level).sum() / n_selected * 100
                base_pct = (baseline_df['ai_adoption'] == level).sum() / len(baseline_df) * 100 if len(baseline_df) > 0 else 0
                ai_comp_data.append({'level': level[:20], 'Selected': sel_pct, 'Baseline': base_pct, 'full_level': level})
            
            ai_comp = pd.DataFrame(ai_comp_data)
            melted = ai_comp.melt(id_vars=['level'], value_vars=['Selected', 'Baseline'],
                                  var_name='group', value_name='percentage')
            
            chart = alt.Chart(melted).mark_bar(cornerRadiusEnd=4).encode(
                y=alt.Y('level:N', title=None),
                x=alt.X('percentage:Q', title='Percentage'),
                color=alt.Color('group:N', scale=alt.Scale(domain=['Selected', 'Baseline'], range=get_compare_colors()),
                               legend=alt.Legend(orient='bottom', direction='horizontal', titleOrient='left')),
                yOffset='group:N',
                tooltip=['level:N', 'group:N', alt.Tooltip('percentage:Q', format='.1f')]
            ).properties(height=360)
            st.altair_chart(chart, use_container_width=True)
        
        with insight_col:
            if ai_comp_data:
                biggest_ai_diff = max(ai_comp_data, key=lambda x: abs(x['Selected'] - x['Baseline']))
                ai_diff = biggest_ai_diff['Selected'] - biggest_ai_diff['Baseline']
                direction = "more" if ai_diff > 0 else "less"
                embedded = next((x for x in ai_comp_data if 'embedded' in x['full_level'].lower()), None)
                experimenting = next((x for x in ai_comp_data if 'experiment' in x['full_level'].lower()), None)
                st.caption(f"The AI adoption landscape reveals an interesting pattern: teams with {pain_desc} are **{abs(ai_diff):.0f}%** {direction} likely to be at the :primary[{biggest_ai_diff['full_level']}] stage.")
                if embedded:
                    emb_diff = embedded['Selected'] - embedded['Baseline']
                    if emb_diff > 3:
                        st.caption(f"A notable **{embedded['Selected']:.0f}%** have :primary[AI fully embedded] in workflows vs **{embedded['Baseline']:.0f}%** baseline. This suggests that {pain_desc} may actually :primary[accelerate AI investment] as teams seek technological solutions to operational challenges.")
                    elif emb_diff < -3:
                        st.caption(f"Only **{embedded['Selected']:.0f}%** have achieved :primary[full AI integration] compared to **{embedded['Baseline']:.0f}%** baseline. The presence of {pain_desc} appears to create :primary[barriers to AI maturity]—perhaps due to competing priorities or resource constraints.")
                    else:
                        st.caption(f"AI embedding rates remain :primary[comparable] (**{embedded['Selected']:.0f}%** vs **{embedded['Baseline']:.0f}%**), indicating that {pain_desc} neither accelerates nor impedes the path to full AI integration.")
                if experimenting and abs(experimenting['Selected'] - experimenting['Baseline']) > 5:
                    exp_diff = experimenting['Selected'] - experimenting['Baseline']
                    exp_dir = "more" if exp_diff > 0 else "fewer"
                    st.caption(f"Additionally, **{abs(exp_diff):.0f}%** {exp_dir} are in the :primary[experimentation phase], hinting at different AI adoption trajectories.")

with st.container(border=True):
    header_left, header_right = st.columns([2, 1])
    with header_left:
        st.markdown("#### :primary[:material/grid_on:] Pain Point Co-occurrence")
    with header_right:
        st.markdown("##### :primary[:material/lightbulb:] Key Insights")
    chart_col, insight_col = st.columns([2, 1])
    
    if len(unique_pains) >= 2:
        top_pains = [p for p in unique_pains[:8]]
        
        cooc_matrix = pd.DataFrame(0, index=top_pains, columns=top_pains)
        
        for pains in df['modeling_pain_points'].dropna():
            pain_list = [p.strip() for p in str(pains).split(', ') if p.strip() in top_pains]
            for p1 in pain_list:
                for p2 in pain_list:
                    cooc_matrix.loc[p1, p2] += 1
        
        for p in top_pains:
            if cooc_matrix.loc[p, p] > 0:
                cooc_matrix.loc[p, :] = cooc_matrix.loc[p, :] / cooc_matrix.loc[p, p] * 100
        
        cooc_matrix = cooc_matrix.round(0)
        
        def wrap_label(text, max_width=20):
            words = text.split()
            lines = []
            current_line = []
            current_len = 0
            for word in words:
                if current_len + len(word) + (1 if current_line else 0) <= max_width:
                    current_line.append(word)
                    current_len += len(word) + (1 if len(current_line) > 1 else 0)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
                    current_len = len(word)
            if current_line:
                lines.append(' '.join(current_line))
            return '<br>'.join(lines)
        
        wrapped_labels = [wrap_label(p) for p in top_pains]
        cooc_matrix.index = wrapped_labels
        cooc_matrix.columns = wrapped_labels
        
        with chart_col:
            fig = px.imshow(
                cooc_matrix,
                color_continuous_scale=get_plotly_scale(),
                labels=dict(color="Co-occurrence %"),
                text_auto='.0f',
                aspect='auto'
            )
            fig.update_traces(xgap=1, ygap=1)
            fig.update_layout(height=450, margin=dict(t=10))
            fig.update_xaxes(tickangle=90)
            fig.update_yaxes(tickangle=0)
            st.plotly_chart(fig, use_container_width=True)
        
        with insight_col:
            cooc_no_diag = cooc_matrix.copy()
            for i in range(len(cooc_no_diag)):
                cooc_no_diag.iloc[i, i] = 0
            max_val = cooc_no_diag.max().max()
            max_pair = None
            for i, row in enumerate(top_pains):
                for j, col in enumerate(top_pains):
                    if i != j and cooc_matrix.iloc[i, j] == max_val:
                        max_pair = (row, col, max_val)
                        break
                if max_pair:
                    break
            
            if max_pair:
                st.caption(f"The strongest co-occurrence appears between :primary[{max_pair[0]}] and :primary[{max_pair[1]}] at **{max_pair[2]:.0f}%**—teams experiencing one are highly likely to face the other.")
            
            avg_cooc = cooc_no_diag.values.sum() / (len(top_pains) * (len(top_pains) - 1)) if len(top_pains) > 1 else 0
            if avg_cooc > 40:
                st.caption(f"With an average co-occurrence of **{avg_cooc:.0f}%**, pain points in this dataset tend to cluster together, suggesting systemic rather than isolated issues.")
            elif avg_cooc > 25:
                st.caption(f"The average co-occurrence of **{avg_cooc:.0f}%** indicates moderate interconnection between pain points—addressing one may partially alleviate others.")
            else:
                st.caption(f"At **{avg_cooc:.0f}%** average co-occurrence, these pain points appear relatively independent, suggesting targeted interventions may be effective.")
            
            row_sums = cooc_no_diag.sum(axis=1)
            most_connected_idx = row_sums.idxmax()
            most_connected_pain = top_pains[list(cooc_matrix.index).index(most_connected_idx)]
            st.caption(f":primary[{most_connected_pain}] shows the highest connectivity to other pain points, making it a potential leverage point for improvement initiatives.")
