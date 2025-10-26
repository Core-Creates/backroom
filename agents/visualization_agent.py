from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from openai import OpenAI
from pathlib import Path
import pandas as pd
import numpy as np
import traceback
import base64
import sys
import os
import io

try:
    import seaborn as sns
    HAVE_SEABORN = True
except ImportError:
    HAVE_SEABORN = False


class VisualizationAgent:
    """AI-powered agent that generates and executes Python visualization code dynamically."""
    
    def __init__(self, db_manager=None, output_dir: str = None):
        """Initialize the visualization agent.
        
        Args:
            db_manager: Database manager instance (optional for compatibility)
            output_dir: Directory to save plots. If None, uses current directory.
        """
        self.db_manager = db_manager
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        if output_dir is None:
            self.output_dir = Path.cwd() / "visualizations"
        else:
            self.output_dir = Path(output_dir)
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True)
        
        # Set up execution environment
        import datetime as dt_module
        self.execution_globals = {
            'plt': plt,
            'sns': sns,
            'pd': pd,
            'np': np,
            'datetime': dt_module,  # Import the module, not the class
            'timedelta': timedelta,
            'mdates': mdates,
            'Path': Path,
            'output_dir': self.output_dir,
        }
    
    def should_create_visualization(self, question: str, query_result: Dict[str, Any] = None) -> bool:
        """Determine if the question requires a visualization.
        
        Args:
            question: User's original question
            query_result: Results from SQL query execution (optional)
            
        Returns:
            bool: True if visualization should be created
        """
        # Keywords that suggest visualization
        viz_keywords = [
            'plot', 'chart', 'graph', 'visualize', 'show', 'display', 'draw',
            'trend', 'over time', 'historical', 'sales over', 'monthly', 'daily', 'weekly', 'yearly',
            'compare', 'comparison', 'distribution', 'pattern', 'pie', 'bar', 'line', 'scatter',
            'time-series', 'time series', 'histogram',
            'box plot', 'heatmap', 'correlation', 'regression', 'forecast'
        ]
        
        question_lower = question.lower()
        
        # Check if question contains visualization keywords
        has_viz_keywords = any(keyword in question_lower for keyword in viz_keywords)
        
        # Check if data has visualization potential (if query_result available)
        if query_result is None or not query_result.get("success", False):
            return has_viz_keywords
            
        data = query_result.get("data")
        if data is None or len(data) == 0:
            return False
        
        # Check for date columns
        has_date_column = any(col.lower() in ['date', 'time', 'datetime', 'timestamp'] 
                             for col in data.columns)
        
        # Check if we have numeric data to plot
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        has_numeric_data = len(numeric_columns) > 0
        
        return has_viz_keywords or (has_date_column and has_numeric_data and len(data) > 1)
    
    def generate_chart_code(self, question: str, data: pd.DataFrame) -> str:
        """Generate Python visualization code using OpenAI based on the question and data.
        
        Args:
            question: User's visualization request
            data: DataFrame to visualize
            
        Returns:
            str: Python code for creating the visualization
        """
        # Analyze the data structure
        data_info = {
            'columns': list(data.columns),
            'dtypes': {col: str(dtype) for col, dtype in data.dtypes.items()},
            'shape': data.shape,
            'numeric_columns': list(data.select_dtypes(include=[np.number]).columns),
            'categorical_columns': list(data.select_dtypes(include=['object']).columns),
            'sample_data': data.head(3).to_dict('records') if len(data) > 0 else []
        }
        
        # Create a detailed prompt for code generation
        prompt = f"""
You are a Python data visualization expert. Generate ONLY executable Python code to create a chart.

USER REQUEST: "{question}"

DATA INFO:
- Columns: {data_info['columns']}
- Types: {data_info['dtypes']} 
- Shape: {data_info['shape']}
- Sample: {data_info['sample_data']}

CRITICAL REQUIREMENTS:
1. Generate ONLY Python code - NO explanations, NO markdown, NO function definitions
2. Available variables: data (DataFrame), plt, sns, np, pd, datetime, output_dir
3. For timestamps use: datetime.now() NOT datetime.datetime.now()
4. Set figsize=(12, 8)
5. Handle missing data gracefully with data.dropna() if needed
6. NO 'return' statements - just assign to 'filepath' variable
7. Use plt.close() after saving
8. Always end with: filepath = str(filepath)

EXACT CODE STRUCTURE (follow this pattern):
```
# Handle data
if len(data) == 0:
    data = pd.DataFrame({{'item': ['No Data'], 'value': [0]}})

# Setup
fig, ax = plt.subplots(figsize=(12, 8))

# Your plotting code here (use data columns)
# Example: ax.bar(data['column1'], data['column2'])

# Formatting
plt.title('Your Chart Title')
plt.tight_layout()

# Save
filename = f"chart_{{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}}.png"
filepath = output_dir / filename
plt.savefig(filepath, dpi=300, bbox_inches='tight')
plt.close()
filepath = str(filepath)
```

CRITICAL: Always use datetime.datetime.now() for timestamps!
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            
            generated_code = response.choices[0].message.content.strip()
            
            # Clean up the code thoroughly
            if '```python' in generated_code:
                # Extract code between ```python and ```
                start = generated_code.find('```python') + 9
                end = generated_code.find('```', start)
                if end != -1:
                    generated_code = generated_code[start:end]
                else:
                    generated_code = generated_code[start:]
            elif '```' in generated_code:
                # Extract code between ``` markers
                parts = generated_code.split('```')
                if len(parts) >= 3:
                    generated_code = parts[1]
                elif len(parts) == 2:
                    generated_code = parts[1]
            
            # Fix common issues in generated code
            lines = generated_code.strip().split('\n')
            clean_lines = []
            for line in lines:
                # Fix datetime issues - ensure we use datetime.datetime.now()
                if 'datetime.now()' in line and 'datetime.datetime.now()' not in line:
                    line = line.replace('datetime.now()', 'datetime.datetime.now()')
                
                # Remove return statements
                if line.strip().startswith('return '):
                    # Convert return statement to assignment
                    value = line.strip()[7:]  # Remove 'return '
                    clean_lines.append(f'filepath = {value}')
                else:
                    clean_lines.append(line)
            
            return '\n'.join(clean_lines)
            
        except Exception as e:
            print(f"AI code generation failed: {e}")
            # Fallback to a simple chart
            return self._fallback_chart_code()
    
    def _fallback_chart_code(self) -> str:
        """Generate a simple fallback chart if AI generation fails."""
        return """# Fallback visualization code
if len(data) == 0:
    data = pd.DataFrame({'item': ['No Data'], 'value': [0]})

fig, ax = plt.subplots(figsize=(12, 8))

# Try to create a simple chart based on data structure
numeric_cols = data.select_dtypes(include=[np.number]).columns
categorical_cols = data.select_dtypes(include=['object']).columns

try:
    if len(numeric_cols) > 0 and len(categorical_cols) > 0:
        # Bar chart
        if len(data) <= 20:
            x_col = categorical_cols[0]
            y_col = numeric_cols[0]
            ax.bar(range(len(data)), data[y_col])
            ax.set_xticks(range(len(data)))
            ax.set_xticklabels(data[x_col], rotation=45, ha='right')
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
        else:
            x_col = categorical_cols[0] 
            y_col = numeric_cols[0]
            top_data = data.nlargest(10, y_col)
            ax.bar(range(len(top_data)), top_data[y_col])
            ax.set_xticks(range(len(top_data)))
            ax.set_xticklabels(top_data[x_col], rotation=45, ha='right')
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
    elif len(numeric_cols) >= 2:
        ax.scatter(data[numeric_cols[0]], data[numeric_cols[1]])
        ax.set_xlabel(numeric_cols[0])
        ax.set_ylabel(numeric_cols[1])
    elif len(numeric_cols) == 1:
        bins = max(1, min(20, len(data)//2))
        ax.hist(data[numeric_cols[0]], bins=bins)
        ax.set_xlabel(numeric_cols[0])
        ax.set_ylabel('Frequency')
    else:
        ax.text(0.5, 0.5, 'No suitable data for visualization', 
               ha='center', va='center', transform=ax.transAxes)
except Exception as e:
    ax.text(0.5, 0.5, f'Visualization error: {str(e)}', 
           ha='center', va='center', transform=ax.transAxes)

ax.set_title('Data Visualization')
plt.tight_layout()

filename = f"chart_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
filepath = output_dir / filename
plt.savefig(filepath, dpi=300, bbox_inches='tight')
plt.close()
filepath = str(filepath)"""

    def execute_chart_code(self, code: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Execute the generated visualization code safely.
        
        Args:
            code: Python code to execute
            data: DataFrame to use for visualization
            
        Returns:
            Dict with execution results
        """
        try:
            # Set up execution environment with data
            exec_globals = self.execution_globals.copy()
            exec_globals['data'] = data
            exec_locals = {}
            
            # Execute the code
            exec(code, exec_globals, exec_locals)
            
            # Get the filepath result
            filepath = exec_locals.get('filepath') or exec_globals.get('filepath')
            
            if filepath and Path(filepath).exists():
                return {
                    "success": True,
                    "chart_path": filepath,
                    "message": "Chart generated successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Chart file was not created or filepath not returned"
                }
                
        except Exception as e:
            error_msg = f"Error executing visualization code: {str(e)}"
            print(f"Execution error: {error_msg}")
            traceback.print_exc()
            
            return {
                "success": False,
                "error": error_msg,
                "traceback": traceback.format_exc()
            }
    
    def create_visualization(self, question: str, query_result: Dict[str, Any], 
                           query_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create visualization using dynamically generated Python code.
        
        Args:
            question: Original user question
            query_result: SQL query results
            query_info: Information about the generated query
            
        Returns:
            Dict with visualization info including file path and description
        """
        if not self.should_create_visualization(question, query_result):
            return {
                "created": False,
                "reason": "No visualization needed for this query"
            }
        
        data = query_result.get("data")
        if data is None or len(data) == 0:
            return {
                "created": False,
                "reason": "No data available for visualization"
            }
        
        try:
            print("🎨 Generating custom visualization code...")
            
            # Generate Python code for the specific request
            chart_code = self.generate_chart_code(question, data)
            
            print("🔧 Executing visualization code...")
            
            # Execute the generated code
            execution_result = self.execute_chart_code(chart_code, data)
            
            if execution_result["success"]:
                chart_path = execution_result["chart_path"]
                
                # Determine chart type from question for description
                question_lower = question.lower()
                if 'pie' in question_lower:
                    chart_type = "Pie Chart"
                elif any(kw in question_lower for kw in ['bar', 'column']):
                    chart_type = "Bar Chart"
                elif any(kw in question_lower for kw in ['line', 'trend', 'time']):
                    chart_type = "Line Chart"
                elif any(kw in question_lower for kw in ['scatter', 'correlation']):
                    chart_type = "Scatter Plot"
                elif any(kw in question_lower for kw in ['histogram', 'distribution']):
                    chart_type = "Histogram"
                elif 'heatmap' in question_lower:
                    chart_type = "Heatmap"
                else:
                    chart_type = "Custom Chart"
                
                return {
                    "created": True,
                    "chart_path": chart_path,
                    "chart_type": chart_type,
                    "description": f"AI-generated {chart_type} showing {len(data)} data points",
                    "generated_code": chart_code,
                    "execution_result": execution_result
                }
            else:
                return {
                    "created": False,
                    "reason": f"Failed to execute visualization code: {execution_result.get('error', 'Unknown error')}",
                    "generated_code": chart_code,
                    "execution_result": execution_result
                }
            
        except Exception as e:
            error_msg = f"Error in visualization generation: {str(e)}"
            print(f"Visualization error: {error_msg}")
            traceback.print_exc()
            
            return {
                "created": False,
                "reason": error_msg,
                "traceback": traceback.format_exc()
            }
    
    def get_chart_description(self, chart_info: Dict[str, Any]) -> str:
        """Generate a description of the created chart for the response.
        
        Args:
            chart_info: Information about the created chart
            
        Returns:
            str: Description to include in response
        """
        if not chart_info.get("created", False):
            return ""
        
        chart_type = chart_info.get("chart_type", "Chart")
        chart_path = chart_info.get("chart_path", "")
        description = chart_info.get("description", "")
        
        result = f"\n\n📊 **{chart_type} Created**\n"
        result += f"✨ {description}\n"
        result += f"📁 Saved at: `{chart_path}`\n\n"
        result += "🎨 This chart was created using AI-generated Python code that analyzes your data structure and creates the most appropriate visualization for your specific request."
        
        return result
    
    def get_generated_code(self, chart_info: Dict[str, Any]) -> str:
        """Get the generated Python code for the visualization.
        
        Args:
            chart_info: Information about the created chart
            
        Returns:
            str: The generated Python code
        """
        if not chart_info.get("created", False):
            return "No code generated - chart creation failed"
        
        code = chart_info.get("generated_code", "Code not available")
        
        return f"""
🐍 **Generated Python Code:**
```python
{code}
```
"""
    
    def create_custom_chart(self, question: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Create a completely custom chart based on natural language description.
        
        Args:
            question: Natural language description of desired chart
            data: DataFrame to visualize
            
        Returns:
            Dict with chart creation results
        """
        try:
            # Generate code for the custom request
            chart_code = self.generate_chart_code(question, data)
            
            # Execute the code
            execution_result = self.execute_chart_code(chart_code, data)
            
            if execution_result["success"]:
                return {
                    "success": True,
                    "chart_path": execution_result["chart_path"],
                    "generated_code": chart_code,
                    "message": "Custom chart created successfully"
                }
            else:
                return {
                    "success": False,
                    "error": execution_result.get("error", "Unknown error"),
                    "generated_code": chart_code
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating custom chart: {str(e)}",
                "traceback": traceback.format_exc()
            }
