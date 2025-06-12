import plotly.graph_objects as go
import plotly.express as px
import json
import numpy as np

# Define component positions in hierarchical layout to minimize overlap
positions = {
    # Interfaces (left column)
    "web_ui": (0.1, 0.8),
    "cli": (0.1, 0.4),
    
    # Core components (center column)
    "ai_engine": (0.4, 0.6),         # Central orchestrator
    "llm_manager": (0.4, 0.8),       # Above AI engine
    "module_system": (0.4, 0.4),     # Below AI engine
    "config_manager": (0.4, 0.2),    # Bottom of core
    
    # Tools/modules (right column)
    "datetime_tool": (0.7, 0.85),
    "math_tools": (0.7, 0.65),
    "task_manager": (0.7, 0.45),
    "web_search": (0.7, 0.25),
    
    # Tests (bottom center)
    "tests": (0.4, 0.05)
}

# Updated color mapping with more distinct colors
color_map = {
    "core": "#5D878F",      # Cyan for core
    "module": "#ECEBD5",    # Light green for modules/tools
    "interface": "#FFC185", # Light orange for interfaces
    "test": "#B4413C"       # Moderate red for tests (more distinct)
}

# Line styles for different connection types
line_styles = {
    "user_request": {"color": "#1FB8CD", "dash": "solid", "width": 3},
    "llm_call": {"color": "#D2BA4C", "dash": "dash", "width": 2},
    "tool_discovery": {"color": "#964325", "dash": "dot", "width": 2},
    "tool_registration": {"color": "#ECEBD5", "dash": "dashdot", "width": 2},
    "tool_execution": {"color": "#944454", "dash": "solid", "width": 2},
    "testing": {"color": "#13343B", "dash": "dash", "width": 2}
}

# Prepare data
components = {
    "ai_engine": {"type": "core", "name": "AI Engine"},
    "module_system": {"type": "core", "name": "Module System"},
    "llm_manager": {"type": "core", "name": "LLM Manager"},
    "config_manager": {"type": "core", "name": "Config Manager"},
    "datetime_tool": {"type": "module", "name": "DateTime Tool"},
    "math_tools": {"type": "module", "name": "Math Tools"},
    "task_manager": {"type": "module", "name": "Task Manager"},
    "web_search": {"type": "module", "name": "Web Search"},
    "web_ui": {"type": "interface", "name": "Web UI"},
    "cli": {"type": "interface", "name": "CLI"},
    "tests": {"type": "test", "name": "Tests"}
}

connections = [
    {"from": "web_ui", "to": "ai_engine", "type": "user_request"},
    {"from": "cli", "to": "ai_engine", "type": "user_request"},
    {"from": "ai_engine", "to": "llm_manager", "type": "llm_call"},
    {"from": "ai_engine", "to": "module_system", "type": "tool_discovery"},
    {"from": "module_system", "to": "datetime_tool", "type": "tool_registration"},
    {"from": "module_system", "to": "math_tools", "type": "tool_registration"},
    {"from": "module_system", "to": "task_manager", "type": "tool_registration"},
    {"from": "module_system", "to": "web_search", "type": "tool_registration"},
    {"from": "ai_engine", "to": "datetime_tool", "type": "tool_execution"},
    {"from": "ai_engine", "to": "math_tools", "type": "tool_execution"},
    {"from": "ai_engine", "to": "task_manager", "type": "tool_execution"},
    {"from": "ai_engine", "to": "web_search", "type": "tool_execution"},
    {"from": "tests", "to": "math_tools", "type": "testing"},
    {"from": "tests", "to": "task_manager", "type": "testing"}
]

fig = go.Figure()

# Add connection lines with arrows and different styles
for conn in connections:
    from_pos = positions[conn["from"]]
    to_pos = positions[conn["to"]]
    conn_type = conn["type"]
    style = line_styles[conn_type]
    
    # Add the connection line
    fig.add_trace(go.Scatter(
        x=[from_pos[0], to_pos[0]],
        y=[from_pos[1], to_pos[1]],
        mode='lines',
        line=dict(
            color=style["color"], 
            dash=style["dash"], 
            width=style["width"]
        ),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Add arrow annotation
    fig.add_annotation(
        x=to_pos[0],
        y=to_pos[1],
        ax=from_pos[0],
        ay=from_pos[1],
        xref="x", yref="y",
        axref="x", ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor=style["color"],
        opacity=0.7
    )

# Group components by type for legend
component_types = {}
for comp_id, comp_data in components.items():
    comp_type = comp_data["type"]
    if comp_type not in component_types:
        component_types[comp_type] = []
    component_types[comp_type].append((comp_id, comp_data))

# Add components as scatter points
for comp_type, comp_list in component_types.items():
    x_coords = []
    y_coords = []
    texts = []
    
    for comp_id, comp_data in comp_list:
        pos = positions[comp_id]
        x_coords.append(pos[0])
        y_coords.append(pos[1])
        texts.append(comp_data["name"])
    
    # Map component type to display name
    type_names = {
        "core": "Core",
        "module": "Tools/Modules", 
        "interface": "UI Interface",
        "test": "Tests"
    }
    
    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode='markers+text',
        marker=dict(
            size=30,
            color=color_map[comp_type],
            line=dict(width=3, color='white')
        ),
        text=texts,
        textposition="middle center",
        textfont=dict(size=9, color='black', family="Arial Black"),
        name=type_names[comp_type],
        hovertemplate='%{text}<extra></extra>',
        cliponaxis=False
    ))

# Add connection type legend
connection_legend_y = 0.95
for i, (conn_type, style) in enumerate(line_styles.items()):
    fig.add_trace(go.Scatter(
        x=[0.85, 0.9],
        y=[connection_legend_y - i*0.04, connection_legend_y - i*0.04],
        mode='lines+text',
        line=dict(
            color=style["color"],
            dash=style["dash"],
            width=style["width"]
        ),
        text=["", conn_type.replace("_", " ").title()],
        textposition="middle right",
        textfont=dict(size=8),
        showlegend=False,
        hoverinfo='skip'
    ))

# Update layout
fig.update_layout(
    title="Python Agent System Architecture",
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    plot_bgcolor='white',
    legend=dict(orientation='h', yanchor='bottom', y=1.05, xanchor='center', x=0.5)
)

fig.update_xaxes(range=[-0.05, 1.05])
fig.update_yaxes(range=[-0.05, 1.05])

fig.write_image("agent_system_architecture.png")