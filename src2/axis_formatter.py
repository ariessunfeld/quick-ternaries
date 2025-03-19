
from typing import Dict, List, Optional

import plotly.io as pio
import plotly.graph_objects as go
from plotly.graph_objects import Figure, Layout

from src2.ternary_trace_maker_4 import TernaryTraceMaker


class AxisFormatter:
    """
    Handles formatting of chemical formulas and axis labels.
    """
    
    @staticmethod
    def format_subscripts(oxide: str) -> str:
        """
        Formats chemical formulas with proper subscripts for HTML display.
        
        Args:
            oxide: A chemical formula or compound name
            
        Returns:
            HTML formatted string with proper subscripts
        """
        if oxide.lower() == 'feot':
            return "FeO<sub>T</sub>"
        return "".join('<sub>' + x + '</sub>' if x.isnumeric() else x for x in oxide)

    @staticmethod
    def format_scaled_name(apex_columns: List[str], scale_map: Dict[str, float]) -> str:
        """
        Formats an axis name considering scale factors.
        
        Args:
            apex_columns: List of column names for the apex
            scale_map: Dictionary mapping column names to scale factors
            
        Returns:
            Formatted axis name with scale factors
        """
        # Get unique scale values for these columns
        unique_scale_vals = sorted(set(scale_map.get(col, 1) for col in apex_columns), reverse=True)
        
        # If all columns have the same scale factor
        if len(unique_scale_vals) == 1 and unique_scale_vals[0] != 1:
            num = round(unique_scale_vals[0],2)
            if num == int(num):
                fmt_num = f'{num:.0f}'
            elif 10*num == int(10*num):
                fmt_num = f'{num:.1f}'
            elif 100*num == int(100*num):
                fmt_num = f'{num:.2f}'
            else:
                fmt_num = num
            return f"{fmt_num}&times;({'+'.join(map(AxisFormatter.format_subscripts, apex_columns))})"

        # If columns have different scale factors
        parts = []
        for val in unique_scale_vals:
            cols = [c for c in apex_columns if scale_map.get(c, 1) == val]
            if not cols:
                continue
                
            if val != 1:
                num = round(val,2)
                if num == int(num):
                    fmt_num = f'{num:.0f}'
                elif 10*num == int(10*num):
                    fmt_num = f'{num:.1f}'
                elif 100*num == int(100*num):
                    fmt_num = f'{num:.2f}'
                else:
                    fmt_num = val
                parts.append(f"{fmt_num}&times;({'+'.join(map(AxisFormatter.format_subscripts, cols))})")
            else:
                parts.extend(map(AxisFormatter.format_subscripts, cols))
                
        return '+'.join(parts)

