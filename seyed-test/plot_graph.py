#!/usr/bin/env python3
"""
Visualize the LangGraph retail data query workflow.
This script creates a visual representation of the graph structure.
"""

import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def plot_langgraph_workflow():
    """Create a visual representation of the LangGraph workflow."""
    
    # Create figure and axis
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Define node positions
    nodes = {
        'START': (1, 9),
        'analyze_question': (1, 7.5),
        'generate_query': (1, 6),
        'execute_query': (1, 4.5),
        'create_visualization': (1, 3),
        'format_response': (1, 1.5),
        'handle_error': (6, 5.5),
        'END': (1, 0)
    }
    
    # Define node colors and descriptions
    node_info = {
        'START': {'color': '#90EE90', 'desc': 'START\n(Entry Point)'},
        'analyze_question': {'color': '#87CEEB', 'desc': 'Analyze Question\n• Parse user input\n• Load database schema\n• Extract intent'},
        'generate_query': {'color': '#DDA0DD', 'desc': 'Generate Query\n• Convert natural language\n• Create SQL query\n• Validate syntax'},
        'execute_query': {'color': '#F0E68C', 'desc': 'Execute Query\n• Run SQL on database\n• Handle results\n• Check for errors'},
        'create_visualization': {'color': '#FFA07A', 'desc': 'Create Visualization\n• Detect chart opportunities\n• Generate charts (pie/bar/line)\n• Save high-quality images'},
        'format_response': {'color': '#98FB98', 'desc': 'Format Response\n• Convert to natural language\n• Add chart information\n• Create user-friendly output'},
        'handle_error': {'color': '#FFB6C1', 'desc': 'Handle Error\n• Process exceptions\n• Create error message\n• Graceful failure'},
        'END': {'color': '#90EE90', 'desc': 'END\n(Exit Point)'}
    }
    
    # Draw nodes
    for node_name, (x, y) in nodes.items():
        info = node_info[node_name]
        
        # Create fancy box
        if node_name in ['START', 'END']:
            # Special styling for start/end
            box = FancyBboxPatch(
                (x-0.4, y-0.3), 0.8, 0.6,
                boxstyle="round,pad=0.1",
                facecolor=info['color'],
                edgecolor='black',
                linewidth=2
            )
        else:
            # Regular nodes
            box = FancyBboxPatch(
                (x-0.7, y-0.4), 1.4, 0.8,
                boxstyle="round,pad=0.1",
                facecolor=info['color'],
                edgecolor='black',
                linewidth=1.5
            )
        
        ax.add_patch(box)
        
        # Add text
        ax.text(x, y, info['desc'], ha='center', va='center', 
                fontsize=9, fontweight='bold', wrap=True)
    
    # Define edges with conditions
    edges = [
        ('START', 'analyze_question', 'always', 'green'),
        ('analyze_question', 'generate_query', 'success', 'green'),
        ('analyze_question', 'handle_error', 'error', 'red'),
        ('generate_query', 'execute_query', 'success', 'green'),
        ('generate_query', 'handle_error', 'error', 'red'),
        ('execute_query', 'create_visualization', 'success', 'green'),
        ('execute_query', 'handle_error', 'error', 'red'),
        ('create_visualization', 'format_response', 'always', 'blue'),
        ('format_response', 'END', 'always', 'green'),
        ('handle_error', 'END', 'always', 'orange')
    ]
    
    # Draw edges
    for start, end, condition, color in edges:
        start_x, start_y = nodes[start]
        end_x, end_y = nodes[end]
        
        # Calculate arrow positions
        if start == 'analyze_question' and end == 'handle_error':
            # Curved arrow to error handler
            ax.annotate('', xy=(end_x-0.7, end_y), xytext=(start_x+0.7, start_y),
                       arrowprops=dict(arrowstyle='->', color=color, lw=2,
                                     connectionstyle="arc3,rad=0.3"))
            # Add condition label
            ax.text(3.5, 6.8, condition, ha='center', va='center', 
                   fontsize=8, color=color, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor=color))
        elif start == 'generate_query' and end == 'handle_error':
            # Curved arrow to error handler
            ax.annotate('', xy=(end_x-0.7, end_y), xytext=(start_x+0.7, start_y),
                       arrowprops=dict(arrowstyle='->', color=color, lw=2,
                                     connectionstyle="arc3,rad=0.2"))
            # Add condition label
            ax.text(3.5, 5.8, condition, ha='center', va='center', 
                   fontsize=8, color=color, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor=color))
        elif start == 'execute_query' and end == 'handle_error':
            # Curved arrow to error handler
            ax.annotate('', xy=(end_x-0.7, end_y), xytext=(start_x+0.7, start_y),
                       arrowprops=dict(arrowstyle='->', color=color, lw=2,
                                     connectionstyle="arc3,rad=0.1"))
            # Add condition label
            ax.text(3.5, 4.8, condition, ha='center', va='center', 
                   fontsize=8, color=color, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor=color))
        elif start == 'handle_error' and end == 'END':
            # Curved arrow from error to end
            ax.annotate('', xy=(end_x+0.7, end_y), xytext=(start_x-0.7, start_y),
                       arrowprops=dict(arrowstyle='->', color=color, lw=2,
                                     connectionstyle="arc3,rad=-0.3"))
        else:
            # Straight arrows for main path
            ax.annotate('', xy=(end_x, end_y+0.4), xytext=(start_x, start_y-0.4),
                       arrowprops=dict(arrowstyle='->', color=color, lw=2))
            
            # Add condition labels for main path
            if condition != 'always':
                mid_y = (start_y + end_y) / 2
                ax.text(start_x+0.5, mid_y, condition, ha='left', va='center', 
                       fontsize=8, color=color, fontweight='bold',
                       bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor=color))
    
    # Add title and legend
    ax.text(5, 9.5, 'LangGraph Retail Data Query Workflow', 
           ha='center', va='center', fontsize=16, fontweight='bold')
    
    # Create legend
    legend_elements = [
        mpatches.Patch(color='#87CEEB', label='Analysis & Parsing'),
        mpatches.Patch(color='#DDA0DD', label='Query Generation'),
        mpatches.Patch(color='#F0E68C', label='Query Execution'),
        mpatches.Patch(color='#FFA07A', label='Visualization Creation'),
        mpatches.Patch(color='#98FB98', label='Response Formatting'),
        mpatches.Patch(color='#FFB6C1', label='Error Handling'),
        mpatches.Patch(color='#90EE90', label='Start/End Points')
    ]
    
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.85))
    
    # Add workflow description
    description = """
    Enhanced Workflow Steps:
    1. User asks question in natural language
    2. System analyzes question and loads database schema
    3. LLM converts question to SQL query
    4. SQL query is executed against DuckDB database
    5. Visualization agent creates charts when appropriate
    6. Results and charts are formatted into natural language response
    7. Any errors are handled gracefully with informative messages
    
    New Feature: Automatic chart generation for:
    • Sales trends (line charts)
    • Top items (bar charts)
    • Distributions (pie charts)
    • Inventory analysis
    """
    
    ax.text(7.5, 3, description, ha='left', va='top', fontsize=9,
           bbox=dict(boxstyle="round,pad=0.5", facecolor='lightgray', alpha=0.8))
    
    plt.tight_layout()
    return fig

def main():
    """Main function to create and display the graph."""
    print("🎨 Creating LangGraph workflow visualization...")
    
    try:
        # Create the plot
        fig = plot_langgraph_workflow()
        
        # Save the plot
        output_path = Path(__file__).parent / 'langgraph_workflow.png'
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Graph saved as: {output_path}")
        
        # Display the plot
        plt.show()
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Install matplotlib: pip install matplotlib")
    except Exception as e:
        print(f"❌ Error creating visualization: {e}")

if __name__ == "__main__":
    main()