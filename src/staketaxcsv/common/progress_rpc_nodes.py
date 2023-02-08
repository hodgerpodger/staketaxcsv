from staketaxcsv.common.progress import Progress


class ProgressRpc(Progress):

    def __init__(self, localconfig, seconds_per_page, seconds_per_tx):
        self.seconds_per_page = seconds_per_page
        self.seconds_per_tx = seconds_per_tx

        super().__init__(localconfig)

    def set_estimate_node(self, node, num_pages, num_txs):
        self.add_stage(node + "_fetch", num_pages, self.seconds_per_page)
        self.add_stage(node + "_normalize", num_txs, self.seconds_per_tx)

    def update_estimate_node(self, node, num_txs):
        self.stages[node + "_normalize"].total_tasks = num_txs
