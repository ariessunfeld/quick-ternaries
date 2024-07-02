from typing import List

from PySide6.QtCore import (
    Slot, QObject, 
)

class PlotlyInterface(QObject):
    def __init__(self):
        super().__init__()
        self.selected_indices = []

    @Slot(list)
    def receive_selected_indices(self, indices: list):
        self.selected_indices = indices

    def get_indices(self) -> List:
        return self.selected_indices.copy()
    
    def applyColorChange(self):
        pass
        all_data = self.main_window.left_side.tab_manager.get_all_data()
        valid_tracenums = range(len(all_data['TraceTabs']))
        for inner_dict in self.selected_indices:
            print('Processing', inner_dict)
            tracenum, idx = inner_dict['curveNumber'], inner_dict['pointIndex']
            if tracenum in valid_tracenums:
                print(f'{tracenum} in valid_tracenums')
                trace_data = all_data['TraceTabs'][tracenum]['dataframe']
                if 0 <= idx < len(trace_data):
                    print(f'{idx} in valid range')
                    trace_data.at[idx, 'color'] = self.selected_color
                else:
                    print(f'{idx} not in valid range')
            else:
                print(f'{tracenum} not in valid_tracenums')
        self.main_window.generate_diagram()
