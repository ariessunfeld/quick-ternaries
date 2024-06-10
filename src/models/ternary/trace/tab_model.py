"""Contains the model for the trace tab scroll area"""

class TabModel:
    def __init__(self):
        self.traces = {}
        self.order = []
        self.tab_counter = 0

    def add_trace(self, trace_data):
        self.tab_counter += 1
        tab_id = str(self.tab_counter)
        self.traces[tab_id] = trace_data
        self.order.append(tab_id)

    def remove_trace(self, identifier):
        if identifier in self.traces:
            del self.traces[identifier]
        if identifier in self.order:
            self.order.remove(identifier)

    def get_trace(self, identifier):
        return self.traces.get(identifier)

    def update_order(self, new_order):
        self.order = new_order

    def get_all_traces(self):
        return {id: self.traces[id] for id in self.order}
    

    def __str__(self):
        return f"""traces: {self.traces},
order: {self.order},
tab_counter: {self.tab_counter}
"""
