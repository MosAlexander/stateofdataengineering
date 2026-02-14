import altair as alt
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st
import textwrap

RAINBOW_COLORS = ['#8B5CF6', '#3B82F6', '#10B981', '#FACC15', '#F59E0B', '#EF4444']
COMPARE_COLORS = ['#8B5CF6', '#F59E0B']
PRIMARY_COLOR = '#3B82F6'
SECONDARY_COLOR = '#10B981'
PLOTLY_SCALE = [[0, '#8B5CF6'], [0.25, '#3B82F6'], [0.5, '#10B981'], [0.75, '#FACC15'], [1, '#EF4444']]

def get_categorical_colors():
    return RAINBOW_COLORS

def get_compare_colors():
    return COMPARE_COLORS

def get_primary_color():
    return PRIMARY_COLOR

def get_secondary_color():
    return SECONDARY_COLOR

def get_plotly_scale():
    return PLOTLY_SCALE


def create_donut_chart(df, column, title=None, height=450, top_n=None, legend_offset=20):
    counts = df[column].value_counts().reset_index()
    counts.columns = ['category', 'count']
    
    if top_n:
        top_counts = counts.head(top_n)
        other_count = counts.iloc[top_n:]['count'].sum()
        if other_count > 0:
            other_row = pd.DataFrame({'category': ['Other'], 'count': [other_count]})
            counts = pd.concat([top_counts, other_row], ignore_index=True)
        else:
            counts = top_counts
    
    counts['percentage'] = (counts['count'] / counts['count'].sum() * 100).round(1)
    
    category_order = counts['category'].tolist()
    
    chart = alt.Chart(counts).mark_arc(innerRadius=50, outerRadius=100).encode(
        theta=alt.Theta('count:Q'),
        color=alt.Color('category:N', scale=alt.Scale(range=get_categorical_colors()), sort=category_order, legend=alt.Legend(title=None, orient='bottom', columns=2, offset=legend_offset)),
        tooltip=['category:N', 'count:Q', alt.Tooltip('percentage:Q', format='.1f', title='%')]
    ).properties(height=height, title=title or '', padding={'top': 0, 'bottom': 0})
    
    return chart


def create_bar_chart(df, column, title=None, height=300, horizontal=True, color=None, top_n=None, varied_colors=True):
    if color is None:
        color = get_primary_color()
    counts = df[column].value_counts().reset_index()
    counts.columns = ['category', 'count']
    counts['percentage'] = (counts['count'] / counts['count'].sum() * 100).round(1)
    
    if top_n:
        counts = counts.head(top_n)
    
    if varied_colors:
        cat_colors = get_categorical_colors()
        color_encoding = alt.Color('category:N', scale=alt.Scale(range=cat_colors), legend=None)
    else:
        color_encoding = alt.value(color)
    
    if horizontal:
        chart = alt.Chart(counts).mark_bar(cornerRadiusEnd=4).encode(
            y=alt.Y('category:N', sort='-x', title=None, axis=alt.Axis(labelLimit=0, labelLineHeight=12)),
            x=alt.X('count:Q', title='Respondents'),
            color=color_encoding,
            tooltip=['category:N', 'count:Q', alt.Tooltip('percentage:Q', format='.1f', title='%')]
        ).properties(height=height, title=title or '')
    else:
        chart = alt.Chart(counts).mark_bar(cornerRadiusEnd=4).encode(
            x=alt.X('category:N', sort='-y', title=None),
            y=alt.Y('count:Q', title='Respondents'),
            color=color_encoding,
            tooltip=['category:N', 'count:Q', alt.Tooltip('percentage:Q', format='.1f', title='%')]
        ).properties(height=height, title=title or '')
    
    return chart


def create_grouped_bar(data, x_col, y_col, group_col, title=None, height=300):
    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X(f'{x_col}:N', title=None),
        y=alt.Y(f'{y_col}:Q', title='Percentage'),
        color=alt.Color(f'{group_col}:N', scale=alt.Scale(range=RAINBOW_COLORS)),
        xOffset=f'{group_col}:N',
        tooltip=[f'{x_col}:N', f'{group_col}:N', alt.Tooltip(f'{y_col}:Q', format='.1f')]
    ).properties(height=height, title=title or '')
    return chart


def wrap_labels(data, column, width=20, max_words_per_line=5):
    def wrap_by_words(text, max_words=max_words_per_line):
        words = str(text).split()
        if len(words) <= max_words:
            return text
        lines = []
        for i in range(0, len(words), max_words):
            lines.append(' '.join(words[i:i+max_words]))
        return '\n'.join(lines)
    
    data = data.copy()
    data[column] = data[column].apply(wrap_by_words)
    return data


def create_diverging_bar(data, category_col, value_col, title=None, height=300, varied_colors=True, wrap_width=None, max_words_per_line=5):
    data = wrap_labels(data, category_col, max_words_per_line=max_words_per_line)
    
    if varied_colors:
        data = data.copy()
        data = data.sort_values(value_col, ascending=False).reset_index(drop=True)
        data['_rank'] = data.index
        num_colors = len(RAINBOW_COLORS)
        data['_color'] = data['_rank'].apply(lambda x: RAINBOW_COLORS[x % num_colors])
        
        color_mapping = dict(zip(data[category_col], data['_color']))
        sorted_categories = data[category_col].tolist()
        
        chart = alt.Chart(data).mark_bar().encode(
            y=alt.Y(f'{category_col}:N', sort=sorted_categories, title=None, axis=alt.Axis(labelLimit=0, labelLineHeight=12)),
            x=alt.X(f'{value_col}:Q', title='Difference from Baseline (%)'),
            color=alt.Color(f'{category_col}:N', scale=alt.Scale(domain=sorted_categories, range=[color_mapping[c] for c in sorted_categories]), legend=None),
            tooltip=[f'{category_col}:N', alt.Tooltip(f'{value_col}:Q', format='.1f')]
        ).properties(height=height, title=title or '')
    else:
        colors = get_compare_colors()
        chart = alt.Chart(data).mark_bar().encode(
            y=alt.Y(f'{category_col}:N', sort='-x', title=None, axis=alt.Axis(labelLimit=0, labelLineHeight=12)),
            x=alt.X(f'{value_col}:Q', title='Difference from Baseline (%)'),
            color=alt.condition(
                alt.datum[value_col] > 0,
                alt.value(colors[0]),
                alt.value(colors[1])
            ),
            tooltip=[f'{category_col}:N', alt.Tooltip(f'{value_col}:Q', format='.1f')]
        ).properties(height=height, title=title or '')
    return chart


def create_stacked_bar(data, x_col, y_col, stack_col, title=None, height=300, x_sort=None):
    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X(f'{x_col}:N', sort=x_sort, title=None),
        y=alt.Y(f'{y_col}:Q', title='Percentage', stack='normalize'),
        color=alt.Color(f'{stack_col}:N', scale=alt.Scale(range=RAINBOW_COLORS)),
        tooltip=[f'{x_col}:N', f'{stack_col}:N', alt.Tooltip(f'{y_col}:Q', format='.1f')]
    ).properties(height=height, title=title or '')
    return chart


def create_heatmap(data, x_col, y_col, value_col, title=None, height=400):
    fig = px.imshow(
        data,
        color_continuous_scale=get_plotly_scale(),
        labels=dict(color=value_col),
        aspect='auto',
        text_auto='.0f'
    )
    fig.update_layout(height=height, title=title or '')
    return fig


def create_sankey(source_list, target_list, values, source_labels, target_labels, title=None, height=500):
    all_labels = source_labels + target_labels
    colors = get_compare_colors()
    
    source_indices = [source_labels.index(s) for s in source_list]
    target_indices = [len(source_labels) + target_labels.index(t) for t in target_list]
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=all_labels,
            color=[colors[0]] * len(source_labels) + [colors[1]] * len(target_labels)
        ),
        link=dict(
            source=source_indices,
            target=target_indices,
            value=values,
            color='rgba(150, 150, 150, 0.3)'
        )
    )])
    fig.update_layout(height=height, title=title or '')
    return fig


def create_radar_chart(categories, values, title=None, height=400):
    color = get_primary_color()
    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor=f'rgba{tuple(list(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + [0.3])}',
        line=dict(color=color, width=2)
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=height,
        title=title or ''
    )
    return fig


def create_gauge_chart(value, title=None, height=250):
    color = get_primary_color()
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title or ''},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 30], 'color': "#FFCCCC"},
                {'range': [30, 70], 'color': "#FFFFCC"},
                {'range': [70, 100], 'color': "#CCFFCC"}
            ]
        }
    ))
    fig.update_layout(height=height)
    return fig


def create_lollipop_chart(data, category_col, value_col, title=None, height=300, color=None, varied_colors=True):
    if color is None:
        color = get_primary_color()
    base = alt.Chart(data)
    
    if varied_colors:
        color_encoding = alt.Color(f'{category_col}:N', scale=alt.Scale(range=RAINBOW_COLORS), legend=None)
    else:
        color_encoding = alt.value(color)
    
    circles = base.mark_circle(size=100).encode(
        y=alt.Y(f'{category_col}:N', sort='-x', title=None, axis=alt.Axis(labelLimit=0)),
        x=alt.X(f'{value_col}:Q', title='Percentage'),
        color=color_encoding,
        tooltip=[f'{category_col}:N', alt.Tooltip(f'{value_col}:Q', format='.1f')]
    )
    
    rules = base.mark_rule(strokeWidth=2).encode(
        y=alt.Y(f'{category_col}:N', sort='-x', axis=alt.Axis(labelLimit=0)),
        x=alt.X(f'{value_col}:Q'),
        x2=alt.value(0),
        color=color_encoding
    )
    
    chart = (rules + circles).properties(height=height, title=title or '')
    return chart


def create_treemap(data, path_cols, value_col, title=None, height=400):
    fig = px.treemap(data, path=path_cols, values=value_col, color_continuous_scale=get_plotly_scale())
    fig.update_layout(height=height, title=title or '')
    return fig
