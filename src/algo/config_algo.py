from common import ExporterTypes as et


class localconfig:

    job = None
    debug = False
    cache = False
    limit = 20000  # max txs
    start_date = None
    end_date = None
    lp_treatment = et.LP_TREATMENT_DEFAULT
    exclude_asas = []
