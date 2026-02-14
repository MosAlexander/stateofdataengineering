import streamlit as st
import pandas as pd
import altair as alt
from data_utils import get_filtered_df
from chart_utils import create_donut_chart, get_compare_colors, get_categorical_colors

st.markdown("# :primary[:material/psychology:] Manager Self-Awareness")
st.markdown("Compare manager vs IC perspectives on leadership challenges and gaps")

df = get_filtered_df()

manager_roles = ['Manager / Director / VP', 'Data Architect', 'Team Lead']
managers_df = df[df['role'].str.contains('Manager|Director|VP|Lead|Architect', case=False, na=False)]
ics_df = df[~df['role'].str.contains('Manager|Director|VP|Lead|Architect', case=False, na=False)]

self_aware_df = managers_df[managers_df['has_leadership_gap'] == True]
non_aware_df = managers_df[managers_df['has_leadership_gap'] == False]

n_managers = len(managers_df)
n_self_aware = len(self_aware_df)
pct_self_aware = n_self_aware / n_managers * 100 if n_managers > 0 else 0

total_leadership_gap = df['has_leadership_gap'].sum()
pct_of_gap = n_self_aware / total_leadership_gap * 100 if total_leadership_gap > 0 else 0

with st.container(border=True):
    st.markdown("#### :primary[:material/analytics:] The Self-Aware Leader Cohort")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Leaders/Managers", f"{n_managers:,}")
    col2.metric("Self-Aware Leaders", f"{n_self_aware:,}")
    col3.metric("% of All Leaders", f"{pct_self_aware:.1f}%")
    col4.metric("% of Leadership Gap Citations", f"{pct_of_gap:.1f}%")

with st.container(border=True):
    st.markdown("#### :primary[:material/compare:] Leaders vs ICs on Leadership Gap")
    
    manager_gap_rate = managers_df['has_leadership_gap'].sum() / n_managers * 100 if n_managers > 0 else 0
    ic_gap_rate = ics_df['has_leadership_gap'].sum() / len(ics_df) * 100 if len(ics_df) > 0 else 0
    
    comparison_data = pd.DataFrame([
        {'group': 'Leaders/Managers', 'gap_rate': manager_gap_rate, 'count': n_managers},
        {'group': 'Individual Contributors', 'gap_rate': ic_gap_rate, 'count': len(ics_df)}
    ])
    
    compare_colors = get_compare_colors()
    chart = alt.Chart(comparison_data).mark_bar(cornerRadiusEnd=4).encode(
        x=alt.X('group:N', title=None, axis=alt.Axis(labelAngle=0, labelLimit=200)),
        y=alt.Y('gap_rate:Q', title='% Citing Leadership Gap'),
        color=alt.Color('group:N', scale=alt.Scale(domain=['Leaders/Managers', 'Individual Contributors'],
                                                    range=compare_colors),
                        legend=alt.Legend(orient='bottom', title=None)),
        tooltip=['group:N', alt.Tooltip('gap_rate:Q', format='.1f'), 'count:Q']
    ).properties(height=300)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.altair_chart(chart, use_container_width=True)
    with col2:
        st.markdown("##### :primary[:material/lightbulb:] Key Insights")
        delta = manager_gap_rate - ic_gap_rate
        if delta > 0:
            st.caption(f"**:primary[Gap difference:]** Leaders cite leadership gaps {delta:.1f}% more than ICs — suggesting greater self-awareness among those in management roles.")
            st.caption(f"**:primary[Leaders:]** {manager_gap_rate:.1f}% acknowledge leadership as a bottleneck — a sign of introspection about their own impact.")
            st.caption(f"**:primary[ICs:]** {ic_gap_rate:.1f}% cite leadership gaps — often reflecting observations of management from below.")
        elif delta < 0:
            st.caption(f"**:primary[Gap difference:]** Leaders cite leadership gaps {abs(delta):.1f}% less than ICs — potential blind spot in self-assessment.")
            st.caption(f"**:primary[Leaders:]** {manager_gap_rate:.1f}% acknowledge leadership issues — lower than their teams perceive.")
            st.caption(f"**:primary[ICs:]** {ic_gap_rate:.1f}% cite leadership gaps — indicating disconnect between management perception and team experience.")
        else:
            st.caption("**Alignment:** Leaders and ICs cite leadership gaps at the same rate — rare consensus on organizational challenges.")

def create_horizontal_bar(data, column, height=250):
    counts = data[column].value_counts().head(6).reset_index()
    counts.columns = ['category', 'count']
    counts['percentage'] = counts['count'] / counts['count'].sum() * 100
    return alt.Chart(counts).mark_bar(cornerRadiusEnd=4).encode(
        y=alt.Y('category:N', sort='-x', title=None),
        x=alt.X('percentage:Q', title='%'),
        color=alt.Color('category:N', scale=alt.Scale(scheme='viridis'), legend=None),
        tooltip=['category:N', alt.Tooltip('percentage:Q', format='.1f', title='%'), 'count:Q']
    ).properties(height=height)

def create_stacked_bar(data, column, height=80):
    counts = data[column].value_counts().head(6).reset_index()
    counts.columns = ['category', 'count']
    counts['percentage'] = counts['count'] / counts['count'].sum() * 100
    return alt.Chart(counts).mark_bar().encode(
        x=alt.X('percentage:Q', stack='normalize', title='%', axis=alt.Axis(format='%')),
        color=alt.Color('category:N', scale=alt.Scale(scheme='viridis'), legend=alt.Legend(orient='bottom', columns=2, title=None)),
        tooltip=['category:N', alt.Tooltip('percentage:Q', format='.1f', title='%'), 'count:Q']
    ).properties(height=height)

def create_treemap(data, column):
    import altair as alt
    counts = data[column].value_counts().head(6).reset_index()
    counts.columns = ['category', 'count']
    counts['percentage'] = counts['count'] / counts['count'].sum() * 100
    total = counts['count'].sum()
    
    def layout_treemap(items, x0, y0, x1, y1, vertical=True):
        if len(items) == 0:
            return []
        if len(items) == 1:
            return [(items[0]['category'], items[0]['count'], x0, y0, x1, y1)]
        
        total_val = sum(i['count'] for i in items)
        mid_val = total_val / 2
        cumsum = 0
        split_idx = 0
        for i, item in enumerate(items):
            cumsum += item['count']
            if cumsum >= mid_val:
                split_idx = i + 1
                break
        split_idx = max(1, min(split_idx, len(items) - 1))
        
        left_items = items[:split_idx]
        right_items = items[split_idx:]
        left_sum = sum(i['count'] for i in left_items)
        ratio = left_sum / total_val if total_val > 0 else 0.5
        
        if vertical:
            mid_x = x0 + (x1 - x0) * ratio
            return layout_treemap(left_items, x0, y0, mid_x, y1, False) + layout_treemap(right_items, mid_x, y0, x1, y1, False)
        else:
            mid_y = y0 + (y1 - y0) * ratio
            return layout_treemap(left_items, x0, y0, x1, mid_y, True) + layout_treemap(right_items, x0, mid_y, x1, y1, True)
    
    items = [{'category': row['category'], 'count': row['count']} for _, row in counts.iterrows()]
    rects = layout_treemap(items, 0, 0, 100, 100)
    
    rect_data = pd.DataFrame(rects, columns=['category', 'count', 'x0', 'y0', 'x1', 'y1'])
    rect_data['percentage'] = rect_data['count'] / rect_data['count'].sum() * 100
    
    chart_rects = alt.Chart(rect_data).mark_rect(stroke='white', strokeWidth=2).encode(
        x=alt.X('x0:Q', axis=None, scale=alt.Scale(domain=[0, 100])),
        x2='x1:Q',
        y=alt.Y('y0:Q', axis=None, scale=alt.Scale(domain=[0, 100])),
        y2='y1:Q',
        color=alt.Color('category:N', scale=alt.Scale(scheme='viridis'), legend=alt.Legend(orient='bottom', columns=2, title=None)),
        tooltip=['category:N', alt.Tooltip('percentage:Q', format='.1f', title='%'), 'count:Q']
    )
    rect_data['width'] = rect_data['x1'] - rect_data['x0']
    rect_data['height'] = rect_data['y1'] - rect_data['y0']
    rect_data['angle'] = rect_data.apply(lambda r: 270 if r['height'] > r['width'] * 1.5 else 0, axis=1)
    
    def format_label(row):
        label = row['category'].replace('/', ' / ')
        if ' / ' in label:
            label = label.replace(' / ', '\n')
        elif len(label) > 12 and ' ' in label:
            mid = len(label) // 2
            space_idx = label.find(' ', mid - 5)
            if space_idx == -1:
                space_idx = label.rfind(' ', 0, mid + 5)
            if space_idx > 0:
                label = label[:space_idx] + '\n' + label[space_idx+1:]
        return label
    
    rect_data['label'] = rect_data.apply(format_label, axis=1)
    
    text = alt.Chart(rect_data).mark_text(fontSize=9, color='white', fontWeight='bold', lineBreak='\n').encode(
        x=alt.X('mid_x:Q', axis=None),
        y=alt.Y('mid_y:Q', axis=None),
        text='label:N',
        angle='angle:Q'
    ).transform_calculate(mid_x='(datum.x0 + datum.x1) / 2', mid_y='(datum.y0 + datum.y1) / 2')
    return (chart_rects + text).properties(height=350, width=350)

def create_lollipop(data, column, height=250):
    counts = data[column].value_counts().head(6).reset_index()
    counts.columns = ['category', 'count']
    counts['percentage'] = counts['count'] / counts['count'].sum() * 100
    line = alt.Chart(counts).mark_rule(strokeWidth=2).encode(
        y=alt.Y('category:N', sort='-x', title=None),
        x=alt.X('percentage:Q', title='%'),
        color=alt.Color('category:N', scale=alt.Scale(scheme='viridis'), legend=None)
    )
    point = alt.Chart(counts).mark_circle(size=100).encode(
        y=alt.Y('category:N', sort='-x'),
        x=alt.X('percentage:Q'),
        color=alt.Color('category:N', scale=alt.Scale(scheme='viridis'), legend=None),
        tooltip=['category:N', alt.Tooltip('percentage:Q', format='.1f', title='%'), 'count:Q']
    )
    return (line + point).properties(height=height)

def create_waffle(data, column, grid_size=10):
    counts = data[column].value_counts().head(6).reset_index()
    counts.columns = ['category', 'count']
    total = counts['count'].sum()
    counts['squares'] = (counts['count'] / total * (grid_size * grid_size)).round().astype(int)
    squares = []
    idx = 0
    for _, row in counts.iterrows():
        for _ in range(int(row['squares'])):
            squares.append({'category': row['category'], 'x': idx % grid_size, 'y': idx // grid_size})
            idx += 1
    squares_df = pd.DataFrame(squares)
    return alt.Chart(squares_df).mark_square(size=200).encode(
        x=alt.X('x:O', axis=None),
        y=alt.Y('y:O', axis=None, sort='descending'),
        color=alt.Color('category:N', scale=alt.Scale(scheme='viridis'), legend=alt.Legend(orient='bottom', columns=2, title=None)),
        tooltip=['category:N']
    ).properties(height=250, width=250)

if n_self_aware > 0:
    with st.container(border=True):
        st.markdown("#### :primary[:material/lightbulb:] What Characterizes Self-Aware Leaders?")
        st.caption("Defined as managers/directors/VPs who cited 'Lack of leadership' as their biggest bottleneck — suggesting they recognize leadership gaps, potentially including their own.")
        
        sa_industry = self_aware_df['industry'].value_counts(normalize=True).head(5) * 100
        sa_size = self_aware_df['org_size'].value_counts(normalize=True).head(5) * 100
        
        col1, col2, col3 = st.columns([3, 3, 2])
        
        with col1:
            st.markdown("##### Their Industries")
            st.altair_chart(create_treemap(self_aware_df, 'industry'), use_container_width=True)
        
        with col2:
            st.markdown("##### Their Org Sizes")
            st.altair_chart(create_treemap(self_aware_df, 'org_size'), use_container_width=True)
        
        with col3:
            st.markdown("##### :primary[:material/lightbulb:] Key Insights")
            top_ind = sa_industry.idxmax() if len(sa_industry) > 0 else "N/A"
            top_ind_pct = sa_industry.max() if len(sa_industry) > 0 else 0
            top_size = sa_size.idxmax() if len(sa_size) > 0 else "N/A"
            top_size_pct = sa_size.max() if len(sa_size) > 0 else 0
            second_ind = sa_industry.index[1] if len(sa_industry) > 1 else "N/A"
            second_ind_pct = sa_industry.iloc[1] if len(sa_industry) > 1 else 0
            st.caption(f"**:primary[Industry mix:]** {top_ind} represents {top_ind_pct:.0f}% of self-aware leaders, followed by {second_ind} ({second_ind_pct:.0f}%) — these sectors have the highest concentration of introspective managers.")
            st.caption(f"**:primary[Org size mix:]** {top_size} accounts for {top_size_pct:.0f}% of self-aware leaders — organizational scale influences leadership introspection.")
            st.caption(f"**:primary[Pattern:]** Self-aware leaders cluster in specific industries and org sizes — indicating that environment shapes leadership self-reflection.")
    
    with st.container(border=True):
        st.markdown("#### :primary[:material/compare:] Self-Aware vs Non-Aware Leaders")
        
        sa_ff = self_aware_df['has_firefighting'].sum() / n_self_aware * 100
        na_ff = non_aware_df['has_firefighting'].sum() / len(non_aware_df) * 100 if len(non_aware_df) > 0 else 0
        sa_growth = (self_aware_df['team_growth_2026'] == 'Grow').sum() / n_self_aware * 100
        na_growth = (non_aware_df['team_growth_2026'] == 'Grow').sum() / len(non_aware_df) * 100 if len(non_aware_df) > 0 else 0
        sa_ai = self_aware_df['ai_embedded'].sum() / n_self_aware * 100
        na_ai = non_aware_df['ai_embedded'].sum() / len(non_aware_df) * 100 if len(non_aware_df) > 0 else 0
        
        ff_diff = sa_ff - na_ff
        growth_diff = sa_growth - na_growth
        ai_diff = sa_ai - na_ai
        
        metric_order = ['Firefighting', 'Expect Growth', 'AI Embedded']
        comparison_df = pd.DataFrame([
            {'metric': 'Firefighting', 'Self-Aware': sa_ff, 'Non-Aware': na_ff},
            {'metric': 'Expect Growth', 'Self-Aware': sa_growth, 'Non-Aware': na_growth},
            {'metric': 'AI Embedded', 'Self-Aware': sa_ai, 'Non-Aware': na_ai}
        ])
        
        col_chart, col_insights = st.columns([2, 1])
        
        with col_chart:
            m1, m2, m3 = st.columns(3)
            m1.metric("Firefighting Rate", f"{sa_ff:.1f}%", delta=f"{ff_diff:+.1f}% vs non-aware", delta_color="inverse")
            m2.metric("Expect Growth", f"{sa_growth:.1f}%", delta=f"{growth_diff:+.1f}% vs non-aware")
            m3.metric("AI Embedded", f"{sa_ai:.1f}%", delta=f"{ai_diff:+.1f}% vs non-aware")
            
            melted = comparison_df.melt(id_vars=['metric'], value_vars=['Self-Aware', 'Non-Aware'], var_name='Group', value_name='Percentage')
            compare_colors = get_compare_colors()
            chart = alt.Chart(melted).mark_bar(cornerRadiusEnd=4).encode(
                x=alt.X('metric:N', title=None, axis=alt.Axis(labelAngle=0), sort=metric_order),
                y=alt.Y('Percentage:Q', title='%'),
                color=alt.Color('Group:N', scale=alt.Scale(domain=['Self-Aware', 'Non-Aware'], range=compare_colors), legend=alt.Legend(orient='bottom', title=None)),
                xOffset='Group:N',
                tooltip=['metric:N', 'Group:N', alt.Tooltip('Percentage:Q', format='.1f')]
            ).properties(height=400)
            st.altair_chart(chart, use_container_width=True)
        
        with col_insights:
            st.markdown("##### :primary[:material/lightbulb:] Key Insights")
            if ff_diff > 0:
                st.caption(f"**:primary[Firefighting:]** Time spent on reactive crisis work. Self-aware leaders report {ff_diff:.1f}% higher rates than non-aware counterparts — suggesting they're more attuned to or honest about the operational chaos their teams face.")
            else:
                st.caption(f"**:primary[Firefighting:]** Time spent on reactive crisis work. Self-aware leaders report {abs(ff_diff):.1f}% lower rates — leadership introspection may correlate with better stability, or calmer environments allow more self-reflection.")
            if growth_diff > 0:
                st.caption(f"**:primary[Growth outlook:]** Whether leaders expect team growth in 2026. Self-aware leaders are {growth_diff:.1f}% more likely to anticipate growth — acknowledging challenges doesn't dampen their optimism about their team's trajectory.")
            else:
                st.caption(f"**:primary[Growth outlook:]** Whether leaders expect team growth in 2026. Self-aware leaders are {abs(growth_diff):.1f}% less likely to anticipate growth — recognizing gaps may bring a more realistic or cautious view.")
            if ai_diff > 0:
                st.caption(f"**:primary[AI embedded:]** Whether AI is integrated into most workflows. Self-aware leaders show {ai_diff:.1f}% higher adoption — openness to recognizing problems may extend to embracing new technologies and solutions.")
            else:
                st.caption(f"**:primary[AI embedded:]** Whether AI is integrated into most workflows. Self-aware leaders show {abs(ai_diff):.1f}% lower adoption — they may prioritize human and process challenges before technical solutions.")

    with st.container(border=True):
        st.markdown("#### :primary[:material/format_quote:] Voices from Leaders")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Self-Aware Leaders")
            leader_wishes = self_aware_df[self_aware_df['industry_wish'].notna() & (self_aware_df['industry_wish'] != '')]
            if len(leader_wishes) > 0:
                all_sa_text = ' '.join(leader_wishes['industry_wish'].str.lower())
                sa_themes = []
                if 'leadership' in all_sa_text or 'leader' in all_sa_text or 'management' in all_sa_text: sa_themes.append("Leadership development")
                if 'culture' in all_sa_text or 'team' in all_sa_text: sa_themes.append("Team culture")
                if 'process' in all_sa_text or 'workflow' in all_sa_text: sa_themes.append("Process improvement")
                if 'ai' in all_sa_text or 'automat' in all_sa_text: sa_themes.append("AI/Automation")
                if 'talent' in all_sa_text or 'hiring' in all_sa_text or 'retention' in all_sa_text: sa_themes.append("Talent")
                if sa_themes:
                    st.caption(f":primary[:material/summarize:] **Common themes:** {', '.join(sa_themes)}")
                
                leader_sample = leader_wishes.sample(min(3, len(leader_wishes)))
                for _, row in leader_sample.iterrows():
                    with st.container(border=True):
                        st.markdown(f"*\"{row['industry_wish']}\"*")
                        st.caption(f"— {row['role']}, {row['industry']}")
                
                remaining = leader_wishes[~leader_wishes.index.isin(leader_sample.index)]
                if len(remaining) > 0:
                    with st.expander(f"Show more ({len(remaining)} more quotes)"):
                        for _, row in remaining.iterrows():
                            st.markdown(f"*\"{row['industry_wish']}\"*")
                            st.caption(f"— {row['role']}, {row['industry']}")
                            st.divider()
            else:
                st.info("No quotes available")
        
        with col2:
            st.markdown("##### Non-Aware Leaders")
            non_aware_wishes = non_aware_df[non_aware_df['industry_wish'].notna() & (non_aware_df['industry_wish'] != '')]
            if len(non_aware_wishes) > 0:
                all_na_text = ' '.join(non_aware_wishes['industry_wish'].str.lower())
                na_themes = []
                if 'tool' in all_na_text or 'technology' in all_na_text or 'tech' in all_na_text: na_themes.append("Better tooling")
                if 'data' in all_na_text or 'quality' in all_na_text: na_themes.append("Data quality")
                if 'budget' in all_na_text or 'resource' in all_na_text or 'cost' in all_na_text: na_themes.append("Resources/Budget")
                if 'ai' in all_na_text or 'automat' in all_na_text: na_themes.append("AI/Automation")
                if 'time' in all_na_text or 'faster' in all_na_text or 'speed' in all_na_text: na_themes.append("Speed/Efficiency")
                if na_themes:
                    st.caption(f":primary[:material/summarize:] **Common themes:** {', '.join(na_themes)}")
                
                non_sample = non_aware_wishes.sample(min(3, len(non_aware_wishes)))
                for _, row in non_sample.iterrows():
                    with st.container(border=True):
                        st.markdown(f"*\"{row['industry_wish']}\"*")
                        st.caption(f"— {row['role']}, {row['industry']}")
                
                remaining = non_aware_wishes[~non_aware_wishes.index.isin(non_sample.index)]
                if len(remaining) > 0:
                    with st.expander(f"Show more ({len(remaining)} more quotes)"):
                        for _, row in remaining.iterrows():
                            st.markdown(f"*\"{row['industry_wish']}\"*")
                            st.caption(f"— {row['role']}, {row['industry']}")
                            st.divider()
            else:
                st.info("No quotes available")
